import importlib
import numpy as np
import pandas as pd
import yfinance as yf
import datetime
from datetime import datetime, timedelta

class StrategyRunner():
    def __init__(self, strategies, available_funds):
        self.strategies = strategies
        self.cash_available = available_funds

    def print_last_rows(self):
        with pd.ExcelWriter("Filer/All_Strategies.xlsx") as writer:
            all_data = pd.DataFrame()  # This DataFrame will hold all data
            for strategy in sorted(self.strategies, key=lambda x: x.priority):
                data_with_signals = strategy.generate_signals()

                if data_with_signals is None:
                    print(f"No backtest data for strategy: {strategy.__class__.__name__}, ticker: {strategy.ticker}")
                    continue


                # Filter data to include only today's data after 9 AM
                today = pd.Timestamp.today()
                data_with_signals = data_with_signals[
                    (data_with_signals.index.date == today.date()) & (data_with_signals.index.hour >= 9)]

                # Add 'Ticker' column
                data_with_signals['Ticker'] = strategy.ticker

                # Creating 'Signal' column
                conditions = [
                    (data_with_signals['Buy_Signal'] == 1),
                    (data_with_signals['Sell_Signal'] == 1)
                ]
                choices = ['Buy', 'Sell']
                data_with_signals['Signal'] = np.select(conditions, choices, default='No Signal')

                # Dropping 'Buy_Signal' and 'Sell_Signal' columns
                data_with_signals = data_with_signals.drop(['Buy_Signal', 'Sell_Signal'], axis=1)

                data_with_signals['Status'] = ''
                data_with_signals['Shares'] = 0
                shares = 0
                consecutive_buys = 0

                from datetime import time

                for index, row in data_with_signals.iterrows():
                    # Ignore signals before 9:00
                    datetime_index = pd.to_datetime(index)
                    time_obj = time(9, 0)  # time object for 9:00
                    if datetime_index.time() < time_obj:
                        continue

                    # Buy or sell shares based on the signal
                    if row['Signal'] == 'Buy':
                        if consecutive_buys < 3 and self.cash_available >= 5000:  # We want to buy shares worth $5000
                            number_of_shares_to_buy = 5000 // row[
                                'Close']  # We buy as many whole shares as $5000 can buy
                            shares += number_of_shares_to_buy
                            purchase_amount = number_of_shares_to_buy * row['Close']  # calculate purchase amount
                            self.cash_available -= purchase_amount  # We reduce our cash available by the purchase amount
                            data_with_signals.at[index, 'Status'] = 'Execute Buy'
                            data_with_signals.at[index, 'Net Cash Change'] = -purchase_amount  # record cash spent
                            consecutive_buys += 1

                        else:
                            data_with_signals.at[
                                index, 'Status'] = 'Consecutive Limit' if consecutive_buys >= 3 else 'Insufficient Funds'
                    elif row['Signal'] == 'Sell':
                        if shares > 0:
                            sales_amount = row['Close'] * shares  # calculate sales amount
                            self.cash_available += sales_amount  # We get money for all our shares
                            shares = 0  # We sold all shares
                            data_with_signals.at[index, 'Status'] = 'Execute Sell'
                            data_with_signals.at[index, 'Net Cash Change'] = sales_amount  # record cash received
                            consecutive_buys = 0  # Reset consecutive buys as a sell has been executed

                        else:
                            data_with_signals.at[index, 'Status'] = 'No Shares'

                    data_with_signals.at[index, 'Shares'] = shares
                    data_with_signals.at[index, 'Cash Available'] = self.cash_available

                    data_with_signals = data_with_signals[
                        ['Ticker', 'Close', 'Signal', 'Status', 'Shares', 'Cash Available', 'Net Cash Change']]
                # Add data to all_data DataFrame
                all_data = pd.concat([all_data, data_with_signals])

                # Save DataFrame to an Excel sheet
                data_with_signals.to_excel(writer, sheet_name=f"{strategy.ticker}_{strategy.__class__.__name__}")

                data_with_signals.index = data_with_signals.index.tz_localize(None)
                last_rows = data_with_signals.tail(3)
                print(f"\nData for {strategy.ticker} using {strategy.__class__.__name__}:")
                print(last_rows)

            # Save all_data DataFrame to the first sheet of the Excel file
            all_data = all_data.sort_index()  # Sort data by date
            all_data.to_excel(writer, sheet_name="All Data")

stocks = [
    {"ticker": "DOGE-USD", "strategy": 11, "interval": "5m", "period": "60d", "priority": 2},
    {"ticker": "SHIB-USD", "strategy": 11, "interval": "5m", "period": "60d", "priority": 1}
]

strategies = []

for stock in stocks:
    priority = stock.pop("priority")
    strategy_num = stock.pop("strategy")
    strategy_module = importlib.import_module(f"strategy{strategy_num}")
    strategy_class = getattr(strategy_module, f"Strategy{strategy_num}")
    strategy = strategy_class(**stock)
    strategy.priority = priority
    strategies.append(strategy)

runner = StrategyRunner(strategies, 25000)
runner.print_last_rows()
