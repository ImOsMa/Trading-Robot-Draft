import math
from random import random

from strategy.base_strategy import *

from tinkoff.invest import (
    Candle,
    HistoricCandle,
    MarketDataResponse,
    Quotation,
    OrderDirection,
)

class RandomStrategy(TradeStrategyBase):
    request_candles: bool = True
    strategy_id: str = 'random'

    low: int
    high: int

    def __init__(self, low: int, high: int):
        self.low = low
        self.high = high

    def decide(self, market_data: MarketDataResponse, params: TradeStrategyParams) -> StrategyDecision:
        return self.decide_by_candle(market_data.candle, params)

    def decide_by_candle(self, candle: Candle | HistoricCandle, params: TradeStrategyParams) -> StrategyDecision:
        low = max(self.low, -params.instrument_balance)
        high = min(self.high, math.floor(params.currency_balance / self.convert_quotation(candle.close)))

        quantity = random.randint(low, high)
        direction = OrderDirection.ORDER_DIRECTION_BUY if quantity > 0 else OrderDirection.ORDER_DIRECTION_SELL

        return StrategyDecision(RobotTradeOrder(quantity=quantity, direction=direction))

    @staticmethod
    def convert_quotation(amount: Quotation) -> float | None:
        if amount is None:
            return None
        return amount.units + amount.nano / (10 ** 9)
