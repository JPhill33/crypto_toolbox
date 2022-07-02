# -*- coding: utf-8 -*-
"""
Created on Sat Jul  2 14:07:05 2022

@author: joshphillips
"""

import requests
import json
from web3 import Web3
from web3 import HTTPProvider 
from urllib.request import Request, urlopen
import json
import pandas as pd
import statistics
import numpy as np
#from scipy.stats import norm
import numpy as np
#import seaborn as sns
from datetime import datetime, date, timedelta



############################################################################################
asset = 'busd'
currency = 'usd'
today = date.today()
yesterday = today - timedelta(days = 1)
to_date = yesterday.strftime("%Y-%m-%d")
initial_investment = 100000

#############################################################################################

def collateral(): 
    
    def coin_collector():
        # Call in list of top 250 coins from coingecko API
        coin_list_url = F'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false'
         
        # Pass through JSON interperter and return dataframe
        req2 = Request(coin_list_url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage2 = urlopen(req2).read()
        pricing_data2 = json.loads(webpage2)
        coin_list_df = pd.DataFrame(pricing_data2)
        
        # Select specific columns to use from dataframe
        coin_list_df = coin_list_df[['symbol', 'name', 'current_price', 'market_cap', 'market_cap_rank', 'total_volume',
                                        'ath_change_percentage', 'ath', 'atl']]
        
        # Set conditions to determine stablecoins
        conditions = [
            (coin_list_df['ath'] <= 1.35) & (coin_list_df['atl'] >= 0.550)
        ]
        values = ['stablecoin']
        coin_list_df['type1'] = np.select(conditions, values, default='')
        
        # Set conditions to determine bluechip coins
        conditions2 = [
            (coin_list_df['type1'] != 'stablecoin') & (coin_list_df['market_cap_rank'] <= 25)
        ]
        values2 = ['bluechip']
        coin_list_df['type2'] = np.select(conditions2, values2, default='')
        
        # Combine previous two columns and replace blanks with altcoin designation
        coin_list_df["type"] = coin_list_df['type1'] + coin_list_df['type2']
        
        coin_list_df['type'] = coin_list_df['type'].replace('', 'altcoin', regex=True)
       
        # Pull out columns to make dataframe to create dictionary
        new_df = coin_list_df[['symbol', 'type']]
        #coin_types = new_df.groupby(['type']).apply(lambda x: x['symbol'].tolist()).to_dict()
        
        coin_types = new_df.set_index('symbol').T.to_dict('list')
        return coin_types
    

    def advanced_var(asset, currency, to_date, initial_investment):
        
        coin_types = coin_collector()
        # Get asset historical pricing
        pricing_url = F"https://api.covalenthq.com/v1/pricing/historical/USD/{asset}/?quote-currency={currency}&format=JSON&to={to_date}&key=ckey_41d020c4ec2c4d7b9781a57b4ba"
        
        req = Request(pricing_url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()
        pricing_data = json.loads(webpage)
    
        # For length of data, get dates
        dates=[]
        for i in range(len(pricing_data['data']['prices'])):    
            dates.append(pricing_data['data']['prices'][i]['date'])
        
        # For length of data, get prices
        prices=[]
        for i in range(len(pricing_data['data']['prices'])):    
            prices.append(pricing_data['data']['prices'][i]['price'])
    
    
        # Put pricing information into dataframe
        dates_df = pd.DataFrame(dates, columns =['date'])     
        prices_df = pd.DataFrame(prices, columns =['price']) 
        prices_df = prices_df.set_index(pd.DatetimeIndex(dates_df['date'])) 
        
        # Calculations for VaR (periodic returns, standard deviation)
        asset_returns = prices_df['price'].pct_change()
        asset_returns = pd.DataFrame(asset_returns)
        
        # Get standard deviation and rollin 3 standard deviation 
        returnstdev = asset_returns.std()
        stdroll3 = asset_returns.rolling(3).std()
        
        # Get VaR values for 90, 95, and 99 confidence intervals, put into dataframe
        VaR90 = asset_returns.quantile(0.1)
        VaR95 = asset_returns.quantile(0.05)
        VaR99 = asset_returns.quantile(0.01)
    
        #VaR90_dollar = pd.DataFrame(VaR90 * initial_investment)
        #VaR95_dollar = pd.DataFrame(VaR95 * initial_investment)
        #VaR99_dollar = pd.DataFrame(VaR99 * initial_investment)
        
        VaR_df = pd.DataFrame()
        VaR_df['VaR90'] = VaR90
        VaR_df['VaR95'] = VaR95 
        VaR_df['VaR99'] = VaR99    
        VaR_df = VaR_df.rename(index={"price": "VaR"})
        
        # Search function - search asset to determing coin type 
        #def search(values, searchFor):
        #    for k in values:
        #        for v in values[k]:
        #            if searchFor in v:
        #                return k
        #    return None
        
        #search_result = search(coin_types, asset) 
        
        search_result = coin_types[asset]
        search_result = ''.join(map(str,search_result))
                    
        # Take search result and establish type/factor
        search_result_ls = []
        if search_result == "bluechip":
            selected_asset = "bluechip"
            search_result_ls.append(selected_asset)
        elif search_result == "stablecoin":
            selected_asset = "stablecoin"
            search_result_ls.append(selected_asset)
        elif search_result == "altcoin":
            selected_asset = "altcoin"
            search_result_ls.append(selected_asset)
            
        search_result_str = search_result_ls[0]
        
        # Establish collateral discount ratio - stablecoins more variable, lower collateral posting
        collat_disc_ratio90 = 1 - abs(VaR_df['VaR90']) # Used for stablecoins
        collat_disc_ratio95 = 1 - abs(VaR_df['VaR95']) # Used for bluechip coins
        collat_disc_ratio99 = 1 - abs(VaR_df['VaR99']) # Used for altcoins
        
        # Filter out collateral posting ratio for bluechip or stablecoin assets
        CR_ls = []
        if selected_asset == "bluechip":
            CR = 1.5
            CR_ls.append(CR)
        elif selected_asset == "stablecoin":
            CR = 1.25
            CR_ls.append(CR)     
        elif selected_asset == "altcoin":
            CR = 1.75
            CR_ls.append(CR)     
        CR_str = CR_ls[0]
        
        # Filter out discount ratio for bluechip or stablecoin assets
        disc_ls = []
        if selected_asset == "bluechip":
            discount = collat_disc_ratio95
            disc_ls.append(discount)
        elif selected_asset == "stablecoin":
            discount = collat_disc_ratio90
            disc_ls.append(discount)
        elif selected_asset == "altcoin":
            discount = collat_disc_ratio99
            disc_ls.append(discount)
        disc_str = disc_ls[0]
        
        
        # Momentum penalty - if rolling 3 day std dev is > historical std dev then
        # assess a penalty, applied to the discount ratio. Ex: 0.94 discount to DAI
        # loan, recent std dev is low, so discount rate decreases (gets closer to 1)
        if stdroll3['price'][-1] > returnstdev['price'] and len(asset_returns > 50):
            momentum_penalty = -0.05
        elif stdroll3['price'][-1] < returnstdev['price'] and len(asset_returns > 50):
            momentum_penalty = 0.05
        else:
            momentum_penalty = 0 
            
        adj_discount = sum([disc_str[0]], momentum_penalty) 
    
        # Calculate collateral coverage ratio - discounted collateral value / total loan amount    
        #ccr = collat_disc_ratio95 / initial_investment
        
        pre_disc_collat = CR_str * initial_investment
        
        # Original and basic collateral calculation
        overage_collat_perc = 1 / disc_str[0]
        post_disc_collat = pre_disc_collat * overage_collat_perc
        
        # Collateral posting adjusted for momentum factor
        mom_overage_collat_perc = 1 / adj_discount
        mom_adj_collateral = pre_disc_collat * mom_overage_collat_perc
            
        
        collat_df = pd.DataFrame({'Asset_Type': search_result_str,
                                  'Coverage_Ratio': CR_str,
                                  'Loan': initial_investment,
                                  'Discount': disc_str[0],
                                  'Collateral': post_disc_collat},
                                 index=[asset])
        
        adj_collat_df = pd.DataFrame({'Asset_Type': search_result_str,
                                  'Coverage_Ratio': CR_str,
                                  'Loan': initial_investment,
                                  'Adj_Discount': adj_discount,
                                  'Collateral': mom_adj_collateral},
                                 index=[asset])
    
        return([collat_df, adj_collat_df])
    return advanced_var(asset, currency, to_date, initial_investment)
    

