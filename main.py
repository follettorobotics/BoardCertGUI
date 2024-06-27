import ttkbootstrap as ttk

import ctypes

from GUI.firmware_tester_app import FirmwareTesterApp


def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    app = ttk.Window("보드 테스트 프로그램", themename="flatly")

    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    window_width = int(screen_width * 0.5)
    window_height = int(screen_height * 0.65)

    center_window(app, window_width, window_height)

    firmware_tester_app = FirmwareTesterApp(app)
    app.protocol("WM_DELETE_WINDOW", firmware_tester_app.on_close)
    app.mainloop()
