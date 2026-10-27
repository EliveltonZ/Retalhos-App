"""Colunas e cores compartilhadas pelas tabelas de retalhos."""
from __future__ import annotations

from PySide6.QtGui import QColor

from ..config import Settings
from ..models import Retalho
from .theme import ROW_FULL_SHEET, ROW_INACTIVE, ROW_RESERVED
from .widgets import ALIGN_LEFT, Column


def retalho_columns(extended: bool = True) -> list[Column[Retalho]]:
    cols = [
        Column("ID", lambda r: r.id, width=60),
        Column("Setor", lambda r: r.setor, width=70),
        Column("Cód.", lambda r: r.codigo, width=60),
        Column("Esp.", lambda r: r.espessura, width=50),
        Column("Material", lambda r: r.descricao, ALIGN_LEFT, stretch=True),
        Column("Largura", lambda r: r.largura, width=75),
        Column("x", lambda r: "x", width=28),  # separador visual: "Largura x Altura"
        Column("Altura", lambda r: r.altura, width=75),
        Column("Entrada", lambda r: r.data_entrada, width=125),
        Column("Reserva", lambda r: r.reserva, width=80),
    ]
    if extended:
        cols += [
            Column("Data reserva", lambda r: r.data_reserva, width=145),
            Column("Reservado por", lambda r: r.reservado_por, width=110),
            Column("Responsável", lambda r: r.responsavel, width=110),
        ]
    return cols


def retalho_row_color(settings: Settings):
    """Prioridade (igual à versão anterior): material inativo > chapa inteira > reservado."""

    def color(r: Retalho) -> QColor | None:
        if not r.material_ativo:
            return ROW_INACTIVE
        if r.chapa_inteira(settings.max_width, settings.max_height):
            return ROW_FULL_SHEET
        if r.reservado:
            return ROW_RESERVED
        return None

    return color
