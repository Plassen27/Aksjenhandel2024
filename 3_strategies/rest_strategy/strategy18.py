import pandas_ta as ta
import numpy as np
import pandas as pd
import yfinance as yf
from base_strategy import BaseStrategy

class BaseStrategy:
    def __init__(self, ticker, interval, period):
        self.ticker = ticker
        self.interval = interval
        self.period = period

class Strategy12(BaseStrategy):
    def __init__(self, ticker, interval, period, short_period=6, long_period=14):
        super().__init__(ticker, interval, period)
        self.short_period = short_period
        self.long_period = long_period
        self.buy_price = None
        self.data = self.fetch_data()

    def fetch_data(self):
        data = yf.download(self.ticker, interval=self.interval, period=self.period)
        data.dropna(inplace=True)
        return data

    def generate_signals(self):
        data = self.data.copy()
        data['short_period_mean'] = data['Close'].rolling(self.short_period).mean()
        data['long_period_mean'] = data['Close'].rolling(self.long_period).mean()

        # Buy and Sell signals
        data['Buy_Signal'] = np.where((data['short_period_mean'] > data['long_period_mean']) &
                                      (data['short_period_mean'].shift(1) < data['long_period_mean'].shift(1)), True,
                                      False)
        data['Sell_Signal'] = np.where((data['short_period_mean'] < data['long_period_mean']) &
                                       (data['short_period_mean'].shift(1) > data['long_period_mean'].shift(1)), True,
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
        buy_signals = []
        sell_signals = []
        sell_date = None
        sell_price = None

        data['Signal'] = np.where(data['Buy_Signal'], 'Buy',
                                  np.where(data['Sell_Signal'], 'Sell', np.nan))

        buy_counter = 0

        for index, row in data.iterrows():
            if row['Signal'] == 'Buy' and buy_counter < 3:
                buy_dates.append(index)
                buy_prices.append(data.loc[index, 'Close'])
                buy_signals.append(True)
                sell_signals.append(False)
                buy_counter += 1
            elif row['Signal'] == 'Sell' and buy_dates:
                sell_date = index
                sell_price = data.loc[index, 'Close']
                for i, buy_date in enumerate(buy_dates):
                    trade_result = (sell_price - buy_prices[i]) / buy_prices[i]
                    trades.append(
                        (buy_date, buy_signals[i], buy_prices[i], sell_date, sell_signals[i], sell_price, trade_result))
                buy_dates = []
                buy_prices = []
                buy_signals = []
                sell_signals = []
                buy_counter = 0

        trade_data = pd.DataFrame(trades, columns=['buy_date', 'Buy_Signal', 'buy_price', 'sell_date', 'Sell_Signal',
                                                   'sell_price', 'trade_result'])

        trade_data['Buy_Date'] = trade_data['buy_date']  # copy 'buy_date' before setting it as index
        trade_data.set_index('buy_date', inplace=True)

        # compute 'Shares' column
        trade_data['Shares'] = 5000 // trade_data['buy_price']  # calculate shares so total cost is under 5000

        return trade_data