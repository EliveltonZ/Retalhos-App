"""Leitura de códigos de barras de retalho e de planos de corte ``.cutplanning``."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..models import Sobra

BARCODE_LENGTH = 21
_FIELD_TAG = "com.geeksystem.cutplanning.cutplan.material.program.cut.data.field"
_BARCODE_FIELD = "160"


def ler_codigo_barras(texto: str) -> Sobra:
    """Decodifica a etiqueta de 21 caracteres: ``[0:7]`` código, ``[8:14]`` largura, ``[14:21]`` altura."""
    texto = texto.strip()
    if len(texto) != BARCODE_LENGTH:
        raise ValueError(f"Código de barras deve ter {BARCODE_LENGTH} caracteres.")
    try:
        return Sobra(codigo=int(texto[:7]), largura=float(texto[8:14]), altura=float(texto[14:21]))
    except ValueError as exc:
        raise ValueError("Código de barras inválido.") from exc


def ler_plano_de_corte(arquivo: str | Path) -> list[Sobra]:
    """Sobras (etiquetas de 21 caracteres) de um arquivo ``.cutplanning`` do Corte Certo."""
    sobras: list[Sobra] = []
    for _, elem in ET.iterparse(str(arquivo), events=("end",)):
        if elem.tag == _FIELD_TAG and elem.get("name") == _BARCODE_FIELD:
            valor = elem.get("value") or ""
            if len(valor) == BARCODE_LENGTH:
                try:
                    sobras.append(ler_codigo_barras(valor))
                except ValueError:
                    pass
        elem.clear()
    return sobras
