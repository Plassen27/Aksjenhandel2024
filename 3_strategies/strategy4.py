import yfinance as yf
import pandas_ta as ta
from base_strategy import BaseStrategy

class Strategy4(BaseStrategy):
    def __init__(self, ticker, interval, period, length=20, std=2):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.length = length
        self.std = std

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = full_data


    def generate_signals(self):
        self.fetch_data()
        data = self.data['Close'].copy()
        data = data.to_frame(name='Close')  # convert series to DataFrame

        # Calculate Bollinger Bands
        bbands = ta.bbands(self.data['Close'], length=self.length, std=self.std)
        if bbands is not None:
            data['lbb'] = bbands.iloc[:, 0]  # Lower Bollinger Band
            data['ubb'] = bbands.iloc[:, 2]  # Upper Bollinger Band
        else:
            print("No Bollinger Bands data.")
            return None

        data['Buy_Signal'] = (data['Close'] <= data['lbb'])
        data['Sell_Signal'] = (data['Close'] >= data['ubb'])

        return data
