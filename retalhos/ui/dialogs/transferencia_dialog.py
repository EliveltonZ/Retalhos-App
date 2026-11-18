from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QCompleter, QFormLayout, QWidget

from ...models import Retalho
from ...services.estoque import SETOR_MAX
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, UpperLineEdit, button, card, label,
)


def _ordem_setor(setor: str) -> tuple:
    """Setores numéricos primeiro, em ordem crescente (1, 2, … 17); depois os de texto."""
    return (0, int(setor), "") if setor.isdigit() else (1, 0, setor)


class TransferenciaDialog(BaseDialog):
    """Transferência de setor dos retalhos selecionados (vários de uma vez)."""

    def __init__(self, retalhos: list[Retalho], setores: list[str], parent: QWidget | None = None) -> None:
        super().__init__(
            "Transferir setor",
            "Muda o setor de todos os retalhos abaixo. Cada transferência fica registrada no histórico "
            "da peça (setor de origem, destino, data/hora e usuário).",
            parent,
        )
        self.setor = ""
        self.setMinimumWidth(640)

        model = ObjectTableModel([
            Column("ID", lambda r: r.id, width=60),
            Column("Setor atual", lambda r: r.setor, width=85),
            Column("Esp.", lambda r: r.espessura, width=45),
            Column("Material", lambda r: r.descricao, ALIGN_LEFT, stretch=True),
            Column("Medida", lambda r: f"{r.largura:g} x {r.altura:g}", width=105),
            Column("Reserva", lambda r: r.reserva, width=80),
        ])
        model.set_rows(retalhos)
        tabela = DataTable(model)
        tabela.setMaximumHeight(min(60 + 30 * len(retalhos), 300))
        self.body.addWidget(tabela)

        frame, layout = card()
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.cb_setor = QComboBox()
        self.cb_setor.setEditable(True)
        self.cb_setor.setLineEdit(UpperLineEdit())
        self.cb_setor.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cb_setor.addItems(sorted({s.upper() for s in setores if s.strip()}, key=_ordem_setor))
        self.cb_setor.setCurrentIndex(-1)
        self.cb_setor.lineEdit().setMaxLength(SETOR_MAX)
        self.cb_setor.lineEdit().setPlaceholderText("Escolha ou digite o setor de destino")
        self.cb_setor.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        form.addRow("Transferir para o setor:", self.cb_setor)
        layout.addLayout(form)
        origens = sorted({r.setor or "(sem setor)" for r in retalhos}, key=_ordem_setor)
        layout.addWidget(label(f"Setor(es) de origem: {', '.join(origens)}", "Muted"))
        self.body.addWidget(frame)

        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        self.bt_ok = button(f"Transferir {len(retalhos)} retalho(s)", "primary")
        self.bt_ok.setEnabled(False)
        self.bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(self.bt_ok)
        self.cb_setor.currentTextChanged.connect(lambda t: self.bt_ok.setEnabled(bool(t.strip())))
        self.cb_setor.lineEdit().returnPressed.connect(self._ok)
        self.cb_setor.setFocus()

    def _ok(self) -> None:
        self.setor = self.cb_setor.currentText().strip().upper()
        if self.setor:
            self.accept()
