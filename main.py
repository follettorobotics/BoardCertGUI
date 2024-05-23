import ttkbootstrap as ttk

from GUI.firmware_tester_app import FirmwareTesterApp

if __name__ == "__main__":
    app = ttk.Window("보드 테스트 프로그램", themename="flatly")
    app.geometry("1000x800")
    FirmwareTesterApp(app)
    app.protocol("WM_DELETE_WINDOW", app.quit)
    app.mainloop()
