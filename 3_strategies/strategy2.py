import numpy as np
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from base_strategy import BaseStrategy



class Strategy2(BaseStrategy):
    def __init__(self, ticker, interval, period, short_window=15, long_window=30):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.short_window = short_window
        self.long_window = long_window

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = pd.DataFrame(full_data.loc[:, 'Close'], columns=['Close'])

    def generate_signals(self):
        self.fetch_data()
        data = pd.DataFrame(index=self.data.index)
        data['Close'] = self.data.values

        # Calculate short and long window SMA
        data['short_sma'] = ta.sma(data['Close'], self.short_window)
        data['long_sma'] = ta.sma(data['Close'], self.long_window)

        data['Buy_Signal'] = (data['short_sma'] > data['long_sma'])
        data['Sell_Signal'] = (data['short_sma'] < data['long_sma'])

        return data




