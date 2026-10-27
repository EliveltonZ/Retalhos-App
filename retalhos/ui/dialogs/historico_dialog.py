from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ...models import Retalho, RetalhoRemovido
from ...services import EstoqueService
from ..widgets import ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, busy, button, label, show_exception


class HistoricoDialog(BaseDialog):
    """Toda a movimentação de um retalho: quem fez, quando e o quê (tblHistorico)."""

    def __init__(self, service: EstoqueService, retalho: Retalho, parent: QWidget | None = None,
                 removido: RetalhoRemovido | None = None) -> None:
        super().__init__(
            f"Histórico do retalho {retalho.id}",
            f"{retalho.descricao}  ·  {retalho.espessura} mm  ·  {retalho.largura:g} x {retalho.altura:g}",
            parent, resizable=True,
        )
        self.resize(820, 460)
        model = ObjectTableModel([
            Column("Data/hora", lambda m: m.data_hora, width=140),
            Column("Ação", lambda m: m.acao, width=130),
            Column("Usuário", lambda m: m.usuario, width=140),
            Column("Detalhe", lambda m: m.detalhe, ALIGN_LEFT, stretch=True),
        ])
        self.body.addWidget(DataTable(model), 1)
        resumo = label("", "Muted")
        resumo.setWordWrap(True)
        self.body.addWidget(resumo)
        try:
            with busy():
                movimentos = service.historico(retalho.id)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Histórico", exc)
            movimentos = []
        model.set_rows(movimentos)
        partes = [f"Lançado por {retalho.responsavel or '—'}"]
        if removido is not None:
            quando = removido.data.strftime("%d/%m/%Y %H:%M") if removido.data else "—"
            partes.append(f"{removido.motivo.lower()} em {quando} por {removido.responsavel or '—'}")
        elif retalho.reservado:
            partes.append(f"reservado p/ {retalho.reserva} por {retalho.reservado_por or '—'}")
        if not movimentos:
            partes.append("sem movimentação registrada (lançamentos anteriores ao histórico)")
        resumo.setText("  ·  ".join(partes))

        bt = button("Fechar", "primary")
        bt.clicked.connect(self.accept)
        self.footer.addStretch()
        self.footer.addWidget(bt)
