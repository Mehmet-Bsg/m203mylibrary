import yfinance as yf
import pandas as pd
import numpy as np
import logging
import hashlib
import time
import pickle
import os
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from scipy.optimize import minimize

from pybacktestchain.broker import RebalanceFlag, EndOfMonth, StopLoss
from pybacktestchain.utils import generate_random_name

from .commodities_broker import CommodityBroker
from .commodities_data_module import CommoditiesFirstTwoMoments, get_commodities_data, CommoditiesDataModule

# --------------------------------------------------------------------------------
# Rebalance flags (we want end-of-month and contract expiry triggers)
# --------------------------------------------------------------------------------

@dataclass
class EndOfMonthOrExpiry(RebalanceFlag):
    """
    Rebalance if it's end-of-month or if any futures contract expires on date t.
    """
    expiry_column: str = 'futures expiry'

    def new_time_to_rebalance(self, t: datetime, data_slice: pd.DataFrame) -> bool:
        # Check end of month
        eom = EndOfMonth().time_to_rebalance(t)
        # Check expiry
        t_str = t.strftime('%Y-%m-%d')
        expiring = False
        if not data_slice.empty and self.expiry_column in data_slice.columns:
            expiring = (data_slice[self.expiry_column] == t_str).any()
            if not data_slice[data_slice[self.expiry_column] == t_str].empty :
                # Print detailed information about expiring contracts
                print(f"Contracts expiring on {t_str}:")
        return eom or expiring

# --------------------------------------------------------------------------------
# Risk model for stop loss
# --------------------------------------------------------------------------------
@dataclass
class CommodityStopLoss(StopLoss):
    """
    Inherits from old StopLoss if you want to keep the same logic, 
    or override if you need special commodity logic.
    """
    def trigger_stop_loss(self, t: datetime, portfolio: dict, prices: dict, broker: CommodityBroker):
        # The logic is basically the same as original stop loss, but typed for CommodityBroker
        for ticker, position in list(broker.positions.items()):
            entry_price = broker.entry_prices[ticker]
            current_price = prices.get(ticker)
            if current_price is None:
                logging.warning(f"Price for {ticker} not available on {t}")
                continue
            loss = (current_price - entry_price) / entry_price
            if loss < -self.threshold:
                logging.info(f"Stop loss triggered for {ticker} at {t}. Selling all shares.")
                broker.sell(ticker, position.quantity, current_price, t)

# --------------------------------------------------------------------------------
# The CommodityBacktest class
# --------------------------------------------------------------------------------
@dataclass
class CommodityBacktest:
    initial_date: datetime
    final_date: datetime
    universe: list = field(default_factory=lambda: ['CL=F', 'BZ=F', 'NG=F', 'HO=F', 'ZS=F', 'ZW=F', 'ZC=F', 'CC=F'])  # list of commodity tickers
    information_class: type = CommoditiesFirstTwoMoments
    s: timedelta = timedelta(days=360)
    time_column: str = 'Date'
    company_column: str = 'ticker'
    adj_close_column: str = 'Close'
    expiry_column: str = 'futures expiry'  # new
    rebalance_flag: type = EndOfMonthOrExpiry
    risk_model: type = CommodityStopLoss
    initial_cash: float = 1000000.0
    name_blockchain: str = 'commodity_backtest'
    verbose: bool = True

    # We instantiate the broker with the given initial cash
    broker: CommodityBroker = field(init=False)

    def __post_init__(self):
        self.broker = CommodityBroker(cash=self.initial_cash, verbose=self.verbose)
        self.backtest_name = generate_random_name()
        self.broker.initialize_blockchain(self.name_blockchain)

    def run_backtest(self):
        logging.info(f"Running backtest from {self.initial_date} to {self.final_date} for commodities: {self.universe}")
        start_str = self.initial_date.strftime('%Y-%m-%d')
        end_str = self.final_date.strftime('%Y-%m-%d')

        # Retrieve data
        df = get_commodities_data(self.universe, start_str, end_str)
        if df.empty:
            logging.warning("No data retrieved. Backtest aborted.")
            return

        # Create the data module
        data_module = CommoditiesDataModule(df)

        # Create the information object
        info = self.information_class(
            s=self.s,
            data_module=data_module,
            time_column=self.time_column,
            company_column=self.company_column,
            adj_close_column=self.adj_close_column,
            expiry_column=self.expiry_column
        )

        # Initialize risk model
        rm = self.risk_model(threshold=0.1)

        # Rebalance flag
        rebal_flag = self.rebalance_flag(expiry_column=self.expiry_column)

        # Main loop
        for t in pd.date_range(start=self.initial_date, end=self.final_date, freq='D'):
            # Check if we need to handle stop losses
            # (Stop losses can happen any day, not only on rebal day)
            prices = info.get_prices(t)
            portfolio_snapshot = {}  # not used by default in stop loss, but let's keep the interface
            rm.trigger_stop_loss(t, portfolio_snapshot, prices, self.broker)

            # Decide if we rebalance
            # For expiry logic, we also want to SELL any contract that expires on t before re-allocation.
            data_slice = info.slice_data(t)

            # SELL all expiring positions before rebal
            # Check positions if they are expiring on day t
            for ticker, pos in list(self.broker.positions.items()):
                if pos.expiry_date == t.strftime('%Y-%m-%d'):
                    # Sell the entire position
                    if ticker in prices and prices[ticker] is not None:
                        logging.info(f"{ticker} contract expires on {t}, selling all shares.")
                        self.broker.sell(ticker, pos.quantity, prices[ticker], t)

            # Now, if it's a rebal day, re-compute the optimal portfolio
            if rebal_flag.new_time_to_rebalance(t, data_slice):
                logging.info("-----------------------------------")
                logging.info(f"Rebalancing portfolio at {t}")
                information_set = info.compute_information(t)
                portfolio = info.compute_portfolio(t, information_set)
                # Execute trades
                self.broker.execute_portfolio(portfolio, prices, t)

        # End of the backtest
        final_prices = info.get_prices(self.final_date)
        final_value = self.broker.get_portfolio_value(final_prices)
        logging.info(f"Backtest completed. Final portfolio value: {final_value}")

        # Transaction log
        df_log = self.broker.get_transaction_log()

        # Save the transaction log
        if not os.path.exists('backtests'):
            os.makedirs('backtests')
        csv_name = f"backtests/{self.backtest_name}.csv"
        df_log.to_csv(csv_name, index=False)
        logging.info(f"Transaction log saved to {csv_name}")

        # Store the backtest results in the blockchain
        self.broker.blockchain.add_block(self.backtest_name, df_log.to_string())

        return df_log

# Example usage (commented out; you can uncomment and run):
# if __name__ == '__main__':
#     backtest = CommodityBacktest(
#         initial_date=datetime(2023, 1, 1),
#         final_date=datetime(2023, 3, 1),
#         universe=['CL=F', 'NG=F', 'ZC=F']
#     )
#     result_log = backtest.run_backtest()
#     print(result_log)
