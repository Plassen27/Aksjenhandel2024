import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
from tkcalendar import DateEntry
import datetime
import json


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Create a label and input field for each setting
        self.total_cash_var = tk.StringVar(value='100000')
        self.total_cash_label = tk.Label(self, text="Total Cash")
        self.total_cash_label.grid(row=0, column=0)
        self.total_cash_entry = tk.Entry(self, textvariable=self.total_cash_var)
        self.total_cash_entry.grid(row=0, column=1)

        self.order_size_var = tk.StringVar(value='5000')
        self.order_size_label = tk.Label(self, text="Order Size")
        self.order_size_label.grid(row=1, column=0)
        self.order_size_entry = tk.Entry(self, textvariable=self.order_size_var)
        self.order_size_entry.grid(row=1, column=1)

        self.kurtasje_var = tk.StringVar(value='0.04')
        self.kurtasje_label = tk.Label(self, text="Kurtasje (%)")
        self.kurtasje_label.grid(row=2, column=0)
        self.kurtasje_entry = tk.Entry(self, textvariable=self.kurtasje_var)
        self.kurtasje_entry.grid(row=2, column=1)

        self.start_date_label = tk.Label(self, text="Start Date")
        self.start_date_label.grid(row=3, column=0)
        self.start_date_entry = DateEntry(self)
        self.start_date_entry.set_date(datetime.date.today())
        self.start_date_entry.grid(row=3, column=1)

        # Create buttons to save and load settings
        self.save_button = tk.Button(self, text="Save Settings", command=self.save_settings)
        self.save_button.grid(row=4, column=0)
        self.load_button = tk.Button(self, text="Load Settings", command=self.load_settings)
        self.load_button.grid(row=4, column=1)

        self.stock_rows = [StockRow(self, 7)]   # Endret fra self.stock_row til self.stock_rows

        self.add_row_button = tk.Button(self, text="+", command=self.add_row)
        self.add_row_button.grid(row=4, column=3)

        tk.Label(self, text="Stock Ticker").grid(row=6, column=0)
        tk.Label(self, text="Strategy").grid(row=6, column=1)
        tk.Label(self, text="Interval").grid(row=6, column=2)

    def add_row(self):
        if self.stock_rows:
            self.stock_rows[-1].remove_button.configure(state='disabled')
        new_row = StockRow(self, len(self.stock_rows) + 7)  # +7 to start from row 7 (6 for the previous widgets + headers)
        self.stock_rows.append(new_row)

    def save_settings(self):
        # Get data from all rows
        stock_data = [stock_row.get_data() for stock_row in self.stock_rows if stock_row.get_data() is not None]

        # Prepare a dictionary that will be saved as a json
        data = {
            'total_cash': self.total_cash_var.get(),
            'order_size': self.order_size_var.get(),
            'kurtasje': self.kurtasje_var.get(),
            'start_date': self.start_date_entry.get_date().isoformat(),  # Save date in a string format
            'stocks': stock_data
        }

        # Save to a json file
        with open('settings.json', 'w') as f:
            json.dump(data, f)
        tkinter.messagebox.showinfo("Info", "Settings saved successfully")

    def load_settings(self):
        # Load data from the json file
        try:
            with open('settings.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        # Set the settings from the file
        self.total_cash_var.set(data.get('total_cash', '100000'))  # Use default values if not found in the file
        self.order_size_var.set(data.get('order_size', '5000'))
        self.kurtasje_var.set(data.get('kurtasje', '0.04'))
        if 'start_date' in data:
            date = datetime.date.fromisoformat(data['start_date'])  # Convert the string back to a date
            self.start_date_entry.set_date(date)

        # Remove all current rows
        for stock_row in self.stock_rows:
            stock_row.destroy()
        self.stock_rows = []

        # Add rows from the loaded data
        for row_data in data.get('stocks', []):
            row = StockRow(self, len(self.stock_rows) + 5)
            row.set_data(row_data)
            self.stock_rows.append(row)
            row.ticker_combobox.grid(row=row.row, column=0)
            row.strategy_combobox.grid(row=row.row, column=1)
            row.interval_combobox.grid(row=row.row, column=2)

        tkinter.messagebox.showinfo("Info", "Settings loaded successfully")


class StockRow:
    def __init__(self, root, row):
        self.root = root
        self.row = row

        self.tickers = ["DNO.OL", "AUTO.OL", "KAHOT.OL", "NEL.OL", "FRO.OL", "GOGL.OL", "PGS.OL", "RECSI.OL",
           "BORR.OL", "KIT.OL", "NOD.OL", "NHY.OL", "AKRBP.OL", "SUBC.OL", "TGS.OL", "MPCC.OL",
           "NAS.OL", "BWLPG.OL", "SHLF.OL", "TOM.OL", "MOWI.OL", "SDRL.OL", "HAUTO.OL"]
        self.strategies = [str(i) for i in range(1, 16)]
        self.intervals = ["15m", "30m", "60m"]

        # Ticker Combobox
        self.ticker_var = tk.StringVar()
        self.ticker_combobox = ttk.Combobox(root, textvariable=self.ticker_var, values=self.tickers)
        self.ticker_combobox.grid(row=row, column=0)

        # Strategy Combobox
        self.strategy_var = tk.StringVar()
        self.strategy_combobox = ttk.Combobox(root, textvariable=self.strategy_var, values=self.strategies)
        self.strategy_combobox.grid(row=row, column=1)

        # Interval Combobox
        self.interval_var = tk.StringVar()
        self.interval_combobox = ttk.Combobox(root, textvariable=self.interval_var, values=self.intervals)
        self.interval_combobox.grid(row=row, column=2)

        # Add a button to remove this row
        self.remove_button = tk.Button(root, text="-", command=self.remove)
        self.remove_button.grid(row=row, column=3)

    def get_data(self):
        ticker = self.ticker_var.get()
        strategy = self.strategy_var.get()
        interval = self.interval_var.get()
        if ticker and strategy and interval:
            return {
                "ticker": ticker,
                "strategy": int(strategy),
                "interval": interval,
            }

    def destroy(self):
        self.ticker_combobox.destroy()
        self.strategy_combobox.destroy()
        self.interval_combobox.destroy()

    def set_data(self, data):
        self.ticker_var.set(data['ticker'])
        self.strategy_var.set(data['strategy'])
        self.interval_var.set(data['interval'])

    def remove(self):
        # Remove this row from the list of stock rows
        self.root.stock_rows.remove(self)

        # Destroy the widgets of this row
        self.destroy()

        # Enable the remove button of the last row if there are any rows left
        if self.root.stock_rows:
            self.root.stock_rows[-1].remove_button.configure(state='normal')

if __name__ == "__main__":
    app = App()

    # Determine the window size and position
    width = 450
    height = 300  # Adjust height as needed
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()

    # Calculate the position to place the window on the right side of the screen
    x = screen_width - width
    y = 0

    # Set the geometry (position and size)
    app.geometry('%dx%d+%d+%d' % (width, height, x, y))

    app.mainloop()
