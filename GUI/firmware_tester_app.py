import struct
import sys
import threading
import queue
import time

import ttkbootstrap as ttk

from Log.gui_log_sink import GuiLogSink, StdoutRedirector
from Log.logger_config import setup_logger
from connection.tcp_client import TcpClient
from message_formatter.message_formatter import MessageFormatter


class ScrollableFrame(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        canvas = ttk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class SensorStatusDisplay(ttk.Frame):
    def __init__(self, master, num_sensors=16):
        super().__init__(master)
        self.sensors = {f"Sensor {i + 1}": 0 for i in range(num_sensors)}
        self.sensor_canvases = {}
        self.create_sensor_displays()
        self.polling_interval = 2000  # milliseconds

    def create_sensor_displays(self):
        sensor_frame = ttk.LabelFrame(self, text="Sensors", padding=(10, 10), style='Info.TLabelframe')
        sensor_frame.pack(padx=10, pady=10, fill=ttk.BOTH, expand=True)

        for i, sensor_name in enumerate(self.sensors):
            row = i % 4
            column = i // 4

            frame = ttk.Frame(sensor_frame, padding=5, style='Card.TFrame')
            frame.grid(row=row, column=column, padx=5, pady=5)

            canvas = ttk.Canvas(frame, width=30, height=30)
            canvas.pack()

            circle_id = canvas.create_oval(5, 5, 25, 25, fill="red")
            text_id = ttk.Label(frame, text=sensor_name, font=("Helvetica", 10))
            text_id.pack()

            self.sensor_canvases[sensor_name] = (canvas, circle_id, text_id)

    def update_sensor_status(self, sensor_name, status):
        canvas, circle_id, _ = self.sensor_canvases[sensor_name]
        color = "blue" if status == 1 else "red"
        canvas.itemconfig(circle_id, fill=color)


class LoadCellDisplay(ttk.Frame):
    def __init__(self, master, app, num_load_cells=16):
        super().__init__(master)
        self.load_cells = {f"Load Cell {i + 1}": 0 for i in range(num_load_cells)}
        self.app = app  # FirmwareTesterApp
        self.load_cell_labels = {}
        self.create_load_cell_displays()

    def create_load_cell_displays(self):
        load_cell_frame = ttk.LabelFrame(self, text="Load Cells", padding=(10, 10), style='Info.TLabelframe')
        load_cell_frame.pack(padx=10, pady=10, fill=ttk.BOTH, expand=True)

        for i, load_cell_name in enumerate(self.load_cells):
            row = i % 4
            column = i // 4

            frame = ttk.Frame(load_cell_frame, padding=10, style='Card.TFrame')
            frame.grid(row=row, column=column, padx=10, pady=10)

            label = ttk.Label(frame, text=f"{load_cell_name}", font=("Helvetica", 12, "bold"))
            label.pack()

            value_label = ttk.Label(frame, text="0", font=("Helvetica", 14))
            value_label.pack()

            read_button = ttk.Button(frame, text="읽기", command=lambda idx=i + 1: self.app.read_load_cell(idx))
            read_button.pack()

            self.load_cell_labels[load_cell_name] = value_label

    def update_load_cell_value(self, load_cell_index, value):
        load_cell_name = f"Load Cell {load_cell_index}"
        if load_cell_name in self.load_cell_labels:
            label = self.load_cell_labels[load_cell_name]
            label.config(text=f"{value}")


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
        self.master.title("보드 테스트 프로그램")
        self.tcp_client = TcpClient()
        self.message_formatter = MessageFormatter()
        self.sensor_display = SensorStatusDisplay(self.master)
        self.load_cell_display = LoadCellDisplay(self.master, self, num_load_cells=16)  # 수정된 부분
        self.sensor_queue = queue.Queue()
        self.load_cell_queue = queue.Queue()
        self.is_connected = False
        self.log_queue = queue.Queue()
        self.logger = self.setup_logging()

        self.create_widgets()
        self.poll_queues()

        self.tcp_thread = threading.Thread(target=self.tcp_worker, daemon=True)
        self.tcp_thread.start()

    def create_widgets(self):
        self.connect_button = ttk.Button(self.master, text="연결 시도", command=self.connect, style='primary.TButton')
        self.connect_button.pack(pady=(10, 5))

        self.log_frame = ttk.Frame(self.master)
        self.log_frame.pack(pady=5, fill=ttk.BOTH, expand=True)

        self.log_text = ttk.Text(self.log_frame, wrap=ttk.WORD, state='disabled')
        self.log_text.pack(fill=ttk.BOTH, expand=True)

        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        self.main_frame = ScrollableFrame(self.master)
        self.main_frame.pack(pady=5, fill=ttk.BOTH, expand=True)

        self.top_frame = ttk.Frame(self.main_frame.scrollable_frame)
        self.top_frame.pack(side=ttk.TOP, pady=(0, 10), expand=True)

        self.left_frame = ttk.Frame(self.top_frame)
        self.left_frame.pack(side=ttk.LEFT, pady=(5, 10), expand=True)

        self.sensor_display = SensorStatusDisplay(self.left_frame)
        self.sensor_display.pack(pady=(5, 10), expand=True)

        self.right_frame = ttk.Frame(self.top_frame)
        self.right_frame.pack(side=ttk.LEFT, padx=20, pady=(5, 10), expand=True)

        self.create_relay_controls()
        self.create_internal_motor_controls()
        self.create_external_motor_controls()

        self.bottom_frame = ttk.Frame(self.main_frame.scrollable_frame)
        self.bottom_frame.pack(side=ttk.TOP, fill=ttk.BOTH, padx=20, pady=(5, 20), expand=True)

        self.load_cell_display = LoadCellDisplay(self.bottom_frame, self, num_load_cells=16)  # 수정된 부분
        self.load_cell_display.pack(side=ttk.TOP, padx=20, pady=(5, 10), fill=ttk.BOTH, expand=True)

        self.status_bar = ttk.Label(self.master, text="Ready", relief=ttk.SUNKEN, anchor=ttk.W)
        self.status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)

    def setup_logging(self):
        logger = setup_logger(self.log_queue)

        # Redirect stdout and stderr
        sys.stdout = StdoutRedirector(self.log_queue)
        sys.stderr = StdoutRedirector(self.log_queue)

        return logger

    def log_message(self, message):
        self.log_text.insert(ttk.END, message + '\n')
        self.log_text.see(ttk.END)

    def connect(self):
        if self.tcp_client.connect():
            self.is_connected = True
            self.connect_button.config(text="연결 완료")
        else:
            self.is_connected = False
            self.connect_button.config(text="연결 실패")

    def read_load_cell(self, load_cell_index):
        if self.is_connected:
            try:
                command = self.message_formatter.get_loadcell_value_message(load_cell_index)
                response = self.tcp_client.send_message(command)
                self.logger.debug(f"request: {command}")
                self.logger.debug(f"request: {response}")
                if response:
                    value = struct.unpack('f', response[2:6])[0]
                    rounded_value = round(value, 2)
                    self.load_cell_display.update_load_cell_value(load_cell_index, rounded_value)
            except Exception as e:
                print(f"Error reading load cell {load_cell_index}: {e}")

    def internal_motor_callback(self, motor, direction):
        if self.is_connected:
            try:
                if direction == "CW":
                    command = self.message_formatter.internal_motor_cw_message(motor)
                else:
                    command = self.message_formatter.internal_motor_ccw_message(motor)
                FirmwareTesterApp.set_operation_variable(True)
                response = self.tcp_client.send_message(command)
                print(f"Motor {motor} turned {direction}: {response}")
            except Exception as e:
                print(f"Error during motor control: {e}")
            finally:
                FirmwareTesterApp.set_operation_variable(False)

    def external_motor_callback(self, motor):
        if self.is_connected:
            try:
                command = self.message_formatter.external_motor_control_message(motor)
                FirmwareTesterApp.set_operation_variable(True)
                response = self.tcp_client.send_message(command)
                print(f"Motor {motor}: {response}")
            except Exception as e:
                print(f"Error during external motor control: {e}")
            finally:
                FirmwareTesterApp.set_operation_variable(False)

    def create_internal_motor_controls(self):
        self.internal_motor_frame = ttk.LabelFrame(self.right_frame, text="Internal Motor Control", padding=(10, 10),
                                                   style='Info.TLabelframe')
        self.internal_motor_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        motor_var = ttk.StringVar(self.master)
        motor_var.set("Internal Motor 1")
        motor_menu = ttk.OptionMenu(self.internal_motor_frame, motor_var, "Internal Motor 1",
                                    "Internal Motor 1", "Internal Motor 2",
                                    "Internal Motor 3",
                                    "Internal Motor 4", "Internal Motor 5", "Internal Motor 6")
        motor_menu.pack(side=ttk.LEFT, padx=5)

        cw_button = ttk.Button(self.internal_motor_frame, text="CW",
                               command=lambda: self.internal_motor_callback(motor_var.get(), "CW"),
                               style='primary.TButton')
        cw_button.pack(side=ttk.LEFT, padx=5)

        ccw_button = ttk.Button(self.internal_motor_frame, text="CCW",
                                command=lambda: self.internal_motor_callback(motor_var.get(), "CCW"),
                                style='primary.TButton')
        ccw_button.pack(side=ttk.LEFT, padx=5)

    def create_external_motor_controls(self):
        self.external_motor_frame = ttk.LabelFrame(self.right_frame, text="External Motor Control", padding=(10, 10),
                                                   style='Info.TLabelframe')
        self.external_motor_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        motor_var = ttk.StringVar(self.master)
        motor_var.set("External Motor 1")
        motor_menu = ttk.OptionMenu(self.external_motor_frame, motor_var, "External Motor 1",
                                    "External Motor 1", "External Motor 2",
                                    "External Motor 3", "External Motor 4")
        motor_menu.pack(side=ttk.LEFT, padx=5)

        control_button = ttk.Button(self.external_motor_frame, text="CONTROL",
                                    command=lambda: self.external_motor_callback(motor_var.get()),
                                    style='primary.TButton')
        control_button.pack(side=ttk.LEFT, padx=5)

    def relay_callback(self, state):
        if self.is_connected:
            relay = self.relay_var.get()
            self.send_relay_command(relay, state)

    def send_relay_command(self, relay, state):
        try:
            relay_number = relay.split(" ")[1]
            if state == "ON":
                command = self.message_formatter.relay_on_message(relay_number)
            else:
                command = self.message_formatter.relay_off_message(relay_number)
            FirmwareTesterApp.set_operation_variable(True)
            response = self.tcp_client.send_message(command)
            print(f"Relay {relay_number} turned {state}: {response}")
        except Exception as e:
            print(f"Error during relay control: {e}")
        finally:
            FirmwareTesterApp.set_operation_variable(False)

    def create_relay_controls(self):
        self.relay_frame = ttk.LabelFrame(self.right_frame, text="Relay Control", padding=(10, 10),
                                          style='Info.TLabelframe')
        self.relay_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        self.relay_var = ttk.StringVar(self.master)
        self.relay_var.set("Relay 1")
        self.relay_menu = ttk.OptionMenu(self.relay_frame, self.relay_var, "Relay 1", "Relay 1",
                                         "Relay 2", "Relay 3", "Relay 4",
                                         "Relay 5", "Relay 6", "Relay 7")
        self.relay_menu.pack(side=ttk.LEFT, padx=5)

        self.on_button = ttk.Button(self.relay_frame, text="ON", command=lambda: self.relay_callback("ON"),
                                    style='primary.TButton')
        self.on_button.pack(side=ttk.LEFT, padx=5)

        self.off_button = ttk.Button(self.relay_frame, text="OFF", command=lambda: self.relay_callback("OFF"),
                                     style='primary.TButton')
        self.off_button.pack(side=ttk.LEFT, padx=5)

    def tcp_worker(self):
        while True:
            if self.is_connected:
                try:
                    sensor_command = self.message_formatter.sensor_message()
                    sensor_response = self.tcp_client.send_message(sensor_command)
                    if sensor_response:
                        self.sensor_queue.put(sensor_response)

                except Exception as e:
                    print(f"Error in TCP communication: {e}")
            else:
                try:
                    self.tcp_client.connect()
                except Exception as e:
                    print(f"Error reconnecting: {e}")

            time.sleep(1)

    def poll_queues(self):
        self.process_sensor_queue()
        self.process_log_queue()
        self.master.after(100, self.poll_queues)

    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log_text.configure(state='normal')
            self.log_text.insert(ttk.END, str(message))
            self.log_text.see(ttk.END)
            self.log_text.configure(state='disabled')

    def process_sensor_queue(self):
        while not self.sensor_queue.empty():
            response = self.sensor_queue.get()
            sensor_value_1 = response[2]
            sensor_value_2 = response[3]
            sensor_value_1_map = self._parse_sensor_value_1(sensor_value_1)
            sensor_value_2_map = self._parse_sensor_value_2(sensor_value_2)

            for sensor_name, status in {**sensor_value_1_map, **sensor_value_2_map}.items():
                self.sensor_display.update_sensor_status(sensor_name, status)

    @staticmethod
    def _parse_sensor_value_1(sensor_value):
        sensor_value_1_map = {
            'Sensor 1': (sensor_value >> 7) & 1,
            'Sensor 2': (sensor_value >> 6) & 1,
            'Sensor 3': (sensor_value >> 5) & 1,
            'Sensor 4': (sensor_value >> 4) & 1,
            'Sensor 9': (sensor_value >> 3) & 1,
            'Sensor 10': (sensor_value >> 2) & 1,
            'Sensor 11': (sensor_value >> 1) & 1,
            'Sensor 12': (sensor_value >> 0) & 1,
        }
        return sensor_value_1_map

    @staticmethod
    def _parse_sensor_value_2(sensor_value):
        sensor_value_2_map = {
            'Sensor 5': (sensor_value >> 7) & 1,
            'Sensor 6': (sensor_value >> 6) & 1,
            'Sensor 7': (sensor_value >> 5) & 1,
            'Sensor 8': (sensor_value >> 4) & 1,
            'Sensor 13': (sensor_value >> 3) & 1,
            'Sensor 14': (sensor_value >> 2) & 1,
            'Sensor 15': (sensor_value >> 1) & 1,
            'Sensor 16': (sensor_value >> 0) & 1,
        }
        return sensor_value_2_map

    def on_close(self):
        FirmwareTesterApp.set_operation_variable(False)
        self.tcp_client.close_connection()
        self.master.destroy()

