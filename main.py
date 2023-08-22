import time
import pandas as pd
from datetime import datetime, timedelta

from api import api

from statsmodels.tsa.stattools import adfuller

import matplotlib.pyplot as plt
plt.style.use('seaborn-darkgrid')

TIMEFRAMES = ['1DAY', '4HOURS', '1HOUR']

class Stationarity:
    def __init__(self) -> None:
        self.client = api(exchange='dydx')
        self.all_markets_list = []
        self.results = {}
        
    def get_markets_info(self):
        while True:
            try:
                data = self.client.public.get_markets()
                break
            except Exception as e:
                print('get_markets_info error', datetime.now(), e)
                time.sleep(3)
        return data.data
        
    def read_data(self, data):
        for key, value in data['markets'].items():
            #filter dead markets
            if value['market'] not in ['LUNA-USD']:

                trades = {'market': value['market'],
                      'trades': int(value['trades24H'])}
                print(trades, '\n')
                self.all_markets_list.append(trades)
    
    def get_ohlcv(self, market, timeframe):
        '''1DAY, 4HOURS, 1HOUR, 30MINS, 15MINS, 5MINS, 1MIN'''
        while True:
            try:
                candles = self.client.public.get_candles(
                market=market,
                resolution=timeframe,
                )
                break
            except Exception as e:
                print('get_markets_info error', datetime.now(), e)
                time.sleep(3)

        #print(candles)
        return candles.data

    def create_df(self, data):
        ohlcv = data['candles']
        df = pd.DataFrame(data = ohlcv, columns = ['startedAt',
                                                   'open',
                                                   'high',
                                                   'low',
                                                   'close',
                                                   'usdVolume'])
        df = df.rename(columns={'startedAt': 'timestamp', 'usdVolume': 'volume'})
        #inversion
        df = df[::-1]
        #convert data types
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        #print(df)
        return df
    
    def calc_stationarity(self, df):
        #p value < 0.05 = stationary
        result = adfuller(df.close)
        print('ADF Test Statistic: %.2f' % result[0])
        print('5%% Critical Value: %.2f' % result[4]['5%'])
        print('p-value: %.2f' % result[1])

        #plt.plot(df['close'])
        #plt.show()
        return result[1]
    
    def show_min_max(self, df):
        #print 3 less stationary and 3 most stationary time series
        min_rows = df.nsmallest(3, 'p').reset_index(drop=True)
        max_rows = df.nlargest(3, 'p').reset_index(drop=True)
        for i in range(0, 3):
            print(f'printing the most stationary: {min_rows["market"].iloc[i]} {min_rows["p"].iloc[i]} {min_rows["timeframe"].iloc[i]}')
            df = self.results[min_rows["market"].iloc[i]][min_rows["timeframe"].iloc[i]]['df']
            plt.plot(df['close'])
            plt.show()
        
        for i in range(0, 3):
            print(f'printing the least stationary: {max_rows["market"].iloc[i]} {max_rows["p"].iloc[i]} {max_rows["timeframe"].iloc[i]}')
            df = self.results[max_rows["market"].iloc[i]][max_rows["timeframe"].iloc[i]]['df']
            plt.plot(df['close'])
            plt.show()

    def show_markets(self, df):
        #calculate the sum of p values from different timeframes
        #then show the most and the least stationary markets in general
        sum_by_market = df.groupby('market')['p'].sum()

        sorted_sum = sum_by_market.sort_values()

        print("Smallest values:")
        print(sorted_sum.head(3))

        print("\nLargest values:")
        print(sorted_sum.tail(3))
    
    def run(self):
        #get markets data
        markets_info = self.get_markets_info()
        #read markets data
        self.read_data(markets_info)
        results = []
        #get candles and make calculations
        for item in self.all_markets_list:
            market = item['market']
            self.results[market] = {}
            total_p = 0
            for timeframe in TIMEFRAMES:
                self.results[market][timeframe] = {}
                #pause due to api limits
                time.sleep(0.1)
                candles = self.get_ohlcv(market, timeframe)
                df = self.create_df(candles)
                #print(market, timeframe, average_trading_range)
                p = self.calc_stationarity(df)

                total_p += p
                
                self.results[market][timeframe] = {'p': p, 'df': df}
                result = [market, timeframe, p]
                results.append(result)
            
            item['total_p'] = total_p
       
        #print(self.all_markets_list)
        #print(self.results)

        df = pd.DataFrame(results, columns=['market', 'timeframe', 'p'])
        print(df)
        self.show_min_max(df)
        self.show_markets(df)

if __name__ == '__main__':
    test = Stationarity()
    test.run()
