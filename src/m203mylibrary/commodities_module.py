#%%
import yfinance as yf
import pandas as pd 
from sec_cik_mapper import StockMapper
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging 
from scipy.optimize import minimize
import numpy as np
from datetime import datetime, timedelta
from pybacktestchain.data_module import DataModule, Information, FirstTwoMoments

# Setup logging
logging.basicConfig(level=logging.INFO)

#---------------------------------------------------------
# Functions
#---------------------------------------------------------

def get_futures_expiry(buy_date, ticker):
    """
    Calculate the expiry date of the front-month futures contract for commodities based on the date of purchase.

    Args:
        buy_date (str): The purchase date in 'YYYY-MM-DD' format.
        ticker (str): The commodity ticker (e.g., 'CL=F', 'BZ=F', 'NG=F', 'HO=F', 'ZS=F', 'ZW=F', 'ZC=F', 'CC=F).

    Returns:
        str: Expiry date of the front-month contract in 'YYYY-MM-DD' format.

    Logic:
        1. Identify the commodity type based on the ticker.
        2. Define expiry rules for the identified commodity.
        3. Determine delivery month based on purchase date.
        4. Handle cases where the expiry of the next delivery month is before the buy date.
        5. Calculate expiry date using specific commodity rules.
        6. Adjust expiry date to the nearest prior business day if it falls on a weekend.
    """
    # Define valid contract months for CBOT commodities
    cbot_contract_months = {
        'ZS=F': [1, 3, 5, 7, 8, 9, 11],  # Soybean
        'ZW=F': [3, 5, 7, 9, 12],        # Wheat
        'ZC=F': [3, 5, 7, 9, 12],        # Corn
        'CC=F': [3, 5, 7, 9, 12],        # Cocoa
    }

    try:
        # Convert purchase date to datetime object
        buy_date = datetime.strptime(buy_date, '%Y-%m-%d')

        if ticker in cbot_contract_months:  # CBOT Commodities
            contract_months = cbot_contract_months[ticker]

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
            expiry_date = datetime(year, front_month, 15) - pd.tseries.offsets.BDay(1)

            # Define a rollover period (e.g., 20 business days before expiry)
            rollover_date = expiry_date - pd.tseries.offsets.BDay(20)

            # If buy_date is on or after the rollover date, move to the next contract
            if buy_date >= rollover_date:
                next_index = contract_months.index(front_month) + 1
                if next_index >= len(contract_months):
                    front_month = contract_months[0]
                    year += 1
                else:
                    front_month = contract_months[next_index]

                # Recalculate expiry date for the new contract
                expiry_date = datetime(year, front_month, 15) - pd.tseries.offsets.BDay(1)

        elif ticker in ['CL=F', 'BZ=F', 'NG=F', 'HO=F']:  # Energy Commodities
            # Start with next delivery month
            delivery_month = (buy_date.month % 12) + 1
            year = buy_date.year + (1 if delivery_month == 1 else 0)

            if ticker == 'CL=F':  # Crude Oil (WTI)
                expiry_year = year if delivery_month > 1 else year - 1
                expiry_month = delivery_month - 1 if delivery_month > 1 else 12
                potential_expiry = pd.Timestamp(expiry_year, expiry_month, 25) - pd.tseries.offsets.BDay(3)

            elif ticker == 'BZ=F':  # Crude Oil (Brent)
                potential_expiry = pd.Timestamp(year, delivery_month, 1) - pd.tseries.offsets.BDay(2)

            elif ticker == 'NG=F':  # Natural Gas
                potential_expiry = pd.Timestamp(year, delivery_month, 1) - pd.tseries.offsets.BDay(3)

            elif ticker == 'HO=F':  # Heating Oil
                expiry_year = year if delivery_month > 1 else year - 1
                expiry_month = delivery_month - 1 if delivery_month > 1 else 12
                potential_expiry = pd.Timestamp(expiry_year, expiry_month, 1) - pd.tseries.offsets.BDay(1)

            # If the expiry is before the buy date, roll to the next delivery month
            if potential_expiry < buy_date:
                delivery_month = (delivery_month % 12) + 1
                year += (1 if delivery_month == 1 else 0)
                if ticker == 'CL=F':
                    expiry_year = year if delivery_month > 1 else year - 1
                    expiry_month = delivery_month - 1 if delivery_month > 1 else 12
                    potential_expiry = pd.Timestamp(expiry_year, expiry_month, 25) - pd.tseries.offsets.BDay(3)
                elif ticker == 'BZ=F':
                    potential_expiry = pd.Timestamp(year, delivery_month, 1) - pd.tseries.offsets.BDay(2)
                elif ticker == 'NG=F':
                    potential_expiry = pd.Timestamp(year, delivery_month, 1) - pd.tseries.offsets.BDay(3)
                elif ticker == 'HO=F':
                    expiry_year = year if delivery_month > 1 else year - 1
                    expiry_month = delivery_month - 1 if delivery_month > 1 else 12
                    potential_expiry = pd.Timestamp(expiry_year, expiry_month, 1) - pd.tseries.offsets.BDay(1)

            expiry_date = potential_expiry

        else:
            raise ValueError(f"Unsupported ticker: {ticker}. Supported tickers are: CL=F, BZ=F, NG=F, HO=F, ZS=F, ZW=F, ZC=F.")

        # Return expiry date
        return expiry_date.strftime('%Y-%m-%d')

    except Exception as e:
        return f"Error calculating expiry date: {e}"

# Example usage
#buy_date = "2024-12-29" 
#ticker = "ZC=F"
#expiry_date = get_futures_expiry(buy_date, ticker)
#print(f"The expiry date for the {ticker} futures contract purchased on {buy_date} is {expiry_date}.")


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

# Metals // NOT YET AVAILABLE
# GC=F --> Gold, SI=F --> Silver, HG = F --> Copper 

#---------------------------------------------------------
# Extended Classes for Commodities Futures
#---------------------------------------------------------

class CommoditiesDataModule(DataModule):
    """
    Extended data module to handle commodities futures with expiry dates.
    """
    expiry_date_column: str = 'ExpiryDate'

    def annotate_expiry_dates(self):
        """
        Add expiry dates for commodities futures based on tickers.
        Assigns '9999-12-31' as a placeholder expiry date for shares.
        """
        self.data[self.expiry_date_column] = self.data['ticker'].apply(
            lambda x: get_futures_expiry(self.data['Date'].iloc[0].strftime('%Y-%m-%d'), x)
            if ':F' in x else '9999-12-31'  # Set a placeholder expiry date for shares
        )

class CommoditiesInformation(Information):
    """
    Extended class to manage information for commodities futures and shares.
    """
    expiry_date_column: str = 'ExpiryDate'

    def slice_data(self, t: datetime):
        """
        Override to exclude expired commodities futures.

        Args:
            t (datetime): Current timestamp for backtesting.

        Returns:
            pd.DataFrame: Filtered data slice excluding expired futures.
        """
        data = super().slice_data(t)
        # Exclude expired futures contracts and retain shares
        data = data[(data[self.expiry_date_column] >= t.strftime('%Y-%m-%d')) | 
                    (data[self.expiry_date_column] == '9999-12-31')]
        return data

    def get_prices(self, t: datetime):
        """
        Override to ensure only valid (non-expired) contracts are included.

        Args:
            t (datetime): Current timestamp for backtesting.

        Returns:
            dict: Dictionary of valid tickers and their prices.
        """
        data = self.slice_data(t)
        prices = data.groupby('ticker')['Close'].last().to_dict()
        return prices