from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from retalhos.config import Settings
from retalhos.models import Usuario

# Para testar contra Access real, aponte RETALHOS_TEST_ACCDB para um .accdb vazio.
ACCESS_TEMPLATE = os.getenv("RETALHOS_TEST_ACCDB")

_ACCESS_DDL = [
    "CREATE TABLE tblChapas (COD DOUBLE, MM TEXT(20), MDF TEXT(255), Ativo BIT)",
    "CREATE TABLE tblRetalhos (id COUNTER PRIMARY KEY, Setor TEXT(50), Cod_Material DOUBLE, "
    "Largura DOUBLE, Altura DOUBLE, DataEntrada DATETIME, Reserva TEXT(50), "
    "DataReserva TEXT(50), Responsavel TEXT(50))",
]
_SQLITE_DDL = [
    "CREATE TABLE tblChapas (COD REAL, MM TEXT, MDF TEXT, Ativo INTEGER)",
    "CREATE TABLE tblRetalhos (id INTEGER PRIMARY KEY AUTOINCREMENT, Setor TEXT, "
    "Cod_Material REAL, Largura REAL, Altura REAL, DataEntrada TIMESTAMP, Reserva TEXT, "
    "DataReserva TEXT, Responsavel TEXT)",
]
_CHAPAS = [(10, "15", "BRANCO TX", True), (20, "18", "LORD SETHOS (ARAUCO)", True),
           (30, "6", "GRAFITO CHESS", False)]


def _create_db(kind: str, tmp: Path) -> Path:
    if kind == "sqlite":
        path = tmp / "retalhos.db"
        conn = sqlite3.connect(path)
        ddl = _SQLITE_DDL
    else:
        import pyodbc
        path = tmp / "retalhos.accdb"
        shutil.copy(ACCESS_TEMPLATE, path)
        conn = pyodbc.connect(f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};")
        ddl = _ACCESS_DDL
    cur = conn.cursor()
    for sql in ddl:
        cur.execute(sql)
    cur.executemany("INSERT INTO tblChapas (COD, MM, MDF, Ativo) VALUES (?, ?, ?, ?)", _CHAPAS)
    conn.commit()
    conn.close()
    return path


_KINDS = ["sqlite"] + (["access"] if ACCESS_TEMPLATE else [])


@pytest.fixture(params=_KINDS)
def settings(request, tmp_path: Path) -> Settings:
    db = _create_db(request.param, tmp_path)
    cc = tmp_path / "corte_certo"
    for sub in ("CHP", "PED"):
        (cc / sub).mkdir(parents=True)
    (cc / "Corte.exe").write_bytes(b"")
    (tmp_path / "lotes").mkdir()

    s = Settings(
        database_path=str(db), corte_certo_dir=str(cc) + os.sep, ret_subdir="CHP\\",
        ped_subdir="PED\\", projects_dir=str(tmp_path / "lotes"),
        sheets_dir=str(tmp_path / "sheets"),
    )
    s.path = tmp_path / "Settings.json"
    s.usuario = Usuario(1, "TESTE", "TESTE", admin=True)  # sessão logada (responsável = TESTE)
    # o banco de teste nasce com a estrutura antiga (como a produção): migra como o app faz ao abrir
    from retalhos.services import EstoqueService
    EstoqueService(s).preparar_banco(pasta_backup=tmp_path / "backups")
    return s
