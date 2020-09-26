from threading import Condition, RLock
from time import monotonic as time


PENDING = 0
RUNNING = 1
CANCELLED = 2
FINISHED = 3


class InvalidStateError(Exception):
    """The operation is not allowed in this state."""


class CancelledError(InvalidStateError):
    """The Future was cancelled."""


class Future:

    def __init__(self):
        self._done_condition = Condition(RLock())
        self._state = PENDING
        self._result = None
        self._exception = None
        self._done_callbacks = []

    def __invoke_callbacks(self):
        for callback in self._done_callbacks:
            try:
                callback(self)
            except Exception:
                print('exception calling callback')

    def __get_result(self):
        if self._exception:
            raise self._exception
        return self._result

    def __result(self):
        if self._state == CANCELLED:
            raise CancelledError()
        if self._state == FINISHED:
            return self.__get_result()

    def result(self, timeout=None):
        """The result method gives us any returned values from the future object."""
        start_time = time()
        with self._done_condition:
            res = self.__result()
            if res:
                return res
            self._done_condition.wait(timeout)
            if timeout and start_time + timeout < time():
                raise TimeoutError()
            return self.__result()

    def set_result(self, result):
        """Sets the return value of work associated with the future."""
        with self._done_condition:
            if self._state in [CANCELLED, FINISHED]:
                raise InvalidStateError()
            self._result = result
            self._state = FINISHED
            self._done_condition.notify_all()
        self.__invoke_callbacks()

    def add_done_callback(self, callback):
        """The add_done_callback allows to specify a callback function which
        will be executed at the point of the future's completion."""
        with self._done_condition:
            if self._state in [PENDING, RUNNING]:
                self._done_callbacks.append(callback)
                return
        try:
            callback(self)
        except Exception:
            print('exception calling callback')

    def running(self):
        """Return True if the future is currently executing."""
        with self._done_condition:
            return self._state == RUNNING

    def done(self):
        """Return True of the future was cancelled or finished executing"""
        with self._done_condition:
            return self._state in [CANCELLED, FINISHED]

    def cancel(self):
        """Cancel the future if possible.
        Returns True if the future was cancelled, False otherwise. A future
        cannot be cancelled if it is running or has already completed.
        """
        with self._done_condition:
            if self._state in [RUNNING, FINISHED]:
                return False
            if self._state == CANCELLED:
                return True
            self._state = CANCELLED
            self._done_condition.notify_all()
        self.__invoke_callbacks()
        return True

    def canceled(self):
        """Return True if the future was cancelled."""
        with self._done_condition:
            return self._state == CANCELLED

    def __exception(self):
        if self._state == CANCELLED:
            raise CancelledError()
        if self._state == FINISHED:
            return self._exception

    def exception(self, timeout=None):
        """Return the exception raised by the call that the future represents."""
        start_time = time()
        with self._done_condition:
            res = self.__exception()
            if res:
                return res
            self._done_condition.wait()
            if timeout and start_time + timeout < time():
                raise TimeoutError()
            return self.__exception()

    def set_exception(self, exception):
        """Sets the result of the future as being the given exception."""
        with self._done_condition:
            if self._state in [CANCELLED, FINISHED]:
                raise InvalidStateError()
            self._exception = exception
            self._state = FINISHED
            self._done_condition.notify_all()

    def set_running(self):
        """Mark the future as running or process any cancel notifications."""
        with self._done_condition:
            if self._state == PENDING:
                self._state = RUNNING
                return True
            return False
