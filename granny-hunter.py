import os
import hashlib
import threading
from datetime import datetime
from pathlib import Path
import argparse
from time import sleep
from html_table import tabulate
from operator import itemgetter


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def search_files(path):
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
            elif entry.is_dir():
                search_files(os.path.join('\\?\\',entry))


def progress_start():
    print('Files count:0 Total size:0', end='')

def progress(file):
    global file_count
    global files_size

    file_count += 1
    files_size += file.stat().st_size


def progress_end():
    print(f'Found files:{file_count} Total size:{files_size} bytes')


def procees_files(files: list):

    for file in files:
        big_dic.append(
            {'hash':md5(file),
            'path':Path(file).resolve(),
            'name':file.name,
            'size':file.stat().st_size,
            'modified':datetime.fromtimestamp(os.path.getmtime(file))}
        )


def loop_print():
    global file_count
    global files_size
    t = threading.current_thread()
    while getattr(t, "do_run", True):
        print(f'\r... Found files:{file_count} Total size:{files_size} bytes', end='')
        sleep(0.1)
        print(f'\r|.. Found files:{file_count} Total size:{files_size} bytes', end='')
        sleep(0.1)
        print(f'\r.|. Found files:{file_count} Total size:{files_size} bytes', end='')
        sleep(0.1)
        print(f'\r..| Found files:{file_count} Total size:{files_size} bytes', end='')
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
    file_count = 0
    files_size = 0

    time_start = datetime.now()

    progres = threading.Thread(target=loop_print)
    progres.start()
    search_files(PATH)

    progres.do_run = False

    big_dic = sorted(big_dic, key=lambda x: (-x['size'], x['modified']))

    time_end = datetime.now()

    print(time_end - time_start)

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

    render_tables('dups', dups)

