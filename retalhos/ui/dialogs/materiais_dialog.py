from __future__ import annotations

from PySide6.QtWidgets import QLineEdit, QWidget

from ...models import Chapa
from ...services import EstoqueService
from ..theme import ROW_INACTIVE
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, busy, button, label, show_exception,
)


class MateriaisDialog(BaseDialog):
    """Lista de materiais. No modo seleção, devolve o código escolhido em :attr:`selected`."""

    def __init__(self, service: EstoqueService, select_mode: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(
            "Materiais",
            "Clique duas vezes para selecionar." if select_mode else "Materiais cadastrados (tblChapas).",
            parent,
            resizable=True,
        )
        self.service = service
        self.select_mode = select_mode
        self.selected: Chapa | None = None
        self.resize(640, 620)

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Filtrar por código ou descrição…")
        self.txt_filter.setClearButtonEnabled(True)
        self.body.addWidget(self.txt_filter)

        self.model = ObjectTableModel(
            [
                Column("Cód.", lambda c: c.codigo, width=70),
                Column("Esp.", lambda c: c.espessura, width=60),
                Column("Descrição", lambda c: c.descricao, ALIGN_LEFT, stretch=True),
                Column("Ativo", lambda c: c.ativo, width=60),
            ],
            row_color=lambda c: None if c.ativo else ROW_INACTIVE,
        )
        self.table = DataTable(self.model)
        self.table.rowActivated.connect(self._choose)
        self.body.addWidget(self.table, 1)
        self.txt_filter.textChanged.connect(self.table.proxy.set_text)

        self.lb_count = label("", "Muted")
        self.footer.addWidget(self.lb_count)
        self.footer.addStretch()
        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        self.footer.addWidget(bt_close)
        if select_mode:
            bt_ok = button("Selecionar", "primary")
            bt_ok.clicked.connect(lambda: self._choose(self.table.selected()))
            self.footer.addWidget(bt_ok)

        self.load()
        self.txt_filter.setFocus()

    def load(self) -> None:
        try:
            with busy():
                materiais = self.service.listar_materiais()
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Materiais", exc)
            return
        self.model.set_rows(materiais)
        self.lb_count.setText(f"{len(materiais)} materiais")

    def _choose(self, chapa: Chapa | None) -> None:
        if self.select_mode and chapa is not None:
            self.selected = chapa
            self.accept()
