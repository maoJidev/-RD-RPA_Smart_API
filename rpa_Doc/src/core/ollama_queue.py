import threading
import queue
import time

class OllamaQueue:
    def __init__(self):
        self.q = queue.Queue()
        self.worker = threading.Thread(
            target=self._worker_loop,
            daemon=True
        )
        self.worker.start()

    def submit(self, func, *args, **kwargs):
        result_q = queue.Queue()
        self.q.put((func, args, kwargs, result_q))
        return result_q.get()  # block แบบมีคิว

    def _worker_loop(self):
        while True:
            func, args, kwargs, result_q = self.q.get()
            try:
                result = func(*args, **kwargs)
                result_q.put(result)
            except Exception as e:
                result_q.put(f"Error: {e}")
            finally:
                self.q.task_done()
