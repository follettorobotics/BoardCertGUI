import threading
import tkinter as tk

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
        self.polling_interval = 200  # milliseconds

    def create_sensor_displays(self):
        for sensor_name in self.sensors:
            canvas = tk.Canvas(self, width=60, height=70)  # width and height adjusted
            canvas.pack(side=tk.LEFT, padx=10, pady=10)

            circle_id = canvas.create_oval(10, 10, 30, 30, fill="red")
            text_id = canvas.create_text(30, 50, text=sensor_name, fill="black", font=("Helvetica", 8))

            self.sensor_canvases[sensor_name] = (canvas, circle_id, text_id)

    def update_sensor_status(self, sensor_name, status):
        canvas, circle_id, text_id = self.sensor_canvases[sensor_name]
        color = "blue" if status == 1 else "red"
        canvas.itemconfig(circle_id, fill=color)

    def poll_sensors(self):
        if not FirmwareTesterApp.get_operation_variable():
            self.simulate_sensor_updates()
        self.after(self.polling_interval, self.poll_sensors)

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
            'Sensor 1': (sensor_value >> 7) & 1,  # table 1
            'Sensor 2': (sensor_value >> 6) & 1,  # table 2
            'Sensor 3': (sensor_value >> 5) & 1,  # table 3
            'Sensor 4': (sensor_value >> 4) & 1,  # top 1
            'Sensor 9': (sensor_value >> 3) & 1,  # bottom 3
            'Sensor 10': (sensor_value >> 2) & 1,  # height check 1
            'Sensor 11': (sensor_value >> 1) & 1,  # height check 2
            'Sensor 12': (sensor_value >> 0) & 1,  # height check 3
        }
        return sensor_value_1_map

    @staticmethod
    def _parse_sensor_value_2(sensor_value):
        sensor_value_2_map = {
            'Sensor 5': (sensor_value >> 7) & 1,  # bottom 1
            'Sensor 6': (sensor_value >> 6) & 1,  # top 2
            'Sensor 7': (sensor_value >> 5) & 1,  # bottom 2
            'Sensor 8': (sensor_value >> 4) & 1,  # top 3
            'Sensor 13': (sensor_value >> 3) & 1,  # folletto coffee sensor
            'Sensor 14': (sensor_value >> 2) & 1,  # folletto table
            'Sensor 15': (sensor_value >> 1) & 1,  # beer machine 1 home
            'Sensor 16': (sensor_value >> 0) & 1,  # beer machine 2 home
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

        self.relay_frame = tk.Frame(self.master)
        self.internal_motor_frame = tk.Frame(self.master)
        self.external_motor_frame = tk.Frame(self.master)

    def internal_motor_callback(self, motor, direction):
        if direction == "CW":
            command = self.message_formatter.internal_motor_cw_message(motor)
        else:
            command = self.message_formatter.internal_motor_ccw_message(motor)
        FirmwareTesterApp.set_operation_variable(True)
        response = self.tcp_client.send_message(command)
        print(f"Motor {motor} turned {direction}: {response}")
        FirmwareTesterApp.set_operation_variable(False)

    def external_motor_callback(self, motor):
        command = self.message_formatter.external_motor_control_message(motor)
        FirmwareTesterApp.set_operation_variable(True)
        response = self.tcp_client.send_message(command)
        print(f"Motor {motor}: {response}")
        FirmwareTesterApp.set_operation_variable(False)

    def create_internal_motor_controls(self):
        motor_var = tk.StringVar(self.master)
        motor_var.set("Internal Motor 1")

        motor_menu = tk.OptionMenu(self.internal_motor_frame, motor_var, "Internal Motor 1", "Internal Motor 2",
                                   "Internal Motor 3", "Internal Motor 4", "Internal Motor 5", "Internal Motor 6")
        motor_menu.pack(side=tk.LEFT, padx=5)

        cw_button = tk.Button(self.internal_motor_frame, text="CW",
                              command=lambda: self.internal_motor_callback(motor_var.get(), "CW"))
        cw_button.pack(side=tk.LEFT, padx=5)

        ccw_button = tk.Button(self.internal_motor_frame, text="CCW",
                               command=lambda: self.internal_motor_callback(motor_var.get(), "CCW"))
        ccw_button.pack(side=tk.LEFT, padx=5)

    def create_external_motor_controls(self):
        motor_var = tk.StringVar(self.master)
        motor_var.set("External Motor 1")

        motor_menu = tk.OptionMenu(self.external_motor_frame, motor_var, "External Motor 1", "External Motor 2",
                                   "External Motor 3", "External Motor 4")
        motor_menu.pack(side=tk.LEFT, padx=5)

        cw_button = tk.Button(self.external_motor_frame, text="CONTROL",
                              command=lambda: self.external_motor_callback(motor_var.get()))
        cw_button.pack(side=tk.LEFT, padx=5)

    def relay_callback(self, state):
        relay = self.relay_var.get()
        self.send_relay_command(relay, state)

    def send_relay_command(self, relay, state):
        relay_number = relay.split(" ")[1]
        if state == "ON":
            command = self.message_formatter.relay_on_message(relay_number)
        else:
            command = self.message_formatter.relay_off_message(relay_number)
        FirmwareTesterApp.set_operation_variable(True)
        response = self.tcp_client.send_message(command)
        FirmwareTesterApp.set_operation_variable(False)
        print(f"Relay {relay_number} turned {state}: {response}")

    def create_relay_controls(self):
        self.relay_var = tk.StringVar(self.master)
        self.relay_var.set("Relay 1")

        self.relay_menu = tk.OptionMenu(self.relay_frame, self.relay_var, "Relay 1", "Relay 2", "Relay 3", "Relay 4",
                                        "Relay 5", "Relay 6", "Relay 7")
        self.relay_menu.pack(side=tk.LEFT, padx=5)

        self.on_button = tk.Button(self.relay_frame, text="ON", command=lambda: self.relay_callback("ON"))
        self.on_button.pack(side=tk.LEFT, padx=5)

        self.off_button = tk.Button(self.relay_frame, text="OFF", command=lambda: self.relay_callback("OFF"))
        self.off_button.pack(side=tk.LEFT, padx=5)

    def connect(self):
        self.tcp_client.connect()
        self.status_label.config(text="Connected")
        self.create_sensor_display()
        self.create_relay_controls()
        self.create_internal_motor_controls()
        self.create_external_motor_controls()
        self.relay_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.internal_motor_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.external_motor_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.start_sensor_polling()

    def create_sensor_display(self):
        if not self.sensor_display:
            self.sensor_display = SensorStatusDisplay(self.master)
            self.sensor_display.pack(pady=10)

    def start_sensor_polling(self):
        self.sensor_display.poll_sensors()

    def on_close(self):
        FirmwareTesterApp.set_operation_variable(False)
        self.tcp_client.close_connection()
        self.master.destroy()

