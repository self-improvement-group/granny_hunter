import os
import hashlib
from datetime import datetime
from pathlib import Path
import sqlite3
import argparse
from html_table import tabulate



file_count = 0
files_size = 0
LIMIT_SIZE = 80000
BULK_SIZE = 10
PATH = 'D:\WorkSpace\Projects_edu\Synonymizer'


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()



def search_files(path):
    file_buf = []
    my_filter=lambda x: x.stat().st_size>=LIMIT_SIZE
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and my_filter(entry):
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
    global file_count
    global files_size

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
    cursor.executemany('INSERT INTO files (file_hash, absolute_path, name, size, last_modified) VALUES (?, ?, ?, ?, ?);', metadata)
    connection.commit()


def create_tables():
    files_all = 'SELECT file_hash, absolute_path, name, size, last_modified FROM files ORDER BY size DESC, last_modified ASC;'
    files_repeated = """SELECT file_hash, absolute_path, name, size, last_modified FROM files WHERE file_hash IN
        (SELECT file_hash FROM files GROUP BY file_hash HAVING COUNT(*) > 1)
        ORDER BY size DESC, last_modified ASC;
    """
    
    tabulate('repeated_files.html', database_fetch(files_repeated))
    tabulate('finded_files.html', database_fetch(files_all))


def database_fetch(query):
    cursor.execute(query)
    return cursor.fetchall()


if __name__ == '__main__':

    if Path('cached_files.db').exists():
        os.remove('cached_files.db')

    connection = sqlite3.connect('cached_files.db')
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS files(
        fileid INTEGER PRIMARY KEY AUTOINCREMENT,
        file_hash TEXT NOT NULL,
        absolute_path TEXT NOT NULL,
        name TEXT,
        size INTEGER NOT NULL,
        last_modified TEXT);
        """)
    connection.commit()


    progress_start()
    time_start = datetime.now()

    search_files(PATH)

    time_end = datetime.now()
    progress_end()
    print(time_end - time_start)
    create_tables()

    connection.close()
    os.remove('cached_files.db')
