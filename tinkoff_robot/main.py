import datetime

from lib.robot_factory import TradingRobotFactory
from strategy.base_strategy import TradeStrategyParams
from strategy.mae_strategy import MAEStrategy
from stats.visualization import Visualizer

token = "t.79UrkCV6A20DjSJ40yep3S_BTgbmmuXrPJoiH4udJ1UdMORlCVi6GxzvdDHtGVsSaMLQiblyqXaYOat6bYkzCA"
account_id = "2063742726"


def backtest(robot):
    stats = robot.backtest(
        TradeStrategyParams(instrument_balance=0, currency_balance=15000, pending_orders=[]),
        train_duration=datetime.timedelta(days=5), test_duration=datetime.timedelta(days=30))
    stats.save_to_file('backtest_stats.pickle')


def trade(robot):
    stats = robot.trade()
    stats.save_to_file('stats.pickle')


def main():
    robot_factory = TradingRobotFactory(token=token, account_id=account_id, ticker='YNDX', class_code='TQBR',
                                        logger_level='INFO')
    robot_factory.get_account_info()
    robot = robot_factory.create_robot(MAEStrategy(visualizer=Visualizer('YNDX', 'RUB')), sandbox_mode=True)

    # backtest(robot)

    trade(robot)


if __name__ == '__main__':
    main()