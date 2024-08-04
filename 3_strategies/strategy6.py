import numpy as np
import pandas as pd

import yfinance as yf
from abc import ABC, abstractmethod
from yahoo_fin import stock_info as si
from base_strategy import BaseStrategy

class Strategy6(BaseStrategy):
    def __init__(self, ticker, interval, period, threshold=0.006):  # Lowered threshold
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.data = self.fetch_data()
        self.threshold = threshold

    def fetch_data(self, ticker=None, interval=None, period=None):
        if ticker is None:
            ticker = self.ticker
        if interval is None:
            interval = self.interval
        if period is None:
            period = self.period
        data = yf.download(ticker, interval=interval, period=period)
        data.dropna(inplace=True)
        return data

    def calculate_beta(self):
        obx_returns = self.fetch_data('OBX.OL', self.interval, self.period)['Close'].pct_change()
        stock_returns = self.data['Close'].pct_change()

        # Align data
        obx_returns, stock_returns = obx_returns.align(stock_returns, join='outer')

        # Find missing indices
        missing_indices_obx = obx_returns[obx_returns.isnull()].index
        missing_indices_stock = stock_returns[stock_returns.isnull()].index
        print(f"Missing indices in OBX returns: {missing_indices_obx}")
        print(f"Missing indices in stock returns: {missing_indices_stock}")

        # Interpolate to fill missing data
        obx_returns.interpolate(method='time', inplace=True)
        stock_returns.interpolate(method='time', inplace=True)

        # Drop any remaining NaN values
        obx_returns.dropna(inplace=True)
        stock_returns.dropna(inplace=True)

        beta = np.polyfit(obx_returns, stock_returns, 1)[0]

        return beta

    def generate_signals(self):
        data = self.data.copy()

        # Calculate beta
        beta = self.calculate_beta()

        # Calculate the deviation from beta
        obx_returns = self.fetch_data('OBX.OL', self.interval, self.period)['Close'].pct_change().dropna()
        deviation = self.data['Close'].pct_change() - beta * obx_returns
        deviation_ma = deviation.rolling(window=2).mean()  # Reduced moving average window size

        # Generate buy and sell signals based on the deviation from beta
        data['Buy_Signal'] = np.where(deviation_ma < -self.threshold, True, False)
        data['Sell_Signal'] = np.where(deviation_ma > self.threshold, True, False)

        return data
