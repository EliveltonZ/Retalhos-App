from __future__ import annotations

from PySide6.QtWidgets import QApplication, QProgressBar, QTextBrowser, QWidget

from ... import __version__
from ...paths import data_dir
from ...services import atualizacao
from ...services.atualizacao import NovaVersao
from ..widgets import BaseDialog, Worker, button, card, label, show_exception


def pasta_downloads():
    return data_dir() / "atualizacoes"


class AtualizacaoDialog(BaseDialog):
    """Pergunta se o usuário quer atualizar agora; baixa, confere e roda o instalador."""

    def __init__(self, nova: NovaVersao, parent: QWidget | None = None) -> None:
        origem = "pasta da rede" if nova.da_rede else "internet"
        super().__init__(
            "Atualização disponível",
            f"A versão {nova.versao} do Retalhos está disponível (você usa a {__version__}). "
            f"Ao atualizar, o Retalhos fecha, instala a versão nova e abre de novo sozinho. "
            f"Suas configurações e planilhas são mantidas.",
            parent,
        )
        self.nova = nova
        self.worker: Worker | None = None
        self.setMinimumWidth(560)

        frame, layout = card()
        detalhe = f"Publicada em {nova.data}  ·  " if nova.data else ""
        tamanho = f"{nova.tamanho / 1_048_576:.0f} MB  ·  " if nova.tamanho else ""
        layout.addWidget(label(f"{detalhe}{tamanho}origem: {origem}", "Muted"))
        if nova.notas.strip():
            layout.addWidget(label("O que mudou", "SectionTitle"))
            notas = QTextBrowser()
            notas.setOpenLinks(False)
            notas.setMarkdown(nova.notas)
            notas.setMinimumHeight(140)
            layout.addWidget(notas, 1)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.lb_status = label("", "Muted")
        self.lb_status.setVisible(False)
        layout.addWidget(self.lb_status)
        self.body.addWidget(frame, 1)

        self.bt_depois = button("Depois")
        self.bt_depois.clicked.connect(self.reject)
        self.bt_atualizar = button("Atualizar agora", "primary")
        self.bt_atualizar.clicked.connect(self._atualizar)
        self.footer.addStretch()
        self.footer.addWidget(self.bt_depois)
        self.footer.addWidget(self.bt_atualizar)
        self.bt_atualizar.setFocus()

    def _atualizar(self) -> None:
        self.bt_atualizar.setEnabled(False)
        self.bt_depois.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.lb_status.setVisible(True)
        self.lb_status.setText("Baixando a versão nova…")
        nova = self.nova
        self.worker = Worker(lambda progresso: atualizacao.baixar_instalador(nova, pasta_downloads(), progresso),
                             self)
        self.worker.progress.connect(self._progresso)
        self.worker.succeeded.connect(self._instalar)
        self.worker.failed.connect(self._falhou)
        self.worker.start()

    def _progresso(self, feito: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, 1000)
            self.progress.setValue(int(feito * 1000 / total))
            self.lb_status.setText(f"Baixando a versão nova… {feito / 1_048_576:.0f} de {total / 1_048_576:.0f} MB")

    def _instalar(self, instalador) -> None:
        self.lb_status.setText("Instalando… o Retalhos vai fechar e abrir de novo.")
        try:
            atualizacao.executar_instalador(instalador)
        except Exception as exc:  # noqa: BLE001
            self._falhou(exc)
            return
        self.accept()
        QApplication.quit()

    def _falhou(self, exc: Exception) -> None:
        self.progress.setVisible(False)
        self.lb_status.setVisible(False)
        self.bt_atualizar.setEnabled(True)
        self.bt_depois.setEnabled(True)
        show_exception(self, "Atualização", exc)

    def reject(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return  # download em andamento: espera terminar
        super().reject()
