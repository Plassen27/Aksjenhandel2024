import yfinance as yf
import pandas as pd
from base_strategy import BaseStrategy
from datetime import datetime


class Strategy14(BaseStrategy):
    def __init__(self, ticker, interval, period, window=14, multiplier=2):
        super().__init__()
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.window = window
        self.multiplier = multiplier


    def fetch_data(self, ticker, start_date, end_date):
        df = yf.download(ticker, start=start_date, end=end_date)

        df['ext_source'] = self.calculate_ext_source(df)
        df['average'] = df['Close'].rolling(window=self.window).mean()
        df['upper'] = df['average'] + df['Close'].rolling(window=self.window).std() * self.multiplier
        df['lower'] = df['average'] - df['Close'].rolling(window=self.window).std() * self.multiplier
        df['bull'] = df['Close'] < df['lower']
        df['bear'] = df['Close'] > df['upper']
        df['exit_bull'] = df['Close'] >= df['average']
        df['exit_bear'] = df['Close'] <= df['average']

        self.data = df
        return df

    def generate_signals(self):
        signals = pd.DataFrame(index=self.data.index)
        signals['buy'] = ((self.data['bull'] & self.data['ext_source'].shift(1)) | 
                          (self.data['bull'] & self.data['bull'].shift(1) & self.data['ext_source']))
        signals['sell'] = ((self.data['bear'] & self.data['ext_source'].shift(1)) | 
                           (self.data['bear'] & self.data['bear'].shift(1) & self.data['ext_source']))
        signals['exit_buy'] = self.data['exit_bull']
        signals['exit_sell'] = self.data['exit_bear']

        return signals