from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QWidget

from ...services import EstoqueService
from ..columns import retalho_columns, retalho_row_color
from ..widgets import BaseDialog, DataTable, ObjectTableModel, busy, button, confirm, info, label, show_exception


class BaixaDialog(BaseDialog):
    """Baixa por consumo: registra data/hora e responsável e oculta os retalhos do sistema."""

    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        super().__init__(
            "Baixa de reservas",
            "Retalhos reservados para o projeto foram consumidos na produção: a baixa registra data/hora e "
            "responsável e eles deixam de aparecer no sistema (o registro fica no banco).",
            parent,
            resizable=True,
        )
        self.service = service
        self.projeto = ""
        self.resize(1000, 560)

        top = QHBoxLayout()
        top.addWidget(label("Número do projeto:"))
        self.txt_proj = QLineEdit()
        self.txt_proj.setMaximumWidth(180)
        self.txt_proj.returnPressed.connect(self.search)
        top.addWidget(self.txt_proj)
        bt_search = button("Buscar", "primary")
        bt_search.clicked.connect(self.search)
        top.addWidget(bt_search)
        top.addStretch()
        self.body.addLayout(top)

        self.model = ObjectTableModel(retalho_columns(), row_color=retalho_row_color(service.settings))
        self.table = DataTable(self.model)
        self.body.addWidget(self.table, 1)

        self.lb_count = label("", "Muted")
        self.bt_remove = button("Dar baixa", "danger")
        self.bt_remove.setEnabled(False)
        self.bt_remove.clicked.connect(self._remove)
        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        self.footer.addWidget(self.lb_count)
        self.footer.addStretch()
        self.footer.addWidget(bt_close)
        self.footer.addWidget(self.bt_remove)
        self.txt_proj.setFocus()

    def search(self) -> None:
        projeto = self.txt_proj.text().strip()
        if not projeto:
            return
        try:
            with busy():
                retalhos = self.service.retalhos_reservados(projeto)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Baixa", exc)
            return
        self.projeto = projeto
        self.model.set_rows(retalhos)
        self.bt_remove.setEnabled(bool(retalhos))
        self.bt_remove.setText(f"Dar baixa em {len(retalhos)} retalho(s)" if retalhos else "Dar baixa")
        self.lb_count.setText(f"{len(retalhos)} retalho(s) reservado(s) para o projeto {projeto}")
        if not retalhos:
            info(self, "Baixa", f"Nenhum retalho reservado para o projeto {projeto}.")
            self.txt_proj.selectAll()

    def _remove(self) -> None:
        total = len(self.model.rows())
        if not confirm(
            self, "Baixa",
            f"Dar baixa em {total} retalho(s) do projeto {self.projeto}?\n\n"
            "Eles deixam de aparecer no sistema; a baixa fica registrada com data/hora e responsável.",
            default_yes=False,
        ):
            return
        try:
            with busy():
                removidos = self.service.dar_baixa(self.projeto)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Baixa", exc)
            return
        self.changed = True
        self.model.set_rows([])
        self.bt_remove.setEnabled(False)
        self.bt_remove.setText("Dar baixa")
        self.lb_count.setText("")
        info(self, "Baixa", f"Baixa registrada em {removidos} retalho(s) do projeto.")
