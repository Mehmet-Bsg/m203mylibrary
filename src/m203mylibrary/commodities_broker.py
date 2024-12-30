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

from commodities_blockchain import Blockchain

@dataclass
class CommodityPosition:
    ticker: str
    quantity: int
    entry_price: float
    expiry_date: str = None  # Store the expiry date for the position

@dataclass
class CommodityBroker:
    cash: float
    positions: dict = None
    transaction_log: pd.DataFrame = None
    entry_prices: dict = None
    verbose: bool = True

    def initialize_blockchain(self, name: str):
        if not os.path.exists('blockchain'):
            os.makedirs('blockchain')
        chains = os.listdir('blockchain')
        ending = f'{name}.pkl'
        if ending in chains:
            if self.verbose:
                logging.warning(f"Blockchain with name {name} already exists. Loading it from disk.")
            with open(f'blockchain/{name}.pkl', 'rb') as f:
                self.blockchain = pickle.load(f)
            return

        self.blockchain = Blockchain(name)
        self.blockchain.store()
        if self.verbose:
            logging.info(f"Blockchain with name {name} initialized and stored.")

    def __post_init__(self):
        if self.positions is None:
            self.positions = {}
        if self.transaction_log is None:
            self.transaction_log = pd.DataFrame(columns=['Date', 'Action', 'Ticker', 'Quantity', 'Price', 'Cash'])
        if self.entry_prices is None:
            self.entry_prices = {}

    def buy(self, ticker: str, quantity: int, price: float, date: datetime, expiry_date: str = None):
        total_cost = price * quantity
        if self.cash >= total_cost:
            self.cash -= total_cost
            if ticker in self.positions:
                position = self.positions[ticker]
                new_quantity = position.quantity + quantity
                new_entry_price = ((position.entry_price * position.quantity) + (price * quantity)) / new_quantity
                position.quantity = new_quantity
                position.entry_price = new_entry_price
                # Update expiry
                if expiry_date:
                    position.expiry_date = expiry_date
            else:
                self.positions[ticker] = CommodityPosition(ticker, quantity, price, expiry_date=expiry_date)
            self.log_transaction(date, 'BUY', ticker, quantity, price)
            self.entry_prices[ticker] = price
        else:
            if self.verbose:
                logging.warning(f"Not enough cash to buy {quantity} shares of {ticker} at {price}. Available cash: {self.cash}")

    def sell(self, ticker: str, quantity: int, price: float, date: datetime):
        if ticker in self.positions and self.positions[ticker].quantity >= quantity:
            position = self.positions[ticker]
            position.quantity -= quantity
            self.cash += price * quantity

            if position.quantity == 0:
                del self.positions[ticker]
                if ticker in self.entry_prices:
                    del self.entry_prices[ticker]
            self.log_transaction(date, 'SELL', ticker, quantity, price)
        else:
            if self.verbose:
                logging.warning(f"Not enough shares to sell {quantity} shares of {ticker}.")

    def log_transaction(self, date, action, ticker, quantity, price):
        transaction = pd.DataFrame([{
            'Date': date,
            'Action': action,
            'Ticker': ticker,
            'Quantity': quantity,
            'Price': price,
            'Cash': self.cash
        }])
        self.transaction_log = pd.concat([self.transaction_log, transaction], ignore_index=True)

    def get_cash_balance(self):
        return self.cash

    def get_portfolio_value(self, market_prices: dict):
        portfolio_value = self.cash
        for tkr, pos in self.positions.items():
            if tkr in market_prices and market_prices[tkr] is not None:
                portfolio_value += pos.quantity * market_prices[tkr]
        return portfolio_value

    def execute_portfolio(self, portfolio: dict, prices: dict, date: datetime):
        """
        Rebalance the portfolio to match the target weights in `portfolio`,
        selling first, then buying.
        """
        # First, handle sells
        for tkr, weight in portfolio.items():
            price = prices.get(tkr)
            if price is None:
                if self.verbose:
                    logging.warning(f"Price for {tkr} not available on {date}")
                continue

            total_value = self.get_portfolio_value(prices)
            target_value = total_value * weight
            current_value = self.positions.get(tkr, CommodityPosition(tkr, 0, 0.0)).quantity * price
            diff_value = target_value - current_value
            quantity_to_trade = int(diff_value / price)

            if quantity_to_trade < 0:
                self.sell(tkr, abs(quantity_to_trade), price, date)

        # Next, handle buys
        for tkr, weight in portfolio.items():
            price = prices.get(tkr)
            if price is None:
                continue

            total_value = self.get_portfolio_value(prices)
            target_value = total_value * weight
            current_value = self.positions.get(tkr, CommodityPosition(tkr, 0, 0.0)).quantity * price
            diff_value = target_value - current_value
            quantity_to_trade = int(diff_value / price)

            if quantity_to_trade > 0:
                available_cash = self.get_cash_balance()
                cost = quantity_to_trade * price
                if cost <= available_cash:
                    
                    expiry_date = None

                    self.buy(tkr, quantity_to_trade, price, date, expiry_date=expiry_date)
                else:
                    # partial buy
                    if self.verbose:
                        logging.warning(f"Not enough cash to buy {quantity_to_trade} of {tkr}. Buying partial.")
                    quantity_to_trade = int(available_cash / price)
                    self.buy(tkr, quantity_to_trade, price, date)

    def get_transaction_log(self):
        return self.transaction_log