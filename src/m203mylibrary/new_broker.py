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


