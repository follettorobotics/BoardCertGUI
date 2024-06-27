import struct
import sys
import threading
import queue
import time
from tkinter import Canvas, Label

import ttkbootstrap as ttk

from Log.gui_log_sink import StdoutRedirector
from Log.logger_config import setup_logger, logger
from connection.tcp_client import TcpClient
from message_formatter.message_formatter import MessageFormatter


class SensorStatusDisplay(ttk.Frame):
    def __init__(self, master, num_sensors=16):
        super().__init__(master)
        self.sensors = {f"센서 {i + 1}": 0 for i in range(num_sensors)}
        self.sensors = {}
        self.font = ("Helvetica", 10)
        self.create_sensor_displays()
        self.polling_interval = 2000  # milliseconds

    def create_sensor_displays(self):
        for i in range(4):
            self.grid_columnconfigure(i, weight=1)
            self.grid_rowconfigure(i, weight=1)

        for i in range(16):
            frame = ttk.Frame(self)
            row = i % 4
            col = i // 4
            frame.grid(row=row, column=col, padx=5, pady=5)

            label = Label(frame, text=f"센서 {i + 1}", font=self.font)
            label.pack(side="bottom", pady=(0, 5))

            canvas = Canvas(frame, width=40, height=40, highlightthickness=0)
            circle = canvas.create_oval(5, 5, 35, 35, fill="red")
            canvas.pack(side="top", pady=(5, 0))

            self.sensors[f"센서 {i + 1}"] = (label, canvas, circle)

    def update_ui(self, sensor_name, status):
        label, canvas, circle_id = self.sensors[sensor_name]
        color = "blue" if status == 1 else "red"
        canvas.itemconfig(circle_id, fill=color)


class LoadCellDisplay(ttk.Frame):
    def __init__(self, master, app, num_load_cells=16):
        super().__init__(master)
        self.load_cells = {f"Load Cell {i + 1}": 0 for i in range(num_load_cells)}
        self.app = app  # FirmwareTesterApp
        self.load_cell_labels = {}
        self.font = ("Helvetica", 12)
        self.create_load_cell_displays()

    def create_load_cell_displays(self):
        for i in range(8):
            self.grid_columnconfigure(i, weight=1)
        for i in range(2):
            self.grid_rowconfigure(i, weight=1)

        for i, load_cell_name in enumerate(self.load_cells):
            row = i // 8
            column = i % 8

            frame = ttk.Frame(self, padding=10, style='Card.TFrame')
            frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

            label = ttk.Label(frame, text=f"{load_cell_name}", font=self.font)
            label.pack()

            value_label = ttk.Label(frame, text="0", font=("Helvetica", 14))
            value_label.pack()

            read_button = ttk.Button(frame, text="읽기", command=lambda idx=i + 1: self.app.read_load_cell(idx),
                                     style='primary.TButton')
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
        self.sensor_queue = queue.Queue()
        self.load_cell_queue = queue.Queue()
        self.is_connected = False
        self.log_queue = queue.Queue()
        self.logger = self.setup_logging()
        self.font = ("Helvetica", 10)

        self.create_styles()
        self.create_widgets()
        self.poll_queues()
        self.tcp_thread = threading.Thread(target=self.tcp_worker, daemon=True)
        self.tcp_thread.start()

    def create_styles(self):
        style = ttk.Style()
        style.configure("TButton", font=self.font)
        style.configure("TLabel", font=self.font)
        style.configure("TCombobox", font=self.font)

    def create_widgets(self):
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill='both', expand=True)

        margin = 0.02

        # Connection Frame
        connection_frame = ttk.Frame(main_frame, padding="10", relief="solid", borderwidth=2)
        connection_frame.place(relx=margin, rely=0.03, relwidth=1 - 2 * margin, relheight=0.2, anchor='nw')
        self.create_connection_widgets(connection_frame)

        # Log Frame within Connection Frame
        log_frame = ttk.Frame(connection_frame, padding="10", relief="solid", borderwidth=2)
        log_frame.pack(fill='both', expand=True, pady=(10, 0))

        # Log Text with Scrollbar
        log_text = ttk.Text(log_frame, wrap=ttk.WORD, state='disabled', font=self.font)
        log_text.pack(side="left", fill="both", expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text = log_text

        # Sensor Display Frame
        sensor_frame = ttk.Frame(main_frame, padding="10", relief="solid", borderwidth=2)
        sensor_frame.place(relx=margin, rely=0.26, relwidth=(1 - 2 * margin) / 2 - 0.01, relheight=0.37, anchor='nw')
        self.sensor_display = SensorStatusDisplay(sensor_frame)
        self.sensor_display.pack(fill='both', expand=True)

        frame_spacing = 0.01
        frame_height = (0.37 / 3) - (frame_spacing * 2 / 3)

        # Relay Frame
        relay_frame = ttk.Frame(main_frame, padding="10", relief="solid", borderwidth=2)
        relay_frame.place(relx=margin + (1 - 2 * margin) / 2 + frame_spacing / 2,
                          rely=0.26,
                          relwidth=(1 - 2 * margin) / 2 - frame_spacing / 2,
                          relheight=frame_height,
                          anchor='nw')
        self.create_relay_controls(relay_frame)

        # Internal Motor Frame
        internal_motor_frame = ttk.Frame(main_frame, padding="10", relief="solid", borderwidth=2)
        internal_motor_frame.place(relx=margin + (1 - 2 * margin) / 2 + frame_spacing / 2,
                                   rely=0.26 + frame_height + frame_spacing,
                                   relwidth=(1 - 2 * margin) / 2 - frame_spacing / 2,
                                   relheight=frame_height,
                                   anchor='nw')
        self.create_internal_motor_controls(internal_motor_frame)

        # External Motor Frame
        external_motor_frame = ttk.Frame(main_frame, padding="10", relief="solid", borderwidth=2)
        external_motor_frame.place(relx=margin + (1 - 2 * margin) / 2 + frame_spacing / 2,
                                   rely=0.26 + 2 * (frame_height + frame_spacing),
                                   relwidth=(1 - 2 * margin) / 2 - frame_spacing / 2,
                                   relheight=frame_height,
                                   anchor='nw')
        self.create_external_motor_controls(external_motor_frame)

        # Load Cell Display
        load_cell_frame = ttk.Frame(main_frame, padding="10", relief="solid", borderwidth=2)
        load_cell_frame.place(relx=margin, rely=0.66, relwidth=1 - 2 * margin, relheight=0.3, anchor='nw')
        self.load_cell_display = LoadCellDisplay(load_cell_frame, self, num_load_cells=16)
        self.load_cell_display.pack(fill='both', expand=True)

    def create_connection_widgets(self, frame):
        self.connect_button = ttk.Button(frame, text="연결 시도", command=self.connect, style='primary.TButton')
        self.connect_button.pack(pady=(10, 5))

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
            self.poll_queues()
        else:
            self.is_connected = False
            self.connect_button.config(text="연결 실패")

    def read_load_cell(self, load_cell_index):
        if self.is_connected:
            try:
                command = self.message_formatter.get_loadcell_value_message(load_cell_index)
                response = self.tcp_client.send_message(command)
                logger.debug(f"request: {command}")
                logger.debug(f"request: {response}")
                if response:
                    value = struct.unpack('f', response[2:6])[0]
                    rounded_value = round(value, 2)
                    self.load_cell_display.update_load_cell_value(load_cell_index, rounded_value)
            except Exception as e:
                logger.error(f"Error reading load cell {load_cell_index}: {e}")
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
                logger.debug(f"Motor {motor} turned {direction}: {response}")
                print(f"Motor {motor} turned {direction}: {response}")
            except Exception as e:
                logger.error(f"모터 컨트롤 에러: {e}")
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
                logger.error(f"외부 모터 제어 에러: {e}")
                print(f"Error during external motor control: {e}")
            finally:
                FirmwareTesterApp.set_operation_variable(False)

    def create_internal_motor_controls(self, frame):
        motor_var = ttk.StringVar()
        motor_var.set("Internal Motor 1")

        inner_frame = ttk.Frame(frame)
        inner_frame.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)

        motor_label = ttk.Label(inner_frame, text="내부 모터 선택:")
        motor_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        motor_menu = ttk.Combobox(inner_frame, textvariable=motor_var,
                                  values=["Internal Motor 1", "Internal Motor 2",
                                          "Internal Motor 3", "Internal Motor 4",
                                          "Internal Motor 5", "Internal Motor 6"],
                                  state="readonly", width=20)
        motor_menu.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        button_frame = ttk.Frame(inner_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.cw_button = ttk.Button(button_frame, text="CW",
                                    command=lambda: self.internal_motor_callback(motor_var.get(), "CW"),
                                    style='primary.TButton', width=10)
        self.cw_button.pack(padx=5)

        self.ccw_button = ttk.Button(button_frame, text="CCW",
                                     command=lambda: self.internal_motor_callback(motor_var.get(), "CCW"),
                                     style='primary.TButton', width=10)
        self.ccw_button.pack(padx=5)
        button_frame.grid_columnconfigure(0, weight=1)

        inner_frame.columnconfigure(1, weight=1)

    def create_external_motor_controls(self, frame):
        motor_var = ttk.StringVar()
        motor_var.set("External Motor 1")

        inner_frame = ttk.Frame(frame)
        inner_frame.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)

        motor_label = ttk.Label(inner_frame, text="외부 모터 선택:")
        motor_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        motor_menu = ttk.Combobox(inner_frame, textvariable=motor_var,
                                  values=["External Motor 1", "External Motor 2",
                                          "External Motor 3", "External Motor 4"],
                                  state="readonly", width=20)
        motor_menu.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        button_frame = ttk.Frame(inner_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.control_button = ttk.Button(button_frame, text="CONTROL",
                                         command=lambda: self.external_motor_callback(motor_var.get()),
                                         style='primary.TButton', width=10)
        self.control_button.pack(padx=5)

        button_frame.grid_columnconfigure(0, weight=1)

        inner_frame.columnconfigure(1, weight=1)

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
            logger.error(f"릴레이 제어 에러: {e}")
            print(f"Error during relay control: {e}")
        finally:
            FirmwareTesterApp.set_operation_variable(False)

    def create_relay_controls(self, frame):
        inner_frame = ttk.Frame(frame)
        inner_frame.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)

        self.relay_var = ttk.StringVar()
        self.relay_var.set("Relay 1")

        relay_label = ttk.Label(inner_frame, text="릴레이 선택:")
        relay_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.relay_menu = ttk.Combobox(inner_frame, textvariable=self.relay_var,
                                       values=["Relay 1", "Relay 2", "Relay 3", "Relay 4",
                                               "Relay 5", "Relay 6", "Relay 7"],
                                       state="readonly", width=20)
        self.relay_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        button_frame = ttk.Frame(inner_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.on_button = ttk.Button(button_frame, text="ON", command=lambda: self.relay_callback("ON"),
                                    style='primary.TButton', width=10)
        self.on_button.pack(side=ttk.LEFT, padx=5)

        self.off_button = ttk.Button(button_frame, text="OFF", command=lambda: self.relay_callback("OFF"),
                                     style='primary.TButton', width=10)
        self.off_button.pack(side=ttk.LEFT, padx=5)

        # Center the button_frame
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Make the relay_menu expand to fill available space
        inner_frame.grid_columnconfigure(1, weight=1)

    def tcp_worker(self):
        while True:
            if self.is_connected:
                try:
                    sensor_command = self.message_formatter.sensor_message()
                    sensor_response = self.tcp_client.send_message(sensor_command)
                    if sensor_response:
                        self.sensor_queue.put(sensor_response)

                except Exception as e:
                    logger.error(f"TCP 통신 에러: {e}")
                    print(f"Error in TCP communication: {e}")
            else:
                try:
                    self.tcp_client.connect()
                except Exception as e:
                    logger.error(f"재연결 에러: {e}")
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
                self.sensor_display.update_ui(sensor_name, status)

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
