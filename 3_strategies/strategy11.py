import pandas_ta as ta
import pandas as pd
import yfinance as yf



class Strategy11():
    def __init__(self, ticker, interval, period, length=18, line_type='kijun'):

        self.length = length
        self.line_type = line_type
        self.buy_dates = []
        self.buy_prices = []
        self.buy_counter = 0
        self.data = yf.download(ticker, interval=interval, period=period)
        if self.data.empty:
            print(f"No data for ticker: {ticker}, interval: {interval}, period: {period}")
            self.data = pd.DataFrame()

    def fetch_data(self):
        full_data = yf.download(self.ticker, interval=self.interval, period=self.period)
        self.data = full_data.loc[:, 'Close']

    def generate_signals(self):
        data = self.data[['Close']].copy()

        high_26 = data['Close'].rolling(window=26).max()
        low_26 = data['Close'].rolling(window=26).min()
        data['kijun'] = (high_26 + low_26) / 2

        # Calculate SMA and EMA
        data['sma'] = ta.sma(data['Close'], self.length)
        data['ema'] = ta.ema(data['Close'], self.length)

        # Choose the line to use based on the type
        if self.line_type == 'kijun':
            data['line'] = data['kijun']
        elif self.line_type == 'sma':
            data['line'] = data['sma']
        elif self.line_type == 'ema':
            data['line'] = data['ema']
        else:
            raise ValueError(f"Invalid line_type: {self.line_type}")

        # Create Buy/Sell signals
        data['up_trend'] = (data['Close'] > data['line']) & (data['Close'].shift(1) > data['line'].shift(1)) & (data['Close'].shift(2) > data['line'].shift(2))
        data['down_trend'] = (data['Close'] < data['line']) & (data['Close'].shift(1) < data['line'].shift(1)) & (data['Close'].shift(2) < data['line'].shift(2))

        data['Buy_Signal'] = data['up_trend']
        data['Sell_Signal'] = data['down_trend']

        return data



    def generate_trades(self):
        data = self.generate_signals()
        trades = []

        for index, row in data.iterrows():
            if row['Buy_Signal'] and self.buy_counter < 3:
                self.buy_dates.append(index)
                self.buy_prices.append(data.loc[index, 'Close'])
                self.buy_counter += 1
            elif row['Sell_Signal'] and self.buy_dates:
                self.sell_date = index
                self.sell_price = data.loc[index, 'Close']
                for i, buy_date in enumerate(self.buy_dates):
                    trade_result = (self.sell_price - self.buy_prices[i]) / self.buy_prices[i]
                    trades.append(
                        (buy_date, True, self.buy_prices[i], self.sell_date, False, self.sell_price, trade_result))
                self.buy_dates = []
                self.buy_prices = []
                self.buy_counter = 0

        trade_data = pd.DataFrame(trades, columns=['buy_date', 'Buy_Signal', 'buy_price', 'sell_date', 'Sell_Signal',
                                                   'sell_price', 'trade_result'])

        trade_data['Buy_Date'] = trade_data['buy_date']  # copy 'buy_date' before setting it as index
        trade_data.set_index('buy_date', inplace=True)

        # compute 'Shares' column
        trade_data['Shares'] = 5000 // trade_data['buy_price']  # calculate shares so total cost is under 5000

        return trade_data

    def estimate_future_close(self, rate_change=0.01):
        data = self.data.copy()

        high_26 = data['Close'].rolling(window=26).max()
        low_26 = data['Close'].rolling(window=26).min()
        data['kijun'] = (high_26 + low_26) / 2

        data['sma'] = ta.sma(data['Close'], self.length)
        data['ema'] = ta.ema(data['Close'], self.length)

        if self.line_type == 'kijun':
            data['line'] = data['kijun']
        elif self.line_type == 'sma':
            data['line'] = data['sma']
        elif self.line_type == 'ema':
            data['line'] = data['ema']
        else:
            raise ValueError(f"Invalid line_type: {self.line_type}")

        last_line = data['line'].iloc[-1]

        future_close_lower = last_line * (1 - rate_change)
        future_close_upper = last_line * (1 + rate_change)

        return future_close_lower, future_close_upper






