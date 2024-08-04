import pandas_ta as ta
import pandas as pd
import yfinance as yf
import numpy as np
from base_strategy import BaseStrategy

class Strategy5(BaseStrategy):
    def __init__(self, ticker, interval, period, length=14):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.length = length
        self.data = self.fetch_data()

    def fetch_data(self):
        data = yf.download(self.ticker, interval=self.interval, period=self.period)
        data.dropna(inplace=True)
        return data

    def generate_signals(self):
        data = self.data.copy()

        # Calculate ADX
        adx = ta.adx(data['High'], data['Low'], data['Close'], self.length)
        data['ADX'] = adx['ADX_14']  # Fetch ADX values from the returned dataframe

        # Calculate VWMA
        data['VWMA'] = ta.vwma(data['Close'], data['Volume'], self.length)

        # Create Buy/Sell signals
        data['Buy_Signal'] = (data['Close'] > data['VWMA']) & (data['ADX'] > 38)
        data['Sell_Signal'] = (data['Close'] < data['VWMA']) & (data['ADX'] > 25)

        # Add a new column 'Signal' based on 'Buy_Signal' and 'Sell_Signal'
        data['Signal'] = np.where(data['Buy_Signal'], 'Buy',
                                  np.where(data['Sell_Signal'], 'Sell', np.nan))
        return data

    def generate_trades(self):
        data = self.generate_signals()

        trades = []
        buy_dates = []
        buy_prices = []

        for index, row in data.iterrows():
            if row['Signal'] == 'Buy':
                buy_dates.append(index)
                buy_prices.append(data.loc[index, 'Close'])
            elif row['Signal'] == 'Sell' and buy_dates:
                sell_date = index
                sell_price = data.loc[index, 'Close']
                for i, buy_date in enumerate(buy_dates):
                    trade_result = (sell_price - buy_prices[i]) / buy_prices[i]
                    trades.append(
                        (buy_date, True, buy_prices[i], sell_date, False, sell_price, trade_result))
                buy_dates = []
                buy_prices = []

        trade_data = pd.DataFrame(trades, columns=['buy_date', 'Buy_Signal', 'buy_price', 'sell_date', 'Sell_Signal',
                                                   'sell_price', 'trade_result'])
        trade_data.set_index('buy_date', inplace=True)

        return trade_data
