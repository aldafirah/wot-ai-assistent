import time


class FpsMeter:
    def __init__(self):
        self.prev = time.time()
        self.fps = 0.0

    def tick(self):
        now = time.time()
        dt = now - self.prev
        self.prev = now
        if dt > 0:
            self.fps = 1.0/dt
        return self.fps
