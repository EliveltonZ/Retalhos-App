from __future__ import annotations

import os

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QWidget

from ...services import EstoqueService, PedidoNaoEncontrado
from ..columns import retalho_columns, retalho_row_color
from ..widgets import (
    BaseDialog, DataTable, ObjectTableModel, busy, button, choose, confirm, info, label, show_exception,
    warning,
)


class ReservaDialog(BaseDialog):
    """Reserva de retalhos para um projeto, a partir dos materiais do pedido (PED)."""

    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        super().__init__(
            "Reserva por projeto",
            "Busque os retalhos compatíveis com o pedido, marque os que serão usados e reserve.",
            parent,
            resizable=True,
        )
        self.service = service
        self.projeto = ""
        self.resize(1100, 680)

        top = QHBoxLayout()
        top.addWidget(label("Número do projeto:"))
        self.txt_proj = QLineEdit()
        self.txt_proj.setPlaceholderText("Ex.: 1206")
        self.txt_proj.setMaximumWidth(180)
        self.txt_proj.returnPressed.connect(self.search)
        top.addWidget(self.txt_proj)
        bt_search = button("Buscar retalhos", "primary")
        bt_search.clicked.connect(self.search)
        top.addWidget(bt_search)
        top.addStretch()
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Filtrar…")
        self.txt_filter.setClearButtonEnabled(True)
        self.txt_filter.setMaximumWidth(260)
        top.addWidget(self.txt_filter)
        self.body.addLayout(top)

        self.model = ObjectTableModel(
            retalho_columns(extended=False), checkable=True,
            row_color=retalho_row_color(service.settings),
        )
        self.table = DataTable(self.model)
        self.body.addWidget(self.table, 1)
        self.txt_filter.textChanged.connect(self.table.proxy.set_text)
        self.model.dataChanged.connect(self._update_count)
        self.model.modelReset.connect(self._update_count)

        bt_all = button("Marcar todos")
        bt_all.clicked.connect(lambda: self.model.set_all_checked(True))
        bt_none = button("Desmarcar")
        bt_none.clicked.connect(lambda: self.model.set_all_checked(False))
        self.lb_count = label("", "Muted")
        self.bt_undo = button("Desfazer reserva", "danger")
        self.bt_undo.clicked.connect(self._undo)
        self.bt_reserve = button("Reservar marcados", "primary")
        self.bt_reserve.clicked.connect(self._reserve)
        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        for w in (bt_all, bt_none, self.lb_count):
            self.footer.addWidget(w)
        self.footer.addStretch()
        for w in (bt_close, self.bt_undo, self.bt_reserve):
            self.footer.addWidget(w)

        self._update_count()
        self.txt_proj.setFocus()

    def _update_count(self, *_: object) -> None:
        marcados = self.model.checked_rows()
        total = len(self.model.rows())
        reservados = sum(1 for r in self.model.rows() if r.reserva == self.projeto and self.projeto)
        self.lb_count.setText(f"{len(marcados)} marcados · {total} encontrados · {reservados} já reservados")
        self.bt_reserve.setEnabled(bool(marcados))
        self.bt_undo.setEnabled(any(r.reserva == self.projeto for r in marcados))

    def search(self) -> None:
        projeto = self.txt_proj.text().strip()
        if not projeto:
            return
        try:
            with busy():
                retalhos = self.service.retalhos_para_projeto(projeto)
        except PedidoNaoEncontrado:
            self.model.set_rows([])
            warning(self, "Reserva", f"Pedido do projeto {projeto} não encontrado no Corte Certo.")
            self.txt_proj.selectAll()
            return
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Reserva", exc)
            return
        self.projeto = projeto
        self.model.set_rows(retalhos)
        if not retalhos:
            info(self, "Reserva", "Nenhum retalho disponível para os materiais deste projeto.")

    def _reserve(self) -> None:
        marcados = self.model.checked_rows()
        if not marcados or not confirm(self, "Reserva",
                                       f"Reservar {len(marcados)} retalho(s) para o projeto {self.projeto}?"):
            return
        if not self.service.corte_gerado(self.projeto) and not confirm(
            self, "Reserva",
            "Não foi encontrado corte gerado para o projeto selecionado.\nContinuar mesmo assim?",
            default_yes=False,
        ):
            return
        try:
            with busy():
                resultado = self.service.reservar(self.projeto, marcados)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Reserva", exc)
            return
        self.changed = True
        self.search()

        texto = f"{resultado.reservados} retalho(s) reservado(s) para o projeto {self.projeto}."
        if resultado.planilha:
            escolha = choose(
                self, "Reserva", f"{texto}\n\nPlanilha gerada:\n{resultado.planilha}",
                [("open", "Abrir planilha", ""), ("ok", "OK", "primary")], default="ok",
            )
            if escolha == "open":
                os.startfile(resultado.planilha)  # noqa: S606 - Windows
        else:
            info(self, "Reserva", texto)

    def _undo(self) -> None:
        marcados = [r for r in self.model.checked_rows() if r.reserva == self.projeto]
        if not marcados or not confirm(self, "Reserva",
                                       f"Desfazer a reserva de {len(marcados)} retalho(s)?", default_yes=False):
            return
        try:
            with busy():
                total = self.service.cancelar_reservas(self.projeto, marcados)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Reserva", exc)
            return
        self.changed = True
        self.search()
        info(self, "Reserva", f"{total} reserva(s) cancelada(s). Os retalhos voltaram ao estoque.")
