import sqlite3


class Database:
    def __init__(self, name):
        self._name = name
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def create(self, query):
        self._connection = sqlite3.connect(self._name)
        self._cursor = self._connection.cursor()
        self._cursor.execute(query)
        self._connection.commit()

    def clear(self, table: str):
        self._cursor.execute(f'DELETE FROM {table};')
        self._connection.commit()
        self._cursor.execute('VACUUM;')
        self._connection.commit()

    def connect(self):
        self._connection = sqlite3.connect(self._name)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()
    
    def disconnect(self):
        self._connection.close()

    def execute(self, query, values=tuple(), commit=True):
        result = self._cursor.execute(query, values)
        if commit:
            self._connection.commit()
        return result

    def executemany(self, query, values, commit=True):
        result = self._cursor.executemany(query, values)
        if commit:
            self._connection.commit()
        return result

    def fetch(self, query, values=tuple()):
        self._cursor.execute(query, values)
        return self._cursor.fetchall()