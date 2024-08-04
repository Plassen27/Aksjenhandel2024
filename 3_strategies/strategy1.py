import pandas as pd
import numpy as np
import yfinance as yf

class Strategy1:
    def __init__(self, ticker, interval, period):
        self.ticker = ticker
        self.interval = interval
        self.period = period
        self.fetch_data()

    def fetch_data(self):
        self.data = yf.download(self.ticker, interval=self.interval, period=self.period)
    # ADX computation
    def compute_adx(self, window=14):
        high = self.data['High']
        low = self.data['Low']
        close = self.data['Close']

        # True range
        self.data['TR'] = np.maximum((high - low),
                                      np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))

        # Plus and minus directional movement
        self.data['+DM'] = np.where((high > high.shift(1)) &
                                     (high - high.shift(1) > low.shift(1) - low), high - high.shift(1), 0)
        self.data['-DM'] = np.where((low < low.shift(1)) &
                                     (high.shift(1) - high < low.shift(1) - low), low.shift(1) - low, 0)

        # Smoothed true range and directional movement
        self.data['ATR'] = self.data['TR'].rolling(window).sum() / window
        self.data['+DM_smooth'] = self.data['+DM'].rolling(window).sum() / window
        self.data['-DM_smooth'] = self.data['-DM'].rolling(window).sum() / window

        # Plus and minus directional index
        self.data['+DI'] = 100 * self.data['+DM_smooth'] / self.data['ATR']
        self.data['-DI'] = 100 * self.data['-DM_smooth'] / self.data['ATR']

        # Directional movement index and average directional index
        DX = 100 * abs(self.data['+DI'] - self.data['-DI']) / (self.data['+DI'] + self.data['-DI'])
        self.data['ADX'] = DX.rolling(window).mean()

    # Bollinger Bands computation
    def compute_bollinger_bands(self, window=20, num_sd=2):
        self.data['rolling_mean'] = self.data['Close'].rolling(window).mean()
        self.data['rolling_std'] = self.data['Close'].rolling(window).std()
        self.data['Bollinger_High'] = self.data['rolling_mean'] + (self.data['rolling_std'] * num_sd)
        self.data['Bollinger_Low'] = self.data['rolling_mean'] - (self.data['rolling_std'] * num_sd)

    def generate_signals(self):
        self.compute_adx(window=14)
        self.compute_bollinger_bands(window=20, num_sd=1.5)

        # Creating the signals based on your strategy
        # Notice that the buy and sell signals are flipped, and the ADX threshold is lowered to 20
        self.data['Buy_Signal'] = np.where((self.data['Close'] < self.data['Bollinger_Low']) &
                                           (self.data['ADX'] > 20), True, False)
        self.data['Sell_Signal'] = np.where((self.data['Close'] > self.data['Bollinger_High']) &
                                            (self.data['ADX'] > 20), True, False)

        return self.data

    def generate_trades(self):
        data = self.generate_signals()

        trades = []
        buy_dates = []
        buy_prices = []
        sell_date = None
        sell_price = None
        buy_signal = None
        sell_signal = None

        for index, row in data.iterrows():
            if row['Buy_Signal']:
                buy_dates.append(index)
                buy_prices.append(data.loc[index, 'Close'])
                buy_signal = True
                sell_signal = False
            elif row['Sell_Signal'] and buy_dates:
                sell_date = index
                sell_price = data.loc[index, 'Close']
                buy_signal = False
                sell_signal = True
                for i, buy_date in enumerate(buy_dates):
                    trade_result = (sell_price - buy_prices[i]) / buy_prices[i]
                    trades.append(
                        (buy_date, buy_prices[i], buy_signal, sell_date, sell_price, sell_signal, trade_result))
                buy_dates = []
                buy_prices = []

        trade_data = pd.DataFrame(trades, columns=['buy_date', 'buy_price', 'Buy_Signal', 'sell_date', 'sell_price',
                                                   'Sell_Signal', 'trade_result'])
        trade_data.set_index('buy_date', inplace=True)

        return trade_data