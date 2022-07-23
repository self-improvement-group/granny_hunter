import os
import hashlib
import configparser
from datetime import datetime
from pathlib import Path
from typing import Callable, Union
from database import Database
from html_table import html_table



file_count = 0
files_size = 0


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def for_files_in(path: Union[str, Path], func: Callable[[os.DirEntry], None], filter: Callable[[os.DirEntry], bool], *args, **kwargs):
    """
    *args and **kwargs applied to func()
    """
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and filter(entry):
                func(entry, *args, **kwargs)
                progress(entry)
            elif entry.is_dir() and CHECK_SUBFOLDER:
                for_files_in(entry, func, filter, *args, **kwargs)


def for_files_bulk(path: Union[str, Path], func: Callable[[os.DirEntry], None], filter: Callable[[os.DirEntry], bool], *args, **kwargs):
    """
    *args and **kwargs applied to func()
    """
    file_buf = []
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file() and filter(entry):
                file_buf.append(entry)
                progress(entry)
            elif entry.is_dir() and CHECK_SUBFOLDER:
                for_files_bulk(entry, func, filter, *args, **kwargs)

            if len(file_buf) >= BULK_SIZE: 
                func(file_buf, **kwargs)
                file_buf = []

    if len(file_buf) > 0: func(file_buf, **kwargs)


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

    print(f'\rFound files:{file_count} Files size:{files_size} bytes')


def get_metadata_os(file) -> tuple:
    file_path = Path(file)
    data = (
        md5(file),
        str(file_path.resolve()),
        str(file.name),
        str(file.stat().st_size),
        str(datetime.fromtimestamp(os.path.getmtime(file)))
    )
    return data


def get_metadata_bulk(files) -> list:
    result = []
    for file in files:
        file_path = Path(file)
        data = (
            md5(file),
            str(file_path.resolve()),
            str(file.name),
            str(file.stat().st_size),
            str(datetime.fromtimestamp(os.path.getmtime(file)))
        )
        result.append(data)
    return result


def save(file, db: Database):
    global chkd_count
    global chkd_size
    query = 'INSERT INTO files (file_hash, absolute_path, name, size, last_modified) VALUES (?, ?, ?, ?, ?);'
    metadata = get_metadata_os(file)
    db.execute(query, metadata)


def save_bulk(files: list, db: Database):
    query = 'INSERT INTO files (file_hash, absolute_path, name, size, last_modified) VALUES (?, ?, ?, ?, ?);'
    db.executemany(query, files)


def proceesd_bulk(files: list, db: Database):
    metadata = get_metadata_bulk(files)
    save_bulk(metadata, db)


def create_tables():
    files_all = 'SELECT file_hash, absolute_path, name, size, last_modified FROM files ORDER BY size DESC, last_modified ASC;'
    files_repeated = """SELECT file_hash, absolute_path, name, size, last_modified FROM files WHERE file_hash IN
        (SELECT file_hash FROM files GROUP BY file_hash HAVING COUNT(*) > 1)
        ORDER BY size DESC, last_modified ASC;
    """
    headers = ['Hash MD5', 'Absolute path', 'Name', 'Size', 'Last modified']
    Path("tables").mkdir(parents=True, exist_ok=True)
    html_table('tables/repeated_files.html', db.fetch(files_repeated), headers)
    html_table('tables/finded_files.html', db.fetch(files_all), headers)


if __name__ == '__main__':

    config = configparser.ConfigParser()
    try:
        config.read('config.ini')

        CHECK_SUBFOLDER = config.getboolean('DEFAULT','CHECK_SUBFOLDER')
        LIMIT_SIZE = config.getint('DEFAULT','LIMIT_SIZE')
        BULK = config.getboolean('DEFAULT','BULK')
        BULK_SIZE = config.getint('DEFAULT','BULK_SIZE')
        paths = config.get('DEFAULT', 'PATHS').split(',')

    except Exception as err:
        print(err)

    db = Database('files.db')

    if Path('files.db').exists():
        print('Clear database? Y/n')
        x = input()
        match x.lower():
            case 'y': 
                db.connect()
                db.clear('files')
            case 'n': db.connect()
            case _: exit()
    else: db.create("""CREATE TABLE IF NOT EXISTS files(
        fileid INTEGER PRIMARY KEY AUTOINCREMENT,
        file_hash TEXT NOT NULL,
        absolute_path TEXT NOT NULL,
        name TEXT,
        size INTEGER NOT NULL,
        last_modified TEXT);
        """)


    print('Make sure that you set up paths for searching\nType Enter to continue...')
    x = input()
    progress_start()
    time_start = datetime.now()
    if BULK:
        for path in paths:
            for_files_bulk(path, proceesd_bulk, filter=lambda x: x.stat().st_size>=LIMIT_SIZE, db=db)
    else:
        for path in paths:
            for_files_in(path, save, filter=lambda x: x.stat().st_size>=LIMIT_SIZE, db=db)
    time_end = datetime.now()
    progress_end()
    print(time_end - time_start)
    create_tables()
