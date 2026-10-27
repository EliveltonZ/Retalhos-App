from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QWidget

from ...config import Settings
from ...db import Database
from ...services import ArquivosCorteCerto
from ..widgets import BaseDialog, busy, button, card, label, show_exception


class ConfigDialog(BaseDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__("Configurações", "Caminhos do Corte Certo e do banco de dados.", parent)
        self.settings = settings
        self.setMinimumWidth(640)

        frame, layout = card()
        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.txt_cc = QLineEdit(settings.corte_certo_dir)
        self.txt_cc.setPlaceholderText(r"\\SERVIDOR\corte_certo_plus\ ")
        bt_cc = button("Procurar…")
        bt_cc.clicked.connect(self._browse_cc)
        form.addRow("Pasta do Corte Certo:", self._row(self.txt_cc, bt_cc))

        self.txt_db = QLineEdit(settings.database_path)
        self.txt_db.setPlaceholderText(r"\\SERVIDOR\sistema\BDretalhos.accdb")
        bt_db = button("Procurar…")
        bt_db.clicked.connect(self._browse_db)
        form.addRow("Banco de dados:", self._row(self.txt_db, bt_db))
        layout.addLayout(form)
        self.body.addWidget(frame)

        status, status_layout = card()
        status_layout.addWidget(label("Diagnóstico", "SectionTitle"))
        self.lb_cc = label("…")
        self.lb_db = label("…")
        diag = QFormLayout()
        diag.addRow("Corte Certo:", self.lb_cc)
        diag.addRow("Banco de dados:", self.lb_db)
        status_layout.addLayout(diag)
        self.body.addWidget(status)

        bt_test = button("Testar")
        bt_test.clicked.connect(self.run_tests)
        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        bt_save = button("Salvar", "primary")
        bt_save.setDefault(True)
        bt_save.clicked.connect(self._save)
        self.footer.addWidget(bt_test)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(bt_save)

        self.run_tests()

    @staticmethod
    def _row(edit: QLineEdit, btn: QWidget) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit, 1)
        h.addWidget(btn)
        return w

    def _browse_cc(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Pasta do Corte Certo", self.txt_cc.text())
        if path:
            self.txt_cc.setText(path.replace("/", "\\").rstrip("\\") + "\\")

    def _browse_db(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Banco de dados", self.txt_db.text(), "Access (*.accdb *.mdb);;Todos (*.*)"
        )
        if path:
            self.txt_db.setText(path.replace("/", "\\"))

    def _candidate(self) -> Settings:
        s = Settings(**{k: v for k, v in vars(self.settings).items() if not k.startswith("_") and k != "path"})
        s.corte_certo_dir = self.txt_cc.text().strip()
        s.database_path = self.txt_db.text().strip()
        return s

    @staticmethod
    def _status(lbl, ok: bool, ok_text: str, fail_text: str) -> None:
        lbl.setText(f"✔ {ok_text}" if ok else f"✖ {fail_text}")
        lbl.setObjectName("Ok" if ok else "Fail")
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    def run_tests(self) -> None:
        s = self._candidate()
        with busy():
            cc_ok = ArquivosCorteCerto(s).instalado()
            db_ok = Database(s.database_path, s.database_password).test()
        self._status(self.lb_cc, cc_ok, f"{s.corte_certo_exe} encontrado", f"{s.corte_certo_exe} não encontrado")
        self._status(self.lb_db, db_ok, "Conectado", "Não foi possível conectar")

    def _save(self) -> None:
        try:
            self.settings.corte_certo_dir = self.txt_cc.text().strip()
            self.settings.database_path = self.txt_db.text().strip()
            self.settings.save()
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Configurações", exc)
            return
        self.changed = True
        self.accept()
