import numpy as np
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from base_strategy import BaseStrategy


class Strategy16(BaseStrategy):
    def __init__(self, ticker, interval, period):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.stoch_thresholds = (25, 75)  # lower and upper thresholds for Stochastic Oscillator

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = full_data.loc[:, ['Close', 'High', 'Low']]  # We need High and Low for Stochastic Oscillator

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate Stochastic Oscillator
        stoch = ta.stoch(data['High'], data['Low'], data['Close'])
        data['Stoch'] = stoch.iloc[:, 1]  # %D line (signal line)

        # Generate signals based on Stochastic Oscillator
        data['Buy_Signal'] = (data['Stoch'] < self.stoch_thresholds[0])
        data['Sell_Signal'] = (data['Stoch'] > self.stoch_thresholds[1])

        return data
