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
import matplotlib.pyplot as plt

from pybacktestchain.broker import Backtest, EndOfMonth, StopLoss, Broker
from pybacktestchain.utils import generate_random_name
from pybacktestchain.blockchain import Block, Blockchain
from pybacktestchain.data_module import FirstTwoMoments

from .commodities_backtest import CommodityBacktest, EndOfMonthOrExpiry, CommodityStopLoss
from .commodities_broker import CommodityBroker
from .commodities_data_module import CommoditiesFirstTwoMoments

from .commodities_backtest import CommodityBacktest

# --------------------------------------------------------------------------------
# The universal backtest class
# --------------------------------------------------------------------------------


# Define class-specific defaults
class_defaults = {
    "stocks": {
        "backtest_class": Backtest,
        "universe": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'INTC', 'CSCO', 'NFLX'],
        "information_class" : FirstTwoMoments,
        "adj_close_column": "Adj Close",
        "rebalance_flag": EndOfMonth,
        "risk_model": StopLoss,
        "broker_class": Broker,
        "name_blockchain" : 'backtest'
    },
    "commodities": {
        "backtest_class": CommodityBacktest,
        "universe": ['CL=F', 'BZ=F', 'NG=F', 'HO=F', 'ZS=F', 'ZW=F', 'ZC=F', 'CC=F'],
        "information_class" : CommoditiesFirstTwoMoments,
        "adj_close_column": "Close",
        "rebalance_flag": EndOfMonthOrExpiry,
        "risk_model": CommodityStopLoss,
        "broker_class": CommodityBroker,
        "name_blockchain" : 'commodity_backtest',
        "expiry_column": "futures expiry",  # Specific to commodities
    },
}

@dataclass
class UniversalBacktest:
    initial_date: datetime
    final_date: datetime
    asset_class: str  # "stocks" or "commodities"
    initial_cash: float = 1000000.0
    verbose: bool = True

    # Optional overrides
    universe: list = None
    rebalance_flag: type = None
    risk_model: type = None
    adj_close_column: str = None
    information_class: str = None
    name_blockchain: str = None
    expiry_column: str = None  # Specific to commodities

    def _get_default_attributes(self):
        """
        Fetch default attributes based on the asset class.
        """
        if self.asset_class not in class_defaults:
            raise ValueError(f"Unsupported asset class: {self.asset_class}")
        return class_defaults[self.asset_class]

    def _calculate_performance(self, df_res):
        """
        Calculate portfolio performance over time from the transaction log.
        """
        # Initialize variables
        cash = 0
        holdings = {}
        performance_data = []

        # Iterate through the transaction log
        for _, row in df_res.iterrows():
            date = row['Date']
            action = row['Action']
            ticker = row['Ticker']
            quantity = row['Quantity']
            price = row['Price']
            cash = row['Cash']  # Update cash from the log

            # Update holdings based on the action
            if action == 'BUY':
                holdings[ticker] = holdings.get(ticker, 0) + quantity
            elif action == 'SELL':
                holdings[ticker] = holdings.get(ticker, 0) - quantity
                if holdings[ticker] <= 0:
                    del holdings[ticker]  # Remove if quantity is zero

            # Calculate total value of holdings
            holdings_value = sum(qty * price for ticker, qty in holdings.items())
            total_value = cash + holdings_value

            # Save performance data
            performance_data.append({'Date': date, 'Portfolio Value': total_value})

        # Convert to DataFrame and return
        return pd.DataFrame(performance_data)
    
    def _plot_performance(self, performance_df):
        """
        Plot portfolio performance metrics over time.
        """
        plt.figure(figsize=(12, 8))

        # Plot each metric
        plt.plot(performance_df['Date'], performance_df['Portfolio Value'], label='Portfolio Value', marker='o', linewidth=2)

        # Add labels, title, and legend
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Portfolio Performance Metrics Over Time')
        plt.legend()
        plt.grid(True)

        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)

        # Adjust layout
        plt.tight_layout()
        plt.show()

    def run_backtest(self):
        # Fetch class-specific defaults
        defaults = self._get_default_attributes()

        # Resolve attributes with user overrides
        universe = self.universe or defaults["universe"]
        adj_close_column = self.adj_close_column or defaults["adj_close_column"]
        rebalance_flag = self.rebalance_flag or defaults["rebalance_flag"]
        risk_model = self.risk_model or defaults["risk_model"]
        information_class = self.information_class or defaults["information_class"]
        name_blockchain = self.name_blockchain or defaults["name_blockchain"]

        # Include expiry_column only for commodities
        extra_attributes = {}
        if self.asset_class == "commodities":
            extra_attributes["expiry_column"] = self.expiry_column or defaults.get("expiry_column")

        # Initialize the backtest
        backtest_class = defaults["backtest_class"]
        backtest_instance = backtest_class(
            initial_date=self.initial_date,
            final_date=self.final_date,
            initial_cash=self.initial_cash,
            verbose=self.verbose,
            information_class = information_class,
            adj_close_column=adj_close_column,
            rebalance_flag=rebalance_flag,
            risk_model=risk_model,
            name_blockchain = name_blockchain,
            **extra_attributes,
        )
        backtest_instance.universe = universe
        # Run the backtest
        backtest_instance.run_backtest()
        df_res = pd.read_csv(f"backtests/{backtest_instance.backtest_name}.csv")

        portfolio_performance = self._calculate_performance(df_res)
        self._plot_performance(portfolio_performance)

        return df_res

# --------------------------------------------------------------------------------
# Some examples
# --------------------------------------------------------------------------------

# Example 1: Run a stock backtest with default settings
#if __name__ == '__main__':
#    verbose = True  # Set to False to suppress logging output
#
#    # Initialize UniversalBacktest for stocks
#    universal_backtest = UniversalBacktest(
#        initial_date=datetime(2019, 1, 1),
#        final_date=datetime(2020, 1, 1),
#        asset_class="stocks",
#        verbose=verbose
#    )

    # Run the backtest
#    result_log = universal_backtest.run_backtest()
#    print(result_log)

# Example 2: Custom commodity backtest with a specific universe 
#if __name__ == '__main__':
#    verbose = True  # Suppress logging output

    # Initialize UniversalBacktest with a custom universe
#    universal_backtest = UniversalBacktest(
#        initial_date=datetime(2022, 1, 1),
#        final_date=datetime(2023, 1, 1),
#        asset_class="commodities",
#        universe=["CL=F", "NG=F", "HO=F"],  # Custom commodity tickers
#        verbose=verbose
#    )

    # Run the backtest
#    result_log = universal_backtest.run_backtest()
#    print(result_log)