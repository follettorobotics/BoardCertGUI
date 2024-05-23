import threading
import ttkbootstrap as ttk
from connection.tcp_client import TcpClient
from message_formatter.message_formatter import MessageFormatter  # 가정된 메시지 포맷터 클래스


class SensorStatusDisplay(ttk.Frame):
    def __init__(self, master, num_sensors=16):
        super().__init__(master)
        self.sensors = {f"Sensor {i + 1}": 0 for i in range(num_sensors)}
        self.sensor_canvases = {}
        self.create_sensor_displays()
        self.tcp_client = TcpClient()
        self.message_formatter = MessageFormatter()
        self.polling_interval = 200  # milliseconds

    def create_sensor_displays(self):
        sensor_frame = ttk.LabelFrame(self, text="Sensors", padding=(10, 10), style='Info.TLabelframe')
        sensor_frame.pack(side=ttk.TOP, padx=10, pady=10, fill=ttk.X)

        for i, sensor_name in enumerate(self.sensors):
            row = i // 4
            column = i % 4

            frame = ttk.Frame(sensor_frame, padding=5, style='Card.TFrame')
            frame.grid(row=row, column=column, padx=5, pady=5)

            canvas = ttk.Canvas(frame, width=30, height=30)
            canvas.pack()

            circle_id = canvas.create_oval(5, 5, 25, 25, fill="red")
            text_id = ttk.Label(frame, text=sensor_name, font=("Helvetica", 10))
            text_id.pack()

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


class LoadCellDisplay(ttk.Frame):
    def __init__(self, master, num_load_cells=16):
        super().__init__(master)
        self.load_cells = {f"Load Cell {i + 1}": 0 for i in range(num_load_cells)}
        self.load_cell_labels = {}
        self.create_load_cell_displays()
        self.polling_interval = 1000  # milliseconds
        self.tcp_client = TcpClient()
        self.message_formatter = MessageFormatter()

    def create_load_cell_displays(self):
        load_cell_frame = ttk.LabelFrame(self, text="Load Cells", padding=(10, 10), style='Info.TLabelframe')
        load_cell_frame.pack(side=ttk.TOP, padx=10, pady=10, fill=ttk.X)

        for i, load_cell_name in enumerate(self.load_cells):
            row = i // 4
            column = i % 4

            frame = ttk.Frame(load_cell_frame, padding=10, style='Card.TFrame')
            frame.grid(row=row, column=column, padx=10, pady=10)

            label = ttk.Label(frame, text=f"{load_cell_name}", font=("Helvetica", 12, "bold"))
            label.pack()

            value_label = ttk.Label(frame, text="0", font=("Helvetica", 14))
            value_label.pack()

            self.load_cell_labels[load_cell_name] = value_label

    def update_load_cell_value(self, load_cell_name, value):
        label = self.load_cell_labels[load_cell_name]
        label.config(text=f"{value}")

    def poll_load_cells(self):
        if not FirmwareTesterApp.get_operation_variable():
            self.simulate_load_cell_updates()
        self.after(self.polling_interval, self.poll_load_cells)

    def simulate_load_cell_updates(self):
        # This function should be updated to get real values from the TCP client
        command = self.message_formatter.get_loadcell_value_message()
        response = self.tcp_client.send_message(command)
        load_cell_values = self.parse_load_cell_values(response)

        for i, value in enumerate(load_cell_values):
            load_cell_name = f"Load Cell {i + 1}"
            self.update_load_cell_value(load_cell_name, value)

    @staticmethod
    def parse_load_cell_values(response):
        load_cell_values = []
        start_index = 2
        for i in range(16):
            value = int.from_bytes(response[start_index:start_index + 4], 'little')
            load_cell_values.append(value)
            start_index += 4
        return load_cell_values


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
        self.sensor_display = None
        self.load_cell_display = None

        self.create_widgets()
        self.command_buttons = []

    def create_widgets(self):
        self.connect_button = ttk.Button(self.master, text="연결 시도", command=self.connect, style='primary.TButton')
        self.connect_button.pack(pady=(10, 5), padx=20)

        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(pady=5, fill=ttk.X, expand=True)

        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(side=ttk.TOP, fill=ttk.X, padx=10, pady=(0, 10), expand=True)

        self.left_frame = ttk.Frame(self.top_frame)
        self.left_frame.pack(side=ttk.LEFT, padx=20, pady=(5, 10), expand=True)

        self.sensor_display = SensorStatusDisplay(self.left_frame)
        self.sensor_display.pack(side=ttk.TOP, padx=20, pady=(5, 10), fill=ttk.X, expand=True)

        self.right_frame = ttk.Frame(self.top_frame, width=400)
        self.right_frame.pack(side=ttk.RIGHT, padx=20, pady=(5, 10), fill=ttk.Y, expand=True)

        self.create_relay_controls()
        self.create_internal_motor_controls()
        self.create_external_motor_controls()

        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.pack(side=ttk.TOP, fill=ttk.X, padx=20, pady=(5, 20), expand=True)

        self.load_cell_display = LoadCellDisplay(self.bottom_frame)
        self.load_cell_display.pack(side=ttk.TOP, padx=20, pady=(5, 10), fill=ttk.X, expand=True)

        self.status_bar = ttk.Label(self.master, text="Ready", relief=ttk.SUNKEN, anchor=ttk.W)
        self.status_bar.pack(side=ttk.BOTTOM, fill=ttk.X)

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
        self.internal_motor_frame = ttk.LabelFrame(self.right_frame, text="Internal Motor Control", padding=(10, 10),
                                                   style='Info.TLabelframe')
        self.internal_motor_frame.pack(fill=ttk.X, pady=10, expand=True)

        motor_var = ttk.StringVar(self.master)
        motor_var.set("Internal Motor 1")
        motor_menu = ttk.OptionMenu(self.internal_motor_frame, motor_var, "Internal Motor 1", "Internal Motor 2",
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
        self.external_motor_frame.pack(fill=ttk.X, pady=10, expand=True)

        motor_var = ttk.StringVar(self.master)
        motor_var.set("External Motor 1")
        motor_menu = ttk.OptionMenu(self.external_motor_frame, motor_var, "External Motor 1", "External Motor 2",
                                    "External Motor 3", "External Motor 4")
        motor_menu.pack(side=ttk.LEFT, padx=5)

        control_button = ttk.Button(self.external_motor_frame, text="CONTROL",
                                    command=lambda: self.external_motor_callback(motor_var.get()),
                                    style='primary.TButton')
        control_button.pack(side=ttk.LEFT, padx=5)

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
        self.relay_frame = ttk.LabelFrame(self.right_frame, text="Relay Control", padding=(10, 10),
                                          style='Info.TLabelframe')
        self.relay_frame.pack(fill=ttk.X, pady=10, expand=True)

        self.relay_var = ttk.StringVar(self.master)
        self.relay_var.set("Relay 1")
        self.relay_menu = ttk.OptionMenu(self.relay_frame, self.relay_var, "Relay 1", "Relay 2", "Relay 3", "Relay 4",
                                         "Relay 5", "Relay 6", "Relay 7")
        self.relay_menu.pack(side=ttk.LEFT, padx=5)

        self.on_button = ttk.Button(self.relay_frame, text="ON", command=lambda: self.relay_callback("ON"),
                                    style='primary.TButton')
        self.on_button.pack(side=ttk.LEFT, padx=5)

        self.off_button = ttk.Button(self.relay_frame, text="OFF", command=lambda: self.relay_callback("OFF"),
                                     style='primary.TButton')
        self.off_button.pack(side=ttk.LEFT, padx=5)

    def connect(self):
        if self.tcp_client.connect():
            self.connect_button.config(text="연결 완료")
            self.start_sensor_polling()

    def start_sensor_polling(self):
        self.sensor_display.poll_sensors()
        self.load_cell_display.poll_load_cells()

    def on_close(self):
        FirmwareTesterApp.set_operation_variable(False)
        self.tcp_client.close_connection()
        self.master.destroy()
