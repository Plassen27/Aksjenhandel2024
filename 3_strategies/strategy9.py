#Hull-Strategi, multiplier=1.0, length=55):

import numpy as np
import yfinance as yf
from base_strategy import BaseStrategy

class Strategy9(BaseStrategy):
    def __init__(self, ticker, interval, period, multiplier=5.0, length=55):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.multiplier = multiplier
        self.length = length
        self.data = None

    def fetch_data(self):
        self.data = yf.download(self.ticker, interval=self.interval, period=self.period)

    def calculate_weighted_moving_average(self, data, period, column='Close'):
        weights = np.arange(1, period + 1)
        return data[column].rolling(period).apply(lambda x: (x * weights).sum() / weights.sum(), raw=True)

    def calculate_hma(self, data, period, column='Close'):
        sqrt_period = int(np.sqrt(period))
        wma_half = self.calculate_weighted_moving_average(data, int(period / 2))
        wma_full = self.calculate_weighted_moving_average(data, period)
        data['deltawma'] = 2 * wma_half - wma_full
        data['hma'] = self.calculate_weighted_moving_average(data, sqrt_period, column='deltawma')
        return data['hma']

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate HMA values and multiply them with the multiplier
        hull_moving_average = self.multiplier * self.calculate_hma(data, self.length)

        # Create signals
        data['Hull_Signal'] = np.where(hull_moving_average > hull_moving_average.shift(2), 1, -1)

        data['Buy_Signal'] = np.where(
            (data['Hull_Signal'] > 0) & (data['Hull_Signal'].shift(1) < 0),
            True, False)

        data['Sell_Signal'] = np.where(
            (data['Hull_Signal'] < 0) & (data['Hull_Signal'].shift(1) > 0),
            True, False)

        # Create signal prices
        data['Buy_Signal_Price'] = np.where(data['Buy_Signal'], data['Close'], np.nan)
        data['Sell_Signal_Price'] = np.where(data['Sell_Signal'], data['Close'], np.nan)

        return data
