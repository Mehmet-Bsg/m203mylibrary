from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from m203mylibrary.option import Option
from pybacktestchain.broker import Broker

@dataclass
class OptionPosition:
    """
    Represents an option position (in addition to shares).
    """
    name: str              # Name identifying the option, e.g. "CALL_AAPL_150".
    option: Option         # Instance of the Option class
    quantity: int          # Number of contracts
    entry_price: float     # Premium by contracts

@dataclass
class ExtendedBroker(Broker):
    option_positions: Dict[str, OptionPosition] = None  # Dictionary to handle options

    def __post_init__(self):
        super().__post_init__()
        if self.option_positions is None:
            self.option_positions = {}

    def buy_option(self, name: str, opt: Option, quantity: int, date: datetime):
        """Buy an option and deduct its premium from cash."""
        # Price with Black-Scholes
        premium_unit = opt.black_scholes()
        total_cost = premium_unit * quantity

        if self.cash < total_cost:
            raise ValueError("Not enough cash to buy the option.")

        self.cash -= total_cost

        if name in self.option_positions:
            existing_pos = self.option_positions[name]
            new_quantity = existing_pos.quantity + quantity
            avg_price = ((existing_pos.entry_price * existing_pos.quantity) + (premium_unit * quantity)) / new_quantity
            existing_pos.quantity = new_quantity
            existing_pos.entry_price = avg_price
        else:
            self.option_positions[name] = OptionPosition(name, opt, quantity, premium_unit)

        if self.verbose:
            print(f"Bought {opt.option_type} option {name} with strike {opt.strike_price} expiring {opt.expiration_date}.")

    def sell_option(self, name: str, quantity: int, premium_unit: float):
        """Sell an option and add the premium to cash."""
        if name not in self.option_positions:
            raise ValueError("Option not found in portfolio.")

        existing_pos = self.option_positions[name]
        if quantity > existing_pos.quantity:
            raise ValueError("Cannot sell more options than held.")

        self.cash += premium_unit * quantity
        existing_pos.quantity -= quantity

        if existing_pos.quantity == 0:
            del self.option_positions[name]

        if self.verbose:
            print(f"Sold {quantity} contracts of option {name} for {premium_unit * quantity}.")

    def evaluate_options(self, current_date: datetime):
        """Evaluate and remove expired options."""
        expired = [name for name, pos in self.option_positions.items() if pos.option.is_expired(current_date)]
        for name in expired:
            del self.option_positions[name]
            if self.verbose:
                print(f"Option {name} expired and was removed from the portfolio.")
