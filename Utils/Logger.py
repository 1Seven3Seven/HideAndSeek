import threading


class Logger:
    lock: threading.Lock = threading.Lock()

    @classmethod
    def log(cls, *args, **kwargs):
        with cls.lock:
            print(*args, **kwargs)
