import tkinter as tk
from tkinter import ttk
import json
from subprocess import Popen, PIPE, STDOUT
import threading
import shlex
import os

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.grid()
        self.create_widgets()
        self.start_live_run()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.text_area = tk.Text(self)
        self.text_area.grid(column=0, row=0, sticky=(tk.W, tk.N, tk.E, tk.S))

        self.settings_button = tk.Button(self)
        self.settings_button["text"] = "Settings"
        self.settings_button["command"] = self.open_settings
        self.settings_button.grid(column=0, row=1)

    def open_settings(self):
        os.system('python settings_inputs.py')

    def on_closing(self):
        # Stop threads and close the window
        self.process.terminate()  # Assuming your Popen object is stored as self.process
        self.master.destroy()

    def save_settings(self):
        settings = {key: entry.get() for key, entry in self.settings_entries.items()}

        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=7)

    def start_live_run(self):
        command = 'python "C:\\Users\\johan\\PycharmProjects\\Aksjebot\\quant_trading\\5_app_data\\main_app\\run_live.py"'
        self.process = Popen(shlex.split(command), stdout=PIPE, stderr=STDOUT)
        threading.Thread(target=self.update_text_area, args=(self.process,)).start()
    def update_text_area(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.text_area.delete('1.0', tk.END)
                self.text_area.insert(tk.END, output.strip())
        rc = process.poll()

root = tk.Tk()
app = Application(master=root)

# Determine the window size and position
width = 400
height = 1200
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the position to place the window on the right side of the screen
x = screen_width - width
y = 0

# Set the geometry (position and size)
root.geometry('%dx%d+%d+%d' % (width, height, x, y))

app.mainloop()

