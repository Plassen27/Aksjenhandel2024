#EMA Slope + EMA Cross, ma1_length, ma2_length, og ma3_length kam endres for å få ny data

import numpy as np
import yfinance as yf
from base_strategy import BaseStrategy

class Strategy7(BaseStrategy):
    def __init__(self, ticker, interval, period, ma1_length=2, ma2_length=4, ma3_length=45):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.ma1_length = ma1_length
        self.ma2_length = ma2_length
        self.ma3_length = ma3_length
        self.data = None

    def fetch_data(self):
        self.data = yf.download(self.ticker, interval=self.interval, period=self.period)

    def generate_signals(self):
        self.fetch_data()
        data = self.data.copy()

        # Calculate EMAs
        data['EMA1'] = data['Close'].ewm(span=self.ma1_length, adjust=False).mean()
        data['EMA2'] = data['Close'].ewm(span=self.ma2_length, adjust=False).mean()
        data['EMA3'] = data['Close'].ewm(span=self.ma3_length, adjust=False).mean()

        # Calculate change in price and EMAs
        data['price_change'] = data['Close'].diff()
        data['EMA1_change'] = data['EMA1'].diff()
        data['EMA2_change'] = data['EMA2'].diff()

        # Generate signals
        data['Buy_Signal'] = np.where(
            (data['Close'].shift(1) < data['EMA3'].shift(1)) &
            ((data['price_change'].shift(1) < 0) & (data['EMA1_change'].shift(1) < 0) &
             (data['Close'].shift(1) < data['EMA1'].shift(1)) & (data['EMA2_change'].shift(1) > 0)),
            True, False)

        data['Sell_Signal'] = np.where(
            (data['Close'].shift(1) > data['EMA3'].shift(1)) &
            ((data['price_change'].shift(1) > 0) & (data['EMA1_change'].shift(1) > 0) &
             (data['Close'].shift(1) > data['EMA1'].shift(1)) & (data['EMA2_change'].shift(1) < 0)),
            True, False)

        return data


