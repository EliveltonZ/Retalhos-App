from __future__ import annotations

from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QCheckBox, QFormLayout, QHBoxLayout, QLineEdit, QWidget

from ...models import Chapa
from ...services import EstoqueService
from ..widgets import BaseDialog, UpperLineEdit, button, card, confirm, info, label, show_exception
from .materiais_dialog import MateriaisDialog


class CadastroDialog(BaseDialog):
    """Cadastro/edição de materiais (cores) em ``tblChapas``."""

    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        super().__init__("Cadastro de cores", "Informe o código para cadastrar ou editar um material.", parent)
        self.service = service
        self.setMinimumWidth(520)

        frame, layout = card()
        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.txt_cod = QLineEdit()
        self.txt_cod.setValidator(QIntValidator(1, 9_999_999))
        self.txt_cod.setPlaceholderText("Código")
        bt_find = button("…", tooltip="Procurar material")
        bt_find.setFixedWidth(40)
        bt_find.clicked.connect(self._pick)
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.txt_cod, 1)
        h.addWidget(bt_find)
        form.addRow("Código:", row)

        self.txt_mm = QLineEdit()
        self.txt_mm.setPlaceholderText("Ex.: 15")
        form.addRow("Espessura (mm):", self.txt_mm)
        self.txt_mdf = UpperLineEdit()
        self.txt_mdf.setPlaceholderText("Ex.: BRANCO TX")
        form.addRow("Descrição:", self.txt_mdf)
        self.chk_active = QCheckBox("Material ativo")
        self.chk_active.setChecked(True)
        form.addRow("", self.chk_active)
        layout.addLayout(form)
        self.lb_mode = label("", "Muted")
        layout.addWidget(self.lb_mode)
        self.body.addWidget(frame)

        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        self.bt_save = button("Salvar", "primary")
        self.bt_save.setEnabled(False)
        self.bt_save.clicked.connect(self._save)
        self.footer.addStretch()
        self.footer.addWidget(bt_close)
        self.footer.addWidget(self.bt_save)

        self.txt_cod.editingFinished.connect(self._lookup)
        self.txt_cod.textChanged.connect(lambda t: self.bt_save.setEnabled(bool(t)))

    def _pick(self) -> None:
        dlg = MateriaisDialog(self.service, select_mode=True, parent=self)
        if dlg.exec() and dlg.selected:
            self.txt_cod.setText(str(dlg.selected.codigo))
            self._lookup()

    def _lookup(self) -> None:
        if not self.txt_cod.text():
            return
        try:
            chapa = self.service.buscar_material(int(self.txt_cod.text()))
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Cadastro", exc)
            return
        if chapa:
            self.txt_mm.setText(chapa.espessura)
            self.txt_mdf.setText(chapa.descricao)
            self.chk_active.setChecked(chapa.ativo)
            self.lb_mode.setText("Editando material existente.")
        else:
            self.txt_mm.clear()
            self.txt_mdf.clear()
            self.chk_active.setChecked(True)
            self.lb_mode.setText("Código livre: será feito um novo cadastro.")
        self.txt_mm.setFocus()

    def _save(self) -> None:
        chapa = Chapa(
            codigo=int(self.txt_cod.text()), espessura=self.txt_mm.text().strip(),
            descricao=self.txt_mdf.text().strip(), ativo=self.chk_active.isChecked(),
        )
        if not confirm(self, "Cadastro", f"Salvar o material {chapa.codigo} - {chapa.descricao}?"):
            return
        try:
            novo = self.service.salvar_material(chapa)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Cadastro", exc)
            return
        self.changed = True
        info(self, "Cadastro", "Material cadastrado com sucesso." if novo else "Material atualizado com sucesso.")
        self.lb_mode.setText("Editando material existente.")
