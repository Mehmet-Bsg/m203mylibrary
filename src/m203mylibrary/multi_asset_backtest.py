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


from pybacktestchain.broker import Backtest, EndOfMonth, StopLoss, Broker
from pybacktestchain.utils import generate_random_name
from pybacktestchain.blockchain import Block, Blockchain
from pybacktestchain.data_module import FirstTwoMoments

from commodities_backtest import CommodityBacktest, EndOfMonthOrExpiry, CommodityStopLoss
from commodities_broker import CommodityBroker
from commodities_data_module import CommoditiesFirstTwoMoments

from commodities_backtest import CommodityBacktest

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
    },
    "commodities": {
        "backtest_class": CommodityBacktest,
        "universe": ['CL=F', 'BZ=F', 'NG=F', 'HO=F', 'ZS=F', 'ZW=F', 'ZC=F', 'CC=F'],
        "information_class" : CommoditiesFirstTwoMoments,
        "adj_close_column": "Close",
        "rebalance_flag": EndOfMonthOrExpiry,
        "risk_model": CommodityStopLoss,
        "broker_class": CommodityBroker,
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
    expiry_column: str = None  # Specific to commodities

    def _get_default_attributes(self):
        """
        Fetch default attributes based on the asset class.
        """
        if self.asset_class not in class_defaults:
            raise ValueError(f"Unsupported asset class: {self.asset_class}")
        return class_defaults[self.asset_class]

    def run_backtest(self):
        # Fetch class-specific defaults
        defaults = self._get_default_attributes()

        # Resolve attributes with user overrides
        universe = self.universe or defaults["universe"]
        adj_close_column = self.adj_close_column or defaults["adj_close_column"]
        rebalance_flag = self.rebalance_flag or defaults["rebalance_flag"]
        risk_model = self.risk_model or defaults["risk_model"]
        information_class = self.information_class or defaults["information_class"]

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
            **extra_attributes,
        )
        backtest_instance.universe = universe
        # Run the backtest
        result_log = backtest_instance.run_backtest()

        return result_log


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