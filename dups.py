import os
import fcntl
import time
from contextlib import suppress


def handle_io_error(fn):

    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IOError as e:
            print(e.strerror)

    return inner


@handle_io_error
def dup(fd):
    return fcntl.fcntl(fd, fcntl.F_DUPFD, 0)


@handle_io_error
def dup2(old_fd, new_fd):
    if old_fd == new_fd:
        return old_fd
    with suppress(IOError):
        os.close(new_fd)
    duplicated = fcntl.fcntl(old_fd, fcntl.F_DUPFD, new_fd)
    return duplicated


if __name__ == '__main__':
    fd = os.open('temp/file1.txt', os.O_RDWR)
    copy_fd = dup2(fd, fd)
    copy_fd1 = dup(fd)
    print(copy_fd1)
    os.write(copy_fd, b'interesting')
    os.write(copy_fd, b'hello bitch')
    os.write(copy_fd1, b'hmmmm')
    os.close(fd)
    os.close(copy_fd1)
