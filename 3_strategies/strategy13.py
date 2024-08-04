import yfinance as yf
import numpy as np
import pandas as pd
import pandas_ta as ta
from base_strategy import BaseStrategy

class Strategy13(BaseStrategy):
    def __init__(self, ticker, interval, period):
        self.ticker = ticker
        self.interval = interval
        self.period = period

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        data = full_data.loc[:, ['Close']]  # Notice the double brackets

        # Calculate RSI
        data['RSI'] = ta.rsi(data['Close'], length=2)

        # Calculate Bollinger Bands
        data['Basis'] = ta.sma(data['Close'], length=20)
        data['Dev'] = 0.5 * ta.stdev(data['Close'], length=20)
        data['Upper'] = data['Basis'] + data['Dev']
        data['Lower'] = data['Basis'] - data['Dev']

        self.data = data

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Define buy and sell signals
        buy_signal = (data['RSI'].shift() < 30) & (data['Close'].shift() < data['Lower'])
        sell_signal = (data['RSI'].shift() > 70) & (data['Close'].shift() > data['Upper'])

        data['Buy_Signal'] = buy_signal
        data['Sell_Signal'] = sell_signal

        return data
