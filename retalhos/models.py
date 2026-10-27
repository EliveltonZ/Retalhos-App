"""Entidades do domínio."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def fmt_number(value: Any) -> str:
    """``15.0`` -> ``"15"``; ``1124.7`` -> ``"1124.7"``; ``None`` -> ``""``."""
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


def to_int(value: Any) -> int:
    return int(float(value))


def to_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def to_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


@dataclass
class Chapa:
    """Material/cor cadastrado em ``tblChapas``."""

    codigo: int
    espessura: str
    descricao: str
    ativo: bool = True


@dataclass
class Retalho:
    """Retalho em estoque (``tblRetalhos`` + dados do material)."""

    id: int
    setor: str
    codigo: int
    espessura: str
    descricao: str
    largura: float
    altura: float
    data_entrada: datetime | None
    reserva: str
    data_reserva: str
    responsavel: str
    material_ativo: bool = True
    reservado_por: str = ""  # usuário que fez a reserva atual

    @property
    def reservado(self) -> bool:
        return bool(self.reserva)

    def chapa_inteira(self, max_width: float, max_height: float) -> bool:
        return self.largura == max_width and self.altura == max_height


@dataclass(frozen=True)
class Movimento:
    """Uma linha do histórico de um retalho (``tblHistorico``)."""

    data_hora: datetime | None
    acao: str
    usuario: str
    detalhe: str = ""


@dataclass
class RetalhoRemovido:
    """Retalho que saiu do sistema por baixa (consumo) ou exclusão; o registro continua no banco."""

    retalho: Retalho
    motivo: str  # "Baixa" ou "Exclusão"
    data: datetime | None
    responsavel: str

    @property
    def baixa(self) -> bool:
        return self.motivo == "Baixa"


@dataclass
class Usuario:
    """Usuário do sistema (``tblUsuarios``). As permissões valem em qualquer computador."""

    id: int
    login: str
    nome: str
    admin: bool = False
    pcp: bool = False
    remover_reserva: bool = False
    reservar_manual: bool = False
    ativo: bool = True
    trocar_senha: bool = False
    ultimo_acesso: datetime | None = None

    @property
    def exibicao(self) -> str:
        """Nome gravado como Responsável nos lançamentos."""
        return self.nome or self.login

    # administrador pode tudo
    @property
    def pode_pcp(self) -> bool:
        return self.admin or self.pcp

    @property
    def pode_remover_reserva(self) -> bool:
        return self.admin or self.remover_reserva

    @property
    def pode_reservar_manual(self) -> bool:
        return self.admin or self.reservar_manual


@dataclass(frozen=True)
class Sobra:
    """Sobra lida de um plano de corte (código de barras de etiqueta)."""

    codigo: int
    largura: float
    altura: float
