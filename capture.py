import time
import cv2
import numpy as np
from mss import mss


def _sleep_if_needed(last_ts, fps_limit):
    if fps_limit and fps_limit > 0:
        dt = time.time() - last_ts[0]
        need = max(0.0, (1.0 / fps_limit) - dt)
        if need > 0:
            time.sleep(need)
        last_ts[0] = time.time()


class ScreenSource:
    def __init__(self, region):
        x, y, w, h = region
        self.bbox = {"left": int(x), "top": int(y), "width": int(w), "height": int(h)}
        self.sct = mss()
        self._last_ts = [time.time()]

    def read(self):
        _sleep_if_needed(self._last_ts, 0)
        img = np.array(self.sct.grab(self.bbox))[:, :, :3]  # BGRA -> BGR
        return True, img

    def release(self):
        self.sct.close()


class CameraSource:
    def __init__(self, index):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()


class UrlSource:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()


class WindowSource:
    """
    Захват заданного окна (Windows) по PID/имени процесса/заголовку.
    Снимаем клиентскую область (без рамок). Работает стабильно в Borderless.
    """
    def __init__(self, match_by="process_name", process_name=None, pid=None,
                 title=None, match_mode="contains", prefer_client=True,
                 fps_limit=60, fallback_region=None, allow_fallback=True):
        try:
            import win32gui, win32con, win32process
            import ctypes
        except Exception as e:
            raise RuntimeError("Установи pywin32: pip install pywin32") from e

        # DPI-Aware, чтобы координаты были точными
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

        self.win32gui = __import__("win32gui")
        self.win32con = __import__("win32con")
        self.win32process = __import__("win32process")

        self.match_by = (match_by or "process_name").lower()
        self.process_name = process_name
        self.target_pid = int(pid) if pid else None
        self.title_query = title or ""
        self.match_mode = match_mode
        self.prefer_client = bool(prefer_client)
        self.fps_limit = int(fps_limit) if fps_limit else 0
        self.allow_fallback = allow_fallback
        self.fallback_region = fallback_region

        self._sct = mss()
        self._last_ts = [time.time()]
        self.hwnd = self._find_window()
        if self.hwnd is None:
            if allow_fallback and fallback_region:
                x, y, w, h = fallback_region
                self._screen_fallback = True
                self.bbox = {"left": int(x), "top": int(y), "width": int(w), "height": int(h)}
                print("[WindowSource] Окно не найдено, используем screen_region.")
            else:
                raise ValueError(self._no_window_msg())
        else:
            self._screen_fallback = False

    def _no_window_msg(self):
        if self.match_by == "pid":
            return f"Окно по PID {self.target_pid} не найдено"
        if self.match_by == "process_name":
            return f"Окно процесса '{self.process_name}' не найдено"
        return f"Окно по заголовку '{self.title_query}' не найдено"

    def _all_visible_windows(self):
        """Список (hwnd, title, pid) для всех видимых окон верхнего уровня."""
        wins = []

        def enum_cb(hwnd, _):
            if not self.win32gui.IsWindowVisible(hwnd):
                return
            title = self.win32gui.GetWindowText(hwnd)
            _, pid = self.win32process.GetWindowThreadProcessId(hwnd)
            wins.append((hwnd, title or "", int(pid)))

        self.win32gui.EnumWindows(enum_cb, None)
        return wins

    def _resolve_pid_from_process_name(self):
        """Находим PID по имени процесса (берём последний активный)."""
        try:
            import psutil
        except Exception as e:
            raise RuntimeError("Для match_by=process_name установи psutil: pip install psutil") from e

        name = (self.process_name or "").lower()
        if not name:
            return None
        candidates = [p for p in psutil.process_iter(["pid", "name"]) if (p.info.get("name") or "").lower() == name]
        return candidates[-1].info["pid"] if candidates else None

    def _match_title(self, title):
        t = (title or "")
        q = self.title_query
        if not q:
            return False
        if self.match_mode == "equals":
            return t.lower() == q.lower()
        if self.match_mode == "regex":
            import re
            return re.search(q, t, flags=re.I) is not None
        return q.lower() in t.lower()  # contains

    def _find_window(self):
        wins = self._all_visible_windows()

        # 1) PID
        if self.match_by == "pid" and self.target_pid:
            for hwnd, title, pid in wins:
                if pid == self.target_pid:
                    return hwnd

        # 2) process_name
        if self.match_by == "process_name":
            pid = self._resolve_pid_from_process_name()
            if pid:
                for hwnd, title, wpid in wins:
                    if wpid == pid:
                        return hwnd

        # 3) title
        if self.match_by == "title":
            for hwnd, title, pid in wins:
                if self._match_title(title):
                    return hwnd

        return None

    def _compute_bbox(self):
        # если окно потерялось — попробуем найти снова
        if self.hwnd is None or not self.win32gui.IsWindow(self.hwnd):
            self.hwnd = self._find_window()
            if self.hwnd is None:
                if self.allow_fallback and self.fallback_region:
                    x, y, w, h = self.fallback_region
                    return {"left": int(x), "top": int(y), "width": int(w), "height": int(h)}
                return None

        if self.prefer_client:
            rect = self.win32gui.GetClientRect(self.hwnd)  # (l,t,r,b) в клиентских координатах
            if not rect:
                return None
            x, y = self.win32gui.ClientToScreen(self.hwnd, (0, 0))
            w = max(0, rect[2] - rect[0])
            h = max(0, rect[3] - rect[1])
        else:
            x1, y1, x2, y2 = self.win32gui.GetWindowRect(self.hwnd)
            x, y, w, h = x1, y1, max(0, x2 - x1), max(0, y2 - y1)

        if w <= 0 or h <= 0:
            return None
        return {"left": int(x), "top": int(y), "width": int(w), "height": int(h)}

    def read(self):
        _sleep_if_needed(self._last_ts, self.fps_limit)
        if getattr(self, "_screen_fallback", False):
            img = np.array(self._sct.grab(self.bbox))[:, :, :3]
            return True, img

        bbox = self._compute_bbox()
        if bbox is None:
            return False, None
        img = np.array(self._sct.grab(bbox))[:, :, :3]
        return True, img

    def release(self):
        self._sct.close()


def make_source(cfg):
    src = cfg.get('source', 'screen')
    if src == 'screen':
        return ScreenSource(cfg.get('screen_region', [0, 0, 1920, 1080]))
    elif src == 'camera':
        return CameraSource(cfg.get('camera_index', 0))
    elif src in ('rtmp', 'hls'):
        return UrlSource(cfg.get('url'))
    elif src == 'window':
        wcfg = cfg.get('window', {}) or {}
        return WindowSource(
            match_by=wcfg.get('match_by', 'process_name'),
            process_name=wcfg.get('process_name'),
            pid=wcfg.get('pid'),
            title=wcfg.get('title', 'World of Tanks'),
            match_mode=wcfg.get('match_mode', 'contains'),
            prefer_client=wcfg.get('prefer_client_area', True),
            fps_limit=wcfg.get('fps_limit', 60),
            fallback_region=cfg.get('screen_region'),
            allow_fallback=wcfg.get('allow_fallback_to_screen', True),
        )
    else:
        raise ValueError(f"Неизвестный source: {src}")
