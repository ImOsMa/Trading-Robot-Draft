import logging
import sys

from tinkoff.invest import (
    AccessLevel,
    AccountStatus,
    AccountType,
    Client,
    InstrumentIdType,
)

from tinkoff.invest.exceptions import InvestError

from strategy.base_strategy import *
from stats.analyzer import TradeStatisticsAnalyzer
from helpers.money import Money
from lib.trading_robot import TradingRobot


class TradingRobotFactory:
    APP_NAME = 'trading_robot'
    instrument_info: Instrument
    token: str
    account_id: str
    logger: logging.Logger
    sandbox_mode: bool

    def __init__(self, token: str, account_id: str, figi: str = None,  # pylint:disable=too-many-arguments
                 ticker: str = None, class_code: str = None, logger_level: int | str = 'INFO'):
        self.instrument_info = self._get_instrument_info(token, figi, ticker, class_code).instrument
        self.token = token
        self.account_id = account_id
        self.logger = self.setup_logger(logger_level)
        self.sandbox_mode = self._validate_account(token, account_id, self.logger)

    def setup_logger(self, logger_level: int | str):
        logger = logging.getLogger(f'robot.{self.instrument_info.ticker}')
        logger.setLevel(logger_level)
        formatter = logging.Formatter(fmt=('%(asctime)s %(levelname)s: %(message)s'))  # todo: fixit
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def create_robot(self, trade_strategy: TradeStrategyBase, sandbox_mode: bool = True) -> TradingRobot:
        money, positions = self._get_current_postitions()
        trade_strategy.load_instrument_info(self.instrument_info)
        stats = TradeStatisticsAnalyzer(
            positions=positions,
            money=money.to_float(),  # todo: change to Money
            instrument_info=self.instrument_info,
            logger=self.logger.getChild(trade_strategy.strategy_id).getChild('stats')
        )
        return TradingRobot(token=self.token, account_id=self.account_id, sandbox_mode=sandbox_mode,
                            trade_strategy=trade_strategy, trade_statistics=stats, instrument_info=self.instrument_info,
                            logger=self.logger.getChild(trade_strategy.strategy_id))

    def _get_current_postitions(self) -> tuple[Money, int]:
        # amount of money and instrument balance
        with Client(self.token, app_name=self.APP_NAME) as client:
            positions = client.operations.get_positions(account_id=self.account_id)

            instruments = [sec for sec in positions.securities if sec.figi == self.instrument_info.figi]
            if len(instruments) > 0:
                instrument = instruments[0].balance
            else:
                instrument = 0

            moneys = [m for m in positions.money if m.currency == self.instrument_info.currency]
            if len(moneys) > 0:
                money = Money(moneys[0].units, moneys[0].nano)
            else:
                money = Money(0, 0)

            return money, instrument

    @staticmethod
    def _validate_account(token: str, account_id: str, logger: logging.Logger) -> bool:
        try:
            with Client(token, app_name=TradingRobotFactory.APP_NAME) as client:
                accounts = [acc for acc in client.users.get_accounts().accounts if acc.id == account_id]
                sandbox_mode = False
                if len(accounts) == 0:
                    sandbox_mode = True
                    accounts = [acc for acc in client.sandbox.get_sandbox_accounts().accounts if acc.id == account_id]
                    if len(accounts) == 0:
                        logger.error(f'Account {account_id} not found.')
                        raise ValueError('Account not found')

                account = accounts[0]
                if account.type not in [AccountType.ACCOUNT_TYPE_TINKOFF, AccountType.ACCOUNT_TYPE_INVEST_BOX]:
                    logger.error(f'Account type {account.type} is not supported')
                    raise ValueError('Unsupported account type')
                if account.status != AccountStatus.ACCOUNT_STATUS_OPEN:
                    logger.error(f'Account status {account.status} is not supported')
                    raise ValueError('Unsupported account status')
                if account.access_level != AccessLevel.ACCOUNT_ACCESS_LEVEL_FULL_ACCESS:
                    logger.error(f'No access to account. Current level is {account.access_level}')
                    raise ValueError('Insufficient access level')
                return sandbox_mode

        except InvestError as error:
            logger.error(f'Failed to validate account. Exception: {error}')
            raise error

    @staticmethod
    def _get_instrument_info(token: str, figi: str = None, ticker: str = None, class_code: str = None):
        with Client(token, app_name=TradingRobotFactory.APP_NAME) as client:
            if figi is None:
                if ticker is None or class_code is None:
                    raise ValueError('figi or both ticker and class_code must be not None')
                return client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                            class_code=class_code, id=ticker)
            return client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi)

    def get_account_info(self):
        with Client(self.token, app_name=TradingRobotFactory.APP_NAME) as client:
            info = client.users.get_info()
            print(info)
            portfolio = client.operations.get_positions(account_id=self.account_id)
            print(portfolio)
