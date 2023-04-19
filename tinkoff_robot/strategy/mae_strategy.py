from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime

from strategy.base_strategy import *
from stats.visualization import *

from tinkoff.invest import (
    Candle,
    HistoricCandle,
    MarketDataResponse,
    OrderDirection,
    SubscriptionInterval,
)
from helpers.money import Money


class MAEStrategy(TradeStrategyBase):
    request_candles: bool = True
    strategy_id: str = 'mae'

    candle_subscription_interval: SubscriptionInterval = SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE
    order_book_subscription_depth = None
    trades_subscription = None

    short_len: int
    long_len: int
    trade_count: int
    prices = dict[datetime.datetime, Money]
    prev_sign: bool

    def __init__(self, short_len: int = 5, long_len: int = 20, trade_count: int = 1, visualizer: Visualizer = None):
        assert long_len > short_len
        self.short_len = short_len
        self.long_len = long_len
        self.trade_count = trade_count
        self.prices = {}
        self.visualizer = visualizer

    def load_candles(self, candles: list[HistoricCandle]) -> None:
        self.prices = {candle.time.replace(second=0, microsecond=0): Money(candle.close)
                       for candle in candles[-self.long_len:]}
        self.prev_sign = self._long_avg() > self._short_avg()

    def decide(self, market_data: MarketDataResponse, params: TradeStrategyParams) -> StrategyDecision:
        return self.decide_by_candle(market_data.candle, params)

    def decide_by_candle(self, candle: Candle | HistoricCandle, params: TradeStrategyParams) -> StrategyDecision:
        time: datetime = candle.time.replace(second=0, microsecond=0)
        order: RobotTradeOrder | None = None
        if time not in self.prices:  # make order only once a minute (when minutely candle is ready)
            sign = self._long_avg() > self._short_avg()
            if sign != self.prev_sign:
                if sign:
                    if params.instrument_balance > 0:
                        order = RobotTradeOrder(quantity=min(self.trade_count, params.instrument_balance),
                                                direction=OrderDirection.ORDER_DIRECTION_SELL)
                        if self.visualizer:
                            self.visualizer.add_sell(time)
                else:
                    lot_price = Money(candle.close).to_float() * self.instrument_info.lot
                    lots_available = int(params.currency_balance / lot_price)
                    if params.currency_balance >= lot_price:
                        order = RobotTradeOrder(quantity=min(self.trade_count, lots_available),
                                                direction=OrderDirection.ORDER_DIRECTION_BUY)
                        if self.visualizer:
                            self.visualizer.add_buy(time)

            self.prev_sign = sign
        self.prices[time] = Money(candle.close)
        if self.visualizer:
            self.visualizer.add_price(time, Money(candle.close).to_float())
            self.visualizer.update_plot()

        return StrategyDecision(robot_trade_order=order)

    def get_prices_list(self) -> list[Money]:
        # sort by keys and then convert to a list of values
        return list(map(lambda x: x[1], sorted(self.prices.items(), key=lambda x: x[0])))

    def _long_avg(self):
        return sum(float(price) for price in self.get_prices_list()[-self.long_len:]) / self.long_len

    def _short_avg(self):
        return sum(float(price) for price in self.get_prices_list()[-self.short_len:]) / self.short_len
