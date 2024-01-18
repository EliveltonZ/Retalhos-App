from __future__ import annotations
# import sqlite3  # Use 'mysql.connector' para MySQL ou 'pyodbc' para SQL Server
import pyodbc
from typing import Any, Tuple, Dict
# import mysql.connector
from abc import ABC, abstractmethod


class ConnectionDB:
    def __init__(self, connection) -> None:
        self.connection = connection

    def __enter__(self) -> ConnectionDB:
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exit_value, value, traceback) -> None:
        self.cursor.close()
        self.connection.close()

    def select(self, sql) -> list:
        self.cursor.execute(sql)
        value = []
        for row in self.cursor:
            value.append(row)
        return value

    def select_item(self, sql: str) -> Any:
        value = self.cursor.execute(sql)
        result = value.fetchone()
        return result

    def insert(self, table: str, column: Tuple[str], values: Tuple[str]) -> None:
        try:
            sql = f"INSERT INTO {table} ({', '.join(column)}) VALUES ({', '.join(['?']*len(column))})"
            self.cursor.execute(sql, values)
            self.connection.commit()
        except Exception as e:
            raise Exception(f"Erro ao executar INSERT: {e}")

    def update(self, table: str, column_condition: str, value_condition: str,
               dados: Dict[str, str]) -> None:
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
            sql = f'DELETE from {table} WHERE {column_condition} = ?'
            self.cursor.execute(sql, value_condition)
            self.connection.commit()
        except Exception as e:
            Exception(f"Erro ao executar DELETE: {e}")


class IConnection(ABC):
    @abstractmethod
    def config_connection(self, *args, **kwargs) -> Connection:
        pass


class SQLConnection(IConnection):
    def config_connection(self, server: str, database: str, username: str, password: str) -> Connection:
        connection_sql = pyodbc.connect(
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        return connection_sql


class MySQLConnection(IConnection):
    def config_connection(self, server: str, database: str, username: str, password: str) -> Connection:
        connection_mysql = mysql.connector.connect(
            f"Server={server};Database={database};Uid={username};Pwd={password};"
        )
        return connection_mysql


class SQLiteConnection(IConnection):
    def config_connection(self, file_path: str) -> Connection:
        connection_sqlite = sqlite3.connect(file_path)
        return connection_sqlite


class AccessConnection(IConnection):
    def config_connection(self, directory: str) -> Connection:
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
    # Exemplo de uso
    path = "C:\\Users\\GD\\Desktop\\BDretalhos.accdb"

    # type_connection = Connection.access()
    # string_connection = type_connection.config_connection(path)
    # _id = '5'
    # user = 'Elivelton'
    # with ConnectionDB(string_connection) as connection:
    #     connection.update('tblRetalhos', 'id', _id, {'DataEntrada': 'Null', 'Reserva':'""', 'DataReserva': 'Null', 'Responsavel': f'"{user}"'})

    if False:
        # Exemplo de SELECT com parâmetros
        select_query = "SELECT * FROM sua_tabela WHERE coluna = ?"
        params_select = ('valor',)
        resultados_select = sql_instance.select(select_query, params_select)
        print("Resultados do SELECT:", resultados_select)

    if False:
        # Exemplo de INSERT com parâmetros
        insert_query = "INSERT INTO sua_tabela (coluna1, coluna2) VALUES (?, ?)"
        params_insert = ('valor1', 'valor2')
        sql_instance.insert(insert_query, params_insert)

    if False:
        # Exemplo de DELETE com parâmetros
        delete_query = "DELETE FROM sua_tabela WHERE coluna = ?"
        params_delete = ('valor',)
        sql_instance.delete(delete_query, params_delete)

    if False:
        # Exemplo de UPDATE com parâmetros
        select_query = "SELECT * FROM sua_tabela"
        resultados_select = sql_instance.select(select_query)
        print("Resultados do SELECT:", resultados_select)

        sql_instance.update(
            update_table, update_values, where_condition, update_params)
