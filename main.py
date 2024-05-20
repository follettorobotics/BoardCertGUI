import tkinter as tk
from tkinter import ttk, scrolledtext

from GUI.firmware_tester_app import FirmwareTesterApp

if __name__ == "__main__":
    root = tk.Tk()
    app = FirmwareTesterApp(root)
    root.mainloop()
