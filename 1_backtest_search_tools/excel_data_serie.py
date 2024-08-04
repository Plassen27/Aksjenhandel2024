import os
import yfinance as yf
import pandas as pd
import sys
import numpy as np
import importlib
from pytz import timezone
from finta import TA

sys.path.append("C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\3_strategies")

STRATEGY_CLASSES = {}
for i in range(1, 16):
    STRATEGY_CLASSES[str(i)] = getattr(importlib.import_module(f"quant_trading.3_strategies.strategy{i}"), f"Strategy{i}")

def main():
    output_dir = 'Filer/excel_data'
    for ticker, strategy_choice, interval in [
        ("AKH.OL", "3", "15m"),
        ("FLNG.OL", "15", "15m"),

    ]:
        try:
            print(f"Processing {ticker} over interval {interval} with strategy {strategy_choice}")
            period = "60d"
            filename = f"{output_dir}/{ticker}_strategy{strategy_choice}_{interval}.xlsx"
            with pd.ExcelWriter(filename) as writer:
                print(f"  Strategy {strategy_choice}")
                generate_strategy_summary(writer, ticker, strategy_choice, interval, period, output_dir)
        except Exception as e:
            print(f"Failed to process {ticker}")
            print(f"Error: {e}")




def convert_to_et(dataframe):
    if dataframe is not None:
        dataframe.index = dataframe.index.tz_convert(None)
        et_tz = timezone('US/Eastern')
        dataframe.index = dataframe.index.tz_localize('UTC').tz_convert(et_tz)
    return dataframe

def business_days(start_date, end_date):
    return len(pd.bdate_range(start_date, end_date))

def generate_strategy_summary(writer, ticker, strategy_choice, interval, period, output_dir):
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

    sheet_name = f"{strategy_choice}_{interval}"
    # Start by adding 'Additional Data' sheet
    additional_data.to_excel(writer, sheet_name=f'{sheet_name}_Additional_Data')

    # Then add the other sheets
    trade_data.to_excel(writer, sheet_name=f'{sheet_name}_Trades')
    histogram.to_excel(writer, sheet_name=f'{sheet_name}_Histogram')
    data_with_signals.to_excel(writer, sheet_name=f'{sheet_name}_Data_with_Signals')
    print(f"Excel sheets for strategy {strategy_choice} generated.")

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
    additional_data.loc['Profitable Trades', 'Value'] = trade_data['profitable'].sum()
    additional_data.loc['Profitable Trades (%)', 'Value'] = trade_data['profitable'].mean() * 100
    additional_data.loc['Average Hold Time (days)', 'Value'] = (trade_data['sell_date'] - trade_data.index).mean().days

    # Profit Factor
    profits = trade_data.loc[trade_data['trade_result'] > 0, 'trade_result'].sum()
    losses = trade_data.loc[trade_data['trade_result'] < 0, 'trade_result'].abs().sum()
    profit_factor = profits / losses if losses != 0 else np.inf
    additional_data.loc['Profit Factor', 'Value'] = profit_factor

    # Number of Gains and Losses
    additional_data.loc['Number of Gains', 'Value'] = (trade_data['trade_result'] > 0).sum()
    additional_data.loc['Number of Losses', 'Value'] = (trade_data['trade_result'] < 0).sum()

    # Win/Loss Ratio
    win_loss_ratio = additional_data.loc['Number of Gains', 'Value'] / additional_data.loc['Number of Losses', 'Value'] if additional_data.loc['Number of Losses', 'Value'] != 0 else np.inf
    additional_data.loc['Win/Loss Ratio', 'Value'] = win_loss_ratio

    # Max Drawdown
    max_drawdown = calculate_max_drawdown(trade_data)
    additional_data.loc['Max Drawdown', 'Value'] = max_drawdown

    data = {}

    # Beregn Sharpe-ratio
    data['Sharpe Ratio'] = calculate_sharpe_ratio(trade_data)

    # Beregn Skewness
    data['Skewness'] = calculate_skewness(trade_data)

    # Beregn Kurtosis
    data['Kurtosis'] = calculate_kurtosis(trade_data)

    # Beregn Calmar-ratio
    period_days = len(trade_data)
    data['Calmar Ratio'] = calculate_calmar_ratio(trade_data)

    # Beregn Omega-ratio
    data['Omega Ratio'] = calculate_omega_ratio(trade_data)

    # Konverter data til en DataFrame
    additional_data_df = pd.DataFrame(data, index=[0])

    # Merge the additional_data and additional_data_df DataFrames
    additional_data_merged = pd.concat([additional_data, additional_data_df.T.rename(columns={0: 'Value'})], axis=0)

    return additional_data_merged

def calculate_max_drawdown(trade_data):
    """Calculates the Maximum Drawdown of a trading strategy."""
    # Calculate cumulative returns
    cumulative_returns = (1 + trade_data['trade_result']).cumprod() - 1

    # Calculate running max
    running_max = np.maximum.accumulate(cumulative_returns)

    # Calculate drawdown
    drawdown = running_max - cumulative_returns

    # Return maximum drawdown
    return drawdown.max()

def calculate_sharpe_ratio(trade_data, risk_free_rate=0.01):
    """Beregner Sharpe-ratio for en tidsserie med avkastning."""
    excess_returns = trade_data['trade_result'] - risk_free_rate
    sharpe_ratio = excess_returns.mean() / excess_returns.std()
    return sharpe_ratio

def calculate_skewness(trade_data):
    """Beregner skjevhet (skewness) for en tidsserie med avkastning."""
    returns = trade_data['trade_result']
    return (3*(returns.mean() - returns.median()) / returns.std())

def calculate_kurtosis(trade_data):
    """Beregner kurtosis for en tidsserie med avkastning."""
    returns = trade_data['trade_result']
    avg_return = returns.mean()
    fourth_moment = (returns - avg_return)**4
    kurtosis = fourth_moment.mean() / (returns.var()**2)
    return kurtosis - 3  # Subtract 3 to calculate excess kurtosis

def calculate_calmar_ratio(trade_data):
    """Beregner Calmar-ratio for en tidsserie med avkastning."""
    returns = trade_data['trade_result']
    annualized_return = ((1 + np.clip(returns, None, 0.075)).prod()) ** (365.25 / len(trade_data)) - 1
    max_drawdown = calculate_max_drawdown(trade_data)
    if abs(max_drawdown) > 0.0:
        calmar_ratio = annualized_return / abs(max_drawdown)
    else:
        calmar_ratio = np.nan  # Undefined if max_drawdown is zero
    return calmar_ratio


def calculate_omega_ratio(trade_data, risk_free_rate=0.0):
    """Beregner Omega-ratio for en tidsserie med avkastning."""
    returns = trade_data['trade_result']
    gain_sum = returns[returns > risk_free_rate].sum()
    loss_sum = -returns[returns < risk_free_rate].sum()
    if loss_sum != 0:
        omega_ratio = gain_sum / loss_sum
    else:
        omega_ratio = np.nan
    return omega_ratio

if __name__ == "__main__":
    main()