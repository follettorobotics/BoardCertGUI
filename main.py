import ttkbootstrap as ttk

import ctypes

from GUI.firmware_tester_app import FirmwareTesterApp


def center_window(root, width, height):
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))


if __name__ == "__main__":
    app = ttk.Window("보드 테스트 프로그램", themename="flatly")

    # 화면 해상도에 따른 윈도우 크기 조정
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.8)

    center_window(app, window_width, window_height)

    FirmwareTesterApp(app)
    app.protocol("WM_DELETE_WINDOW", app.quit)
    app.mainloop()
