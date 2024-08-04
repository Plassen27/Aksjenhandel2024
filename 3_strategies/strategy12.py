import numpy as np
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from base_strategy import BaseStrategy

class Strategy12(BaseStrategy):
    def __init__(self, ticker, interval, period, bb_length=20, bb_std=2, take_profit=0.03, stop_loss=0.01, trailing_stop=0.02):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.bb_length = bb_length
        self.bb_std = bb_std
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = full_data.loc[:, ['Open', 'High', 'Low', 'Close', 'Volume']]

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate Bollinger Bands
        bb = ta.bbands(data['Close'], length=self.bb_length, std=self.bb_std)
        data = pd.concat([data, bb], axis=1)

        # Create Buy/Sell signals
        data['Buy_Signal'] = (data['Close'] < data['BBL_20_2.0']).astype(int) # Breakout from lower Bollinger Band
        data['Sell_Signal'] = (data['Close'] > data['BBU_20_2.0']).astype(int) # Breakout from upper Bollinger Band

        # Calculate Take Profit and Stop Loss levels
        data['Take_Profit'] = data['Close'] * (1 + self.take_profit)
        data['Stop_Loss'] = data['Close'] * (1 - self.stop_loss)

        # Trailing Stop functionality
        data['Trailing_Stop'] = data['Close'] * (1 - self.trailing_stop)
        data['Trailing_Stop'] = np.where(data['Trailing_Stop'] > data['Trailing_Stop'].shift(), data['Trailing_Stop'], data['Trailing_Stop'].shift())

        return data
