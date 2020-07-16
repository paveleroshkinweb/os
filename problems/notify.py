import inotify.adapters
import os
import argparse

# создание удаление переименование

def watch(directory):
    mask = inotify.constants.IN_CREATE | inotify.constants.IN_DELETE | inotify.constants.IN_MODIFY
    notifier = inotify.adapters.InotifyTree(path=directory, mask=mask)
    for event in notifier.event_gen(yield_nones=False):
        print(event)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='program to watch folder')
    parser.add_argument('directory', help='directory to watch')
    args = parser.parse_args()
    watch(args.directory)
