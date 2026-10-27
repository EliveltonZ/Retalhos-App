from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QWidget

from ...models import Retalho
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, UpperLineEdit, button, card, label,
)


class ReservaManualDialog(BaseDialog):
    """Reserva livre: guardar retalho(s) para um projeto que ainda será feito (sem PED/plano de corte)."""

    def __init__(self, retalhos: list[Retalho], parent: QWidget | None = None) -> None:
        super().__init__(
            "Reservar retalho(s)",
            "Reserva manual: use para guardar uma sobra para um projeto que ainda será feito. "
            "O retalho sai da lista de disponíveis do Corte Certo até a reserva ser liberada.",
            parent,
        )
        self.projeto = ""
        self.setMinimumWidth(640)

        model = ObjectTableModel([
            Column("ID", lambda r: r.id, width=60),
            Column("Setor", lambda r: r.setor, width=60),
            Column("Esp.", lambda r: r.espessura, width=45),
            Column("Material", lambda r: r.descricao, ALIGN_LEFT, stretch=True),
            Column("Medida", lambda r: f"{r.largura:g} x {r.altura:g}", width=105),
        ])
        model.set_rows(retalhos)
        tabela = DataTable(model)
        tabela.setMaximumHeight(min(60 + 30 * len(retalhos), 240))
        self.body.addWidget(tabela)

        frame, layout = card()
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.txt_projeto = UpperLineEdit()
        self.txt_projeto.setMaxLength(50)
        self.txt_projeto.setPlaceholderText("Nº do projeto ou identificação (ex.: 14010)")
        form.addRow("Reservar para:", self.txt_projeto)
        layout.addLayout(form)
        layout.addWidget(label("Para desfazer, selecione o retalho na tela principal e use \"Liberar reserva\".",
                               "Muted"))
        self.body.addWidget(frame)

        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        self.bt_ok = button(f"Reservar {len(retalhos)} retalho(s)", "primary")
        self.bt_ok.setEnabled(False)
        self.bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(self.bt_ok)
        self.txt_projeto.textChanged.connect(lambda t: self.bt_ok.setEnabled(bool(t.strip())))
        self.txt_projeto.returnPressed.connect(self._ok)
        self.txt_projeto.setFocus()

    def _ok(self) -> None:
        self.projeto = self.txt_projeto.text().strip()
        if self.projeto:
            self.accept()
