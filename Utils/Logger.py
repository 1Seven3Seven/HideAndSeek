import threading


class Logger:
    lock: threading.Lock = threading.Lock()

    @classmethod
    def log(cls, *args, **kwargs):
        with cls.lock:
            thread_name = threading.current_thread().name

            if thread_name == "MainThread":
                print(*args, **kwargs)
            else:
                print(f"{thread_name}:", *args, **kwargs)
