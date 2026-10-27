from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QProgressBar, QWidget

from ...models import Chapa, Sobra
from ...services import EstoqueService, ler_plano_de_corte
from ..theme import ROW_ERROR
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, Worker, busy, button, confirm, info,
    label, show_exception, warning,
)


@dataclass
class _Item:
    sobra: Sobra
    chapa: Chapa | None

    @property
    def valido(self) -> bool:
        return self.chapa is not None


class LeitorXmlDialog(BaseDialog):
    """Importa sobras de um plano de corte (``.cutplanning``) já reservadas para um projeto."""

    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        super().__init__(
            "Leitor de plano de corte",
            "Abra um arquivo .cutplanning do Corte Certo para lançar as sobras no estoque.",
            parent,
            resizable=True,
        )
        self.service = service
        self.worker: Worker | None = None
        self.resize(900, 620)

        top = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Arquivo .cutplanning")
        self.txt_path.returnPressed.connect(self.load)
        top.addWidget(self.txt_path, 1)
        bt_browse = button("Procurar…")
        bt_browse.clicked.connect(self._browse)
        top.addWidget(bt_browse)
        self.bt_load = button("Ler arquivo", "primary")
        self.bt_load.clicked.connect(self.load)
        top.addWidget(self.bt_load)
        self.body.addLayout(top)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.body.addWidget(self.progress)

        self.model = ObjectTableModel(
            [
                Column("Cód.", lambda i: i.sobra.codigo, width=70),
                Column("Esp.", lambda i: i.chapa.espessura if i.chapa else "", width=60),
                Column("Material", lambda i: i.chapa.descricao if i.chapa else "MATERIAL NÃO CADASTRADO",
                       ALIGN_LEFT, stretch=True),
                Column("Largura", lambda i: i.sobra.largura, width=90),
                Column("Altura", lambda i: i.sobra.altura, width=90),
            ],
            checkable=True,
            row_color=lambda i: None if i.valido else ROW_ERROR,
            can_check=lambda i: i.valido,
        )
        self.table = DataTable(self.model)
        self.body.addWidget(self.table, 1)
        self.model.dataChanged.connect(self._update_state)
        self.model.modelReset.connect(self._update_state)

        bt_all = button("Marcar todos")
        bt_all.clicked.connect(lambda: self.model.set_all_checked(True))
        bt_none = button("Desmarcar")
        bt_none.clicked.connect(lambda: self.model.set_all_checked(False))
        self.lb_count = label("", "Muted")
        self.txt_proj = QLineEdit()
        self.txt_proj.setPlaceholderText("Projeto")
        self.txt_proj.setFixedWidth(130)
        self.txt_proj.textChanged.connect(self._update_state)
        self.bt_launch = button("Lançar marcados", "primary")
        self.bt_launch.clicked.connect(self._launch)
        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        for w in (bt_all, bt_none, self.lb_count):
            self.footer.addWidget(w)
        self.footer.addStretch()
        self.footer.addWidget(label("Reservar para:"))
        for w in (self.txt_proj, bt_close, self.bt_launch):
            self.footer.addWidget(w)
        self._update_state()

    def _browse(self) -> None:
        start = str(Path(self.txt_path.text()).parent) if self.txt_path.text() else ""
        path, _ = QFileDialog.getOpenFileName(self, "Plano de corte", start, "Corte Certo (*.cutplanning)")
        if path:
            self.txt_path.setText(path.replace("/", "\\"))
            self.load()

    def _update_state(self, *_: object) -> None:
        marcados = len(self.model.checked_rows())
        total = len(self.model.rows())
        invalidos = sum(1 for i in self.model.rows() if not i.valido)
        texto = f"{marcados} marcados · {total} sobras"
        if invalidos:
            texto += f" · {invalidos} com material não cadastrado"
        self.lb_count.setText(texto)
        self.bt_launch.setEnabled(marcados > 0 and bool(self.txt_proj.text().strip()))

    def load(self) -> None:
        path = self.txt_path.text().strip()
        if not path:
            self._browse()
            return
        if not Path(path).is_file():
            warning(self, "Plano de corte", "Arquivo não encontrado.")
            return
        service = self.service

        def task(progress):
            sobras = ler_plano_de_corte(path)
            progress(1, 2)
            chapas = service.buscar_materiais(s.codigo for s in sobras)
            progress(2, 2)
            return [_Item(s, chapas.get(s.codigo)) for s in sobras]

        self.model.set_rows([])
        self.bt_load.setEnabled(False)
        self.progress.setRange(0, 0)  # indeterminado
        self.progress.setVisible(True)
        self.worker = Worker(task, self)
        self.worker.succeeded.connect(self._loaded)
        self.worker.failed.connect(lambda exc: show_exception(self, "Plano de corte", exc))
        self.worker.finished.connect(self._finished)
        self.worker.start()

    def _finished(self) -> None:
        self.progress.setVisible(False)
        self.bt_load.setEnabled(True)

    def _loaded(self, items: list[_Item]) -> None:
        self.model.set_rows(items)
        if not items:
            info(self, "Plano de corte", "Não existem sobras no programa selecionado.")

    def _launch(self) -> None:
        marcados: list[_Item] = self.model.checked_rows()
        projeto = self.txt_proj.text().strip()
        if not confirm(self, "Lançar sobras",
                       f"Lançar {len(marcados)} sobra(s) reservada(s) para o projeto {projeto}?"):
            return
        try:
            with busy():
                total = self.service.lancar_sobras([i.sobra for i in marcados], projeto)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Lançar sobras", exc)
            return
        self.changed = True
        # remove da lista o que já foi lançado, evitando lançamento em duplicidade
        lancados = {id(i) for i in marcados}
        self.model.set_rows([i for i in self.model.rows() if id(i) not in lancados])
        info(self, "Lançar sobras", f"{total} sobra(s) lançada(s) e reservada(s) para o projeto {projeto}.")

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.worker and self.worker.isRunning():
            self.worker.wait(5000)
        super().closeEvent(event)

    def reject(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.wait(5000)
        super().reject()
