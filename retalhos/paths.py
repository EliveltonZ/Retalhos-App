"""Resolução de caminhos que funciona tanto no código-fonte quanto no executável (PyInstaller)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Pasta do executável quando empacotado, ou raiz do projeto em desenvolvimento."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return _PACKAGE_DIR.parent


def resource_path(name: str) -> Path:
    """Caminho de um arquivo dentro de ``retalhos/resources``."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "retalhos" / "resources" / name  # type: ignore[attr-defined]
    return _PACKAGE_DIR / "resources" / name


def data_dir() -> Path:
    """Pasta gravável para logs (``%LOCALAPPDATA%\\Retalhos``)."""
    base = os.getenv("LOCALAPPDATA")
    path = Path(base) / "Retalhos" if base else app_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path
