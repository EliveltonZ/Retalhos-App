from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter, QFileDialog, QHBoxLayout, QLineEdit, QWidget

from ...models import RetalhoRemovido
from ...paths import app_dir
from ...services import EstoqueService
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, busy, button, choose, confirm, label,
    show_exception, warning,
)
from .historico_dialog import HistoricoDialog

_MOTIVOS = {"Todos": None, "Baixas": "Baixa", "Exclusões": "Exclusão"}


class RemovidosDialog(BaseDialog):
    """Consulta dos retalhos que receberam baixa ou foram excluídos, sempre de um material por vez.

    Administradores podem restaurar (o retalho volta ao estoque disponível e ao RET do Corte Certo).
    """

    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        super().__init__(
            "Retalhos removidos",
            "Retalhos que saíram do sistema por baixa (consumo) ou exclusão. Escolha o material para consultar.",
            parent, resizable=True,
        )
        self.service = service
        self.resize(1040, 600)

        filtros = QHBoxLayout()
        filtros.setSpacing(8)
        self.cb_material = QComboBox()
        self.cb_material.setEditable(True)
        self.cb_material.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.cb_material.lineEdit().setPlaceholderText("Digite ou escolha o material…")
        completer = self.cb_material.completer()
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        filtros.addWidget(label("Material:"))
        filtros.addWidget(self.cb_material, 3)
        self.cb_motivo = QComboBox()
        self.cb_motivo.addItems(list(_MOTIVOS))
        filtros.addWidget(label("Motivo:"))
        filtros.addWidget(self.cb_motivo)
        self.txt_filtro = QLineEdit()
        self.txt_filtro.setPlaceholderText("Filtrar (ID, medida, projeto, responsável…)")
        self.txt_filtro.setClearButtonEnabled(True)
        filtros.addWidget(self.txt_filtro, 2)
        self.body.addLayout(filtros)

        self.model = ObjectTableModel([
            Column("ID", lambda x: x.retalho.id, width=70),
            Column("Largura", lambda x: x.retalho.largura, width=80),
            Column("x", lambda _x: "x", width=24),
            Column("Altura", lambda x: x.retalho.altura, width=80),
            Column("Esp.", lambda x: x.retalho.espessura, width=55),
            Column("Setor", lambda x: x.retalho.setor, width=70),
            Column("Motivo", lambda x: x.motivo, width=85),
            Column("Data/hora", lambda x: x.data, width=130),
            Column("Responsável", lambda x: x.responsavel, width=120),
            Column("Projeto", lambda x: x.retalho.reserva if x.baixa else "", width=100),
            Column("Lançado por", lambda x: x.retalho.responsavel, ALIGN_LEFT, stretch=True),
        ])
        self.table = DataTable(self.model)
        self.body.addWidget(self.table, 1)
        self.lb_info = label("", "Muted")
        self.body.addWidget(self.lb_info)

        self.bt_historico = button("Histórico…")
        self.bt_export = button("Exportar Excel…")
        self.bt_restaurar = button("Restaurar ao estoque")
        self.bt_restaurar.setVisible(service.settings.is_admin)
        bt_close = button("Fechar", "primary")
        self.bt_historico.clicked.connect(self._historico)
        self.bt_export.clicked.connect(self._exportar)
        self.bt_restaurar.clicked.connect(self._restaurar)
        bt_close.clicked.connect(self.accept)
        self.footer.addWidget(self.bt_historico)
        self.footer.addWidget(self.bt_export)
        self.footer.addStretch()
        self.footer.addWidget(self.bt_restaurar)
        self.footer.addWidget(bt_close)

        self.cb_material.activated.connect(lambda _i: self._carregar())
        self.cb_motivo.currentIndexChanged.connect(lambda _i: self._aplicar_filtro())
        self.txt_filtro.textChanged.connect(self.table.proxy.set_text)
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._botoes())
        self.table.proxy.modelReset.connect(self._botoes)
        self.table.proxy.layoutChanged.connect(self._botoes)
        self.table.rowActivated.connect(lambda _x: self._historico())

        self._carregar_materiais()
        self._botoes()

    # -------------------------------------------------------------- dados
    def _carregar_materiais(self, manter: int | None = None) -> None:
        try:
            with busy():
                contagem = self.service.contar_removidos_por_material()
                materiais = self.service.buscar_materiais(contagem) if contagem else {}
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Retalhos removidos", exc)
            contagem, materiais = {}, {}
        self.cb_material.blockSignals(True)
        self.cb_material.clear()
        for cod, chapa in sorted(materiais.items(), key=lambda kv: (kv[1].descricao, kv[0])):
            n = contagem[cod]
            self.cb_material.addItem(
                f"{chapa.descricao}  ·  {chapa.espessura} mm  ({cod})  —  {n} removido{'s' if n > 1 else ''}", cod
            )
        self.cb_material.setCurrentIndex(self.cb_material.findData(manter) if manter is not None else -1)
        self.cb_material.blockSignals(False)
        if not contagem:
            self.lb_info.setText("Nenhum retalho removido registrado.")

    def _codigo(self) -> int | None:
        i = self.cb_material.currentIndex()
        return self.cb_material.itemData(i) if i >= 0 else None

    def _carregar(self) -> None:
        cod = self._codigo()
        if cod is None:
            self.model.set_rows([])
            return
        try:
            with busy():
                removidos = self.service.listar_removidos(cod)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Retalhos removidos", exc)
            removidos = []
        self.model.set_rows(removidos)
        self._aplicar_filtro()

    def _aplicar_filtro(self) -> None:
        motivo = _MOTIVOS[self.cb_motivo.currentText()]
        self.table.proxy.set_predicate(None if motivo is None else lambda x: x.motivo == motivo)
        self._botoes()

    def _botoes(self) -> None:
        sel = self.table.selected()
        self.bt_historico.setEnabled(sel is not None)
        self.bt_restaurar.setEnabled(sel is not None)
        visiveis = self.table.visible_rows()
        self.bt_export.setEnabled(bool(visiveis))
        if self._codigo() is not None:
            baixas = sum(1 for x in visiveis if x.baixa)
            self.lb_info.setText(f"{len(visiveis)} retalho(s): {baixas} baixa(s), {len(visiveis) - baixas} exclusão(ões)")

    # -------------------------------------------------------------- ações
    def _historico(self) -> None:
        x: RetalhoRemovido | None = self.table.selected()
        if x is not None:
            HistoricoDialog(self.service, x.retalho, self, removido=x).exec()

    def _exportar(self) -> None:
        removidos = self.table.visible_rows()
        if not removidos:
            return
        pasta = self.service.settings.sheets_dir or str(app_dir())
        nome = f"REMOVIDOS_{removidos[0].retalho.codigo}.xlsx"
        destino, _ = QFileDialog.getSaveFileName(self, "Exportar removidos", os.path.join(pasta, nome),
                                                 "Excel (*.xlsx)")
        if not destino:
            return
        try:
            arquivo = self.service.exportar_removidos(removidos, destino)
        except PermissionError:
            warning(self, "Exportar", f"Não foi possível salvar:\n{destino}\n\n"
                                      "O arquivo provavelmente está aberto no Excel. Feche-o e tente de novo.")
            return
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Exportar", exc)
            return
        if choose(self, "Exportar", f"Planilha gerada:\n{arquivo}",
                  [("open", "Abrir planilha", ""), ("ok", "OK", "primary")], default="ok") == "open":
            os.startfile(arquivo)  # noqa: S606 - Windows

    def _restaurar(self) -> None:
        x: RetalhoRemovido | None = self.table.selected()
        if x is None:
            return
        r = x.retalho
        if not confirm(self, "Restaurar retalho",
                       f"Restaurar o retalho {r.id} — {r.descricao} {r.largura:g} × {r.altura:g}?\n\n"
                       "Ele volta ao estoque como disponível (sem reserva) e ao arquivo do Corte Certo.\n"
                       "A restauração fica registrada no histórico.",
                       default_yes=False):
            return
        try:
            self.service.restaurar_retalho(x)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Restaurar retalho", exc)
            return
        self.changed = True
        cod = self._codigo()
        self._carregar_materiais(manter=cod)
        self._carregar()
        self.lb_info.setText(f"✔ Retalho {r.id} restaurado ao estoque.  ·  " + self.lb_info.text())
