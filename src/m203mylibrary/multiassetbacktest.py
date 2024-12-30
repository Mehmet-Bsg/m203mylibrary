from pybacktestchain.broker import Backtest  # Import the existing class
from pybacktestchain.utils import generate_random_name
from pybacktestchain.blockchain import Block, Blockchain

from commodities_module import CommoditiesDataModule, CommoditiesInformation, get_commodities_data
import pandas as pd
import os
import logging

class MultiAssetBacktest(Backtest):
    def __init__(self, initial_date, final_date, asset_type='stocks', **kwargs):
        """
        Initialize the backtest for stocks or commodities.

        Args:
            initial_date (datetime): Start date of the backtest.
            final_date (datetime): End date of the backtest.
            asset_type (str): Type of assets to backtest ('stocks' or 'commodities').
            **kwargs: Additional arguments passed to the parent class.
        """
        super().__init__(initial_date, final_date, **kwargs)
        self.asset_type = asset_type.lower()  # Normalize to lowercase
        if self.asset_type not in ['stocks', 'commodities']:
            raise ValueError("`asset_type` must be 'stocks' or 'commodities'.")

    def run_backtest(self):
        """
        Execute the backtest based on the selected asset type.
        """
        if self.asset_type == 'stocks':
            self.run_stock_backtest()
        elif self.asset_type == 'commodities':
            self.run_commodities_backtest()

    def run_stock_backtest(self):
        """
        Execute the backtest for a stock portfolio.
        """
        logging.info("Running stock backtest...")
        super().run_backtest()  # Call the logic already implemented for stocks

    def run_commodities_backtest(self):
        """
        Execute the backtest for a commodities portfolio.
        """
        logging.info(f"Running commodities backtest from {self.initial_date} to {self.final_date}.")
        logging.info(f"Retrieving price data and contracts expiry for commodities futures universe")
        self.risk_model = self.risk_model(threshold=0.1)
        # self.initial_date to yyyy-mm-dd format
        init_ = self.initial_date.strftime('%Y-%m-%d')
        # self.final_date to yyyy-mm-dd format
        final_ = self.final_date.strftime('%Y-%m-%d')
        df = get_commodities_data (self.universe, init_, final_)

        # Initialize the DataModule
        commodities_data_module = CommoditiesDataModule(df)

        # Create the Information object
        info = CommoditiesInformation(s = self.s, 
                                    data_module = commodities_data_module,
                                    time_column=self.time_column,
                                    commodity_column=self.commodity_column,
                                    adj_close_column=self.adj_close_column)
        
        # Run the backtest
        for t in pd.date_range(start=self.initial_date, end=self.final_date, freq='D'):
            
            if self.risk_model is not None:
                portfolio = info.compute_portfolio(t, info.compute_information(t))
                prices = info.get_prices(t)
                self.risk_model.trigger_stop_loss(t, portfolio, prices, self.broker)
           
            if self.rebalance_flag().time_to_rebalance(t) or self.has_expired_contracts(commodities_data_module, t):
                logging.info("-----------------------------------")
                logging.info(f"Rebalancing portfolio at {t}")
                information_set = info.compute_information(t)
                portfolio = info.compute_portfolio(t, information_set)
                self.broker.sell_expired_contracts(t, prices)  # Sell expired contracts
                self.broker.execute_portfolio(portfolio, prices, t)

        logging.info(f"Backtest completed. Final portfolio value: {self.broker.get_portfolio_value(info.get_prices(self.final_date))}")
        df = self.broker.get_transaction_log()

        # create backtests folder if it does not exist
        if not os.path.exists('backtests'):
            os.makedirs('backtests')

        # save to csv, use the backtest name 
        df.to_csv(f"backtests/{self.backtest_name}.csv")

        # store the backtest in the blockchain
        self.broker.blockchain.add_block(self.backtest_name, df.to_string())