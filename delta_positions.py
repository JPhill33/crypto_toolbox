# -*- coding: utf-8 -*-
"""
Created on Sat Sep  3 19:36:06 2022

@author: joshphillips
"""

import requests
import json
from urllib.request import Request, urlopen
import json
import pandas as pd
import statistics
import numpy as np
import datetime
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib
import plotly.express as px
import time
from black_scholes import *
from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("C_KEY")

############################################################################################
assets = ['btc']
currency = 'usd'
initial_investment = 500000
allocation_pct = [1.0]
today = date.today()
to_date = '2020-12-30'
from_date = today.strftime("%Y-%m-%d")
#############################################################################################

def get_delta_neutral(assets, currency, from_date, to_date, initial_investment):

    def historical_prices(assets, currency, from_date, to_date):
        # Get asset historical pricing
        dates = []
        prices = []
        for i in assets:
            pricing_url = F"https://api.covalenthq.com/v1/pricing/historical/USD/{i}/?quote-currency={currency}&format=JSON&from={from_date}&to={to_date}&key={key}"
            req = Request(pricing_url, headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()
            pricing_data = json.loads(webpage)
            
            for i in range(len(pricing_data['data']['prices'])):
                    dates.append(pricing_data['data']['prices'][i]['date'])
                    prices.append(pricing_data['data']['prices'][i]['price'])
                    
        # Divide date and pricing lists into equal parts for asset returns and return dataframe
        chunk_size = int(len(prices) / len(assets))
        chunk_check = float(chunk_size).is_integer()
    
        if (chunk_check == True):
            list_chunked = [prices[i:i + chunk_size] for i in range(0, len(prices), chunk_size)]
        else:
            raise Exception("Asset pricing data is not equal")
    
    
        df = pd.DataFrame(list_chunked).T
        df.columns = assets
        df['Date'] = dates[0:chunk_size]
        df = df.set_index('Date')
        df = df.reindex(index=df.index[::-1])
        
        return df
    
    def get_delta(assets, currency, from_date, to_date, initial_investment):
        # Run historical prices function and get daily return data for asset
        asset_prices = historical_prices(assets, currency, from_date, to_date)
        asset_daily_returns = asset_prices.pct_change()
        
        # Call option data in from bit and load raw data into dataframe, adjusting strike price to numeric
        bit_url = F"https://betaapi.bitexch.dev/v1/instruments?currency=BTC&category=option&active=true"
        bit_req = Request(bit_url, headers={'User-Agent': 'Mozilla/5.0'})
        bit_webpage = urlopen(bit_req).read()
        bit_data = json.loads(bit_webpage)
        
        bit_df = pd.DataFrame(bit_data['data'])
        bit_df_put = bit_df[bit_df['option_type'] == 'put']
        bit_df_put['strike_price_num'] = pd.to_numeric(bit_df_put['strike_price'])
        
        bit_df_put['expiration_at'] = pd.to_datetime(bit_df_put['expiration_at'], unit='ms')
        
        # Get current time to get time to expiry calculation
        date_time = date.today()
        current_time = time.mktime(date_time.timetuple())
        bit_df_put['today'] = int(current_time)*1000
        bit_df_put['today'] = pd.to_datetime(bit_df_put['today'],unit='ms')
    
        bit_df_put['time_to_expiry'] = (bit_df_put['expiration_at'] - bit_df_put['today']).dt.round('24H')
        days_to_expiry = list((bit_df_put['time_to_expiry'] / np.timedelta64(1, 'D')).astype(int))
        bit_df_put['time_to_expiry'] = days_to_expiry
        
        sigma = np.sqrt(365) * asset_daily_returns.std()
        
        # Create empty list, for loop strike prices and time to expiry to get deltas of contracts
        deltas = []        
        for a,b in zip(bit_df_put['strike_price_num'], bit_df_put['time_to_expiry']):
            delta = bs_delta(S = asset_prices.iloc[-1,],
                                         X = a,
                                         T = b / 365,
                                         r = 0.02,
                                         sigma = sigma,
                                         option_type = 'put')
            deltas.append(delta)
         
        # Calculate long position delta, convert strike and delta values
        long_delta = initial_investment / asset_prices.iloc[-1,] 
        strike_num = bit_df_put['strike_price'].astype(float)
        strike_num = pd.Series.tolist(strike_num)
        deltas_numeric = list(map(float, deltas))
    
        # Create delta dataframe that will be used to calculate contracts needed and net delta
        delta_df = pd.DataFrame({'strike': strike_num,
                               'longDelta': float(long_delta),
                               'contractDelta': deltas_numeric}, index = bit_df_put['instrument_id'])
        
        contracts_needed = delta_df['longDelta'] / delta_df['contractDelta']
        contracts_needed = pd.Series.round(contracts_needed)
        
        delta_df['contractsNeeded'] = contracts_needed
        delta_df['netDelta'] = delta_df['longDelta'] - (delta_df['contractDelta'] * delta_df['contractsNeeded'])
        
        # Filter delta dataframe for smallest amount of contracts needed, and positive delta under 0.05
        zero_delta_df = delta_df[(delta_df['contractsNeeded'] <= 50) & (delta_df['netDelta'] >= 0) & (delta_df['netDelta'] <= 0.05)]
                    
        return(zero_delta_df)
    return get_delta(assets, currency, from_date, to_date, initial_investment)
   