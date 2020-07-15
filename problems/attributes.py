import os
import xattr
import argparse

def _setxattr(arguments, flag):
    namespace = arguments.namespace
    file = arguments.file
    attr = arguments.attr
    value = arguments.value
    return xattr.setxattr(file, f'{namespace}.{attr}', value, flag)


def createattr(arguments):
    return _setxattr(arguments, xattr.XATTR_CREATE)


def getattr(arguments):
    namespace = arguments.namespace
    attr = arguments.attr
    file = arguments.file
    return xattr.getxattr(file, f'{namespace}.{attr}')


def listattr(arguments):
    file = arguments.file
    return xattr.listxattr(file, )

def updateattr(arguments):
    return _setxattr(arguments, xattr.XATTR_REPLACE)

def cmd(arguments):
    try:
        command_handlers = {
            'setattr': setattr,
            'getattr': getattr,
            'listattr': listattr,
            'createattr': createattr
        }
        handler = command_handlers[arguments.command]
        print(handler(arguments))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    command_choices = ['createattr', 'getattr', 'listattr', 'updateattr']
    namespace_choices = ['user', 'trusted', 'system', 'security']
    parser = argparse.ArgumentParser(description='A program to work with extra arguments for file')
    parser.add_argument('command', choices=command_choices, help='command to execute')
    parser.add_argument('-namespace', '--namespace', choices=namespace_choices, help='namespace for attributes', default='user')
    parser.add_argument('-file', '--file', help='filepath', required=True)
    parser.add_argument('-attr', '--attr', help='attribute to process')
    parser.add_argument('-value', '--value', help='value to set or update')
    arguments = parser.parse_args()
    cmd(arguments)
