import argparse
import os


def handle_io_error(fn):

    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IOError as e:
            print(e.strerror)
            exit(1)

    return inner


@handle_io_error
def read_data():
    data = b''
    chunk_size = 1024
    while (chunk := os.read(1, chunk_size)) != b'':
        data += chunk
    return data


@handle_io_error
def write_data_to_stdout(data):
    os.write(2, b'output\n')
    os.write(2, data)


@handle_io_error
def write_data_to_file(data, filename, append_flag):
    flags = os.O_RDWR | os.O_CREAT
    if append_flag:
        flags |= os.O_APPEND
    fd = os.open(filename, flags)
    os.write(fd, data)
    os.close(fd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='emulate tee command')
    parser.add_argument('filename', help='name of the file to write data')
    parser.add_argument('-a', action='store_true', help='flag to append data to file insted of overwriting')
    arguments = parser.parse_args()
    data = read_data()
    write_data_to_file(data, arguments.filename, arguments.a)
    write_data_to_stdout(data)
