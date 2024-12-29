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

#---------------------------------------------------------
# Functions
#---------------------------------------------------------

from datetime import datetime, timedelta

def get_cbot_expiry(buy_date, commodity):
    """
    Calculate the expiry date of the front-month futures contract for CBOT commodities based on the date of purchase.

    Args:
        buy_date (str): The purchase date in 'YYYY-MM-DD' format.
        commodity (str): The commodity type ('soybean', 'wheat', 'corn', 'cocoa').

    Returns:
        str: Expiry date of the front-month contract in 'YYYY-MM-DD' format.

    Logic:
        1. Identify valid contract months for the specified commodity.
        2. Determine the front-month contract based on the purchase date.
        3. Calculate the expiry date for the front-month contract using the rule:
           "Business day before the 15th of the contract month."
        4. Define a rollover period (20 business days before expiry) to simulate realistic market behavior.
        5. If the purchase date falls within the rollover period, roll to the next contract.
    """
    # Define valid contract months for each commodity
    cbot_contract_months = {
        'soybean': [1, 3, 5, 7, 8, 9, 11],  # January, March, May, July, August, September, November
        'wheat': [3, 5, 7, 9, 12],          # March, May, July, September, December
        'corn': [3, 5, 7, 9, 12],           # March, May, July, September, December
        'cocoa': [3, 5, 7, 9, 12],          # March, May, July, September, December
    }

    try:
        # Convert input date to datetime object
        buy_date = datetime.strptime(buy_date, '%Y-%m-%d')

        # Get the contract months for the selected commodity
        if commodity not in cbot_contract_months:
            raise ValueError(f"Unsupported commodity: {commodity}. Supported commodities are: {', '.join(cbot_contract_months.keys())}")

        contract_months = cbot_contract_months[commodity]

        # Determine the front-month contract
        year = buy_date.year
        month = buy_date.month

        # Find the nearest valid contract month
        for contract_month in contract_months:
            if contract_month >= month:
                front_month = contract_month
                break
        else:
            # If no valid month in current year, roll to the next year's first contract month
            front_month = contract_months[0]
            year += 1

        # Calculate the expiry date for the front-month contract
        expiry_date = datetime(year, front_month, 15) - timedelta(days=1)
        while expiry_date.weekday() in (5, 6):  # Ensure expiry date is a business day
            expiry_date -= timedelta(days=1)

        # Define a rollover period (e.g., 20 business days before expiry)
        rollover_date = expiry_date
        business_days = 0
        while business_days < 20:
            rollover_date -= timedelta(days=1)
            if rollover_date.weekday() < 5:  # Count only weekdays (Monday-Friday)
                business_days += 1

        # If buy_date is on or after the rollover date, move to the next contract
        if buy_date >= rollover_date:
            next_index = contract_months.index(front_month) + 1
            if next_index >= len(contract_months):
                front_month = contract_months[0]
                year += 1
            else:
                front_month = contract_months[next_index]

            # Recalculate expiry date for the new contract
            expiry_date = datetime(year, front_month, 15) - timedelta(days=1)
            while expiry_date.weekday() in (5, 6):
                expiry_date -= timedelta(days=1)

        return expiry_date.strftime('%Y-%m-%d')

    except Exception as e:
        return f"Error calculating expiry date: {e}"

# Example usage
#buy_date = "2024-12-29"  # Replace with the date of purchase
#commodity = "soybean"  # Replace with 'wheat', 'corn', or 'cocoa'
#expiry_date = get_cbot_expiry(buy_date, commodity)
#print(f"The expiry date for the front-month {commodity} futures contract purchased on {buy_date} is {expiry_date}.")


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
# ZS=F --> Soybean, ZC=F --> Corn, ZW=F --> Wheat

# Energy Commodities
# CL=F --> Crude (WTI), BZ=F --> Crude (Brent), NG=F --> Natural Gas, HO=F --> Heating Oil

# Metals 
# GC=F --> Gold, SI=F --> Silver, HG = F --> Copper