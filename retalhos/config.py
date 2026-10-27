"""Leitura e gravação do ``Settings.json``.

As chaves do JSON são mantidas iguais às da versão anterior para que os arquivos
de configuração já distribuídos continuem funcionando.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from .models import Usuario
from .paths import app_dir

SETTINGS_FILE = "Settings.json"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

# atributo -> chave no JSON
_KEYS: dict[str, str] = {
    "database_path": "Directory_data_base",
    "corte_certo_dir": "Directory_cc",
    "ret_subdir": "ret",
    "mat_subdir": "mat",
    "ped_subdir": "ped",
    "corte_certo_exe": "Corte_certo",
    # "User", "Menu", "Remover" e "ReservarManual" não são mais usados: usuário e permissões vêm do login
    "last_login": "UltimoLogin",
    "database_password": "Password",
    "max_width": "Largura",
    "max_height": "Altura",
    "min_width": "Largura_min",
    "min_height": "Altura_min",
    "update_zip": "local_zip",
    "projects_dir": "Projeto gerado",
    "sheets_dir": "Sheet_proj",
    "last_update": "ultima_att",
    "theme": "Tema",
    "conf_folha_lote": "ConFolhaLote",
    "auto_refresh_minutes": "AtualizarMinutos",
}

_FLAG_ON = "Ativado"
_FLAG_OFF = "Desativado"


def find_settings_file() -> Path:
    """Procura o ``Settings.json`` ao lado do executável e, depois, na pasta atual."""
    candidates = [app_dir() / SETTINGS_FILE, Path.cwd() / SETTINGS_FILE]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


@dataclass
class Settings:
    database_path: str = ""
    corte_certo_dir: str = ""
    ret_subdir: str = "CHP\\"
    mat_subdir: str = "MAT\\"
    ped_subdir: str = "PED\\"
    corte_certo_exe: str = "Corte.exe"
    last_login: str = ""  # último usuário que entrou nesta máquina (vem preenchido no login)
    database_password: str = ""
    max_width: float = 2740.0
    max_height: float = 1840.0
    min_width: float = 350.0
    min_height: float = 350.0
    update_zip: str = ""
    projects_dir: str = ""
    sheets_dir: str = ""
    last_update: str = ""
    theme: str = "Claro"  # Claro | Escuro | Automático
    conf_folha_lote: str = "\\\\GDD02\\sistema\\ConFolhaLote.xlsx"  # projetos do lote (capa)
    auto_refresh_minutes: float = 3.0  # atualização automática da lista principal; 0 desliga

    path: Path | None = field(default=None, repr=False, compare=False)
    _raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)
    # usuário logado nesta sessão (só em memória; nunca gravado no Settings.json)
    usuario: Usuario | None = field(default=None, repr=False, compare=False)

    # ------------------------------------------------ usuário e permissões
    @property
    def user(self) -> str:
        """Responsável gravado nos lançamentos: o nome do usuário logado."""
        return self.usuario.exibicao if self.usuario else ""

    @property
    def is_admin(self) -> bool:
        return bool(self.usuario and self.usuario.admin)

    @property
    def menu_pcp_enabled(self) -> bool:
        return bool(self.usuario and self.usuario.pode_pcp)

    @property
    def allow_remove_reserve(self) -> bool:
        return bool(self.usuario and self.usuario.pode_remover_reserva)

    @property
    def allow_manual_reserve(self) -> bool:
        return bool(self.usuario and self.usuario.pode_reservar_manual)

    # ------------------------------------------------------------------ I/O
    @classmethod
    def load(cls, path: Path | str | None = None) -> Settings:
        file = Path(path) if path else find_settings_file()
        raw: dict[str, Any] = {}
        if file.is_file():
            with open(file, "r", encoding="utf-8-sig") as fp:  # aceita UTF-8 com BOM (editado no Bloco de Notas)
                raw = json.load(fp)

        settings = cls(path=file, _raw=raw)
        for attr, key in _KEYS.items():
            if key in raw:
                setattr(settings, attr, settings._convert(attr, raw[key]))
        return settings

    def save(self) -> None:
        if self.path is None:
            self.path = app_dir() / SETTINGS_FILE
        data = dict(self._raw)
        for attr, key in _KEYS.items():
            data[key] = self._serialize(attr, getattr(self, attr))
        tmp = self.path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)
        self._raw = data

    @property
    def exists(self) -> bool:
        return self.path is not None and self.path.is_file()

    # ------------------------------------------------------------ conversão
    def _type_of(self, attr: str) -> Any:
        return next(f.default for f in fields(self) if f.name == attr)

    def _convert(self, attr: str, value: Any) -> Any:
        default = self._type_of(attr)
        if isinstance(default, bool):
            return str(value).strip().lower() == _FLAG_ON.lower()
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        if attr == "database_password":
            # versões antigas gravavam a senha como número
            return "" if value in (None, "", 0) else str(value)
        return "" if value is None else str(value)

    def _serialize(self, attr: str, value: Any) -> Any:
        if isinstance(value, bool):
            return _FLAG_ON if value else _FLAG_OFF
        if isinstance(value, float):
            return int(value) if value.is_integer() else value
        if attr == "database_password" and str(value).isdigit():
            return int(value)
        return value

    # --------------------------------------------------------------- pastas
    @property
    def ret_dir(self) -> str:
        """Pasta dos arquivos de retalho (``RETxxxxx.TAB``)."""
        return os.path.join(self.corte_certo_dir, self.ret_subdir)

    @property
    def ped_dir(self) -> str:
        """Pasta dos arquivos de pedido (``PEDxxxxx.TAB``)."""
        return os.path.join(self.corte_certo_dir, self.ped_subdir)

    @property
    def corte_certo_exe_path(self) -> str:
        return os.path.join(self.corte_certo_dir, self.corte_certo_exe)
