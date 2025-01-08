
# m203BacktestLibrary

`m203BacktestLibrary` is a Python package that extends the functionality of the `pybacktestchain` library by introducing commodity futures contracts. The library introduces new features like handling futures expirations, a universal backtest class and performance plotting.

## What's New

### Futures Expiration Logic

The library introduces a methodology for managing futures contracts by:
- Calculating expiry dates for multiple commodity types, including energy, soft commodities, and metals.
- Implementing automatic rollover logic when contracts near expiration.
- Introducing distinct handling for energy commodities (e.g., Crude Oil, Natural Gas) and CBOT agricultural products (e.g., Soybean, Corn).
- Adjusting expiry dates to ensure they align with business days and accounting for specific market conventions.

This ensures that backtests reflect real-world trading scenarios where contracts expire and roll over to the next available month. It is also a methodology that make it possible to deal with yahoo finance data which is free but not really extensive for commodities, hence building expiry dates from available data.

### Universal Backtest Framework

The new `UniversalBacktest` class provides:
- A unified interface for running backtests across stocks and commodities portofolios.
- Customizable inputs for the trading universe, risk models, rebalancing flags, and time intervals.
- Support for commodity-specific features (futures expiry handling).
- An integrated performance tracking and plotting feature.

### Portfolio Performance Visualization

Performance metrics are now with the `UniversalBacktest` class. This feature enables:
- Visualization of portfolio value, cash balance, and holdings value over time.
- A clearer understanding of how the strategy evolves during the backtest period.

---

## Installation

```bash
$ pip install m203backtestlibrary
```

---

## Usage

### Universal Backtest

The `UniversalBacktest` class is the centerpiece of the library, offering an enhanced backtesting framework. Below is a detailed explanation of its inputs and functionality.

#### Input Parameters

- `initial_date` (datetime): The start date of the backtest.
- `final_date` (datetime): The end date of the backtest.
- `asset_class` (str): Specify `"stocks"` or `"commodities"`.
- `initial_cash` (float, default=1,000,000): The initial capital for the backtest.
- `verbose` (bool, default=True): Enables detailed logging of operations.
- `universe` (list, optional): A list of tickers to include in the backtest. Defaults:
  - For stocks: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'INTC', 'CSCO', 'NFLX'].
  - For commodities: ['CL=F', 'BZ=F', 'NG=F', 'HO=F', 'ZS=F', 'ZW=F', 'ZC=F', 'CC=F'].
- `rebalance_flag` (type, optional): Rebalancing logic. Defaults:
  - `EndOfMonth` for stocks.
  - `EndOfMonthOrExpiry` for commodities.
- `risk_model` (type, optional): Risk management logic. Defaults:
  - `StopLoss` for stocks.
  - `CommodityStopLoss` for commodities.
- `adj_close_column` (str, optional): Column used for price adjustments (default: `"Adj Close"` for stocks, `"Close"` for commodities).
- `expiry_column` (str, optional): Specific to commodities; specifies the column for futures expiry.

#### Example Usage

1. **Stock Backtest**

```python
from m203backtestlibrary import UniversalBacktest
from datetime import datetime

backtest = UniversalBacktest(
    initial_date=datetime(2020, 1, 1),
    final_date=datetime(2021, 1, 1),
    asset_class="stocks",
    initial_cash=500000,
    verbose=True
)

result_log = backtest.run_backtest()
```

2. **Commodity Backtest with Custom Universe**

```python
from m203backtestlibrary import UniversalBacktest
from datetime import datetime

backtest = UniversalBacktest(
    initial_date=datetime(2020, 1, 1),
    final_date=datetime(2024, 1, 1),
    asset_class="commodities",
    universe=["CL=F", "NG=F", "ZS=F"],  # Custom tickers for Crude Oil, Natural Gas, Soybeans
    initial_cash=1000000,
    verbose=True
)

result_log = backtest.run_backtest()
```

---

### Futures Expiration Example

```python
from m203backtestlibrary.commodities_data_module import get_futures_expiry

buy_date = "2024-12-15"
ticker = "CL=F"  # Crude Oil futures
expiry_date = get_futures_expiry(buy_date, ticker)

print(f"The expiry date for {ticker} futures purchased on {buy_date} is {expiry_date}.")
```

---

### Performance Visualization

The `UniversalBacktest` class automatically calculates and plots performance metrics, including:
- **Portfolio Value**: Total value of holdings and cash.
- **Holdings Value**: Value of all held positions.
- **Cash**: Remaining liquid capital.

```python
# Example Backtest with Plotting
from m203backtestlibrary import UniversalBacktest
from datetime import datetime

backtest = UniversalBacktest(
    initial_date=datetime(2020, 1, 1),
    final_date=datetime(2021, 1, 1),
    asset_class="commodities",
    universe=["CL=F", "NG=F"],
    verbose=True
)

backtest.run_backtest()
```

After running the backtest, a performance plot will automatically be displayed, providing insights into the strategy's evolution over time.

---

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`m203backtestlibrary` was created by Mehmet Basagac. It is licensed under the terms of the MIT license.

## Credits

`m203backtestlibrary` builds upon `pybacktestchain` and was developed using [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) with the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).
