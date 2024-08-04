import pandas_ta as ta
import numpy as np
import pandas as pd
import yfinance as yf
from base_strategy import BaseStrategy


class Strategy17(BaseStrategy):
    def __init__(self, ticker, interval, period, short_period=6, long_period=14):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.short_period = short_period
        self.long_period = long_period
        self.data = self.fetch_data()

    def fetch_data(self):
        data = yf.download(self.ticker, interval=self.interval, period=self.period)
        data.dropna(inplace=True)
        return data

    def generate_signals(self):
        data = self.data.copy()
        data['short_period_mean'] = data['Close'].rolling(self.short_period).mean()
        data['long_period_mean'] = data['Close'].rolling(self.long_period).mean()

        # Buy and Sell signals
        data['Buy_Signal'] = np.where((data['short_period_mean'] > data['long_period_mean']) &
                                      (data['short_period_mean'].shift(1) < data['long_period_mean'].shift(1)), True,
                                      False)
        data['Sell_Signal'] = np.where((data['short_period_mean'] < data['long_period_mean']) &
                                       (data['short_period_mean'].shift(1) > data['long_period_mean'].shift(1)), True,
                                       False)

        # Add a new column 'Signal' based on 'Buy_Signal' and 'Sell_Signal'
        data['Signal'] = np.where(data['Buy_Signal'], 1,
                                  np.where(data['Sell_Signal'], -1, np.nan))

        return data