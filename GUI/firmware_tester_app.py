import tkinter as tk
from tkinter import ttk, scrolledtext


class FirmwareTesterApp:

    def __init__(self, master):
        self.master = master
        self.master.title("Firmware Tester")

        # Layout configuration
        self.setup_widgets()

    def setup_widgets(self):
        # Buttons frame
        self.frame_buttons = ttk.Frame(self.master)
        self.frame_buttons.grid(row=0, column=0, padx=10, pady=10)

        # Start button
        self.btn_start = ttk.Button(self.frame_buttons, text="Start Test", command=self.start_test)
        self.btn_start.grid(row=0, column=0, padx=5, pady=5)

        # Stop button
        self.btn_stop = ttk.Button(self.frame_buttons, text="Stop Test", command=self.stop_test)
        self.btn_stop.grid(row=0, column=1, padx=5, pady=5)

        # Status Log
        self.log = scrolledtext.ScrolledText(self.master, width=40, height=10, wrap=tk.WORD)
        self.log.grid(row=1, column=0, padx=10, pady=10)

    def start_test(self):
        # Insert starting log
        self.log.insert(tk.END, "Test started...\n")

        # Simulated test actions
        # Here you might add code to interface with firmware or hardware
        # For example, sending commands to a microcontroller or reading sensor data
        self.log.insert(tk.END, "Sending commands to firmware...\n")

    def stop_test(self):
        # Insert stopping log
        self.log.insert(tk.END, "Test stopped.\n")

        # Simulated cleanup actions
        # Here you might add code to clean up or reset hardware
        self.log.insert(tk.END, "Cleanup completed.\n")
