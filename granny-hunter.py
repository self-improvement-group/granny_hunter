import os
import hashlib
from queue import Queue
import threading
from datetime import datetime
from pathlib import Path
import argparse
from time import sleep
from html_table import tabulate
from operator import itemgetter
from jinja2.filters import do_filesizeformat


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def search_loop():
    while not q.empty():
        search(q.get())

def search(path):
    global scanned_size
    folders = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and entry.stat().st_size>=LIMIT_SIZE:
                big_dic.append(
                    {'hash':md5(entry),
                    'path':Path(entry).resolve(),
                    'name':entry.name,
                    'size':entry.stat().st_size,
                    'modified':datetime.fromtimestamp(os.path.getmtime(entry))}
                )
                progress(entry)
            if entry.is_file():
                scanned_size += entry.stat().st_size
            elif entry.is_dir():
                folders.append(entry)
    for f in folders:
        q.put(f)

def progress_start():
    print('Files count:0 Total size:0', end='')

def progress(file):
    global file_count
    global files_size

    file_count += 1
    files_size += file.stat().st_size

def progress_end():
    print(f'Found files:{file_count} Total size:{files_size} bytes')

def loop_print():
    global file_count
    global files_size
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        print(f'\r... Found files:{file_count} Scanned:{do_filesizeformat(scanned_size).ljust(7)}', end='')
        sleep(0.1)
        print(f'\r|.. Found files:{file_count} Scanned:{do_filesizeformat(scanned_size).ljust(7)}', end='')
        sleep(0.1)
        print(f'\r.|. Found files:{file_count} Scanned:{do_filesizeformat(scanned_size).ljust(7)}', end='')
        sleep(0.1)
        print(f'\r..| Found files:{file_count} Scanned:{do_filesizeformat(scanned_size).ljust(7)}', end='')
        sleep(0.1)

def render_tables(name, data):
    offset = 0
    page = 1
    while True:
        page_data = data[offset:offset+60:]
        if len(page_data) == 0:
            break
        tabulate(ARGS.report.joinpath(name + str(page) + '.html'), name, page_data, page)
        page += 1
        offset += 60

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Searches for files larger than the specified size')
    parser.add_argument('path', type=Path)
    parser.add_argument('size', type=int)
    parser.add_argument('-unit', choices=['B', 'KB', 'MB', 'GB'], default='B')
    parser.add_argument('-report', type=Path, default=Path('report'))
    ARGS = parser.parse_args()

    PATH = ARGS.path.resolve()

    LIMIT_SIZE = {
        'B': ARGS.size,
        'KB': ARGS.size << 10,
        'MB': ARGS.size << 20,
        'GB': ARGS.size << 30
    }[ARGS.unit]

    big_dic = []
    scanned_size = 0
    file_count = 0
    files_size = 0

    q = Queue()
    tl = []
    time_start = datetime.now()
    print('Time start: ',time_start)
    progres = threading.Thread(target=loop_print)
    progres.start()
    search(PATH)
    for i in range(4):
        tl.append(threading.Thread(target=search_loop))
        tl[i].start()

    for t in tl:
        t.join()

    progres.do_run = False

    big_dic = sorted(big_dic, key=lambda x: (-x['size'], x['modified']))

    time_end = datetime.now()

    Path(ARGS.report).mkdir(exist_ok=True)
    render_tables('all', big_dic)

    big_dic = sorted(big_dic, key=itemgetter('hash'))

    dups = []
    for i in range(1, len(big_dic)-1):
        previous = big_dic[i-1]['hash']
        current = big_dic[i]['hash']
        next_i = big_dic[i+1]['hash']
        if current == previous and current != next_i:
            dups.append(big_dic[i])
            dups.append(big_dic[i-1])
        elif current == previous and current == next_i:
                dups.append(big_dic[i])

    dups = sorted(dups, key=lambda x: (-x['size'], x['modified']))
    render_tables('dups', dups)

    print()
    print('Folder: ', ARGS.path, ' Limit size: ', ARGS.size, ARGS.unit)
    print('Found files size: ', do_filesizeformat(files_size))
    print('Time end: ',time_end)
    print('Took time: ', time_end - time_start)
    print('Report saved in: ', Path(ARGS.report).resolve())