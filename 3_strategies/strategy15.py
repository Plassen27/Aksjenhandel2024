#Mean Reversal

import yfinance as yf
from base_strategy import BaseStrategy


class Strategy15(BaseStrategy):
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
        data['SMA'] = data['Close'].rolling(window=20).mean()  # We use 20 periods for the simple moving average
        data['Standard_Deviation'] = data['Close'].rolling(window=20).std()  # We use 20 periods for the standard deviation
        data['Upper_Band'] = data['SMA'] + (2 * data['Standard_Deviation'])  # We use 2 standard deviations for the upper band
        data['Lower_Band'] = data['SMA'] - (2 * data['Standard_Deviation'])  # We use 2 standard deviations for the lower band

        data['Buy_Signal'] = data['Close'] < data['Lower_Band']
        data['Sell_Signal'] = data['Close'] > data['Upper_Band']

        return data