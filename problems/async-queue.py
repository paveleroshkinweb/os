import threading
import queue
from collections import deque
from time import monotonic as time

try:
    from _queue import Empty
except ImportError:
    class Empty(Exception):
        pass


class Full(Exception):
    pass


class Queue:

    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self.queue = deque()
        self.mutex = threading.RLock()

        # Notify whenever an item is added to the queue; a
        # thread waiting to get is notified then.
        self.item_added = threading.Condition(self.mutex)

        # Notify not_full whenever an item is removed from the queue;
        # a thread waiting to put is notified then.
        self.item_removed = threading.Condition(self.mutex)

        # Notify all_tasks_done whenever the number of unfinished tasks
        # drops to zero; thread waiting to join() is notified to resume
        self.all_tasks_done = threading.Condition(self.mutex)
        self.unfinished_tasks = 0

    def _qsize(self):
        return len(self.queue)
    
    def _put(self, item):
        self.queue.append(item)
    
    def _get(self):
        return self.queue.popleft()

    def qsize(self):
        with self.mutex:
            return self._qsize()
    
    def empty(self):
        with self.mutex:
            return not self._qsize()
    
    def task_done(self):
        with self.all_tasks_done:
            unfinished = self.unfinished_tasks - 1
            if unfinished < 0:
                raise ValueError('task_done() called to many times')
            elif unfinished == 0:
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished

    def join(self):
        with self.all_tasks_done:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()
    
    def put(self, item, block=True, timeout=None):
        with self.item_added:
            if not block:
                if self._qsize() >= self.maxsize:
                    raise Full
            elif timeout is None:
                while self._qsize() >= self.maxsize:
                    self.item_removed.wait()
            elif timeout < 0:
                raise ValueError('timeout must be greater than 0')
            else:
                endtime = time() + timeout
                while self._qsize() >= self.maxsize:
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Full
                    self.item_removed.wait(timeout)
            self._put(item)
            self.item_added.notify_all()
            self.unfinished_tasks += 1

    def get(self, block=True, timeout=None):
        with self.item_removed:
            if not block:
                if self._qsize() == 0:
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.item_added.wait()
            elif timeout < 0:
                raise ValueError('timeout must be greater than 0')
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.item_added.wait(timeout)
            self.item_removed.notify_all()
            return self._get()
