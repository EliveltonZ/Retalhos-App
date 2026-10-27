"""Atualizador (``Update.exe``): baixa o ``Retalhos.zip`` da rede e extrai na pasta do sistema."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QProgressBar, QVBoxLayout, QWidget

from .app import create_app, install_excepthook, setup_logging
from .config import DATE_FORMAT, Settings
from .paths import app_dir
from .services import atualizacao
from .ui.widgets import Worker, app_icon, button, card, label, show_exception


class UpdaterWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.worker: Worker | None = None
        self.setWindowTitle("Atualização — Retalhos")
        self.setWindowIcon(app_icon())
        self.setFixedSize(520, 300)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 18)
        root.addWidget(label("Atualização do sistema", "Title"))
        frame, layout = card()
        self.lb_status = label("")
        self.lb_status.setWordWrap(True)
        layout.addWidget(self.lb_status)
        self.lb_detail = label("", "Muted")
        self.lb_detail.setWordWrap(True)
        layout.addWidget(self.lb_detail)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        layout.addStretch()
        root.addWidget(frame, 1)

        self.bt_update = button("Atualizar", "primary")
        self.bt_update.clicked.connect(self.update_app)
        self.bt_open = button("Abrir Retalhos")
        self.bt_open.clicked.connect(self.open_app)
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self.bt_open)
        footer.addWidget(self.bt_update)
        root.addLayout(footer)
        self.setCentralWidget(central)
        self.check()

    def check(self) -> None:
        pacote = Path(self.settings.update_zip)
        if not pacote.is_file():
            self.lb_status.setText("Pacote de atualização não encontrado.")
            self.lb_detail.setText(str(pacote))
            self.bt_update.setVisible(False)
            return
        data = atualizacao.data_modificacao(pacote).strftime(DATE_FORMAT)
        self.lb_detail.setText(f"Instalada: {self.settings.last_update or '—'}\nDisponível: {data}")
        if atualizacao.ha_atualizacao(self.settings):
            self.lb_status.setText("Há uma nova versão disponível. Deseja atualizar?")
            self.bt_update.setVisible(True)
        else:
            self.lb_status.setText("✔ O sistema já está atualizado.")
            self.bt_update.setVisible(False)

    def update_app(self) -> None:
        settings = self.settings
        own_exe = Path(sys.executable).name if getattr(sys, "frozen", False) else atualizacao.UPDATER_EXE

        def task(progress):
            atualizacao.encerrar_processos(atualizacao.APP_EXE)
            falhas = atualizacao.extrair_pacote(
                settings.update_zip, app_dir(), progress, ignorar={own_exe, "Settings.json"}
            )
            atualizacao.registrar_atualizacao(settings)
            return falhas

        self.bt_update.setEnabled(False)
        self.bt_open.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.lb_status.setText("Atualizando… o Retalhos será fechado.")
        self.worker = Worker(task, self)
        self.worker.progress.connect(lambda i, n: self.progress.setValue(int(i * 100 / max(n, 1))))
        self.worker.succeeded.connect(self._done)
        self.worker.failed.connect(self._failed)
        self.worker.start()

    def _done(self, falhas: list[str]) -> None:
        self.bt_open.setEnabled(True)
        self.bt_update.setVisible(False)
        if falhas:
            self.lb_status.setText(f"Atualização concluída com {len(falhas)} arquivo(s) não substituído(s).")
            self.lb_detail.setText("\n".join(falhas[:5]))
        else:
            self.lb_status.setText("✔ Atualização concluída.")
            self.lb_detail.setText(f"Atualizado em {datetime.now().strftime(DATE_FORMAT)}")

    def _failed(self, exc: Exception) -> None:
        self.bt_update.setEnabled(True)
        self.bt_open.setEnabled(True)
        self.progress.setVisible(False)
        self.lb_status.setText("Falha na atualização.")
        show_exception(self, "Atualização", exc)

    def open_app(self) -> None:
        exe = app_dir() / atualizacao.APP_EXE
        if exe.is_file():
            subprocess.Popen([str(exe)], cwd=str(app_dir()))  # noqa: S603
        self.close()


def run() -> int:
    setup_logging()
    settings = Settings.load()
    app = create_app(settings.theme)
    install_excepthook()
    window = UpdaterWindow(settings)
    window.show()
    return app.exec()
