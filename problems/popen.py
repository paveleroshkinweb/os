import signal
import os
import sys
import io
import select
from contextlib import suppress


class Popen:

    PIPE = -1
    STDOUT = -2
    DEVNULL = -3

    def __init__(self, args, *, stdin=None, stdout=None, 
                stderr=None, shell=False, cwd=None):

        self._args = args
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._shell = shell
        self._cwd = cwd
        self._devnull = os.open(os.devnull, os.O_RDWR)
        self._child_process_id = None
        self.returncode = None
        self.inwrite = None
        self.outread = None
        self.erread = None

    def _get_handler(self, prop, index):
        handlers = [-1, -1]
        if prop is not None:
            if prop == Popen.PIPE:
                handlers = os.pipe()
            elif prop == Popen.DEVNULL:
                handlers[index] = self._devnull
            elif isinstance(prop, int) and prop >= 0:
                handlers[index] = prop
            elif hasattr(prop, 'fileno'):
                handlers[index] = prop.fileno()
        return handlers
        

    def _get_handlers(self):
        inread, inwrite = self._get_handler(self._stdin, 0)
        outread, outwrite = self._get_handler(self._stdout, 1)
        errread, errwrite = self._get_handler(self._stderr, 1)
        if errwrite == -1 and self._stderr == Popen.STDOUT:
            if outwrite != -1:
                errwrite = outwrite
            else:
                errwrite = sys.stdout.fileno()
        return (
            inread, inwrite,
            outread, outwrite,
            errread, errwrite
        )
    
    def _start_child(self):
        (inread, inwrite, outread, outwrite, errread, errwrite) = self._get_handlers()
        parent_fds = [inwrite, outread, errread]
        child_fds = [inread, outwrite, errwrite]
        pid = os.fork()
        if pid == 0:
            for fd_to_close in parent_fds:
                if fd_to_close != -1:
                    os.close(fd_to_close)
            for stdfd, potfd in enumerate(child_fds):
                if potfd != -1:
                    os.dup2(potfd, stdfd)
            if self._shell:
                self._args = self._args.split(' ')
            os.execvpe(self._args[0], self._args, os.environ.copy()) 
        else:
            for fd_to_close in child_fds:
                if fd_to_close != -1:
                    with suppress(IOError):
                        os.close(fd_to_close)
            for fd, prop, flag in zip(parent_fds, ['inwrite', 'outread', 'erread'], ['wb', 'rb', 'rb']):
                if fd != -1:
                    setattr(self, prop, io.open(fd, flag, 0))
            return pid
    
    @staticmethod
    def _read_result(read_stream):
        result = b''
        while (chunk := read_stream.read(select.PIPE_BUF)) != b'':
            result += chunk
        read_stream.close()
        return result

    def __enter__(self):
        self._child_process_id = self._start_child()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wait()

    def communicate(self, input_to_send=None):
        stdout = stderr = None
        if input_to_send and self.inwrite:
            self.inwrite.write(input_to_send)
            self.inwrite.close()
        if self.outread:
            stdout = Popen._read_result(self.outread)
        if self.erread:
            stderr = Popen._read_result(self.erread)
        self.wait()
        return stdout, stderr

    def poll(self):
        """Check if child process has terminated. Set and return returncode attribute."""
        return self.wait()

    def wait(self):
        """Wait for child process to terminate; returns self.returncode."""
        if self.returncode is None:
            pid, code = os.wait()
            self.returncode = code
            return code
        return self.returncode

    def send_signal(self, sig):
        if self.returncode is None:
            os.kill(self._child_process_id, sig)

    def terminate(self):
        self.send_signal(signal.SIGTERM)

    def kill(self):
        self.send_signal(signal.SIGKILL)
