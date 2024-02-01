from __future__ import annotations
# import sqlite3  # Use 'mysql.connector' para MySQL ou 'pyodbc' para SQL Server
import pyodbc
from typing import Tuple, Dict, List, Any
# import mysql.connector
# from mysql.connector import MySQLConnection
from abc import ABC, abstractmethod


class ConnectionDB:

    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def __enter__(self) -> ConnectionDB:
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exit_value: None, value: None, traceback: None) -> None:
        self.cursor.close()
        self.connection.close()

    def select(self, sql: str) -> List[str]:
        self.cursor.execute(sql)
        value = [row for row in self.cursor]
        return value

    def select_item(self, sql: str) -> Any:
        value = self.cursor.execute(sql)
        result = value.fetchone()
        return result

    def insert(self, table: str, column: Tuple[str], values: Tuple) -> None:
        try:
            sql = f"INSERT INTO {table} ({', '.join(column)}) VALUES ({', '.join(['?']*len(column))})"
            self.cursor.execute(sql, values)
            self.connection.commit()
        except Exception as e:
            raise Exception(f"Erro ao executar INSERT: {e}")

    def update(self, table: str, column_condition: str, value_condition: str, dados: Dict[str, str]) -> None:
        try:
            set_clause = ", ".join([f"{k} = ?" for k in dados.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {column_condition} = ?"
            values = list(dados.values()) + [value_condition]
            self.cursor.execute(sql, values)
            self.connection.commit()
        except Exception as e:
            raise Exception(f"Erro ao executar UPDATE: {e}")

    def delete(self, table: str, column_condition: str, value_condition: str) -> None:
        try:
            sql = f'DELETE FROM {table} WHERE {column_condition} = ?'
            self.cursor.execute(sql, value_condition)
            self.connection.commit()
        except Exception as e:
            raise Exception(f"Erro ao executar DELETE: {e}")


class IConnection(ABC):
    @abstractmethod
    def config_connection(self, *args, **kwargs) -> None:
        pass


class SQLConnection(IConnection):
    def config_connection(self, server: str, database: str, username: str, password: str) -> pyodbc.Connection:
        connection_sql = pyodbc.connect(
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        return connection_sql


class MySQLConnection(IConnection):
    def config_connection(self, server: str, database: str, username: str, password: str) -> Any | MySQLConnection:
        connection_mysql = mysql.connector.connect(
            f"Server={server};Database={database};Uid={username};Pwd={password};"
        )
        return connection_mysql


class SQLiteConnection(IConnection):
    def config_connection(self, file_path: str) -> sqlite3.Connection:
        connection_sqlite = sqlite3.connect(file_path)
        return connection_sqlite


class AccessConnection(IConnection):
    def config_connection(self, directory: str, password: str | None = None) -> Connection:
        if password:
            connection_access = pyodbc.connect(
                f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={directory};PWD={password}")
        else:
            connection_access = pyodbc.connect(
                f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={directory};")
        return connection_access


class Connection:

    @staticmethod
    def sql() -> SQLConnection:
        return SQLConnection()

    @staticmethod
    def mysql() -> MySQLConnection:
        return MySQLConnection()

    @staticmethod
    def access() -> AccessConnection:
        return AccessConnection()

    @staticmethod
    def sqlite() -> SQLiteConnection:
        return SQLiteConnection()


if __name__ == '__main__':
    # rgb(69, 111, 223)
    ...