#%%
import yfinance as yf
import pandas as pd 
from sec_cik_mapper import StockMapper
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging 
from scipy.optimize import minimize
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)

# Define the month codes used in futures tickers (e.g., F for January, G for February)
months = {
    "F": "Jan", "G": "Feb", "H": "Mar", "J": "Apr",
    "K": "May", "M": "Jun", "N": "Jul", "Q": "Aug",
    "U": "Sep", "V": "Oct", "X": "Nov", "Z": "Dec"
}

#---------------------------------------------------------
# Functions
#---------------------------------------------------------

def get_available_futures(base_ticker, start_year=2023, end_year=2025):
    """
    Searches for available futures on Yahoo Finance for a given commodity.

    Args:
        base_ticker (str): The base ticker of the commodity (e.g., "CL" for WTI crude oil).
        start_year (int): The starting year for checking futures.
        end_year (int): The ending year for checking futures.

    Returns:
        list: A list of available futures tickers.
    """
    available_futures = []  # List to store available tickers

    # Loop through years and months to generate futures tickers
    for year in range(start_year, end_year + 1):  # Iterate over the range of years
        for month_code, month_name in months.items():  # Iterate over month codes
            # Construct the ticker for the future (e.g., CLM24 for WTI June 2024)
            ticker = f"{base_ticker}{month_code}{str(year)[-2:]}"  
            try:
                # Fetch data for the ticker using yfinance
                future = yf.Ticker(ticker)
                data = future.history(period="1d")  # Retrieve 1-day historical data
                if not data.empty:  # If data exists, the future is available
                    available_futures.append(ticker)
                    logging.info(f"Available: {ticker} ({month_name} {year})")
            except Exception as e:
                # Log a warning if there's an error retrieving the data
                logging.warning(f"Error with {ticker}: {e}")
    
    return available_futures  # Return the list of available tickers

# Example: Search for futures contracts for WTI crude oil
#commodity_base_ticker = "CL"  # Base ticker for WTI crude oil
#available_tickers = get_available_futures(commodity_base_ticker, start_year=2023, end_year=2025)

# Display the results
#print("\nAvailable Futures:")
#print(available_tickers)

# Function to retrieve historical data for a single commodity
def get_commodity_data(ticker, start_date, end_date):
    """
    Retrieves historical data on prices for a given commodity.

    Args:
        ticker (str): The commodity ticker
        start_date (str): Start date in the format 'YYYY-MM-DD'
        end_date (str): End date in the format 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: A pandas dataframe with the historical data

    Example:
        df = get_commodity_data('CL=F', '2020-01-01', '2020-12-31')
    """
    try:
        commodity = yf.Ticker(ticker)
        data = commodity.history(start=start_date, end=end_date, auto_adjust=False, actions=False)
        df = pd.DataFrame(data)
        df['ticker'] = ticker
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        logging.warning(f"Error retrieving data for {ticker}: {e}")
        return pd.DataFrame()

# Function to retrieve historical data for multiple commodities
def get_commodities_data(tickers, start_date, end_date):
    """
    Retrieves historical data on prices for a list of commodities.

    Args:
        tickers (list): List of commodity tickers
        start_date (str): Start date in the format 'YYYY-MM-DD'
        end_date (str): End date in the format 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: A pandas dataframe with the historical data

    Example:
        df = get_commodities_data(['CL=F', 'NG=F'], '2020-01-01', '2020-12-31')
    """
    dfs = []
    for ticker in tickers:
        try:
            df = get_commodity_data(ticker, start_date, end_date)
            if not df.empty:
                dfs.append(df)
        except Exception as e:
            logging.warning(f"Commodity {ticker} not found: {e}")
    # Concatenate all dataframes
    data = pd.concat(dfs, ignore_index=True)
    return data

#---------------------------------------------------------
# Example Usage
#---------------------------------------------------------

# Example commodity tickers
#commodity_tickers = ['CL=F', 'NG=F']  # Crude Oil and Natural Gas

# Get historical data for commodities
#start_date = '2023-01-01'
#end_date = '2023-12-31'

#commodities_data = get_commodities_data(commodity_tickers, start_date, end_date)
#print(commodities_data)

#---------------------------------------------------------
# Commodities tickers
#---------------------------------------------------------

# Soft Commodities
