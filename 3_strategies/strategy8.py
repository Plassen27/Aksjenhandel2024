#Bollinger + RSI,

import numpy as np
import yfinance as yf
from pyti.relative_strength_index import relative_strength_index as rsi
from pyti.bollinger_bands import lower_bollinger_band as lbb
from pyti.bollinger_bands import upper_bollinger_band as ubb
from base_strategy import BaseStrategy

class Strategy8(BaseStrategy):
    def __init__(self, ticker, interval, period, RSI_length=8, RSI_value=65, BB_length=10, BB_mult=0.5):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.RSI_length = RSI_length
        self.RSI_value = RSI_value
        self.BB_length = BB_length
        self.BB_mult = BB_mult
        self.data = None

    def fetch_data(self):
        self.data = yf.download(self.ticker, interval=self.interval, period=self.period)

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate RSI
        data['rsi'] = rsi(data['Close'].values, self.RSI_length)

        # Calculate Bollinger Bands
        data['ubb'] = ubb(data['Close'].values, self.BB_length)
        data['lbb'] = lbb(data['Close'].values, self.BB_length)

        # Generate buy signal
        data['Buy_Signal'] = np.where(
            (data['rsi'].shift(1) < self.RSI_value) &
            (data['Close'].shift(1) < data['lbb'].shift(1)) &
            (data['Close'] > data['lbb']),
            True,
            False)

        # Generate sell signal
        data['Sell_Signal'] = np.where(
            (data['rsi'].shift(1) > (100 - self.RSI_value)) &
            (data['Close'].shift(1) > data['ubb'].shift(1)) &
            (data['Close'] < data['ubb']),
            True,
            False)

        return data