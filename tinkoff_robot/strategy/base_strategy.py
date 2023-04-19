from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tinkoff.invest import (
    Candle,
    HistoricCandle,
    Instrument,
    MarketDataResponse,
    OrderType,
    OrderDirection,
    OrderState,
    SubscriptionInterval,
)
from helpers.money import Money


@dataclass
class TradeStrategyParams:
    instrument_balance: int
    currency_balance: float
    pending_orders: list[OrderState]


@dataclass
class RobotTradeOrder:
    quantity: int
    direction: OrderDirection
    price: Money | None = None
    order_type: OrderType = OrderType.ORDER_TYPE_MARKET


@dataclass
class StrategyDecision:
    robot_trade_order: RobotTradeOrder | None = None
    cancel_orders: list[OrderState] = field(default_factory=list)


class TradeStrategyBase(ABC):
    instrument_info: Instrument

    @property
    @abstractmethod
    def candle_subscription_interval(self) -> SubscriptionInterval:
        return SubscriptionInterval.SUBSCRIPTION_INTERVAL_ONE_MINUTE

    @property
    @abstractmethod
    def order_book_subscription_depth(self) -> int | None:  # set not None to subscribe robot to order book
        return None

    @property
    @abstractmethod
    def trades_subscription(self) -> bool:  # set True to subscribe robot to trades stream
        return False

    @property
    @abstractmethod
    def strategy_id(self) -> str:
        """
        string representing short strategy name for logger
        """
        raise NotImplementedError()

    def load_instrument_info(self, instrument_info: Instrument):
        self.instrument_info = instrument_info

    def load_candles(self, candles: list[HistoricCandle]) -> None:
        """
        Method used by robot to load historic data
        """
        pass

    @abstractmethod
    def decide(self, market_data: MarketDataResponse, params: TradeStrategyParams) -> StrategyDecision:
        if market_data.candle:
            return self.decide_by_candle(market_data.candle, params)
        return StrategyDecision()

    @abstractmethod
    def decide_by_candle(self, candle: Candle | HistoricCandle, params: TradeStrategyParams) -> StrategyDecision:
        pass
