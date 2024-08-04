import pandas as pd
import os
import sys
import importlib
import pytz
import time
import json
from datetime import datetime
from datetime import timedelta
from collections import defaultdict

sys.path.append("C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\3_strategies")

# Load settings from the json file
with open('settings.json', 'r') as f:
    settings = json.load(f)

def get_period(interval):
    if interval in ['15m', '30m']:
        return '30d'
    elif interval == '60m':
        return '720d'
    else:
        raise ValueError(f"Invalid interval value: {interval}")

def get_datetime(date_string):
    # Parse date string to datetime object
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    # Set time and timezone
    dt = dt.replace(hour=6, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('Europe/Oslo'))
    return dt

# Extract settings
stocks = settings['stocks']
for i, stock in enumerate(stocks):
    stock['priority'] = i
    stock['period'] = get_period(stock['interval'])

start_date = get_datetime(settings['start_date'])
Kolonnevisning = len(stocks) * 2

# Continue with the rest of your script...



stocks = settings['stocks']
start_date = datetime.fromisoformat(settings['start_date'])
total_cash = int(settings['total_cash'])
order_size = int(settings['order_size'])
kurtajse = float(settings['kurtasje'])



strategies = {}
for i in range(1, 16):
    try:
        strategies[i] = getattr(importlib.import_module(f"strategy{i}"), f"Strategy{i}")
        print(f"Successfully imported Strategy{i}")
    except Exception as e:
        print(f"Failed to import Strategy{i}: {e}")


class Portfolio:
    def __init__(self, stocks, start_date, end_date, cash):
        self.stocks = stocks
        self.start_date = start_date
        self.end_date = end_date
        self.cash = cash
        self.portfolio = {}
        self.order_history = []
        self.consecutive_buys = defaultdict(int)
        self.preload_periods = 200
        for stock in self.stocks:
            self.portfolio[stock["ticker"]] = {"shares": 0}

    def run_backtest(self):
        all_signals = []
        for stock in self.stocks:
            ticker = stock["ticker"]
            strategy_num = stock["strategy"]
            strategy = strategies[strategy_num](ticker, stock["interval"], stock["period"])
            signals = strategy.generate_signals()
            signals['Date'] = signals.index
            signals["ticker"] = ticker

            # Filter signals based on start and end dates
            signals = signals.loc[(signals['Date'].dt.tz_localize('Europe/Oslo') >= self.start_date) & (
                    signals['Date'].dt.tz_localize('Europe/Oslo') <= self.end_date)]

            # Append all signals into a list
            all_signals.append(signals)

        # Concatenate all signals into a single DataFrame
        all_signals_df = pd.concat(all_signals)

        # Sort all_signals by 'Date' and then by priority of the stocks
        all_signals_df.sort_values(by=['Date', 'ticker'], key=lambda x: (x, self.get_priority_of_stock(x)),
                                   inplace=True)

        for _, signal in all_signals_df.iterrows():
            date, ticker = signal['Date'], signal['ticker']
            price = signal['Close']
            if signal['Buy_Signal']:
                self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'Buy Signal')
            elif signal['Sell_Signal']:
                self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'Sell Signal')
            else:
                self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'No Signal')

    def run_backtest(self):
        all_signals = []
        for stock in self.stocks:
            ticker = stock["ticker"]
            strategy_num = stock["strategy"]
            strategy = strategies[strategy_num](ticker, stock["interval"], stock["period"])
            signals = strategy.generate_signals()
            signals['Date'] = signals.index
            signals["ticker"] = ticker

            # Filter signals based on start and end dates
            signals = signals.loc[(signals['Date'].dt.tz_localize('Europe/Oslo') >= self.start_date) & (
                    signals['Date'].dt.tz_localize('Europe/Oslo') <= self.end_date)]

            # Append all signals into a list
            all_signals.append(signals)

        # Concatenate all signals into a single DataFrame
        all_signals_df = pd.concat(all_signals)

        # Add priority column to all_signals_df
        all_signals_df['priority'] = all_signals_df['ticker'].apply(self.get_priority_of_stock)

        # Sort all_signals by 'Date' and then by priority of the stocks
        all_signals_df.sort_values(by=['Date', 'priority'], ascending=[True, True], inplace=True)

        for _, signal in all_signals_df.iterrows():
            date, ticker = signal['Date'], signal['ticker']
            price = signal['Close']
            if signal['Buy_Signal']:
                self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'Buy Signal')
            elif signal['Sell_Signal']:
                self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'Sell Signal')
            else:
                self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'No Signal')

    def get_strategy_number_of_stock(self, ticker):
            for stock in self.stocks:
                if stock['ticker'] == ticker:
                    return stock['strategy']
            return None

    def get_priority_of_stock(self, ticker):
        for stock in self.stocks:
            if stock['ticker'] == ticker:
                return stock['priority']
        return None

    def add_signal(self, ticker, date, price, strategy_num, signal_type):
        # Set the transaction fee rate
        transaction_fee_rate = kurtajse

        # Calculate shares given an order size of 5000, rounded down to whole share amounts
        shares = min(self.cash // price, order_size // price) if signal_type == 'Buy Signal' else \
        self.portfolio[ticker][
            "shares"]

        # Calculate transaction fee
        transaction_fee = shares * price * transaction_fee_rate

        # Calculate net cash change
        net_cash_change = -(
                shares * price + transaction_fee) if signal_type == 'Buy Signal' else shares * price - transaction_fee
        # Create a new order
        signal = {
            "T": ticker,  # Changed to 'T'
            "ST": signal_type,  # Changed to 'ST'
            "SN": strategy_num,  # Changed to 'SN'
            "D": date.strftime("%H:%M:%S"),  # Changed to 'D', format is now time only
            "P": price,  # Changed to 'P'
            "S": shares,  # Changed to 'S'
            "ES": None,  # Changed to 'ES'
            "NCC": net_cash_change,  # Changed to 'NCC'
            "TF": transaction_fee,  # Changed to 'TF'
            "FC": self.cash  # Changed to 'FC', no change here yet
        }

        if signal_type == "Buy Signal":
            if self.consecutive_buys[ticker] >= 3:
                signal["ES"] = "Consecutive Limit"
            elif price > self.cash:
                signal["ES"] = "Insufficient Funds"
            else:
                self.cash += net_cash_change
                self.consecutive_buys[ticker] += 1
                self.portfolio[ticker]["shares"] += shares
                signal["ES"] = "Execute Buy"
                signal["FC"] = self.cash  # Update 'FC' only if the buy is executed

        elif signal_type == "Sell Signal":
            if self.portfolio[ticker]["shares"] == 0:
                signal["ES"] = "No Shares"
            else:
                self.cash += net_cash_change
                self.portfolio[ticker]["shares"] = 0
                self.consecutive_buys[ticker] = 0
                signal["ES"] = "Execute Sell"
                signal["FC"] = self.cash  # Update 'FC' only if the sell is executed

        else:
            signal["ES"] = "No Order"

        self.order_history.append(signal)

    def run_live(self):
        self.run_backtest()
        # Create a DataFrame from the order history
        order_history_df = pd.DataFrame(self.order_history,
                                        columns=["T", "ST", "SN", "D", "P",
                                                 "S",
                                                 "ES", "NCC", "TF",
                                                 "FC"])

        # Remove unwanted columns
        order_history_df = order_history_df.drop(columns=["NCC", "TF"])

        # Round 'Free Cash' column to 2 decimal places
        order_history_df['FC'] = order_history_df['FC'].round(2)

        # Print the last 10 rows of data every minute
        while True:
            print(order_history_df.tail(Kolonnevisning))
            time.sleep(60)


if __name__ == "__main__":
    # Sort the stocks based on priority before creating the Portfolio
    stocks = sorted(stocks, key=lambda x: x['priority'])

    now = datetime.now(pytz.timezone('Europe/Oslo'))
    end_date = now
    start_date = get_datetime(settings['start_date'])


    portfolio = Portfolio(stocks, start_date, end_date, total_cash)
    portfolio.run_live()
