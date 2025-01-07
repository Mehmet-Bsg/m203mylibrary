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

from pybacktestchain.broker import Position, Broker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --------------------------------------------------------------------------------
# New Broker and execution logic
# --------------------------------------------------------------------------------

@dataclass
class CommodityPosition(Position):
    """
    Extends Position with an expiry_date field for futures.
    """
    expiry_date: str = None

@dataclass
class CommodityBroker(Broker):
    """
    Inherits from the Broker class
    We store an expiry_date in our CommodityPosition.
    """
    def buy(self, ticker: str, quantity: int, price: float, date: datetime, expiry_date: str = None):
        total_cost = price * quantity
        if self.cash >= total_cost:
            self.cash -= total_cost
            if ticker in self.positions:
                position = self.positions[ticker]
                new_quantity = position.quantity + quantity
                if new_quantity > 0:  # To avoid a division by 0
                    new_entry_price = ((position.entry_price * position.quantity) + (price * quantity)) / new_quantity
                    position.quantity = new_quantity
                    position.entry_price = new_entry_price
                else:
                    # If new_quantity is null, don't update entry
                    logging.warning(f"Invalid trade for {ticker}: resulting quantity is zero.")
                # Update expiry if needed
                if expiry_date:
                    position.expiry_date = expiry_date
            else:
                self.positions[ticker] = CommodityPosition(ticker, quantity, price, expiry_date=expiry_date)
            self.log_transaction(date, 'BUY', ticker, quantity, price)
            self.entry_prices[ticker] = price
        else:
            if self.verbose:
                logging.warning(f"Not enough cash to buy {quantity} shares of {ticker} at {price}. Available cash: {self.cash}")
