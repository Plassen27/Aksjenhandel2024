import pandas as pd
import yfinance as yf
import numpy as np
import importlib
import sys
from collections import defaultdict
from pandas import ExcelWriter
from portfolio_inputs import stocks, start_date, end_date, total_cash, order_size

strategies = {}

sys.path.append("C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\3_strategies")

class Portfolio:
    def __init__(self, stocks, start_date, end_date):
        self.stocks = stocks
        self.start_date = start_date
        self.end_date = end_date
        self.cash = total_cash
        self.shares = {}
        self.equity = defaultdict(int)
        self.order_history = []
        self.portfolio = {}
        self.trades = pd.DataFrame()

        for stock in self.stocks:
            self.portfolio[stock["ticker"]] = {"shares": 0}

    def buy_stock(self, ticker, date, buy_price, strategy_num):
        shares = order_size // buy_price  # calculate shares so total cost is under 5000
        net_cash_change = -(shares * buy_price)  # negative because cash is decreasing

        if self.cash + net_cash_change < 0:  # Check if there is sufficient free cash
            self.order_history.append({
                "Ticker": ticker,
                "Action": "Buy",
                "Date": date,
                "Price": buy_price,
                "Shares": shares,
                "Total Shares": self.portfolio[ticker]["shares"],
                "Status": "Failed - Insufficient Funds",
                "Net Cash Change": net_cash_change,
                "Free Cash": self.cash  # Current free cash
            })
        else:
            self.cash += net_cash_change  # Update free cash
            self.portfolio[ticker]["shares"] += shares  # Update the total shares in the portfolio
            self.order_history.append({
                "Ticker": ticker,
                "Action": "Buy",
                "Date": date,
                "Price": buy_price,
                "Shares": shares,
                "Total Shares": self.portfolio[ticker]["shares"],
                "Status": "Executed",
                "Net Cash Change": net_cash_change,
                "Free Cash": self.cash  # Current free cash
            })

    def sell_stock(self, ticker, date, sell_price, strategy_num):
        shares = self.portfolio[ticker]["shares"]
        net_cash_change = shares * sell_price  # Positive because cash is increasing
        self.cash += net_cash_change  # Update free cash
        self.portfolio[ticker]["shares"] = 0  # Empty the position

        self.order_history.append({
            "Ticker": ticker,
            "Action": "Sell",
            "Date": date,
            "Price": sell_price,
            "Shares": shares,
            "Total Shares": self.portfolio[ticker]["shares"],
            "Status": "Executed",
            "Net Cash Change": net_cash_change,
            "Free Cash": self.cash  # Current free cash
        })

    def run_backtest(self):
        for stock in self.stocks:
            ticker = stock["ticker"]
            strategy_num = stock["strategy"]
            strategy = strategies[strategy_num](ticker, stock["interval"], stock["period"])

            trades = strategy.generate_trades()
            trades["ticker"] = ticker

            # Filter trades based on start and end dates
            trades = trades.loc[(trades.index >= self.start_date) & (trades.index <= self.end_date)]

            for date, row in trades.iterrows():
                if date.date() != self.end_date.date():  # Exclude last trading day for regular buy/sell signals
                    self.buy_stock(ticker, date, row["buy_price"], strategy_num)
                    self.sell_stock(ticker, row['sell_date'], row["sell_price"], strategy_num)
                else:  # For the last trading day, execute sell order at 16:00 regardless of buy/sell signals
                    self.sell_stock(ticker, date, row['sell_price'], strategy_num)

            # Remove 'Buy_Signal', 'Sell_Signal' columns
            trades = trades.drop(columns=['Buy_Signal', 'Sell_Signal'])

            # Calculate 'Trade Result in Cash'
            trades['Trade Result in Cash'] = trades['Shares'] * (trades['sell_price'] - trades['buy_price'])

            # Reorder columns to have 'Buy_Date' as the first column
            cols = ['Buy_Date'] + [col for col in trades.columns if col != 'Buy_Date']
            trades = trades[cols]

            self.trades = pd.concat([self.trades, trades])

        self.order_history = sorted(self.order_history, key=lambda x: x['Date'])

        for i, order in enumerate(self.order_history):
            if i == 0:  # For the first order, "Free Cash" is the starting cash balance (100000) plus "Net Cash Change"
                order["Free Cash"] = total_cash + order["Net Cash Change"]  # changed from order_size to total_cash
            else:  # For subsequent orders, "Free Cash" is the previous "Free Cash" plus the current "Net Cash Change"
                order["Free Cash"] = self.order_history[i - 1]["Free Cash"] + order["Net Cash Change"]

            if order["Free Cash"] < 0:  # This is to avoid negative cash situation.
                order["Status"] = "Failed - Insufficient funds"
                order["Net Cash Change"] = 0
                order["Free Cash"] = 0  # reset Free Cash to 0 if it's negative.

    def get_benchmark_data(self):
        data = yf.download('OBX.OL', self.start_date, self.end_date)
        return data['Close']

    def calculate_portfolio_return(self):
        self.trades['Return'] = self.trades['Net Cash Change'].pct_change()
        self.trades = self.trades.dropna(subset=['Return'])

    def calculate_benchmark_return(self):
        benchmark_data = self.get_benchmark_data()
        benchmark_return = benchmark_data.pct_change().dropna()
        return benchmark_return

    def calculate_alpha_beta(self):
        benchmark_return = self.calculate_benchmark_return()
        portfolio_return = self.trades['Return']

        # Ensuring both returns series have the same index
        benchmark_return = benchmark_return.reindex(portfolio_return.index)
        portfolio_return = portfolio_return.reindex(benchmark_return.index)

        # Reshaping data for regression
        X = benchmark_return.values
        y = portfolio_return.values

        # Linear regression with np.polyfit
        beta, alpha = np.polyfit(X, y, 1)

        return alpha, beta

    def generate_summary(self):
        total_trades = len(self.order_history)
        failed_trades = len([trade for trade in self.order_history if trade['Status'] != 'Executed'])
        avg_profit_per_trade = self.trades['Net Cash Change'].sum() / total_trades * 100
        alpha, beta = self.calculate_alpha_beta()
        sharpe_ratio = self.calculate_sharpe_ratio()

        summary_df = pd.DataFrame({
            "Total Profit": [self.trades['Net Cash Change'].sum()],
            "Total Trades": [total_trades],
            "Failed Trades": [failed_trades],
            "Failed Trades (%)": [failed_trades / total_trades * 100],
            "Average Profit per Trade (%)": [avg_profit_per_trade],
            "Alpha": [alpha],
            "Beta": [beta],
            "Sharpe Ratio": [sharpe_ratio]
        }).transpose()

        with pd.ExcelWriter('Portfolio_Backtest.xlsx', engine='openpyxl', mode='a') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', header=False)

    def calculate_sharpe_ratio(self):
        portfolio_return = self.trades['Return']
        sharpe_ratio = portfolio_return.mean() / portfolio_return.std()
        return sharpe_ratio

    def generate_excel(self):
        with ExcelWriter('Portfolio_Backtest.xlsx') as writer:
            order_history_df = pd.DataFrame(self.order_history,
                                            columns=["Ticker", "Action", "Date", "Price", "Shares",
                                                     "Status", "Net Cash Change", "Free Cash"])

            order_history_df.to_excel(writer, sheet_name='Order History', index=False)
            self.trades.to_excel(writer, sheet_name='Trades_Backtest', index=False)

            # Summary calculations
            total_profit = self.trades['Trade Result in Cash'].sum()
            total_trades = len(order_history_df) // 2  # Since each trade consists of a pair of buy/sell orders
            failed_trades = len(order_history_df[order_history_df['Status'] != 'Executed']) // 2
            failed_trades_percent = failed_trades / total_trades * 100
            avg_profit_per_trade = total_profit / (total_trades - failed_trades)  # For whole trade (buy and sell)

            # Max Drawdown
            self.trades['Cumulative Profit'] = self.trades['Trade Result in Cash'].cumsum()
            max_value = self.trades['Cumulative Profit'].cummax()
            drawdown = (self.trades['Cumulative Profit'] - max_value) / max_value
            max_drawdown = drawdown.min()

            # Beta and Alpha calculation
            benchmark_data = yf.download('OBX.OL', start=self.start_date, end=self.end_date)['Close'].pct_change()
            portfolio_data = self.trades['Trade Result in Cash'].pct_change()

            benchmark_data = benchmark_data.dropna()
            portfolio_data = portfolio_data.dropna()

            # Ensure both series have the same index
            benchmark_data = benchmark_data.reindex(portfolio_data.index, method='nearest')
            portfolio_data = portfolio_data.reindex(benchmark_data.index, method='nearest')

            benchmark_returns = benchmark_data.values
            portfolio_returns = portfolio_data.values

            beta, alpha = np.polyfit(benchmark_returns, portfolio_returns, 1)

            summary = pd.DataFrame({
                'Total Profit in Period (NOK)': [total_profit],
                'Total Profit in Period (%)': [total_profit / total_cash],  # Assuming initial capital is 100_000 NOK
                'Total Trades in Period': [total_trades],
                'Failed Trades': [failed_trades],
                'Failed Trades (%)': [failed_trades_percent],
                'Average Profit per Trade (%)': [avg_profit_per_trade / 100],
                'Max Drawdown (%)': [max_drawdown / 100],
                'Beta': [beta / 100],
                'Alpha': [alpha]
            })

            summary.to_excel(writer, sheet_name='Summary', index=False)




portfolio = Portfolio(stocks, start_date, end_date)
portfolio.run_backtest()
portfolio.generate_excel()