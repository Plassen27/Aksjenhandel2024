import os
import pandas as pd
import importlib
import sys

sys.path.append("C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\3_strategies")

TICKERS = ["DNO.OL", "AUTO.OL", "KAHOT.OL", "NEL.OL", "FRO.OL", "GOGL.OL", "PGS.OL", "RECSI.OL",
           "BORR.OL", "KIT.OL", "NOD.OL", "NHY.OL", "AKRBP.OL", "SUBC.OL", "TGS.OL", "MPCC.OL",
           "NAS.OL", "BWLPG.OL", "SHLF.OL", "TOM.OL", "MOWI.OL", "SDRL.OL", "HAUTO.OL", "SCATC.OL", "VAR.OL", "AKH.OL", "AKSO.OL"]

STRATEGY_CLASSES = {}
for i in range(1, 16):
    STRATEGY_CLASSES[str(i)] = getattr(importlib.import_module(f"quant_trading.3_strategies.strategy{i}"), f"Strategy{i}")


def calculate_additional_data(trade_data):
    additional_data = pd.DataFrame(columns=['Value'])

    trade_data['profitable'] = trade_data['trade_result'] > 0

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

    return additional_data


def get_user_input():
    print("Choose a strategy:")
    for i in range(1, 16):
        print(f"{i}: Strategy {i}")

    print("16: Run all strategies")

    strategy_choice = input("Enter a number: ")

    intervals = [("15m", "60d"), ("30m", "60d"), ("60m", "720d"), ("1d", "3y")]

    if strategy_choice == '16':
        return STRATEGY_CLASSES.values(), intervals

    if strategy_choice not in STRATEGY_CLASSES.keys():
        print("Invalid strategy choice. Please enter a number between 1 and 16.")
        return None, None

    strategy_class = STRATEGY_CLASSES[strategy_choice]

    return [strategy_class], intervals


def generate_strategy_summary(strategy_classes, intervals):
    output_dir = 'Filer/Serie'

    for strategy_class in strategy_classes:
        strategy_name = strategy_class.__name__

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with pd.ExcelWriter(f"{output_dir}/{strategy_name}_summary.xlsx", engine='xlsxwriter') as writer:
            for interval, period in intervals:
                summary_data = pd.DataFrame()
                for ticker in TICKERS:
                    strategy = strategy_class(ticker, interval, period)
                    try:
                        data_with_signals = strategy.generate_signals()
                        trade_data = strategy.generate_trades()
                    except Exception as e:
                        print(f"Failed to generate trades for strategy: {strategy_class.__name__}, "
                              f"ticker: {ticker}, interval: {interval}, period: {period}")
                        print(f"Error: {e}")
                        continue

                    if data_with_signals is None or trade_data is None:
                        print(
                            f"No backtest data for strategy: {strategy_name}, ticker: {ticker}, interval: {interval}, period: {period}")
                        continue

                    additional_data = calculate_additional_data(trade_data)
                    additional_data_transposed = additional_data.transpose()

                    # Add ticker name to the DataFrame
                    additional_data_transposed['Ticker'] = ticker

                    # Add data for current ticker to summary
                    summary_data = pd.concat([summary_data, additional_data_transposed], axis=0)

                # Set ticker names as index
                summary_data.set_index('Ticker', inplace=True)

                write_to_excel(writer, interval, period, summary_data)

        print(f"Excel file generated: {output_dir}/{strategy_name}_summary.xlsx")


def write_to_excel(writer, interval, period, summary_data):
    # Set column names
    summary_data.columns = ['Profitable Trades', 'Average Profit Per Trade', 'Number of Trades', 'Average Hold Duration (days)']

    # Sort the DataFrame by 'Average Profit Per Trade' in descending order
    summary_data.sort_values('Average Profit Per Trade', ascending=False, inplace=True)

    # Write to the sheet for the current interval and period
    summary_data.to_excel(writer, sheet_name=f"{interval}_{period}")


def main():
    strategy_classes, intervals = get_user_input()
    if strategy_classes is None:
        return
    generate_strategy_summary(strategy_classes, intervals)


if __name__ == "__main__":
    main()
