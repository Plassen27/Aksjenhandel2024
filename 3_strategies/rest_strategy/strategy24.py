#Williams %-strategi, ligner på RSI

import yfinance as yf
from base_strategy import BaseStrategy

class Strategy14(BaseStrategy):
    def __init__(self, ticker, interval, period):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.data = self.fetch_data()

    def fetch_data(self):
        data = yf.download(self.ticker, period=self.period, interval=self.interval)
        data.dropna(inplace=True)
        return data

    def generate_signals(self):
        data = self.data.copy()
        data['High'] = data['High'].rolling(window=14).max()  # We use 14 periods to calculate the high
        data['Low'] = data['Low'].rolling(window=14).min()  # We use 14 periods to calculate the low
        data['%R'] = -100 * ((data['High'] - data['Close']) / (data['High'] - data['Low']))

        data['Buy_Signal'] = (data['%R'].shift(1) <= -80) & (data['%R'] > -80)
        data['Sell_Signal'] = (data['%R'].shift(1) >= -20) & (data['%R'] < -20)

        return data
