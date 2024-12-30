# m203mylibrary

This library is part of the **m203 python project**, extending functionality from `pybacktestchain` (and related classes) to handle both **equity backtesting** and **commodity futures backtesting** with blockchain-based result storage.

---

## Installation

```bash
pip install m203mylibrary
```

---

## Overview

The final goal of this library is to **build and backtest advanced trading strategies** (e.g., options, futures, equities). It provides:

1. **Equity Backtesting:** Reuses the original classes (`Broker`, `Backtest`, `Information`, etc.) for stocks.  
2. **Commodity Futures Backtesting:** Inherits from the original classes, adding commodity-specific logic such as **futures expiry** and specialized rebalancing triggers for expiry dates.

The code also integrates a **blockchain** data structure to store and validate historical backtest results.

---

## Quick Start

To verify that the library installed correctly, you can run:

```python
from m203mylibrary import test_function

test_function()
```

If you see the expected test output, your library is installed and functioning properly.

---

## Basic Usage

Below are two usage examples: one for **equity** backtesting (using the *old classes*), and one for **commodity** backtesting (using the *new classes*).

### 1. Equity Backtest Example

```python
from datetime import datetime
from m203mylibrary.old_script import Backtest

# Create a standard equity backtest from 2020-01-01 to 2020-12-31
equity_backtest = Backtest(
    initial_date=datetime(2020, 1, 1),
    final_date=datetime(2020, 12, 31),
    initial_cash=1000000
)

# Run backtest
equity_results = equity_backtest.run_backtest()
print(equity_results.head())
```

This will:
1. Retrieve historical stock data from Yahoo Finance for the default universe (AAPL, MSFT, etc.).
2. Compute mean-variance optimal weights (via the `FirstTwoMoments` class).
3. Execute trades through the `Broker`.
4. Store results in a local blockchain pickle file.

---

### 2. Commodity Futures Backtest Example

```python
from datetime import datetime
from m203mylibrary.new import CommodityBacktest

# Create a commodity futures backtest for CL=F (Crude Oil), etc.
commodity_backtest = CommodityBacktest(
    initial_date=datetime(2023, 1, 1),
    final_date=datetime(2023, 3, 1),
    initial_cash=1_000_000,
    universe=['CL=F', 'BZ=F']  # Focus on two commodity tickers
)

# Run the backtest
commodity_results = commodity_backtest.run_backtest()
print(commodity_results.head())
```

This process:
1. Retrieves daily commodity futures prices from Yahoo Finance.
2. Generates a `futures expiry` date for each row and stores it.
3. Creates a specialized `CommodityBroker` that can store expiry dates in each position.
4. Sells expiring contracts before rebalancing.
5. Also stores final results in the local blockchain.

---

## Explanation of Key Components

1. **`Broker` and `CommodityBroker`:**  
   - `Broker` (old script) handles equity positions.  
   - `CommodityBroker` (new script) inherits from `Broker` and adds `expiry_date` support for futures contracts.

2. **`Backtest` and `CommodityBacktest`:**  
   - `Backtest` is the original class for running equity strategies.  
   - `CommodityBacktest` inherits from `Backtest` but overrides data retrieval (e.g. `get_commodities_data`) and supports contract expiry logic.

3. **`Blockchain`:**  
   - Both the equity and commodity backtests automatically store final results in a simple blockchain-like pickle file, ensuring the historical record can't be easily tampered with.

4. **`Information` vs. `CommodityInformation`:**  
   - `Information` slices stock data in a rolling window.  
   - `CommodityInformation` does the same but can track `futures expiry` columns if needed.

5. **`RiskModel` and `StopLoss`:**  
   - These classes implement a simple 10% stop-loss.  
   - In commodity mode, we can also *optionally* handle rolling logic or rebalancing triggers based on expiry.

---

## Contributing

Interested in contributing to `m203mylibrary`? Check out the [contributing guidelines](CONTRIBUTING.md).  
By contributing to this project, you agree to abide by its [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

`m203mylibrary` was created by Mehmet Basagac. It is licensed under the terms of the MIT license. See the [LICENSE](LICENSE) file for more details.

---

## Credits

`m203mylibrary` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).  

This library also leverages **yfinance** for retrieving historical asset prices, **pandas** for data manipulation, **NumPy**/**SciPy** for optimization, and **logging** for structured logging outputs.

---
