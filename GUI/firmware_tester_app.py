import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext

from connection.tcp_client import TcpClient
from message_formatter.message_formatter import MessageFormatter  # 가정된 메시지 포맷터 클래스


class SensorStatusDisplay(tk.Frame):
    def __init__(self, master, num_sensors=16):
        super().__init__(master)
        self.sensors = {f"Sensor {i + 1}": 0 for i in range(num_sensors)}
        self.sensor_canvases = {}
        self.create_sensor_displays()
        self.tcp_client = TcpClient()
        self.message_formatter = MessageFormatter()

    def create_sensor_displays(self):
        for sensor_name in self.sensors:
            canvas = tk.Canvas(self, width=50, height=60)
            canvas.pack(side=tk.LEFT, padx=10, pady=10)

            circle_id = canvas.create_oval(10, 10, 25, 25, fill="red")
            text_id = canvas.create_text(20, 55, text=sensor_name, fill="black", font=("Helvetica", 8))

            self.sensor_canvases[sensor_name] = (canvas, circle_id, text_id)

    def update_sensor_status(self, sensor_name, status):
        canvas, circle_id, text_id = self.sensor_canvases[sensor_name]
        color = "blue" if status == 1 else "red"
        canvas.itemconfig(circle_id, fill=color)

    def simulate_sensor_updates(self):
        command = self.message_formatter.sensor_message()
        response = self.tcp_client.send_message(command)
        if len(response) > 4:
            sensor_value_1 = response[2]
            sensor_value_2 = response[3]
            sensor_value_1_map = self._parse_sensor_value_1(sensor_value_1)
            sensor_value_2_map = self._parse_sensor_value_2(sensor_value_2)

            for sensor_name, status in {**sensor_value_1_map, **sensor_value_2_map}.items():
                self.update_sensor_status(sensor_name, status)

    @staticmethod
    def _parse_sensor_value_1(sensor_value):
        sensor_value_1_map = {
            'sensor_1': (sensor_value >> 7) & 1,  # table 1
            'sensor_2': (sensor_value >> 6) & 1,  # table 2
            'sensor_3': (sensor_value >> 5) & 1,  # table 3
            'sensor_4': (sensor_value >> 4) & 1,  # top 1
            'sensor_9': (sensor_value >> 3) & 1,  # bottom 3
            'sensor_10': (sensor_value >> 2) & 1,  # height check 1
            'sensor_11': (sensor_value >> 1) & 1,  # height check 2
            'sensor_12': (sensor_value >> 0) & 1,  # height check 3
        }
        return sensor_value_1_map

    @staticmethod
    def _parse_sensor_value_2(sensor_value):
        sensor_value_2_map = {
            'sensor_5': (sensor_value >> 7) & 1,  # bottom 1
            'sensor_6': (sensor_value >> 6) & 1,  # top 2
            'sensor_7': (sensor_value >> 5) & 1,  # bottom 2
            'sensor_8': (sensor_value >> 4) & 1,  # top 3
            'sensor_13': (sensor_value >> 3) & 1,  # folletto coffee sensor
            'sensor_14': (sensor_value >> 2) & 1,  # folletto table
            'sensor_15': (sensor_value >> 1) & 1,  # beer machine 1 home
            'sensor_16': (sensor_value >> 0) & 1,  # beer machine 2 home
        }
        return sensor_value_2_map


class FirmwareTesterApp:

    _operation = False
    _operation_lock = threading.Lock()

    @classmethod
    def get_operation_variable(cls):
        with cls._operation_lock:
            return cls._operation

    @classmethod
    def set_operation_variable(cls, value: bool):
        with cls._operation_lock:
            cls._operation = value
            return True

    def __init__(self, master):
        self.master = master
        self.master.title("Firmware Tester")
        self.tcp_client = TcpClient()
        self.message_formatter = MessageFormatter()
        self.sensor_display = None

        self.create_widgets()
        self.command_buttons = []

    def create_widgets(self):
        self.connect_button = tk.Button(self.master, text="Connect", command=self.connect)
        self.connect_button.pack(pady=10)

        self.status_label = tk.Label(self.master, text="Not connected")
        self.status_label.pack(pady=5)

    def connect(self):
        self.tcp_client.connect()
        self.status_label.config(text="Connected")
        self.create_sensor_display()
        self.start_sensor_simulation()

    def create_sensor_display(self):
        if not self.sensor_display:
            self.sensor_display = SensorStatusDisplay(self.master)
            self.sensor_display.pack(pady=10)

    def start_sensor_simulation(self):
        if not FirmwareTesterApp.get_operation_variable():
            FirmwareTesterApp.set_operation_variable(True)
            thread = threading.Thread(target=self.sensor_display.simulate_sensor_updates, daemon=True)
            thread.start()

    def on_close(self):
        FirmwareTesterApp.set_operation_variable(False)
        self.tcp_client.close_connection()
        self.master.destroy()
