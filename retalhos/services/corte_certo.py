"""Arquivos de integração com o Corte Certo Plus.

``RETxxxxx.TAB`` (um por material) - estoque de retalhos que o Corte Certo pode usar.
Cada linha é CSV separado por vírgula::

    <id>,+,1,<largura>,<altura>,<reserva ou espaço>,<id>,

A coluna 6 (id) identifica a linha para remoção.

``PEDxxxxx.TAB`` (um por projeto) - peças do pedido, separadas por espaço;
a coluna 5 contém o código do material.
"""
from __future__ import annotations

import csv
import io
import os
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from ..config import Settings
from ..models import Retalho, to_int

_ENCODING = "latin-1"
_ID_COLUMN = 6
_PED_MATERIAL_COLUMN = 5


class CorteCertoError(Exception):
    """Pasta ou arquivo do Corte Certo indisponível."""


class PedidoNaoEncontrado(CorteCertoError):
    pass


def nome_arquivo(valor: int | str, prefixo: str = "RET", extensao: str = ".TAB") -> str:
    """``nome_arquivo(123)`` -> ``RET00123.TAB``; ``nome_arquivo('1206', 'PED')`` -> ``PED01206.TAB``."""
    return f"{prefixo}{str(valor).strip().zfill(5)}{extensao}"


def _fmt_medida(valor: float) -> str:
    return str(float(valor))


def linha_retalho(retalho_id: int, largura: float, altura: float, reserva: str = "") -> list[str]:
    rid = str(retalho_id)
    return [rid, "+", "1", _fmt_medida(largura), _fmt_medida(altura), reserva or " ", rid, ""]


def _mesmo_id(valor: str, retalho_id: int) -> bool:
    try:
        return to_int(valor) == retalho_id
    except (TypeError, ValueError):
        return False


class ArquivosCorteCerto:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ------------------------------------------------------------ verificações
    @property
    def ret_dir(self) -> Path:
        return Path(self.settings.ret_dir)

    @property
    def ped_dir(self) -> Path:
        return Path(self.settings.ped_dir)

    def instalado(self) -> bool:
        return Path(self.settings.corte_certo_exe_path).is_file()

    def garantir_pasta_retalhos(self) -> None:
        """Falha antes de alterar o banco se a pasta de retalhos não estiver acessível."""
        if not self.ret_dir.is_dir():
            raise CorteCertoError(
                f"Pasta de retalhos do Corte Certo não encontrada:\n{self.ret_dir}\n\n"
                "Verifique a conexão de rede e as Configurações."
            )

    # ---------------------------------------------------------- arquivos RET
    def arquivo_retalho(self, codigo: int) -> Path:
        return self.ret_dir / nome_arquivo(codigo)

    def adicionar(self, codigo: int, retalho_id: int, largura: float, altura: float,
                  reserva: str = "") -> None:
        """Acrescenta o retalho ao arquivo do material, sem duplicar o id."""
        self.remover(codigo, retalho_id)
        with open(self.arquivo_retalho(codigo), "a", newline="", encoding=_ENCODING) as fp:
            csv.writer(fp).writerow(linha_retalho(retalho_id, largura, altura, reserva))

    def remover(self, codigo: int, retalho_id: int) -> bool:
        """Remove a linha do retalho. Retorna ``True`` se algo foi removido."""
        arquivo = self.arquivo_retalho(codigo)
        if not arquivo.is_file():
            return False
        with open(arquivo, "r", newline="", encoding=_ENCODING) as fp:
            linhas = list(csv.reader(fp))
        mantidas = [
            linha for linha in linhas
            if not (len(linha) > _ID_COLUMN and _mesmo_id(linha[_ID_COLUMN], retalho_id))
        ]
        if len(mantidas) == len(linhas):
            return False
        self._gravar(arquivo, mantidas)
        return True

    def recriar(self, retalhos: Iterable[Retalho]) -> int:
        """Apaga todos os ``RET*`` e recria a partir dos retalhos informados."""
        self.garantir_pasta_retalhos()
        for arquivo in self.ret_dir.iterdir():
            if arquivo.is_file() and arquivo.name.upper().startswith("RET"):
                arquivo.unlink()

        por_material: dict[int, list[list[str]]] = defaultdict(list)
        for r in retalhos:
            por_material[r.codigo].append(linha_retalho(r.id, r.largura, r.altura))
        for codigo, linhas in por_material.items():
            self._gravar(self.arquivo_retalho(codigo), linhas)
        return len(por_material)

    @staticmethod
    def _gravar(arquivo: Path, linhas: list[list[str]]) -> None:
        tmp = arquivo.with_name(arquivo.name + ".tmp")
        with open(tmp, "w", newline="", encoding=_ENCODING) as fp:
            csv.writer(fp).writerows(linhas)
        os.replace(tmp, arquivo)

    # ---------------------------------------------------------- arquivos PED
    def codigos_do_pedido(self, projeto: str) -> list[int]:
        """Códigos de material usados no pedido do projeto (sem alterar o arquivo)."""
        arquivo = self.ped_dir / nome_arquivo(projeto, prefixo="PED")
        if not arquivo.is_file():
            raise PedidoNaoEncontrado(f"Pedido do projeto {projeto} não encontrado:\n{arquivo}")

        conteudo = arquivo.read_text(encoding=_ENCODING)
        # mesma normalização da versão anterior: reduz espaços duplos
        for _ in range(3):
            conteudo = conteudo.replace("  ", " ")

        codigos: list[int] = []
        for linha in csv.reader(io.StringIO(conteudo), delimiter=" "):
            if len(linha) <= _PED_MATERIAL_COLUMN:
                continue
            try:
                codigo = to_int(linha[_PED_MATERIAL_COLUMN])
            except ValueError:
                continue
            if codigo not in codigos:
                codigos.append(codigo)
        return codigos
