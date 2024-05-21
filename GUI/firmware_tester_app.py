import tkinter as tk
from tkinter import ttk, scrolledtext

from connection.tcp_client import TcpClient


class FirmwareTesterApp:

    def __init__(self, master):
        self.master = master
        self.master.title("Firmware Tester")
        self.tcp_client = TcpClient()

        # Layout configuration
        self.create_widgets()

    def create_widgets(self):
        self.connect_button = tk.Button(self.master, text="Connect", command=self.connect)
        self.connect_button.pack(pady=10)

        self.send_button = tk.Button(self.master, text="Send Command", command=self.send_command, state=tk.DISABLED)
        self.send_button.pack(pady=10)

    def connect(self):
        self.tcp_client.connect()
        self.send_button.config(state=tk.NORMAL)

    def send_command(self):
        message = "Firmware Command"  # 전송할 명령어
        self.tcp_client.send_message(message)

    def on_close(self):
        self.tcp_client.close_connection()
        self.master.destroy()
