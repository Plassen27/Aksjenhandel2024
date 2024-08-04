import numpy as np
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import sys
from base_strategy import BaseStrategy
sys.path.insert(0, r"C:\Users\johan\PycharmProjects\Aksjebot\quant_trading\3_strategies")



class Strategy1(BaseStrategy):
    def __init__(self, ticker, interval, period):
        self.ticker = ticker
        self.interval = interval
        self.period = period

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = full_data.loc[:, ['Close']]  # Notice the double brackets

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate MACD
        macd = ta.macd(data['Close'].squeeze())  # Use squeeze() to get a Series
        data['MACD'] = macd.iloc[:, 0]  # MACD line
        data['MACD_Signal'] = macd.iloc[:, 1]  # MACD Signal line

        data['Buy_Signal'] = (data['MACD'] > data['MACD_Signal'])
        data['Sell_Signal'] = (data['MACD'] < data['MACD_Signal'])

        return data
