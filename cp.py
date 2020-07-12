import argparse
import os
import time


def handle_io_error(fn):

    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IOError as e:
            print(e.strerror)
            exit(1)

    return inner


def read_file(filepath):
    fd = os.open(filepath, os.O_RDONLY)
    data = b''
    chunk_size = 1024
    while (chunk := os.read(fd, chunk_size)) != b'':
        data += chunk
    os.close(fd)
    return data


def write_copy(data, filepath):
    dirname = os.path.dirname(filepath)
    copy_filename = f'copy-{os.path.basename(filepath)}'
    path = os.path.join(dirname, copy_filename)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT)
    os.write(fd, data)
    os.close(fd)


@handle_io_error
def cp(filepath):
    data = read_file(filepath)
    write_copy(data, filepath)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='cp command to copy files with holes')
    parser.add_argument('filepath', help='file to copy')
    args = parser.parse_args()
    cp(args.filepath)
