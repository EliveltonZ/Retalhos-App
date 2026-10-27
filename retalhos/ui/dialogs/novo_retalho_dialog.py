from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QWidget

from ...models import Chapa
from ...services import EstoqueService, RegraDeNegocioError, ler_codigo_barras
from ...services.etiquetas import BARCODE_LENGTH
from ..widgets import (
    BaseDialog, UpperLineEdit, button, card, confirm, label, parse_float, set_invalid, show_exception,
)


class NovoRetalhoDialog(BaseDialog):
    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        st = service.settings
        super().__init__(
            "Novo retalho",
            "Leia a etiqueta com o leitor de código de barras ou preencha os campos manualmente.",
            parent,
        )
        self.service = service
        self.material: Chapa | None = None
        self.setMinimumWidth(560)

        frame, layout = card()
        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setMaxLength(BARCODE_LENGTH)
        self.txt_barcode.setPlaceholderText(f"{BARCODE_LENGTH} caracteres")
        form.addRow("Código de barras:", self.txt_barcode)

        self.txt_cod = QLineEdit()
        self.txt_cod.setValidator(QIntValidator(1, 9_999_999))
        bt_pick = button("…", tooltip="Escolher material (F4)")
        bt_pick.setFixedWidth(40)
        bt_pick.setShortcut("F4")
        bt_pick.clicked.connect(self._pick)
        form.addRow("Código do material:", self._row(self.txt_cod, bt_pick))

        self.txt_material = QLineEdit()
        self.txt_material.setReadOnly(True)
        self.txt_material.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        form.addRow("Material:", self.txt_material)

        self.txt_setor = UpperLineEdit()
        self.txt_setor.setPlaceholderText("Opcional")
        form.addRow("Setor:", self.txt_setor)

        self.txt_largura = QLineEdit()
        self.txt_altura = QLineEdit()
        self.txt_largura.setPlaceholderText(f"{st.min_width:g} a {st.max_width:g}")
        self.txt_altura.setPlaceholderText(f"{st.min_height:g} a {st.max_height:g}")
        medidas = QWidget()
        h = QHBoxLayout(medidas)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.txt_largura)
        h.addWidget(QLabel("×"))
        h.addWidget(self.txt_altura)
        form.addRow("Largura × Altura (mm):", medidas)

        resp = QLineEdit(st.user)
        resp.setReadOnly(True)
        resp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        form.addRow("Responsável:", resp)
        layout.addLayout(form)

        self.lb_message = label("")
        self.lb_message.setWordWrap(True)
        layout.addWidget(self.lb_message)
        self.body.addWidget(frame)

        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        self.bt_save = button("Lançar retalho", "primary")
        self.bt_save.setEnabled(False)
        self.bt_save.clicked.connect(self._save)
        self.footer.addStretch()
        self.footer.addWidget(bt_close)
        self.footer.addWidget(self.bt_save)

        self.txt_barcode.returnPressed.connect(self._read_barcode)
        self.txt_barcode.textChanged.connect(self._barcode_changed)
        self.txt_cod.editingFinished.connect(self._lookup)
        self.txt_cod.textEdited.connect(self._clear_material)
        for edit in (self.txt_largura, self.txt_altura):
            edit.textEdited.connect(lambda _=None, e=edit: (set_invalid(e, False), self._message("")))
        self.txt_barcode.setFocus()

    @staticmethod
    def _row(edit: QLineEdit, btn: QWidget) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit, 1)
        h.addWidget(btn)
        return w

    def _message(self, text: str, kind: str = "Error") -> None:
        self.lb_message.setText(text)
        self.lb_message.setObjectName(kind)
        self.lb_message.style().unpolish(self.lb_message)
        self.lb_message.style().polish(self.lb_message)

    # ------------------------------------------------------------ material
    def _barcode_changed(self, text: str) -> None:
        # leitores costumam não enviar Enter: lê ao completar 21 caracteres
        if len(text) == BARCODE_LENGTH:
            self._read_barcode()

    def _read_barcode(self) -> None:
        text = self.txt_barcode.text()
        if not text:
            return
        try:
            sobra = ler_codigo_barras(text)
        except ValueError as exc:
            set_invalid(self.txt_barcode, True)
            self._message(str(exc))
            return
        set_invalid(self.txt_barcode, False)
        self.txt_cod.setText(str(sobra.codigo))
        self.txt_largura.setText(f"{sobra.largura:g}")
        self.txt_altura.setText(f"{sobra.altura:g}")
        self._lookup()
        self.txt_setor.setFocus()

    def _pick(self) -> None:
        from .materiais_dialog import MateriaisDialog

        dlg = MateriaisDialog(self.service, select_mode=True, parent=self)
        if dlg.exec() and dlg.selected:
            self.txt_cod.setText(str(dlg.selected.codigo))
            self._lookup()
            self.txt_largura.setFocus()

    def _clear_material(self) -> None:
        self.material = None
        self.txt_material.clear()
        self.bt_save.setEnabled(False)

    def _lookup(self) -> None:
        if not self.txt_cod.text():
            return
        try:
            self.material = self.service.buscar_material(int(self.txt_cod.text()))
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Novo retalho", exc)
            return
        if self.material is None:
            self.txt_material.setText("")
            set_invalid(self.txt_cod, True)
            self._message("Código inexistente. Verifique se foi digitado corretamente.")
        else:
            self.txt_material.setText(f"{self.material.descricao}  ·  {self.material.espessura} mm")
            set_invalid(self.txt_cod, False)
            self._message("" if self.material.ativo else "Atenção: material inativo.", "Muted")
        self.bt_save.setEnabled(self.material is not None)

    # ---------------------------------------------------------------- salvar
    def _measure(self, edit: QLineEdit, name: str) -> float:
        try:
            return parse_float(edit.text())
        except ValueError:
            set_invalid(edit, True)
            edit.setFocus()
            raise RegraDeNegocioError(f"{name} inválida.") from None

    def _save(self) -> None:
        if self.material is None:
            return
        try:
            largura = self._measure(self.txt_largura, "Largura")
            altura = self._measure(self.txt_altura, "Altura")
            self.service.validar_medidas(largura, altura)
        except RegraDeNegocioError as exc:
            self._message(str(exc))
            return

        if not confirm(self, "Novo retalho",
                       f"Lançar retalho {largura:g} × {altura:g} de {self.material.descricao}?"):
            return
        try:
            novo_id = self.service.lancar_retalho(
                self.material.codigo, largura, altura, self.txt_setor.text()
            )
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Novo retalho", exc)
            return

        self.changed = True
        self._reset()
        self._message(f"✔ Retalho {novo_id} lançado com sucesso. Pronto para o próximo.", "Ok")

    def _reset(self) -> None:
        for edit in (self.txt_barcode, self.txt_cod, self.txt_largura, self.txt_altura):
            edit.clear()
        self._clear_material()
        self.txt_barcode.setFocus()
