import pandas_ta as ta
import numpy as np
import pandas as pd
import yfinance as yf
from base_strategy import BaseStrategy


class Strategy20(BaseStrategy):
    def __init__(self, ticker, interval, period, bollinger_period=15, bollinger_std=2.5, rsi_period=2, rsi_overbought=55, rsi_oversold=45):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.bollinger_period = bollinger_period
        self.bollinger_std = bollinger_std
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.data = self.fetch_data()

    def fetch_data(self):
        data = yf.download(self.ticker, interval=self.interval, period=self.period)
        data.dropna(inplace=True)
        return data

    def generate_signals(self):
        data = self.data.copy()
        bollinger = ta.bbands(data['Close'], length=self.bollinger_period, std=self.bollinger_std)
        data['lower_band'] = bollinger['BBL_' + str(self.bollinger_period) + '_' + "{:.1f}".format(self.bollinger_std)]
        data['upper_band'] = bollinger['BBU_' + str(self.bollinger_period) + '_' + "{:.1f}".format(self.bollinger_std)]

        # Calculate RSI
        data['RSI'] = ta.rsi(data['Close'], length=self.rsi_period)

        # Buy and Sell signals
        data['Buy_Signal'] = np.where((data['Close'] < data['lower_band']) & (data['RSI'] < self.rsi_oversold), True,
                                      False)
        data['Sell_Signal'] = np.where((data['Close'] > data['upper_band']) & (data['RSI'] > self.rsi_overbought), True,
                                       False)
        # Add a new column 'Signal' based on 'Buy_Signal' and 'Sell_Signal'
        data['Signal'] = np.where(data['Buy_Signal'], 1,
                                  np.where(data['Sell_Signal'], -1, np.nan))

        return data

    def generate_trades(self):
        data = self.generate_signals()

        trades = []
        buy_dates = []
        buy_prices = []
        buy_signals = []  # Add this line
        sell_signals = []  # Add this line
        sell_date = None
        sell_price = None

        # Add a new column 'Signal' based on 'Buy_Signal' and 'Sell_Signal'
        data['Signal'] = np.where(data['Buy_Signal'], 'Buy',
                                  np.where(data['Sell_Signal'], 'Sell', np.nan))

        for index, row in data.iterrows():
            if row['Signal'] == 'Buy':
                buy_dates.append(index)
                buy_prices.append(data.loc[index, 'Close'])
                buy_signals.append(True)  # Add this line
                sell_signals.append(False)  # Add this line
            elif row['Signal'] == 'Sell' and buy_dates:
                sell_date = index
                sell_price = data.loc[index, 'Close']
                for i, buy_date in enumerate(buy_dates):
                    trade_result = (sell_price - buy_prices[i]) / buy_prices[i]
                    trades.append(
                        (buy_date, buy_signals[i], buy_prices[i], sell_date, sell_signals[i], sell_price, trade_result))
                buy_dates = []
                buy_prices = []
                buy_signals = []  # Add this line
                sell_signals = []  # Add this line

        trade_data = pd.DataFrame(trades, columns=['buy_date', 'Buy_Signal', 'buy_price', 'sell_date', 'Sell_Signal',
                                                   'sell_price', 'trade_result'])
        trade_data.set_index('buy_date', inplace=True)

        return trade_data
