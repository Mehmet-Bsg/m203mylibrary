from m203mylibrary.commodities_data_module import get_futures_expiry
from m203mylibrary.commodities_data_module import get_commodity_data
from m203mylibrary.commodities_backtest import CommodityBacktest
from m203mylibrary.multi_asset_backtest import UniversalBacktest
from datetime import datetime, timedelta
import pandas as pd

def test_get_futures_expiry():
    """Test the expiry date calculation for futures."""
    buy_date = "2024-12-15"
    ticker = "CL=F"
    expected_expiry = "2024-12-20"  # Adjusted to nearest business day
    actual_expiry = get_futures_expiry(buy_date, ticker)
    assert actual_expiry == expected_expiry, f"Expected {expected_expiry}, but got {actual_expiry}."

def test_get_commodity_data():
    """Test fetching historical data for a commodity."""
    ticker = "CL=F"
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    data = get_commodity_data(ticker, start_date, end_date)
    assert not data.empty, "Dataframe is empty; expected historical data."
    assert "futures expiry" in data.columns, "Expected 'futures expiry' column in data."


def test_universal_backtest():
    backtest = UniversalBacktest(
        initial_date=datetime(2005, 1, 1),
        final_date=datetime(2022, 12, 31),
        asset_class="commodities",
        universe=['CL=F'],
        name_blockchain = 'test_blockchain1',
    )
    result = backtest.run_backtest()
    assert result is not None, "Backtest returned no results."


def test_universal_backtest():
    backtest = UniversalBacktest(
        initial_date=datetime(2020, 1, 1),
        final_date=datetime(2022, 12, 31),
        asset_class="commodities",
        universe=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'INTC', 'CSCO', 'NFLX'],
        name_blockchain = 'test_blockchain2',
    )
    result = backtest.run_backtest()
    assert result is not None, "Backtest returned no results."


def test_calculate_performance():
    """Test the calculate_performance method."""
    # Load sample transaction log
    test_data = pd.read_csv("tests/test.csv")
    
    # Create a mock UniversalBacktest instance (or pass required params)
    universal_backtest = UniversalBacktest(
        initial_date="2023-01-01",
        final_date="2023-01-15",
        asset_class="stocks"
    )

    # Call the private method (using underscore for access)
    performance = universal_backtest._calculate_performance(test_data)
    
    # Assert portfolio value calculation
    assert not performance.empty, "Performance DataFrame is empty"
    assert "Portfolio Value" in performance.columns, "Portfolio Value column missing"


def test_commodity_backtest():
    """Test the CommodityBacktest class."""
    # Initialize a backtest instance for commodities
    backtest = CommodityBacktest(
        initial_date=datetime(2023, 1, 1),
        final_date=datetime(2023, 3, 31),
        universe=["CL=F", "NG=F"],  # Crude Oil and Natural Gas
        initial_cash=50000,
        verbose=False
    )

    # Run the backtest
    result = backtest.run_backtest()

    # Assert result is not None
    assert result is not None, "Commodity backtest did not return results"



