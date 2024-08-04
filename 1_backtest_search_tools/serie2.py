import os
import pandas as pd
import importlib
import sys
sys.path.append("C:\\Users\\Johannes\\PycharmProjects\\pythonProject\\Aksjehandel-Quant-main\\3_strategies")


TICKERS = ["DNO.OL", "AUTO.OL", "KAHOT.OL", "NEL.OL", "FRO.OL", "GOGL.OL", "PGS.OL", "RECSI.OL",
           "BORR.OL", "KIT.OL", "NOD.OL", "EQNR.OL", "AKRBP.OL", "SUBC.OL", "TGS.OL", "MPCC.OL",
           "NAS.OL", "BWLPG.OL", "SHLF.OL", "TOM.OL", "MOWI.OL", "SDRL.OL", "HAUTO.OL", "FLNG.OL", "ORK.OL", "YAR.OL", "AKSO.OL"]

STRATEGY_CLASSES = {}
for i in range(1, 16):
    STRATEGY_CLASSES[str(i)] = getattr(importlib.import_module(f"Aksjehandel-Quant-main.3_strategies.strategy{i}"), f"Strategy{i}")

def get_user_input():
    print("Choose a stock:")
    for i, ticker in enumerate(TICKERS, 1):
        print(f"{i}: {ticker}")

    print(f"{len(TICKERS) + 1}: All stocks")

    stock_choice = input("Enter a number: ")

    if not stock_choice.isdigit() or int(stock_choice) < 1 or int(stock_choice) > len(TICKERS) + 1:
        print("Invalid stock choice. Please enter a number between 1 and {len(TICKERS) + 1}.")
        return None, None

    intervals = [("15m", "60d"), ("30m", "60d"), ("60m", "720d"), ("1d", "3y")]

    if int(stock_choice) == len(TICKERS) + 1:
        return TICKERS, STRATEGY_CLASSES.values(), intervals

    chosen_ticker = TICKERS[int(stock_choice) - 1]
    return [chosen_ticker], STRATEGY_CLASSES.values(), intervals

def generate_strategy_summary(chosen_ticker, strategy_classes, intervals):
    output_dir = 'Filer/Serie2'

    # Check if the output directory exists, if not, create it.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with pd.ExcelWriter(f"{output_dir}/{chosen_ticker}_summary.xlsx", engine='xlsxwriter') as writer:
        for interval, period in intervals:
            summary_data = pd.DataFrame()
            for strategy_class in strategy_classes:
                strategy_name = strategy_class.__name__

                strategy = strategy_class(chosen_ticker, interval, period)
                try:
                    data_with_signals = strategy.generate_signals()
                    trade_data = strategy.generate_trades()
                except Exception as e:
                    print(f"Failed to generate trades for strategy: {strategy_class.__name__}, "
                          f"ticker: {chosen_ticker}, interval: {interval}, period: {period}")
                    print(f"Error: {e}")
                    continue

                if data_with_signals is None or trade_data is None:
                    print(
                        f"No backtest data for strategy: {strategy_name}, ticker: {chosen_ticker}, interval: {interval}, period: {period}")
                    continue

                additional_data = calculate_additional_data(trade_data)
                additional_data_transposed = additional_data.transpose()

                # Add strategy name to the DataFrame
                additional_data_transposed['Strategy'] = strategy_name

                # Add data for current ticker to summary
                summary_data = pd.concat([summary_data, additional_data_transposed], axis=0)

            # Set strategy names as index
            summary_data.set_index('Strategy', inplace=True)

            write_to_excel(writer, interval, period, summary_data)

        print(f"Excel file generated: {output_dir}/{chosen_ticker}_summary.xlsx")


def write_to_excel(writer, interval, period, summary_data):
    # Set column names
    # Set column names
    summary_data.columns = ['Profitable Trades', 'Average Profit Per Trade', 'Number of Trades',
                            'Average Hold Duration (days)', 'Max Drawdown']

    # Sort the DataFrame by 'Average Profit Per Trade' in descending order
    summary_data.sort_values('Average Profit Per Trade', ascending=False, inplace=True)

    # Write to the sheet for the current interval and period
    summary_data.to_excel(writer, sheet_name=f"{interval}_{period}")

def main():
    chosen_tickers, strategy_classes, intervals = get_user_input()
    if chosen_tickers is None:
        return
    for ticker in chosen_tickers:
        generate_strategy_summary(ticker, strategy_classes, intervals)

def calculate_additional_data(trade_data):
    additional_data = pd.DataFrame(columns=['Value'])

    trade_data['profitable'] = trade_data['trade_result'] > 0
    trade_data['return_series'] = (1 + trade_data['trade_result']).cumprod() - 1

    additional_data.loc['Profitable Trades', 'Value'] = trade_data['profitable'].mean()
    additional_data.loc['Average Profit Per Trade', 'Value'] = trade_data['trade_result'].mean()
    additional_data.loc['Number of Trades', 'Value'] = len(trade_data)

    trade_data.index = pd.to_datetime(trade_data.index)

    # Check for 'sell_date' in trade_data and calculate hold_duration
    if 'sell_date' in trade_data.columns:
        trade_data['sell_date'] = pd.to_datetime(trade_data['sell_date'])
        trade_data['hold_duration'] = trade_data['sell_date'].sub(trade_data.index).dt.days

        average_hold_duration = trade_data['hold_duration'].mean()
        additional_data.loc['Average Hold Duration (days)', 'Value'] = average_hold_duration
    else:
        print("No 'sell_date' found in trade_data. Cannot calculate hold_duration.")

    additional_data.loc['Max Drawdown', 'Value'] = calculate_max_drawdown(trade_data['return_series'])

    return additional_data

def calculate_max_drawdown(return_series):
    comp_ret = (1 + return_series).cumprod()
    peak = comp_ret.expanding().max()
    dd = (comp_ret / peak) - 1
    max_dd = dd.min()
    return max_dd

if __name__ == "__main__":
    main()


