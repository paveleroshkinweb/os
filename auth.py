import os
import pwd
import sys
import spwd
import crypt
import getpass
from contextlib import suppress


def handle_io_error(fn):

    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IOError as e:
            print(e.strerror)
            exit(1)

    return inner


def get_pass(username):
    with suppress(Exception):
        return pwd.getpwnam(username)


def write_message(message):
    sys.stdout.write(message)
    sys.stdout.flush()


@handle_io_error
def read_username_and_pass():
    write_message('Enter your username(32 symbols at max): ')
    max_name_length = 32
    username = os.read(0, max_name_length).strip().decode()
    password_structure = get_pass(username)
    if not password_structure:
        write_message('Incorrect username, please try again\n')
        return read_username_and_pass()
    return username, password_structure


@handle_io_error
def expected_pass_and_method(username, password_structure):
    shadow = password_structure.pw_passwd == 'x'
    if shadow:
        return spwd.getspnam(username).sp_pwdp, shadow
    return password_structure.pw_passwd, shadow


if __name__ == '__main__':
    username, password_structure = read_username_and_pass()
    expected_password, shadow = expected_pass_and_method(username, password_structure)
    password = getpass.getpass(prompt='Password: ')
    if shadow:
        password = crypt.crypt(password, salt=expected_password)
    if expected_password == password:
        print('Authorized')
    else:
        print('Not authorized')
