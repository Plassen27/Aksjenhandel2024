import pandas as pd
import pandas_ta as ta
import yfinance as yf
import numpy as np
from base_strategy import BaseStrategy

class BaseStrategy:
    def __init__(self, ticker, interval, period, start=None, end=None):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.start = start
        self.end = end
        self.data = None
class Strategy19(BaseStrategy):
    def __init__(self,
                 ticker,
                 interval,
                 period,
                 ATR_period=10,
                 ATR_multiplier=3.0,
                 start=None,
                 end=None):
        super().__init__(ticker, interval, period, start, end)
        self.ATR_period = ATR_period
        self.ATR_multiplier = ATR_multiplier

    def fetch_data(self):
        # Fetch the data for the given ticker and set the time range
        self.data = yf.download(self.ticker, interval=self.interval, period=self.period)

    def generate_signals(self):
        self.fetch_data()  # Ensure that data is fetched before generating signals
        # Calculate the SuperTrend
        super_trend = ta.supertrend(self.data['High'], self.data['Low'], self.data['Close'],
                                    length=self.ATR_period, multiplier=self.ATR_multiplier)
        # Concatenate super_trend to the original data
        self.data = pd.concat([self.data, super_trend], axis=1)

        # Create a signal column
        self.data['signal'] = 0

        # Generate buy and sell signals
        self.data['signal'] = self.data['SUPERTd_10_3.0'].apply(lambda x: 1 if x == 1 else -1)

        # Create 'Buy_Signal' and 'Sell_Signal' columns
        self.data['Buy_Signal'] = np.where(self.data['signal'] == 1, True, False)
        self.data['Sell_Signal'] = np.where(self.data['signal'] == -1, True, False)

        # Find where the trend changes to generate trading orders
        self.data['entry'] = self.data['signal'].diff()

        return self.data

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