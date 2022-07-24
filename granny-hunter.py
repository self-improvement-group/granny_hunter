from operator import concat
import os
import hashlib
from datetime import datetime
from pathlib import Path
import sqlite3
import argparse
from html_table import tabulate



def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def search_files(path):
    file_buf = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and entry.stat().st_size>=LIMIT_SIZE:
                file_buf.append(entry)
                progress(entry)
            elif entry.is_dir():
                search_files(entry)

            if len(file_buf) >= BULK_SIZE: 
                procees_files(file_buf)
                file_buf = []
    if len(file_buf) > 0: procees_files(file_buf)


def progress_start():
    print('Files count:0 Total size:0', end='')

def progress(file):
    global file_count
    global files_size

    file_count += 1
    files_size += file.stat().st_size
    print(f'\rFound files:{file_count} Total size:{files_size} bytes', end='')

def progress_end():
    print(f'\rFound files:{file_count} Total size:{files_size} bytes')


def procees_files(files: list):
    metadata = []
    for file in files:
        metadata.append(
            (md5(file),
            str(Path(file).resolve()),
            str(file.name),
            str(file.stat().st_size),
            str(datetime.fromtimestamp(os.path.getmtime(file))))
        )
    connection.executemany('INSERT INTO files (file_hash, absolute_path, name, size, last_modified) VALUES (?, ?, ?, ?, ?);', metadata)


def render_tables(name, query):
    offset = 0
    page = 1
    while True:
        data = connection.execute(concat(query, str(offset) + ';')).fetchall()
        if len(data) == 0:
            break
        tabulate(ARGS.report.joinpath(name + str(page) + '.html'), name, data, page)
        page += 1
        offset += 60


if __name__ == '__main__':
    BULK_SIZE = 10

    QUERY_ALL = 'SELECT file_hash, absolute_path, name, size, last_modified FROM files ORDER BY size DESC, last_modified ASC LIMIT 60 OFFSET '
    
    QUERY_REPEATED = """SELECT file_hash, absolute_path, name, size, last_modified FROM files WHERE file_hash IN
            (SELECT file_hash FROM files GROUP BY file_hash HAVING COUNT(*) > 1)
            ORDER BY size DESC, last_modified ASC LIMIT 60 OFFSET 
            """

    parser = argparse.ArgumentParser(description='Searches for files larger than the specified size')
    parser.add_argument('path', type=Path)
    parser.add_argument('size', type=int)
    parser.add_argument('-unit', choices=['B', 'KB', 'MB', 'GB'], default='B')
    parser.add_argument('-report', type=Path, default=Path('report'))
    ARGS = parser.parse_args()

    PATH = ARGS.path.resolve()

    sizing = {
        'B': ARGS.size,
        'KB': ARGS.size << 10,
        'MB': ARGS.size << 20,
        'GB': ARGS.size << 30
    }
    LIMIT_SIZE = sizing[ARGS.unit]

    if Path('cached_files.db').exists():
        os.remove('cached_files.db')

    connection = sqlite3.connect('cached_files.db')
    connection.execute("""CREATE TABLE IF NOT EXISTS files(
        fileid INTEGER PRIMARY KEY AUTOINCREMENT,
        file_hash TEXT NOT NULL,
        absolute_path TEXT NOT NULL,
        name TEXT,
        size INTEGER NOT NULL,
        last_modified TEXT);
        """)

    file_count = 0
    files_size = 0
    progress_start()
    time_start = datetime.now()

    search_files(PATH)

    time_end = datetime.now()
    progress_end()
    print(time_end - time_start)

    Path(ARGS.report).mkdir(exist_ok=True)
    render_tables('all', QUERY_ALL)
    render_tables('repeated', QUERY_REPEATED)
    
    connection.close()
    os.remove('cached_files.db')
