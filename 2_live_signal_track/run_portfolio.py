import pandas as pd
import importlib
import pytz
import sys
import yfinance as yf
from datetime import datetime
from datetime import timedelta
from pandas import ExcelWriter
from collections import defaultdict
from inputs import stocks, start_date, total_cash, order_size, kurtajse, order_size_minimum
from yfinance import download
from pandas.tseries.offsets import BDay

sys.path.append("C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\3_strategies")

# Import all strategies using importlib
strategies = {}
for i in range(1, 16):
    strategies[i] = getattr(importlib.import_module(f"strategy{i}"), f"Strategy{i}")

class Portfolio:
    def __init__(self, stocks, start_date, end_date, cash):
        self.stocks = stocks
        self.start_date = start_date
        self.end_date = end_date
        self.cash = cash
        self.trades = []
        self.portfolio = {}
        self.order_history = []
        self.consecutive_buys = defaultdict(int)
        self.preload_periods = 200  # Add this line

        for stock in self.stocks:
            self.portfolio[stock["ticker"]] = {"shares": 0}

        # Initialize a new attribute to hold all the stock data
        self.stock_data = self.get_stock_data()

    def generate_excel(self):
        with ExcelWriter('Portfolio_Backtest.xlsx') as writer:
            order_history_df = pd.DataFrame(self.order_history,
                                            columns=["Ticker", "Signal Type", "Strategy Number", "Date", "Price",
                                                     "Shares",
                                                     "Total Shares",
                                                     "Execution Status", "Net Cash Change", "Transaction Fee",
                                                     "Free Cash"])

            # Remove timezone information
            order_history_df['Date'] = order_history_df['Date'].dt.tz_localize(None)

            # Create a copy for new sheet
            order_execute_df = order_history_df.copy()

            # Filter 'Execution Status' only for 'Execute Buy' or 'Execute Sell'
            order_execute_df = order_execute_df[
                (order_execute_df["Execution Status"] == "Execute Buy") |
                (order_execute_df["Execution Status"] == "Execute Sell")]

            # Drop the 'Signal Type' column
            order_execute_df = order_execute_df.drop(columns="Signal Type")

            order_history_df.to_excel(writer, sheet_name='Order History', index=False)
            order_execute_df.to_excel(writer, sheet_name='Executed Orders', index=False)

            trades_df = pd.DataFrame(self.trades,
                                     columns=["Ticker", "Buy Date", "Buy Price", "Sell Date", "Sell Price",
                                              "Trade Result", "Shares"])

            # Remove timezone information
            trades_df['Buy Date'] = trades_df['Buy Date'].dt.tz_localize(None)
            trades_df['Sell Date'] = trades_df['Sell Date'].dt.tz_localize(None)

            # Sort by 'Buy Date' and then 'Ticker'
            trades_df = trades_df.sort_values(["Buy Date", "Ticker"])

            # Now calculate 'Cash Change' and 'Cumulative Cash':
            trades_df['Cash Change'] = trades_df['Trade Result'] * trades_df['Buy Price'] * trades_df['Shares']
            trades_df['Cumulative Cash'] = trades_df['Cash Change'].cumsum() + total_cash

            trades_df.to_excel(writer, sheet_name='Trades', index=False)

            summary_df = self.generate_summary_sheet()
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            price_summary_df = self.generate_price_summary()
            price_summary_df.to_excel(writer, sheet_name='Price Summary', index=True)
    def get_stock_data(self):
        """
        Download the stock data for all the stocks in the portfolio.
        """
        data = {}
        for stock in self.stocks:
            ticker_data = yf.download(stock["ticker"], start=self.start_date, end=self.end_date,
                                      interval=stock["interval"], period=stock["period"])
            data[stock["ticker"]] = ticker_data

        return data
    def generate_price_summary(self):
        price_summary = {}

        # Fetch close price data for each stock and calculate the required values
        for stock in self.stocks:
            data = self.stock_data[stock['ticker']]
            price_summary[stock['ticker']] = {
                'First Close Price': data['Close'].iloc[0],
                'Last Close Price': data['Close'].iloc[-1],
                'Highest Close Price': data['Close'].max(),
                'Lowest Close Price': data['Close'].min(),
                'Return': (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
            }

        # Convert to DataFrame
        price_summary_df = pd.DataFrame(price_summary).T

        # Convert 'Return' to percentage
        price_summary_df['Return'] = price_summary_df['Return'].apply(lambda x: round(x * 100, 2))

        # Transpose DataFrame
        price_summary_df = price_summary_df.T

        # Compute the average return
        average_return = price_summary_df.loc['Return'].mean()

        # Add the average return to the DataFrame
        price_summary_df['Average Return'] = round(average_return, 2)

        return price_summary_df

    def get_priority_of_stock(self, ticker):
        for stock in self.stocks:
            if stock['ticker'] == ticker:
                return stock['priority']
        return None
    def get_strategy_number_of_stock(self, ticker):
        for stock in self.stocks:
            if stock['ticker'] == ticker:
                return stock['strategy']
        return None
    def calculate_max_drawdown(self, cash_hist):
        max_value = max(cash_hist)
        min_after_max = min(cash_hist[cash_hist.index > cash_hist[cash_hist == max_value].index[0]])

        return (min_after_max - max_value) / max_value
    def generate_summary_sheet(self):
        summary_df = pd.DataFrame(columns=["Total Return", "Benchmark Return", "Excess Return",
                                           "Max Drawdown", "Average Profit per Trade", "Profitable Trades %",
                                           "Profit Factor"])

        trades_df = pd.DataFrame(self.trades,
                                 columns=["Ticker", "Buy Date", "Buy Price", "Sell Date", "Sell Price",
                                          "Trade Result", "Shares"])

        trades_df['Cash Change'] = trades_df['Trade Result'] * trades_df['Buy Price'] * trades_df['Shares']
        trades_df['Cumulative Cash'] = trades_df['Cash Change'].cumsum() + total_cash

        # Calculate total return
        total_return = (trades_df['Cumulative Cash'].dropna().iloc[-1] - total_cash) / total_cash

        # Calculate benchmark return (assuming OBX.OL is the benchmark)
        benchmark_start = self.get_price('OBX.OL', self.start_date)  # Corrected function call
        benchmark_end = self.get_price('OBX.OL', self.end_date)  # function to get the price at a certain date
        benchmark_return = benchmark_end / benchmark_start - 1

        # Calculate excess return
        excess_return = total_return - benchmark_return

        # Calculate max drawdown
        max_drawdown = (trades_df['Cumulative Cash'].min() - total_cash) / total_cash

        # Calculate average profit per trade
        average_profit_per_trade = trades_df[trades_df['Trade Result'] > 0]['Trade Result'].mean()

        # Calculate % of profitable trades
        profitable_trades_pct = len(trades_df[trades_df['Trade Result'] > 0]) / len(trades_df)

        # Calculate profit factor
        profit_factor = trades_df[trades_df['Trade Result'] > 0]['Cash Change'].sum() / abs(
            trades_df[trades_df['Trade Result'] < 0]['Cash Change'].sum())

        summary_df.loc[0] = [total_return, benchmark_return, excess_return,
                             max_drawdown, average_profit_per_trade, profitable_trades_pct,
                             profit_factor]

        # Transpose the DataFrame before returning
        return summary_df.T

    def get_price(self, ticker, date):
        # We should fetch data for 5 business days, as sometimes Yahoo finance doesn't have data for a specific date.
        # We use '5 B' to get 5 business days, not counting weekends.
        end_date = date + BDay(5)

        # Fetch data from Yahoo Finance
        data = download(tickers=ticker, start=date, end=end_date)

        # Return the first 'Close' price we have, assuming we have any data
        if not data.empty:
            return data.iloc[0]['Close']

        return None
    def add_signal(self, ticker, date, price, strategy_num, signal_type):
        # Set the transaction fee rate
        transaction_fee_rate = kurtajse

        # Calculate shares given an order size of 5000, rounded down to whole share amounts
        shares = min(self.cash // price, order_size // price) if signal_type == 'Buy Signal' else \
            self.portfolio[ticker]["shares"]

        # Calculate transaction fee
        transaction_fee = shares * price * transaction_fee_rate

        # Calculate net cash change
        net_cash_change = -(
                shares * price + transaction_fee) if signal_type == 'Buy Signal' else shares * price - transaction_fee

        # Create a new order
        signal = {
            "Ticker": ticker,
            "Signal Type": signal_type,
            "Strategy Number": strategy_num,
            "Date": date,
            "Price": price,
            "Shares": shares,
            "Total Shares": None,
            "Execution Status": "No Order" if signal_type == "No Signal" else None,
            "Net Cash Change": net_cash_change,
            "Transaction Fee": transaction_fee,
            "Free Cash": self.cash + net_cash_change if self.cash + net_cash_change >= 0 else None,
        }

        # rest of your add_signal() method...

        if signal_type == "Buy Signal":
            # Calculate total order value
            total_order_value = shares * price

            # Check if the total order value is below the minimum order size
            if total_order_value < order_size_minimum:
                signal["Execution Status"] = "Insufficient Funds"
            elif self.consecutive_buys[ticker] >= 3:
                signal["Execution Status"] = "Consecutive Limit"
            elif price > self.cash:
                signal["Execution Status"] = "Insufficient Funds"
            else:
                self.cash += net_cash_change
                self.consecutive_buys[ticker] += 1
                self.portfolio[ticker]["shares"] += shares
                signal["Execution Status"] = "Execute Buy"
                signal["Total Shares"] = self.portfolio[ticker]["shares"]
                # Record a trade for buys
                self.trades.append({
                    "Ticker": ticker,
                    "Buy Date": date,
                    "Buy Price": price,
                    "Sell Date": None,
                    "Sell Price": None,
                    "Trade Result": None,
                    "Shares": shares
                })

        elif signal_type == "Sell Signal":
            if self.portfolio[ticker]["shares"] == 0:
                signal["Execution Status"] = "No Shares"
            else:
                self.cash += net_cash_change
                self.portfolio[ticker]["shares"] = 0
                self.consecutive_buys[ticker] = 0
                signal["Execution Status"] = "Execute Sell"
                signal["Total Shares"] = 0
                # Record a trade for sells
                for trade in reversed(self.trades):
                    if trade["Ticker"] == ticker and trade["Sell Date"] is None:
                        trade["Sell Date"] = date
                        trade["Sell Price"] = price
                        trade["Trade Result"] = (price - trade["Buy Price"]) / trade["Buy Price"]
                        break
                # Check for previous trades without a sell date and update them
                for trade in self.trades:
                    if trade["Ticker"] == ticker and trade["Sell Date"] is None:
                        trade["Sell Date"] = date
                        trade["Sell Price"] = price
                        trade["Trade Result"] = (price - trade["Buy Price"]) / trade["Buy Price"]

        self.order_history.append(signal)
    def run_backtest(self):
            all_signals = []
            for stock in self.stocks:
                ticker = stock["ticker"]
                strategy_num = stock["strategy"]
                strategy = strategies[strategy_num](ticker, stock["interval"], stock["period"])

                signals = strategy.generate_signals()
                signals["ticker"] = ticker

                # Filter signals based on start and end dates
                signals = signals.loc[(signals.index.tz_localize('Europe/Oslo') >= self.start_date) & (
                            signals.index.tz_localize('Europe/Oslo') <= self.end_date)]

                # Append all signals into a list
                all_signals.append(signals)

            # Combine all signals into a single DataFrame
            all_signals_df = pd.concat(all_signals)

            # Sort the DataFrame by index (Date)
            all_signals_df = all_signals_df.sort_index()

            for index, row in all_signals_df.iterrows():
                date = index
                ticker = row['ticker']
                price = row['Close']
                if row['Buy_Signal']:
                    self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'Buy Signal')
                elif row['Sell_Signal']:
                    self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'Sell Signal')
                else:
                    self.add_signal(ticker, date, price, self.get_strategy_number_of_stock(ticker), 'No Signal')

if __name__ == "__main__":
    # Sort the stocks based on priority before creating the Portfolio
    stocks = sorted(stocks, key=lambda x: x['priority'])

    now = datetime.now(pytz.timezone('Europe/Oslo'))
    end_date = now

    portfolio = Portfolio(stocks, start_date, end_date, total_cash)  # Creating an instance of the Portfolio class
    portfolio.run_backtest()  # Calling the run_backtest method on the instance
    portfolio.generate_excel()
