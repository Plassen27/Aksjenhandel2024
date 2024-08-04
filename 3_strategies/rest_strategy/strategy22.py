#supertrend, multiplier=3.0 kan endres som sensitivitet

import numpy as np
import yfinance as yf
from base_strategy import BaseStrategy

class Strategy22(BaseStrategy):
    def __init__(self, ticker, interval, period, multiplier=3.0, atr_period=10):
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

        # Calculate ATR
        data['atr'] = data['hl2'].rolling(window=self.atr_period).apply(lambda x: x[-1] - x[0])

        # Calculate Supertrend Up and Down
        data['up'] = data['hl2'] - self.multiplier * data['atr']
        data['dn'] = data['hl2'] + self.multiplier * data['atr']

        # Adjust Up and Down
        data['up'] = np.where((data['up'] < data['up'].shift(1)) & (data['Close'].shift(1) > data['up'].shift(1)),
                              data['up'].shift(1), data['up'])
        data['dn'] = np.where((data['dn'] > data['dn'].shift(1)) & (data['Close'].shift(1) < data['dn'].shift(1)),
                              data['dn'].shift(1), data['dn'])

        # Initialize trend
        data['trend'] = 1
        data['trend'] = np.where((data['trend'].shift(1) == -1) & (data['Close'] > data['dn'].shift(1)), 1,
                                 np.where((data['trend'].shift(1) == 1) & (data['Close'] < data['up'].shift(1)), -1,
                                          data['trend'].shift(1)))

        # Generate Buy and Sell signals
        data['Buy_Signal_Price'] = np.where((data['trend'] == 1) & (data['trend'].shift(1) == -1), data['Close'],
                                            np.nan)
        data['Sell_Signal_Price'] = np.where((data['trend'] == -1) & (data['trend'].shift(1) == 1), data['Close'],
                                             np.nan)

        # Generate Buy and Sell signals as True or False
        data['Buy_Signal'] = np.where((data['trend'] == 1) & (data['trend'].shift(1) == -1), True, False)
        data['Sell_Signal'] = np.where((data['trend'] == -1) & (data['trend'].shift(1) == 1), True, False)

        return data
