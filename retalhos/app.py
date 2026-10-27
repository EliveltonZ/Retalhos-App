"""Inicialização do aplicativo principal."""
from __future__ import annotations

import logging
import sys
import traceback

from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .config import Settings
from .paths import data_dir
from .ui.theme import THEME_LIGHT, apply_theme
from .ui.widgets import app_icon, error

log = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        filename=data_dir() / "retalhos.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def install_excepthook() -> None:
    """Sem console (``--noconsole``), erros não tratados seriam silenciosos: mostra e registra."""

    def hook(exc_type, exc, tb):
        log.critical("Erro não tratado", exc_info=(exc_type, exc, tb))
        error(None, APP_NAME, f"Erro inesperado:\n{exc}", "".join(traceback.format_exception(exc_type, exc, tb)))

    sys.excepthook = hook


def create_app(theme: str = THEME_LIGHT) -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(app_icon())
    apply_theme(app, theme)
    return app  # type: ignore[return-value]


def entrar(settings: Settings):
    """Prepara a tabela de usuários, cria o 1º administrador se preciso e faz o login.

    Retorna o usuário logado ou ``None`` se a pessoa desistir.
    """
    from .services import EstoqueService, UsuarioService
    from .ui.dialogs import ConfigDialog, LoginDialog, PrimeiroAdminDialog
    from .ui.widgets import show_exception

    while True:
        usuarios = UsuarioService(settings)
        try:
            usuarios.preparar_tabela()  # cria tblUsuarios na primeira vez
            EstoqueService(settings).preparar_banco()  # colunas da baixa registrada (com backup antes)
            tem_usuario = usuarios.existe_usuario()
            break
        except Exception as exc:  # noqa: BLE001 - banco fora da rede / caminho errado
            show_exception(None, "Banco de dados", exc)
            if not ConfigDialog(settings).exec():  # deixa corrigir o caminho do banco
                return None

    if not tem_usuario:
        primeiro = PrimeiroAdminDialog(usuarios)
        if not primeiro.exec():
            return None
        settings.last_login = primeiro.usuario.login if primeiro.usuario else ""

    login = LoginDialog(usuarios, settings)
    return login.usuario if login.exec() else None


def run() -> int:
    setup_logging()
    settings = Settings.load()
    app = create_app(settings.theme)
    install_excepthook()

    from .ui.dialogs import ConfigDialog
    from .ui.main_window import MainWindow

    if not settings.exists:
        # primeira execução: cria o Settings.json a partir da tela de configurações
        if not ConfigDialog(settings).exec():
            return 0

    usuario = entrar(settings)
    if usuario is None:
        return 0
    settings.usuario = usuario
    window = MainWindow(settings)
    window.showMaximized()
    return app.exec()
