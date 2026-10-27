"""Acesso às tabelas ``tblChapas`` e ``tblRetalhos``. Todo SQL é parametrizado."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any

from ..models import Chapa, Movimento, Retalho, RetalhoRemovido, Usuario, fmt_number, to_datetime, to_int, to_text
from .database import Session

# Limite de parâmetros por cláusula IN (o Access tem limite de tamanho de SQL)
_CHUNK = 200


def _chunks(values: Sequence[Any], size: int = _CHUNK) -> Iterable[Sequence[Any]]:
    for start in range(0, len(values), size):
        yield values[start:start + size]


def _placeholders(count: int) -> str:
    return ", ".join("?" * count)


class ChapaRepository:
    _SELECT = "SELECT COD, MM, MDF, Ativo FROM tblChapas"

    def __init__(self, session: Session) -> None:
        self.s = session

    @staticmethod
    def _to_model(row: tuple) -> Chapa:
        return Chapa(
            codigo=to_int(row[0]),
            espessura=fmt_number(row[1]),
            descricao=to_text(row[2]),
            ativo=True if row[3] is None else bool(row[3]),
        )

    def listar(self) -> list[Chapa]:
        rows = self.s.query(f"{self._SELECT} ORDER BY MDF, COD")
        return [self._to_model(r) for r in rows]

    def buscar(self, codigo: int) -> Chapa | None:
        row = self.s.query_one(f"{self._SELECT} WHERE COD = ?", (codigo,))
        return self._to_model(row) if row else None

    def buscar_varios(self, codigos: Iterable[int]) -> dict[int, Chapa]:
        unicos = sorted(set(codigos))
        result: dict[int, Chapa] = {}
        for parte in _chunks(unicos):
            rows = self.s.query(f"{self._SELECT} WHERE COD IN ({_placeholders(len(parte))})", parte)
            for row in rows:
                chapa = self._to_model(row)
                result[chapa.codigo] = chapa
        return result

    def inserir(self, chapa: Chapa) -> None:
        self.s.execute(
            "INSERT INTO tblChapas (COD, MM, MDF, Ativo) VALUES (?, ?, ?, ?)",
            (chapa.codigo, chapa.espessura, chapa.descricao, chapa.ativo),
        )

    def atualizar(self, chapa: Chapa) -> None:
        self.s.execute(
            "UPDATE tblChapas SET MM = ?, MDF = ?, Ativo = ? WHERE COD = ?",
            (chapa.espessura, chapa.descricao, chapa.ativo, chapa.codigo),
        )


class RetalhoRepository:
    _CAMPOS = (
        "tblRetalhos.id, tblRetalhos.Setor, tblRetalhos.Cod_Material, tblChapas.MM, "
        "tblChapas.MDF, tblRetalhos.Largura, tblRetalhos.Altura, tblRetalhos.DataEntrada, "
        "tblRetalhos.Reserva, tblRetalhos.DataReserva, tblRetalhos.Responsavel, tblChapas.Ativo, "
        "tblRetalhos.ResponsavelReserva"
    )
    _FROM = " FROM tblChapas INNER JOIN tblRetalhos ON tblChapas.COD = tblRetalhos.Cod_Material"
    _SELECT = f"SELECT {_CAMPOS}{_FROM}"
    _SELECT_REMOVIDOS = (f"SELECT {_CAMPOS}, tblRetalhos.DataBaixa, tblRetalhos.ResponsavelBaixa, "
                         f"tblRetalhos.DataExclusao, tblRetalhos.ResponsavelExclusao{_FROM}")
    _ORDER = " ORDER BY tblChapas.MDF, tblRetalhos.Cod_Material, tblRetalhos.id"

    def __init__(self, session: Session) -> None:
        self.s = session

    @staticmethod
    def _to_model(row: tuple) -> Retalho:
        return Retalho(
            id=to_int(row[0]),
            setor=to_text(row[1]),
            codigo=to_int(row[2]),
            espessura=fmt_number(row[3]),
            descricao=to_text(row[4]),
            largura=float(row[5] or 0),
            altura=float(row[6] or 0),
            data_entrada=to_datetime(row[7]),
            reserva=to_text(row[8]),
            data_reserva=to_text(row[9]),
            responsavel=to_text(row[10]),
            material_ativo=True if row[11] is None else bool(row[11]),
            reservado_por=to_text(row[12]),
        )

    # Controles acrescentados à tabela (só colunas novas e vazias; nada existente é alterado):
    # quem reservou; baixa por consumo e exclusão registradas (o retalho some do sistema, mas fica no banco)
    _COLUNAS_NOVAS = {
        "ResponsavelReserva": {"access": "TEXT(60)", "sqlite": "TEXT"},
        "DataBaixa": {"access": "DATETIME", "sqlite": "TIMESTAMP"},
        "ResponsavelBaixa": {"access": "TEXT(60)", "sqlite": "TEXT"},
        "DataExclusao": {"access": "DATETIME", "sqlite": "TIMESTAMP"},
        "ResponsavelExclusao": {"access": "TEXT(60)", "sqlite": "TEXT"},
    }
    # retalho "existe" no sistema enquanto não recebeu baixa nem foi excluído
    _ATIVO = "tblRetalhos.DataBaixa IS NULL AND tblRetalhos.DataExclusao IS NULL"
    _REMOVIDO = "(tblRetalhos.DataBaixa IS NOT NULL OR tblRetalhos.DataExclusao IS NOT NULL)"

    def colunas_faltando(self) -> list[str]:
        existentes = self.s.colunas("tblRetalhos")
        return [c for c in self._COLUNAS_NOVAS if c.lower() not in existentes]

    def precisa_migrar(self) -> bool:
        return bool(self.colunas_faltando())

    def migrar(self) -> None:
        for coluna in self.colunas_faltando():
            tipo = self._COLUNAS_NOVAS[coluna][self.s.dialect]
            self.s.execute(f"ALTER TABLE tblRetalhos ADD COLUMN {coluna} {tipo}")

    def _listar(self, where: str = "", params: Sequence[Any] = ()) -> list[Retalho]:
        filtro = f"{self._ATIVO} AND ({where})" if where else self._ATIVO
        sql = f"{self._SELECT} WHERE {filtro}{self._ORDER}"
        return [self._to_model(r) for r in self.s.query(sql, params)]

    def listar(self) -> list[Retalho]:
        return self._listar()

    def listar_disponiveis(self) -> list[Retalho]:
        return self._listar("(tblRetalhos.Reserva IS NULL OR tblRetalhos.Reserva = '')")

    def buscar(self, retalho_id: int) -> Retalho | None:
        encontrados = self._listar("tblRetalhos.id = ?", (retalho_id,))
        return encontrados[0] if encontrados else None

    def listar_por_reserva(self, projeto: str) -> list[Retalho]:
        return self._listar("tblRetalhos.Reserva = ?", (projeto,))

    def listar_por_materiais(self, codigos: Iterable[int]) -> list[Retalho]:
        unicos = sorted(set(codigos))
        result: list[Retalho] = []
        for parte in _chunks(unicos):
            result += self._listar(
                f"tblRetalhos.Cod_Material IN ({_placeholders(len(parte))})", parte
            )
        result.sort(key=lambda r: (r.descricao, r.codigo, r.id))
        return result

    def inserir(
        self,
        *,
        codigo: int,
        largura: float,
        altura: float,
        data_entrada: datetime,
        responsavel: str,
        setor: str | None = None,
        reserva: str | None = None,
        data_reserva: str | None = None,
    ) -> int:
        colunas = ["Cod_Material", "Largura", "Altura", "DataEntrada", "Responsavel"]
        valores: list[Any] = [codigo, largura, altura, data_entrada, responsavel]
        opcionais = [("Setor", setor), ("Reserva", reserva), ("DataReserva", data_reserva),
                     ("ResponsavelReserva", responsavel if reserva else None)]  # sobra já nasce reservada
        for coluna, valor in opcionais:
            if valor:
                colunas.append(coluna)
                valores.append(valor)
        self.s.execute(
            f"INSERT INTO tblRetalhos ({', '.join(colunas)}) VALUES ({_placeholders(len(colunas))})",
            valores,
        )
        return self.s.last_insert_id()

    def excluir(self, retalho_id: int, quando: datetime, responsavel: str) -> None:
        """Exclusão registrada: grava data/hora e quem excluiu; o retalho some do sistema (não é apagado)."""
        self.s.execute(
            "UPDATE tblRetalhos SET DataExclusao = ?, ResponsavelExclusao = ? "
            "WHERE id = ? AND DataExclusao IS NULL",
            (quando, responsavel, retalho_id),
        )

    def dar_baixa(self, retalho_id: int, quando: datetime, responsavel: str) -> None:
        """Baixa por consumo: registra data/hora e responsável; o retalho deixa de aparecer no sistema."""
        self.s.execute(
            "UPDATE tblRetalhos SET DataBaixa = ?, ResponsavelBaixa = ? WHERE id = ? AND DataBaixa IS NULL",
            (quando, responsavel, retalho_id),
        )

    def reservar(self, retalho_id: int, projeto: str, data_reserva: str, responsavel: str) -> None:
        self.s.execute(
            "UPDATE tblRetalhos SET Reserva = ?, DataReserva = ?, ResponsavelReserva = ? WHERE id = ?",
            (projeto, data_reserva, responsavel, retalho_id),
        )

    def cancelar_reserva(self, retalho_id: int) -> None:
        """Limpa a reserva (o histórico guarda quem tinha reservado); lançamento não é alterado."""
        self.s.execute(
            "UPDATE tblRetalhos SET Reserva = '', DataReserva = '', ResponsavelReserva = '' WHERE id = ?",
            (retalho_id,),
        )

    # ------------------------------------------------- removidos (baixa/exclusão)
    def _removido(self, row: tuple) -> RetalhoRemovido:
        n = len(self._CAMPOS.split(","))
        data_baixa, resp_baixa, data_exclusao, resp_exclusao = row[n:n + 4]
        if data_baixa is not None:
            return RetalhoRemovido(self._to_model(row), "Baixa", to_datetime(data_baixa), to_text(resp_baixa))
        return RetalhoRemovido(self._to_model(row), "Exclusão", to_datetime(data_exclusao), to_text(resp_exclusao))

    def contar_removidos_por_material(self) -> dict[int, int]:
        rows = self.s.query(
            f"SELECT tblRetalhos.Cod_Material, COUNT(*){self._FROM} WHERE {self._REMOVIDO} "
            "GROUP BY tblRetalhos.Cod_Material"
        )
        return {to_int(r[0]): to_int(r[1]) for r in rows}

    def listar_removidos(self, codigo: int) -> list[RetalhoRemovido]:
        """Removidos de um material, do mais recente para o mais antigo."""
        rows = self.s.query(
            f"{self._SELECT_REMOVIDOS} WHERE {self._REMOVIDO} AND tblRetalhos.Cod_Material = ?", (codigo,)
        )
        result = [self._removido(r) for r in rows]
        result.sort(key=lambda x: (x.data or datetime.min, x.retalho.id), reverse=True)
        return result

    def buscar_removido(self, retalho_id: int) -> RetalhoRemovido | None:
        row = self.s.query_one(f"{self._SELECT_REMOVIDOS} WHERE {self._REMOVIDO} AND tblRetalhos.id = ?",
                               (retalho_id,))
        return self._removido(row) if row else None

    def restaurar(self, retalho_id: int) -> None:
        """Volta ao estoque como disponível: limpa baixa, exclusão e reserva (o histórico guarda tudo)."""
        self.s.execute(
            "UPDATE tblRetalhos SET DataBaixa = NULL, ResponsavelBaixa = NULL, DataExclusao = NULL, "
            "ResponsavelExclusao = NULL, Reserva = '', DataReserva = '', ResponsavelReserva = '' WHERE id = ?",
            (retalho_id,),
        )


class HistoricoRepository:
    """``tblHistorico``: uma linha por ação em um retalho (quem, quando, o quê)."""

    TABELA = "tblHistorico"
    _DDL = {
        "access": [
            "CREATE TABLE tblHistorico (id COUNTER PRIMARY KEY, RetalhoId LONG, Acao TEXT(20), "
            "DataHora DATETIME, Usuario TEXT(60), Detalhe TEXT(255))",
            "CREATE INDEX ix_historico_retalho ON tblHistorico (RetalhoId)",
        ],
        "sqlite": [
            "CREATE TABLE tblHistorico (id INTEGER PRIMARY KEY AUTOINCREMENT, RetalhoId INTEGER, Acao TEXT, "
            "DataHora TIMESTAMP, Usuario TEXT, Detalhe TEXT)",
            "CREATE INDEX ix_historico_retalho ON tblHistorico (RetalhoId)",
        ],
    }

    def __init__(self, session: Session) -> None:
        self.s = session

    def precisa_criar(self) -> bool:
        return not self.s.tabela_existe(self.TABELA)

    def garantir_tabela(self) -> bool:
        if not self.precisa_criar():
            return False
        for sql in self._DDL[self.s.dialect]:
            self.s.execute(sql)
        return True

    def registrar(self, retalho_id: int, acao: str, quando: datetime, usuario: str, detalhe: str = "") -> None:
        self.s.execute(
            "INSERT INTO tblHistorico (RetalhoId, Acao, DataHora, Usuario, Detalhe) VALUES (?, ?, ?, ?, ?)",
            (retalho_id, acao, quando, usuario, detalhe[:255]),
        )

    def listar(self, retalho_id: int) -> list[Movimento]:
        rows = self.s.query(
            "SELECT DataHora, Acao, Usuario, Detalhe FROM tblHistorico WHERE RetalhoId = ? ORDER BY DataHora, id",
            (retalho_id,),
        )
        return [Movimento(to_datetime(r[0]), to_text(r[1]), to_text(r[2]), to_text(r[3])) for r in rows]


class UsuarioRepository:
    """``tblUsuarios``: login, permissões e hash da senha (nunca a senha em texto)."""

    TABELA = "tblUsuarios"
    _DDL = {
        "access": [
            "CREATE TABLE tblUsuarios (id COUNTER PRIMARY KEY, Login TEXT(30) NOT NULL, Nome TEXT(60), "
            "SenhaHash TEXT(200) NOT NULL, Admin BIT, PCP BIT, RemoverReserva BIT, ReservarManual BIT, "
            "Ativo BIT, TrocarSenha BIT, CriadoEm DATETIME, UltimoAcesso DATETIME)",
            "CREATE UNIQUE INDEX ux_usuarios_login ON tblUsuarios (Login)",
        ],
        "sqlite": [
            "CREATE TABLE tblUsuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, Login TEXT NOT NULL, Nome TEXT, "
            "SenhaHash TEXT NOT NULL, Admin INTEGER, PCP INTEGER, RemoverReserva INTEGER, ReservarManual INTEGER, "
            "Ativo INTEGER, TrocarSenha INTEGER, CriadoEm TIMESTAMP, UltimoAcesso TIMESTAMP)",
            "CREATE UNIQUE INDEX ux_usuarios_login ON tblUsuarios (Login)",
        ],
    }
    _SELECT = ("SELECT id, Login, Nome, Admin, PCP, RemoverReserva, ReservarManual, Ativo, TrocarSenha, "
               "UltimoAcesso FROM tblUsuarios")

    def __init__(self, session: Session) -> None:
        self.s = session

    def garantir_tabela(self) -> bool:
        """Cria a tabela se ainda não existir. Retorna ``True`` se criou."""
        if self.s.tabela_existe(self.TABELA):
            return False
        for sql in self._DDL[self.s.dialect]:
            self.s.execute(sql)
        return True

    @staticmethod
    def _to_model(row: tuple) -> Usuario:
        return Usuario(
            id=to_int(row[0]), login=to_text(row[1]), nome=to_text(row[2]),
            admin=bool(row[3]), pcp=bool(row[4]), remover_reserva=bool(row[5]), reservar_manual=bool(row[6]),
            ativo=bool(row[7]), trocar_senha=bool(row[8]), ultimo_acesso=to_datetime(row[9]),
        )

    def contar(self) -> int:
        row = self.s.query_one("SELECT COUNT(*) FROM tblUsuarios")
        return int(row[0]) if row else 0

    def contar_admins_ativos(self) -> int:
        row = self.s.query_one("SELECT COUNT(*) FROM tblUsuarios WHERE Admin = ? AND Ativo = ?", (True, True))
        return int(row[0]) if row else 0

    def listar(self) -> list[Usuario]:
        return [self._to_model(r) for r in self.s.query(f"{self._SELECT} ORDER BY Login")]

    def buscar(self, login: str) -> Usuario | None:
        row = self.s.query_one(f"{self._SELECT} WHERE Login = ?", (login,))
        return self._to_model(row) if row else None

    def hash_da_senha(self, login: str) -> str | None:
        row = self.s.query_one("SELECT SenhaHash FROM tblUsuarios WHERE Login = ?", (login,))
        return to_text(row[0]) if row else None

    def inserir(self, u: Usuario, senha_hash: str, criado_em: datetime) -> int:
        self.s.execute(
            "INSERT INTO tblUsuarios (Login, Nome, SenhaHash, Admin, PCP, RemoverReserva, ReservarManual, "
            "Ativo, TrocarSenha, CriadoEm) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (u.login, u.nome, senha_hash, u.admin, u.pcp, u.remover_reserva, u.reservar_manual, u.ativo,
             u.trocar_senha, criado_em),
        )
        return self.s.last_insert_id()

    def atualizar(self, u: Usuario) -> None:
        self.s.execute(
            "UPDATE tblUsuarios SET Nome = ?, Admin = ?, PCP = ?, RemoverReserva = ?, ReservarManual = ?, "
            "Ativo = ? WHERE id = ?",
            (u.nome, u.admin, u.pcp, u.remover_reserva, u.reservar_manual, u.ativo, u.id),
        )

    def definir_senha(self, usuario_id: int, senha_hash: str, trocar_senha: bool) -> None:
        self.s.execute("UPDATE tblUsuarios SET SenhaHash = ?, TrocarSenha = ? WHERE id = ?",
                       (senha_hash, trocar_senha, usuario_id))

    def registrar_acesso(self, usuario_id: int, quando: datetime) -> None:
        self.s.execute("UPDATE tblUsuarios SET UltimoAcesso = ? WHERE id = ?", (quando, usuario_id))
