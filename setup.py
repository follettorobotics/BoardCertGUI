from cx_Freeze import setup, Executable

buildOptions = {
    "packages": [
        "ctypes",
        "struct",
        "threading",
        "queue",
        "time",
        "ttkbootstrap",
        "loguru",
        "socket",
    ],
    "excludes": [
    ]
}

exe = [Executable('main.py', base='Win32GUI')]

setup(
    name='main',
    version='1.0',
    author='me',
    options=dict(build_exe=buildOptions),
    executables=exe
)

