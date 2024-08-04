#MACD Strategi, endre multiplier for mer data

import numpy as np
import yfinance as yf
from pyti.average_true_range import average_true_range as atr
from base_strategy import BaseStrategy

class Strategy23(BaseStrategy):
    def __init__(self, ticker, interval, period, multiplier=0.15, atr_period=10):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.multiplier = multiplier
        self.atr_period = atr_period
        self.data = None

    def fetch_data(self):
        self.data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data['hl2'] = (self.data['High'] + self.data['Low']) / 2

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        data['atr'] = atr(data['Close'].values, self.atr_period)
        data['up'] = data['hl2'] + self.multiplier * data['atr']
        data['dn'] = data['hl2'] - self.multiplier * data['atr']

        # Buy when price goes below 'dn' and sell when price goes above 'up'
        data['Buy_Signal_Price'] = np.where(data['Close'] < data['dn'], data['Close'], np.nan)
        data['Sell_Signal_Price'] = np.where(data['Close'] > data['up'], data['Close'], np.nan)

        # Generate Buy_Signal and Sell_Signal columns
        data['Buy_Signal'] = np.where(~np.isnan(data['Buy_Signal_Price']), True, False)
        data['Sell_Signal'] = np.where(~np.isnan(data['Sell_Signal_Price']), True, False)

        return data
