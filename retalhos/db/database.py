"""Conexão com o banco de dados.

Produção usa Microsoft Access (``.accdb``/``.mdb``) via ODBC. Arquivos ``.db``/``.sqlite``
abrem com SQLite, o que permite testar e desenvolver sem o banco da rede.
Todo SQL do sistema é escrito de forma compatível com os dois.
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

_SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


class DatabaseError(Exception):
    """Falha de conexão ou de comando no banco."""


class Session:
    """Conexão aberta; criada por :meth:`Database.session`."""

    def __init__(self, connection: Any, dialect: str) -> None:
        self._conn = connection
        self._cursor = connection.cursor()
        self.dialect = dialect

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[tuple]:
        self._cursor.execute(sql, tuple(params))
        return [tuple(row) for row in self._cursor.fetchall()]

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> tuple | None:
        self._cursor.execute(sql, tuple(params))
        row = self._cursor.fetchone()
        return tuple(row) if row is not None else None

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        self._cursor.execute(sql, tuple(params))
        return self._cursor.rowcount

    def colunas(self, tabela: str) -> set[str]:
        """Nomes das colunas da tabela, em minúsculas."""
        if self.dialect == "sqlite":
            return {str(r[1]).lower() for r in self.query(f"PRAGMA table_info({tabela})")}
        return {str(c.column_name).lower() for c in self._cursor.columns(table=tabela)}

    def tabela_existe(self, nome: str) -> bool:
        if self.dialect == "sqlite":
            return self.query_one("SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (nome,)) is not None
        return self._cursor.tables(table=nome, tableType="TABLE").fetchone() is not None

    def last_insert_id(self) -> int:
        if self.dialect == "sqlite":
            return int(self._cursor.lastrowid)
        row = self.query_one("SELECT @@IDENTITY")
        if row is None or row[0] is None:
            raise DatabaseError("Não foi possível obter o ID do registro inserido.")
        return int(row[0])

    def close(self) -> None:
        try:
            self._cursor.close()
        finally:
            self._conn.close()


class Database:
    def __init__(self, path: str, password: str = "") -> None:
        self.path = path
        self.password = password

    @property
    def dialect(self) -> str:
        return "sqlite" if Path(self.path).suffix.lower() in _SQLITE_SUFFIXES else "access"

    def _connect(self) -> Any:
        if not self.path:
            raise DatabaseError("Caminho do banco de dados não configurado.")
        if not Path(self.path).is_file():
            raise DatabaseError(f"Banco de dados não encontrado:\n{self.path}")

        if self.dialect == "sqlite":
            sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))
            return sqlite3.connect(self.path)

        import pyodbc  # import tardio: só é necessário com Access

        conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.path};"
        if self.password:
            conn_str += f"PWD={self.password};"
        try:
            return pyodbc.connect(conn_str, autocommit=False)
        except pyodbc.Error as exc:
            raise DatabaseError(f"Não foi possível conectar ao banco de dados:\n{exc}") from exc

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Abre uma sessão transacional: confirma no sucesso, desfaz em caso de erro."""
        session = Session(self._connect(), self.dialect)
        try:
            yield session
            session._conn.commit()
        except Exception:
            session._conn.rollback()
            raise
        finally:
            session.close()

    def test(self) -> bool:
        try:
            with self.session() as s:
                s.query_one("SELECT COUNT(*) FROM tblChapas")
            return True
        except Exception:
            return False
