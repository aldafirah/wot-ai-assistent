import win32gui, win32process

def enum_cb(hwnd, _):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if title.strip():
            print(f"{hex(hwnd)}  PID={pid}  TITLE={title}")

win32gui.EnumWindows(enum_cb, None)
