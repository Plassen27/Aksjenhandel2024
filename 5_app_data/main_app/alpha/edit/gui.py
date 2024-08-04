import tkinter as tk
from tkinter import ttk
import subprocess
from subprocess import Popen, PIPE, STDOUT
import shlex
import sys
import os
import json
import threading
from datetime import datetime
import read_holdings
from read_holdings import get_holdings_data
from tkinter import messagebox, Toplevel, Label, Entry, Button

class SignalScreener(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid(sticky='nsew')
        self.configure(bg='black')  # Set the background color of the main frame
        self.create_widgets()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.color_combinations = [
            {"foreground": "#FFFFFF", "background": "#000000"},  # White/Black
            {"foreground": "#1E90FF", "background": "#000000"},  # Yellow/Black
            {"foreground": "#FF6600", "background": "#000000"},  # Orange/Black
            {"foreground": "#EE82EE", "background": "#000000"},  # Red/Black
            {"foreground": "#FFC0CB", "background": "#000000"},  # Green/Black
        ]
        self.current_color_index = 0

        self.fonts = ["Courier", "Consolas"]
        self.current_font_index = 0

        self.load_holdings_data()
        self.load_settings()
        self.start_live_run()
        self.start_predict_signals()

    def load_holdings_data(self):
        holdings_data = get_holdings_data()  # Call function from read_holdings.py
        self.predict_text_area.delete('1.0', tk.END)  # Clear the text area
        self.predict_text_area.insert(tk.END, holdings_data)  # Insert the new data
    def create_widgets(self):
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Refresh", command=self.refresh_live_run)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Change Colors", command=self.change_colors)
        view_menu.add_command(label="Change Font", command=self.change_font)

        actions_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Actions", menu=actions_menu)
        actions_menu.add_command(label="Register Trades", command=self.open_edit_trading_data)

        terminal_frame = ttk.Frame(self, style="Bloomberg.TFrame")
        terminal_frame.grid(row=0, column=0, sticky='nsew')

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(0, weight=1)
        terminal_frame.grid_rowconfigure(1, weight=1)  # change this line
        terminal_frame.grid_columnconfigure(0, weight=1)

        self.text_area = tk.Text(terminal_frame, bg='black', fg='white', wrap='word', font=('Digital-7', 10))
        self.text_area.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        scrollbar = ttk.Scrollbar(terminal_frame, orient='vertical', command=self.text_area.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.text_area['yscrollcommand'] = scrollbar.set

        # Change the height of predict_text_area here
        self.predict_text_area = tk.Text(terminal_frame, bg='black', fg='white', wrap='word', font=('Courier', 10),
                                         height=8)  # Adjust the height as desired
        self.predict_text_area.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        predict_scrollbar = ttk.Scrollbar(terminal_frame, orient='vertical', command=self.predict_text_area.yview)
        predict_scrollbar.grid(row=1, column=1, sticky='ns')
        self.predict_text_area['yscrollcommand'] = predict_scrollbar.set

        clock_frame = ttk.Frame(self, style="Clock.TFrame")
        clock_frame.grid(row=2, column=0, sticky='s')

        self.clock_label = tk.Label(clock_frame, bg='black', font=('Digital-7', 20))
        self.clock_label.pack(side='left', padx=20, pady=10)
        self.edit_text_area = tk.Text(terminal_frame, bg='black', fg='white', wrap='word', font=('Courier', 10),
                                      height=3)  # Juster høyden etter behov
        self.edit_text_area.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)

        edit_scrollbar = ttk.Scrollbar(terminal_frame, orient='vertical', command=self.edit_text_area.yview)
        edit_scrollbar.grid(row=2, column=1, sticky='ns')
        self.edit_text_area['yscrollcommand'] = edit_scrollbar.set

        self.save_button = ttk.Button(terminal_frame, text='Save Changes', command=self.save_changes_to_json)
        self.save_button.grid(row=2, column=2, sticky='ns', padx=10, pady=10)

        self.trade_button = Button(self.master, text="Trade", command=self.open_new_trade_window)
        self.trade_button.grid(row=3, column=0)

    def save_changes_to_json(self):
        data = self.edit_text_area.get("1.0", 'end-1c')
        with open('edit_trading_data.py', 'w') as f:
            f.write(data)
        # Her kan du kjøre scriptet og håndtere eventuelle feil
        os.system('python edit_trading_data.py')

    def start_predict_signals(self):
        command = 'python "C:\\Users\\Johannes\\PycharmProjects\\pythonProject\\Aksjehandel-Quant-main\\5_app_data\\main_app\\alpha\\run_log.py"'

        self.predict_process = Popen(shlex.split(command), stdout=PIPE, stderr=STDOUT, bufsize=1,
                                     universal_newlines=True)
        thread = threading.Thread(target=self.update_predict_text_area)
        thread.daemon = True
        thread.start()

    def open_settings(self):
        subprocess.Popen([sys.executable, 'settings_inputs.py'])

    def open_edit_trading_data(self):
        subprocess.Popen([sys.executable, 'edit_trading_data.py'])

    def on_closing(self):
        self.process.terminate()
        self.predict_process.terminate()
        # self.edit_process.terminate()  # Removed this line
        self.save_settings()
        self.master.destroy()

    def open_new_trade_window(self):
        new_window = Toplevel(root)
        new_window.title("Register new trade")

        Label(new_window, text="TP value:").pack()
        tp_entry = Entry(new_window)
        tp_entry.pack()

        save_button = Button(new_window, text="Save trade", command=lambda: self.save_new_trade(tp_entry.get()))

    def save_new_trade(self, tp_value):
        # Her kan du kalle edit_trading_data.py funksjonene med den nye TP-verdien
        pass

    def start_live_run(self):
        threading.Thread(target=self.run_live, daemon=True).start()


    def run_live(self):
        command = 'python "C:\\Users\\Johannes\\PycharmProjects\\pythonProject\\Aksjehandel-Quant-main\\5_app_data\\main_app\\alpha\\run_live.py"'
        self.process = Popen(shlex.split(command), stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True)
        self.update_text_area()

    def update_text_area(self):
        try:
            for line in iter(self.process.stdout.readline, ''):
                if not line.strip():
                    continue
                if line.startswith(
                        "Successfully imported Strategy") or "[*********************100%***********************]  1 of 1 completed" in line:
                    continue
                if not line.endswith("\n"):
                    line += "\n"

                if "Ex. Sell" in line:
                    self.text_area.insert(tk.END, line, 'sell')
                    self.text_area.tag_config('sell', foreground='red')
                elif "Ex. Buy" in line:
                    self.text_area.insert(tk.END, line, 'buy')
                    self.text_area.tag_config('buy', foreground='green')
                else:
                    self.text_area.insert(tk.END, line)

                self.text_area.see(tk.END)
        except KeyboardInterrupt:
            pass
        finally:
            self.process.stdout.close()
            self.process.wait()

    def refresh_live_run(self):
        self.process.terminate()
        self.predict_process.terminate()
        # self.edit_process.terminate()  # Removed this line
        self.text_area.delete('1.0', tk.END)  # Clear the text_area
        self.predict_text_area.delete('1.0', tk.END)  # Clear the predict_text_area
        # self.edit_text_area.delete('1.0', tk.END)  # Removed this line
        self.start_live_run()
        self.start_predict_signals()
        self.load_holdings_data()

    def start_edit_text_area(self):
        command = 'python "edit_trading_data.py"'
        self.edit_process = Popen(shlex.split(command), stdout=PIPE, stderr=STDOUT, bufsize=1, universal_newlines=True)
        thread = threading.Thread(target=self.update_edit_text_area)
        thread.daemon = True
        thread.start()

    def update_edit_text_area(self):
        try:
            for line in iter(self.edit_process.stdout.readline, ''):
                if not line.strip():
                    continue
                if not line.endswith("\n"):
                    line += "\n"
                self.edit_text_area.insert(tk.END, line)
                self.edit_text_area.see(tk.END)
        except KeyboardInterrupt:
            pass
        finally:
            self.edit_process.stdout.close()
            self.edit_process.wait()

    def change_colors(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.color_combinations)
        self.text_area['foreground'] = self.color_combinations[self.current_color_index]['foreground']
        self.text_area['background'] = self.color_combinations[self.current_color_index]['background']
        self.predict_text_area['foreground'] = self.color_combinations[self.current_color_index][
            'foreground']  # Syncing colors with predict_text_area
        self.predict_text_area['background'] = self.color_combinations[self.current_color_index][
            'background']  # Syncing colors with predict_text_area

    def change_font(self):
        self.current_font_index = (self.current_font_index + 1) % len(self.fonts)
        selected_font = self.fonts[self.current_font_index]
        self.text_area.configure(font=(selected_font, 10))
        self.save_settings()
        print(f"Font {selected_font} has been applied.")

    def save_settings(self):
        settings = {
            "color_index": self.current_color_index,
            "font_index": self.current_font_index
        }
        with open("color_settings.json", "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open("color_settings.json", "r") as f:
                settings = json.load(f)
                self.current_color_index = settings.get("color_index", 0)
                self.current_font_index = settings.get("font_index", 0)
        except FileNotFoundError:
            self.current_color_index = 0
            self.current_font_index = 0

        selected_combination = self.color_combinations[self.current_color_index]
        self.text_area.configure(fg=selected_combination["foreground"], bg=selected_combination["background"])
        self.predict_text_area.configure(fg=selected_combination["foreground"],
                                          bg=selected_combination["background"])

        selected_font = self.fonts[self.current_font_index]
        self.text_area.configure(font=(selected_font, 10))
        self.predict_text_area.configure(font=(selected_font, 10))

        # Update clock color
        self.clock_label.configure(fg=selected_combination["foreground"], bg=selected_combination["background"])

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=now)
        self.clock_label.after(1000, self.update_clock)

    def run_predict_signals(self):
        command = 'python "C:\\Users\\Johannes\\PycharmProjects\\pythonProject\\Aksjehandel-Quant-main\\5_app_data\\main_app\\alpha\\run_log.py"'

        self.predict_process = Popen(shlex.split(command), stdout=PIPE, stderr=STDOUT, bufsize=1,
                                     universal_newlines=True)
        threading.Thread(target=self.update_predict_text_area).start()

    def update_predict_text_area(self):
        try:
            for line in iter(self.predict_process.stdout.readline, ''):
                if not line.strip():
                    continue
                if line.startswith(
                        "Successfully imported Strategy") or "[*********************100%***********************]  1 of 1 completed" in line:
                    continue
                if not line.endswith("\n"):
                    line += "\n"
                self.predict_text_area.insert(tk.END, line)
                self.predict_text_area.see(tk.END)
        except KeyboardInterrupt:
            pass
        finally:
            self.predict_process.stdout.close()
            self.predict_process.wait()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.title("Signal Screener")  # Set the window title
        root.configure(bg='black')  # Set the background color of the root window

        style = ttk.Style()
        style.configure("Bloomberg.TFrame", background="black")
        style.configure("Bloomberg.TButton", background="#000000", foreground="white")  # Change button style
        style.configure("Clock.TFrame", background="black")

        app = SignalScreener(master=root)

        text_area_width = 95
        text_area_height = 18
        predict_text_area_height = 8  # Adjust the height of the prediction text area
        app.text_area.configure(width=text_area_width, height=text_area_height)
        app.predict_text_area.configure(width=text_area_width, height=predict_text_area_height)

        width = 610
        height = 1200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        x = screen_width - width
        y = 0

        root.geometry('%dx%d+%d+%d' % (width, height, x, y))

        app.update_clock()

        app.mainloop()

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(-1)
