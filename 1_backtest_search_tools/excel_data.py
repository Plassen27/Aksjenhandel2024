import os
import yfinance as yf
import pandas as pd
import sys
import numpy as np
import importlib
from pytz import timezone

sys.path.append("C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\3_strategies")

STRATEGY_CLASSES = {}
for i in range(1, 16):
    STRATEGY_CLASSES[str(i)] = getattr(importlib.import_module(f"quant_trading.3_strategies.strategy{i}"), f"Strategy{i}")

def convert_to_et(dataframe):
    if dataframe is not None:
        dataframe.index = dataframe.index.tz_convert(None)
        et_tz = timezone('US/Eastern')
        dataframe.index = dataframe.index.tz_localize('UTC').tz_convert(et_tz)
    return dataframe

def business_days(start_date, end_date):
    return len(pd.bdate_range(start_date, end_date))

def get_user_input():
    while True:
        ticker = input("Enter ticker: ")

        print("Choose a strategy:")
        for i in range(1, 16):
            print(f"{i}: Strategy {i}")
        print("16: All strategies")
        strategy_choice = input("Enter a number: ")

        print("Choose an interval:")
        print("1: 15m")
        print("2: 30m")
        print("3: 1h")
        print("4: 1d")
        interval_choice = input("Enter a number: ")

        intervals = [("15m", "60d"), ("30m", "60d"), ("60m", "720d"), ("1d", "3y")]

        if interval_choice in ["1", "2", "3", "4"] and strategy_choice in [str(i) for i in range(1, 17)]:
            interval, period = intervals[int(interval_choice) - 1]
            return ticker, strategy_choice, interval, period
        else:
            print("Invalid input. Please try again.")

def main():
    ticker, strategy_choice, interval, period = get_user_input()
    if ticker is None:
        return
    if strategy_choice == "16":
        for i in range(1, 16):
            generate_strategy_summary(ticker, str(i), interval, period)
    else:
        generate_strategy_summary(ticker, strategy_choice, interval, period)

def generate_strategy_summary(ticker, strategy_choice, interval, period):
    output_dir = 'Filer.Excel_data'

    if strategy_choice not in STRATEGY_CLASSES:
        print("Invalid strategy choice.")
        return

    strategy_class = STRATEGY_CLASSES[str(strategy_choice)]
    strategy = strategy_class(ticker, interval, period)
    data_with_signals = strategy.generate_signals()

    if data_with_signals is None:
        print(f"No backtest data for strategy: {strategy_choice}, ticker: {ticker}, interval: {interval}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data_with_signals.index = data_with_signals.index.tz_localize(None).strftime('%Y-%m-%d %H:%M:%S')

    trade_data = strategy.generate_trades()

    bins = list(np.arange(-0.05, 0.05, 0.0025))
    bins += list(np.arange(0.05, 0.10, 0.01))
    bins += [np.inf]
    trade_data['bin'] = pd.cut(trade_data['trade_result'], bins=bins, labels=bins[1:])
    histogram = trade_data['bin'].value_counts().sort_index()

    strategy.data['Return'] = strategy.data['Close'].pct_change()

    additional_data = calculate_additional_data_new(strategy, trade_data, interval, period)

    with pd.ExcelWriter(f"{output_dir}/{ticker}_{strategy_choice}_{interval}_summary.xlsx") as writer:
        trade_data.to_excel(writer, sheet_name='Trades')
        histogram.to_excel(writer, sheet_name='Histogram')
        additional_data.to_excel(writer, sheet_name='Additional Data')
        data_with_signals.to_excel(writer, sheet_name='Data with Signals')
        print(f"Excel file generated: {output_dir}/{ticker}_{strategy_choice}_{interval}_summary.xlsx")


def calculate_additional_data(strategy, trade_data, interval, period):
    additional_data = pd.DataFrame(columns=['Value'])

    # Calculate benchmark returns
    benchmark_data = yf.download('OBX.OL', interval=interval, period=period)

    if benchmark_data.empty:
        print("Benchmark data is empty.")
        return additional_data

    benchmark_return = benchmark_data['Close'].pct_change().dropna()

    # Calculate alpha and beta
    benchmark_return = benchmark_return.reindex(strategy.data.index)
    strategy.data['Return'] = strategy.data['Return'].reindex(benchmark_return.index)

    # Drop NaN values
    combined_data = pd.concat([benchmark_return, strategy.data['Return']], axis=1).dropna()

    # Add check for empty dataframe
    if combined_data.empty:
        print("Combined data is empty. Could not calculate alpha and beta.")
        return additional_data

    try:
        beta, alpha = np.polyfit(combined_data['Close'], combined_data['Return'], 1)
        additional_data.loc['Alpha', 'Value'] = alpha
        additional_data.loc['Beta', 'Value'] = beta
    except Exception as e:
        print(f"Error calculating alpha and beta: {e}")

    return additional_data


def calculate_additional_data_new(strategy, trade_data, interval, period):
    additional_data = calculate_additional_data(strategy, trade_data, interval, period)

    trade_data['profitable'] = trade_data['trade_result'] > 0
    trade_data.index = pd.to_datetime(trade_data.index)
    trade_data['sell_date'] = pd.to_datetime(trade_data['sell_date'])

    # Additional calculations...
    additional_data.loc['Number of Trades', 'Value'] = len(trade_data)
    additional_data.loc['Average Profit Per Trade', 'Value'] = trade_data['trade_result'].mean()
    additional_data.loc['Profitable Trades', 'Value'] = trade_data['profitable'].mean()

    losing_trades_total = abs(trade_data.loc[~trade_data['profitable'], 'trade_result'].sum())

    if losing_trades_total != 0:  # Avoid division by zero
        additional_data.loc['Profit Factor', 'Value'] = trade_data.loc[trade_data['profitable'], 'trade_result'].sum() / losing_trades_total
    else:
        additional_data.loc['Profit Factor', 'Value'] = np.inf

    average_trade_duration_sec = (trade_data.index.to_series().diff().dt.total_seconds().mean())
    average_trade_duration_days = average_trade_duration_sec / (60 * 60 * 24)

    if isinstance(strategy.data, pd.DataFrame):
        additional_data.loc['Total Stock Return Over Period', 'Value'] = (strategy.data['Close'].iloc[-1] / strategy.data['Close'].iloc[0] - 1) * 100
    else:  # strategy.data is a Series
        additional_data.loc['Total Stock Return Over Period', 'Value'] = (strategy.data.iloc[-1] / strategy.data.iloc[0] - 1) * 100

    roll_max = trade_data['trade_result'].cummax()
    drawdown = trade_data['trade_result'] - roll_max
    max_drawdown = drawdown.min()

    additional_data.loc['Max Drawdown', 'Value'] = max_drawdown

    returns = trade_data['trade_result'].pct_change()
    sharpe_ratio = returns.mean() / returns.std()

    additional_data.loc['Sharpe Ratio', 'Value'] = sharpe_ratio

    num_gains = trade_data['profitable'].sum()
    num_losses = len(trade_data) - num_gains

    additional_data.loc['Number of Gains', 'Value'] = num_gains
    additional_data.loc['Number of Losses', 'Value'] = num_losses

    win_loss_ratio = num_gains / num_losses if num_losses != 0 else np.inf

    additional_data.loc['Win/Loss Ratio', 'Value'] = win_loss_ratio

    if 'hold_duration' in trade_data.columns:
        if isinstance(trade_data['hold_duration'].iloc[0], pd.Timedelta):
            trade_data['hold_duration'] = trade_data['hold_duration'].dt.days
        average_hold_duration = trade_data['hold_duration'].mean()
        additional_data.loc['Average Hold Duration (days)', 'Value'] = average_hold_duration
    else:
        trade_data['sell_date'] = pd.to_datetime(trade_data['sell_date'])
        trade_data['hold_duration'] = trade_data['sell_date'].sub(trade_data.index).dt.days
        trade_data = trade_data.loc[:, ['Buy_Signal', 'buy_price', 'Sell_Signal', 'sell_price', 'trade_result', 'hold_duration']]
        average_hold_duration = trade_data['hold_duration'].mean()
        additional_data.loc['Average Hold Duration (days)', 'Value'] = average_hold_duration

        # Calculate skewness and kurtosis
        returns = trade_data['trade_result'].pct_change().dropna()
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        additional_data.loc['Skewness', 'Value'] = skewness
        additional_data.loc['Kurtosis', 'Value'] = kurtosis

        # Calculating the Calmar ratio (annual return rate / maximum drawdown)
        # assuming 'Return' column in strategy.data contains daily returns
        annual_return = strategy.data['Return'].mean() * 252
        max_drawdown = calculate_max_drawdown(strategy.data['Return'].dropna())  # assuming this function is defined
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else np.inf

        additional_data.loc['Calmar Ratio', 'Value'] = calmar_ratio

        # Omega ratio needs a risk-free rate, assuming risk-free rate to be 1%
        risk_free_rate = 0.01
        excess_return = returns - risk_free_rate
        upside_potential = excess_return[excess_return > 0].sum()
        downside_risk = abs(excess_return[excess_return < 0].sum())
        omega_ratio = upside_potential / downside_risk if not np.isnan(downside_risk) and downside_risk != 0 else np.inf
        if not np.isnan(downside_risk) and not np.isinf(downside_risk) and downside_risk != 0:
            omega_ratio = upside_potential / downside_risk
        else:
            omega_ratio = np.inf

        additional_data.loc['Omega Ratio', 'Value'] = omega_ratio

        return additional_data


def calculate_max_drawdown(return_series):
    comp_ret = (1 + return_series).cumprod()
    peak = comp_ret.expanding().max()
    dd = (comp_ret / peak) - 1
    max_dd = dd.min()
    return max_dd




if __name__ == "__main__":
    main()