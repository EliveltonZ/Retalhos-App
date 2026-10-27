"""Atualização do sistema a partir do pacote ``Retalhos.zip`` na rede."""
from __future__ import annotations

import shutil
import zipfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from ..config import DATE_FORMAT, Settings

UPDATER_EXE = "Update.exe"
APP_EXE = "Retalhos.exe"


def data_modificacao(arquivo: str | Path) -> datetime:
    return datetime.fromtimestamp(Path(arquivo).stat().st_mtime).replace(microsecond=0)


def ha_atualizacao(settings: Settings) -> bool:
    """O pacote na rede é mais novo que a última atualização instalada?"""
    pacote = Path(settings.update_zip)
    if not pacote.is_file():
        return False
    try:
        ultima = datetime.strptime(settings.last_update, DATE_FORMAT)
    except ValueError:
        return True
    return data_modificacao(pacote) > ultima


def encerrar_processos(nome: str) -> int:
    """Encerra todos os processos com o nome informado. Retorna quantos foram encerrados."""
    import psutil  # import tardio: só o atualizador precisa

    alvo = nome.lower()
    encerrados = []
    for proc in psutil.process_iter(["name"]):
        if (proc.info.get("name") or "").lower() == alvo:
            try:
                proc.terminate()
                encerrados.append(proc)
            except psutil.Error:
                pass
    psutil.wait_procs(encerrados, timeout=5)
    return len(encerrados)


def extrair_pacote(
    pacote: str | Path,
    destino: str | Path,
    progresso: Callable[[int, int], None] | None = None,
    ignorar: set[str] | None = None,
) -> list[str]:
    """Extrai o pacote arquivo a arquivo. Retorna a lista de arquivos que não puderam ser gravados."""
    ignorar = {n.lower() for n in (ignorar or set())}
    falhas: list[str] = []
    with zipfile.ZipFile(pacote) as zf:
        membros = zf.infolist()
        for i, membro in enumerate(membros, start=1):
            if Path(membro.filename).name.lower() not in ignorar:
                try:
                    zf.extract(membro, destino)
                except OSError:
                    falhas.append(membro.filename)
            if progresso:
                progresso(i, len(membros))
    return falhas


def registrar_atualizacao(settings: Settings) -> None:
    settings.last_update = data_modificacao(settings.update_zip).strftime(DATE_FORMAT)
    settings.save()


def atualizar_atualizador(settings: Settings, destino: Path) -> Path:
    """Copia o ``Update.exe`` que está na mesma pasta do pacote para ``destino``."""
    origem = Path(settings.update_zip).parent / UPDATER_EXE
    if not origem.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado:\n{origem}")
    alvo = destino / UPDATER_EXE
    shutil.copy2(origem, alvo)
    return alvo
