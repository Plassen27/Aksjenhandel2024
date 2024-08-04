import numpy as np
import yfinance as yf
import pandas_ta as ta
from base_strategy import BaseStrategy


class Strategy3(BaseStrategy):
    def __init__(self, ticker, interval, period, ema_length=20, take_profit=0.05, stop_loss=0.03, trailing_stop=0.015, gap=0.01):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.ema_length = ema_length
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.gap = gap

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = full_data.loc[:, ['Open', 'High', 'Low', 'Close', 'Volume']]

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate EMA
        data['EMA'] = ta.ema(data['Close'], self.ema_length)

        # Get yesterday's high
        data['Yesterday_High'] = data['High'].shift()
        data['Yesterday_High_with_gap'] = data['Yesterday_High'] * (1 + self.gap)

        # Calculate 30-day average volume
        data['Average_Volume'] = ta.sma(data['Volume'], 30)

        # Create Buy signal when yesterday's high is broken and volume is at least twice the average
        data['Buy_Signal'] = ((data['High'] > data['Yesterday_High_with_gap']) & (data['Volume'] >= 2.2 * data['Average_Volume'])).astype(int)

        # Calculate Take Profit and Stop Loss levels
        data['Take_Profit'] = data['Close'] * (1 + self.take_profit)
        data['Stop_Loss'] = data['Close'] * (1 - self.stop_loss)

        # Trailing Stop functionality
        data['Trailing_Stop'] = data['Close'] * (1 - self.trailing_stop)
        data['Trailing_Stop'] = np.where(data['Trailing_Stop'] > data['Trailing_Stop'].shift(), data['Trailing_Stop'], data['Trailing_Stop'].shift())

        # Create conditional Sell signal based on EMA
        data['Sell_Signal'] = (data['Close'] < data['EMA']).astype(int)

        return data
