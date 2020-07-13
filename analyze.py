import os
from contextlib import suppress
from collections import defaultdict
from pwd import getpwnam


def extract_value(line):
    return line.split(':')[1].strip().split('\t')[0].strip()


def exctact_properties(filepath, line_indexes):
    with open(filepath, 'r') as file:
        lines = file.readlines()
        return [extract_value(lines[index]) for index in line_indexes]


def get_ppid_state(filepath):
    return exctact_properties(filepath, [2, 6])


def get_name_uid(filepath):
    return exctact_properties(filepath, [0, 8])


def get_entries():
    folder = '/proc'
    process_ids = [id for id in os.listdir(folder) if id.isnumeric()]
    entries = {}
    for process_id in process_ids:
        with suppress(IOError):
            process_path = os.path.join(folder, process_id)
            if os.path.exists(process_path):
                status_path = os.path.join(process_path, 'status')
                state, ppid = get_ppid_state(status_path)
                entries[process_id] = (ppid, state)
    return entries


def get_buckets(entries):
    buckets = defaultdict(set)
    for process_id, value in entries.items():
        buckets[value[0]].add(process_id)
    return buckets


def construct_tree(entries, buckets):
    tree = {'0': {'command': None, 'childrens': {}}}
    queue = [('0', tree['0'])]
    while queue:
        pid, subtree = queue.pop()
        childrens = buckets[pid]
        for children in childrens:
            process_obj = {'command': entries[children][1], 'childrens': {}}
            subtree['childrens'][children] = process_obj
            queue.append((children, process_obj))
    return tree


def processes_tree():
    entries = get_entries()
    buckets = get_buckets(entries)
    return construct_tree(entries, buckets)


def find_processes_with_file(filename):
    folder = '/proc'
    filepath = os.path.abspath(filename)
    process_ids = [id for id in os.listdir(folder) if id.isnumeric()]
    processes = []
    for process_id in process_ids:
        fd_path = os.path.join(folder, process_id, 'fd')
        descriptors = os.listdir(fd_path)
        for descriptor in descriptors:
            path_to_descriptor = os.path.join(fd_path, descriptor)
            if os.path.exists(path_to_descriptor):
                link = os.readlink(path_to_descriptor)
                if link == filepath:
                    processes.append(process_id)
    return processes


def find_processes_with_user(username):
    uid = getpwnam(username).pw_uid
    folder = '/proc'
    processes = []
    process_ids = [id for id in os.listdir(folder) if id.isnumeric()]
    for process_id in process_ids:
        status_path = os.path.join(folder, process_id, 'status')
        if os.path.exists(status_path):
            name, cur_uid = get_name_uid(status_path)
            if int(cur_uid) == uid:
                processes.append((process_id, name))
    return processes



if __name__ == '__main__':
    tree = processes_tree()
    processes = find_processes_with_file('/snap/atom/257/usr/share/atom/resources/electron.asar')
    processes_with_user = find_processes_with_user('root')
    [print(el) for el in [tree, processes, processes_with_user]]
