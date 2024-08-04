import tkinter as tk
from tkinter import ttk
import pandas as pd
import json
import subprocess
import uuid
from io import StringIO

columns = ['Ticker', 'Datetime', 'Signal Price', 'Trading Price', 'Shares', 'Direction', 'Free Cash', 'NR', 'id']


process = subprocess.Popen(["python", "run_log2.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
print("STDOUT:", stdout.decode())
print("STDERR:", stderr.decode())

def load_trading_data():
    with open('trading_data.json') as file:
        data = json.load(file)
    return pd.DataFrame(data)

def load_log_data():
    log_data = pd.read_csv('log_data.csv')
    log_data_var.set(log_data.to_csv(index=False))
    return log_data
def add_row(log_data, trading_data_treeview, log_data_treeview, tp_entry):
    # Read from log_data_var
    log_data = pd.read_csv(StringIO(log_data_var.get()))


    if not trading_data_treeview.selection(): return  # Exit if no item is selected
    selected_item = trading_data_treeview.selection()[0]
    selected_values = trading_data_treeview.item(selected_item)["values"]

    # Get the manually entered TP value from the text entry, or use the value of 'P' if not provided
    tp_value = tp_entry.get() if tp_entry.get() else selected_values[3]

    # Create a new row for log_data
    new_row = {
        'Ticker': selected_values[0],
        'Datetime': selected_values[2],
        'Signal Price': selected_values[3],
        'Trading Price': tp_value,
        'Shares': selected_values[5],
        'Direction': selected_values[6],
        'Free Cash': selected_values[7],
        'NR': selected_values[8],
        'id': str(uuid.uuid4())
    }

    # Append the new row to log_data DataFrame
    new_row_df = pd.DataFrame([new_row])
    log_data = pd.concat([log_data, new_row_df], ignore_index=True)

    # Write changes to log_data.csv
    log_data.to_csv('log_data.csv', index=False)
    log_data_var.set(log_data.to_csv(index=False))  # Update the StringVar

    # Add the new row to the log_data_treeview
    new_item = log_data_treeview.insert('', 'end', values=list(new_row.values())[:-1])

    # Select the newly added item in the treeview
    log_data_treeview.selection_set(new_item)
    log_data_treeview.see(new_item)

    return log_data


def delete_row(log_data, log_data_treeview, trading_data_treeview):
    selected_items = log_data_treeview.selection()
    if selected_items:  # Check if there are any selected items
        selected_item = selected_items[0]
        selected_row = log_data_treeview.item(selected_item, "values")
        matching_id = selected_row[-1]  # Assuming the UUID is the last value
        log_data.drop(log_data[log_data.id == matching_id].index, inplace=True)  # Delete the row with the matching UUID
        log_data.reset_index(drop=True, inplace=True)
        log_data_treeview.delete(selected_item)
        log_data.to_csv('log_data.csv', index=False)  # Write changes to log_data.csv
        log_data_var.set(log_data.to_csv(index=False))  # Update the StringVar
        trading_data_treeview.yview_moveto(1.0)  # Scroll to the bottom
        log_data_treeview.yview_moveto(1.0)
    return log_data


def update_log_data_treeview():
    # Clear existing rows
    log_data_treeview.delete(*log_data_treeview.get_children())

    # Add rows from log_data DataFrame
    for index, row in log_data.iterrows():
        log_data_treeview.insert('', 'end', values=row[:-1].tolist())

    # Scroll to the bottom
    log_data_treeview.yview_moveto(1)


def create_treeview(frame, data, hide_id_column=True):
    style = ttk.Style()

    style.theme_use('default')
    style.configure('Treeview', background='#333333', foreground='#FFFFFF', fieldbackground='#333333')  # Dark theme for treeview
    style.map('Treeview', background=[('selected', '#0073e6')])  # Highlight color for selected row
    treeview = ttk.Treeview(frame)

    # Determine columns based on hide_id_column
    if hide_id_column:
        columns = [col for col in data.columns if col != 'id']
    else:
        columns = list(data.columns)

    # Create columns
    treeview['columns'] = columns

    # Format columns
    treeview.column("#0", width=0, stretch=tk.NO)
    for column in columns:
        if column == 'Datetime':
            treeview.column(column, anchor=tk.W, width=200)  # Set bredde for Datetime-kolonnen
        else:
            treeview.column(column, anchor=tk.W, width=100)

    # Create headings
    for column in columns:
        treeview.heading(column, text=column, anchor=tk.W)

    # Add rows
    for index, row in data.iterrows():
        treeview.insert(parent='', index='end', iid=index, text='', values=list(row))

    return treeview


def update_entry(event):
    selected_items = trading_data_treeview.selection()
    if selected_items:  # Check if there are any selected items
        selected_item = selected_items[0]
        tp_entry.delete(0, tk.END)
        tp_entry.insert(tk.END, trading_data.loc[int(selected_item), 'P'])

def on_select(event):
    if event.widget == trading_data_treeview:
        add_button.config(state='normal')
        delete_button.config(state='disabled')
    elif event.widget == log_data_treeview:
        add_button.config(state='disabled')
        delete_button.config(state='normal')
def on_trading_data_select(event):
    selected_item = trading_data_treeview.selection()
    if selected_item:
        selected_item = selected_item[0]
        selected_row = trading_data_treeview.item(selected_item)
        P_value = selected_row['values'][3]  # Assuming 'P' is at index 3
        tp_entry.delete(0, tk.END)
        tp_entry.insert(0, P_value)



# Main Code
root = tk.Tk()
log_data_var = tk.StringVar()
root.geometry("+0+0")  # Set the window at the top of the screen
root.attributes('-topmost', True)  # Making the application window appear on top
root.after_idle(root.attributes, '-topmost', False)  # Reset topmost attribute after window is created
root.title("Register Trade")


style = ttk.Style()
style.theme_use('default')
style.configure('Treeview', background='#333333', foreground='#FFFFFF', fieldbackground='#333333')  # Dark theme for treeview
style.map('Treeview', background=[('selected', '#0073e6')])  # Highlight color for selected row
root.configure(bg='#000000')  # Black background color
root.configure(bg='#000000')  # Black background color


# Pane to hold trading and log data
treeview_pane = tk.PanedWindow(root)
treeview_pane.pack(fill=tk.BOTH, expand=1)

# Trading data frame
trading_data_frame = tk.Frame(treeview_pane, bg="#000000")
treeview_pane.add(trading_data_frame)

# Load trading data
trading_data = load_trading_data()

# Create trading data treeview
trading_data_treeview = create_treeview(trading_data_frame, trading_data)
trading_data_treeview.bind('<<TreeviewSelect>>', on_trading_data_select)
trading_data_treeview.pack(pady=20)
trading_data_treeview.yview_moveto(1)


# Log data frame
log_data_frame = tk.Frame(treeview_pane, bg="#000000")
treeview_pane.add(log_data_frame)

# Load log data
log_data = load_log_data()
log_data_var.set(log_data.to_csv(index=False))

# Create log data treeview
log_data_treeview = create_treeview(log_data_frame, log_data, hide_id_column=True)
log_data_treeview.pack(pady=20)
log_data_treeview.yview_moveto(1.0)

# Buttons and Entry frame
button_frame = tk.Frame(root, bg="#000000")
button_frame.pack(fill=tk.X, padx=20)

# Add Entry box
tp_entry = tk.Entry(button_frame, fg="#FFFFFF", bg="#000000")
tp_entry.pack(side=tk.LEFT, padx=10)

# Add button
add_button = tk.Button(button_frame, text="Add Row", command=lambda: add_row(log_data, trading_data_treeview, log_data_treeview, tp_entry))
add_button.pack(side=tk.LEFT, padx=10)

# Delete button
delete_button = tk.Button(button_frame, text="Delete Row", command=lambda: delete_row(log_data, log_data_treeview, trading_data_treeview))
delete_button.pack(side=tk.LEFT, padx=10)

style = ttk.Style()
style.theme_use('default')
style.configure('Treeview', background='#333333', foreground='#FFFFFF', fieldbackground='#333333')  # Dark theme for treeview
style.map('Treeview', background=[('selected', '#0073e6')])  # Highlight color for selected row
root.configure(bg='#000000')  # Black background color

root.mainloop()