import os
from queue import SimpleQueue
from threading import Thread, RLock
from future import Future
from time import monotonic as time


def _worker(queue):
    while True:
        work_item = queue.get()
        if not work_item:
            break
        future, task, args, kwargs = work_item
        try:
            result = task(*args, **kwargs)
        except Exception as e:
            future.set_exception(e)
        else:
            future.set_result(result)


class ExecutorShutdown(Exception):
    """Throws when client tries to submit a new task after shutdown"""


class ThreadPoolExecutor:

    def __init__(self, max_workers=None):

        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) + 4)

        if max_workers <= 0:
            raise ValueError('max_workers must be greater than 0')

        self._max_workers = max_workers
        self._work_queue = SimpleQueue()
        self._threads = []
        self._shutdown = False
        self._shutdown_lock = RLock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.shutdown(wait=True)

    def _adjust_thread(self):
        if len(self._threads) < self._max_workers:
            thread = Thread(target=_worker, args=(self._work_queue,), daemon=True)
            self._threads.append(thread)
            thread.start()

    def map(self, task, *iterables, timeout=None):
        if timeout is not None:
            end_time = time() + timeout
        futures = [self.submit(task, *args) for args in zip(*iterables)]
        for future in futures:
            if timeout:
                yield future.result(end_time - time())
            else:
                yield future.result()

    def submit(self, task, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise ExecutorShutdown()
            future_result = Future()
            work_item = (future_result, task, args, kwargs)
            self._work_queue.put(work_item)
            self._adjust_thread()
            return future_result

    def shutdown(self, wait=False):
        with self._shutdown_lock:
            self._shutdown = True
        for _ in range(len(self._threads)):
            self._work_queue.put(None)
        if wait:
            for thread in self._threads:
                thread.join()
