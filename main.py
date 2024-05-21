import tkinter as tk

from GUI.firmware_tester_app import FirmwareTesterApp

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Firmware Command Sender")
    app = FirmwareTesterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
