import logging
from dataclasses import dataclass
from datetime import datetime

from pybacktestchain.broker import Broker, Position
from pybacktestchain.broker import logging
from pybacktestchain.blockchain import Blockchain
from m203mylibrary.option import Option

@dataclass
class OptionPosition:
    """
    Represents an option position (in addition to shares).
    """
    name: str              # Name identifying the option, e.g. “CALL_AAPL_150”.
    option: Option         # Instance of the Option class
    quantity: int          # Number of contracts
    entry_price: float     # Premium by contracts


@dataclass
class ExtendedBroker(Broker):
    
    option_positions: dict = None  

    def __post_init__(self):
        super().__post_init__()  
        if self.option_positions is None:
            self.option_positions = {}

    def buy_option(self, name: str, opt: Option, quantity: int, date: datetime):
        
        # Price with Black Scholes
        premium_unit = opt.black_scholes()
        total_cost = premium_unit * quantity
        
        if self.cash >= total_cost:
            self.cash -= total_cost

            if name in self.option_positions:
                
                existing_pos = self.option_positions[name]
                new_quantity = existing_pos.quantity + quantity
                
                avg_price = ((existing_pos.entry_price * existing_pos.quantity) 
                             + (premium_unit * quantity)) / new_quantity
                existing_pos.quantity = new_quantity
                existing_pos.entry_price = avg_price
            else:
                
                self.option_positions[name] = OptionPosition(
                    name=name,
                    option=opt,
                    quantity=quantity,
                    entry_price=premium_unit
                )

            self.log_transaction(date, 'BUY_OPTION', name, quantity, premium_unit)
        else:
            if self.verbose:
                logging.warning(
                    f"Not enough cash to buy {quantity} of {name}. "
                    f"Needed: {total_cost}, Available: {self.cash}"
                )

    def sell_option(self, name: str, quantity: int, date: datetime):
 
        if name not in self.option_positions:
            if self.verbose:
                logging.warning(f"No option position found for {name}")
            return

        existing_pos = self.option_positions[name]

        if existing_pos.quantity < quantity:
            if self.verbose:
                logging.warning(f"Not enough {name} to sell. Holding {existing_pos.quantity}, asked to sell {quantity}")
            return

        premium_unit = existing_pos.option.black_scholes()
        total_credit = premium_unit * quantity
        self.cash += total_credit

        
        existing_pos.quantity -= quantity
        self.log_transaction(date, 'SELL_OPTION', name, quantity, premium_unit)

        if existing_pos.quantity == 0:
            del self.option_positions[name]

    def get_portfolio_value(self, market_prices: dict) -> float:
        """
        Add options value to the calcul of the portofolio
        """
        
        portfolio_value = super().get_portfolio_value(market_prices)

        
        for name, opt_pos in self.option_positions.items():
            current_price = opt_pos.option.black_scholes()  
            portfolio_value += current_price * opt_pos.quantity

        return portfolio_value