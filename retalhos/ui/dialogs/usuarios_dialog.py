"""Administração de usuários (somente administradores)."""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QCheckBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget

from ...models import Usuario
from ...services import UsuarioService
from ...services.usuarios import SENHA_MINIMA
from ..theme import ROW_INACTIVE
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, UpperLineEdit, busy, button, card, info, label,
    show_exception,
)

_PERMISSOES = [
    ("admin", "Administrador", "Tudo: usuários, configurações e recriar arquivos do Corte Certo"),
    ("pcp", "PCP", "Menu PCP: plano de corte, consumo/compras, reservas e cadastro de cores"),
    ("remover_reserva", "Remover reserva", "Liberar reserva de retalho (devolver ao estoque)"),
    ("reservar_manual", "Reservar manual", "Botão Reservar… na tela principal (projeto livre)"),
]


def _sim(valor: bool) -> str:
    return "✔" if valor else ""


class UsuariosDialog(BaseDialog):
    def __init__(self, service: UsuarioService, admin: Usuario, parent: QWidget | None = None) -> None:
        super().__init__("Usuários", "Cadastro de usuários e permissões (valem em qualquer computador).",
                         parent, resizable=True)
        self.service = service
        self.admin = admin
        self.resize(920, 520)
        self.model = ObjectTableModel(
            [
                Column("Login", lambda u: u.login, ALIGN_LEFT, width=120),
                Column("Nome", lambda u: u.nome, ALIGN_LEFT, stretch=True),
                Column("Admin", lambda u: _sim(u.admin), width=60),
                Column("PCP", lambda u: _sim(u.pcp), width=50),
                Column("Remover reserva", lambda u: _sim(u.remover_reserva), width=115),
                Column("Reservar manual", lambda u: _sim(u.reservar_manual), width=115),
                Column("Ativo", lambda u: _sim(u.ativo), width=55),
                Column("Último acesso", lambda u: u.ultimo_acesso, width=130),
            ],
            row_color=lambda u: None if u.ativo else ROW_INACTIVE,
        )
        self.table = DataTable(self.model)
        self.table.rowActivated.connect(self._editar)
        self.table.selectionModel().selectionChanged.connect(self._atualizar_botoes)
        self.body.addWidget(self.table, 1)

        bt_novo = button("Novo usuário…", "primary")
        bt_novo.clicked.connect(self._novo)
        self.bt_editar = button("Editar…")
        self.bt_editar.clicked.connect(lambda: self._editar(self.table.selected()))
        self.bt_senha = button("Redefinir senha…")
        self.bt_senha.clicked.connect(self._redefinir_senha)
        bt_fechar = button("Fechar")
        bt_fechar.clicked.connect(self.reject)
        for w in (bt_novo, self.bt_editar, self.bt_senha):
            self.footer.addWidget(w)
        self.footer.addStretch()
        self.footer.addWidget(bt_fechar)
        self.carregar()

    def carregar(self) -> None:
        try:
            with busy():
                self.model.set_rows(self.service.listar(self.admin))
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Usuários", exc)
        self._atualizar_botoes()

    def _atualizar_botoes(self, *_: object) -> None:
        tem = self.table.selected() is not None
        self.bt_editar.setEnabled(tem)
        self.bt_senha.setEnabled(tem)

    def _novo(self) -> None:
        dlg = UsuarioEditDialog(None, self)
        if dlg.exec():
            try:
                novo = self.service.criar(self.admin, dlg.usuario, dlg.senha)
            except Exception as exc:  # noqa: BLE001
                show_exception(self, "Novo usuário", exc)
                return
            info(self, "Novo usuário", f"Usuário {novo.login} cadastrado.\n"
                                       "Na primeira entrada ele vai cadastrar a própria senha.")
            self.carregar()

    def _editar(self, usuario: Usuario | None) -> None:
        if usuario is None:
            return
        dlg = UsuarioEditDialog(usuario, self)
        if dlg.exec():
            try:
                self.service.atualizar(self.admin, dlg.usuario)
            except Exception as exc:  # noqa: BLE001
                show_exception(self, "Editar usuário", exc)
                return
            if dlg.usuario.id == self.admin.id:  # as permissões do próprio admin valem já nesta sessão
                for campo in ("nome", "pcp", "remover_reserva", "reservar_manual"):
                    setattr(self.admin, campo, getattr(dlg.usuario, campo))
                self.changed = True
            self.carregar()

    def _redefinir_senha(self) -> None:
        usuario = self.table.selected()
        if usuario is None:
            return
        dlg = SenhaTemporariaDialog(usuario, self)
        if dlg.exec():
            try:
                self.service.redefinir_senha(self.admin, usuario, dlg.senha)
            except Exception as exc:  # noqa: BLE001
                show_exception(self, "Redefinir senha", exc)
                return
            info(self, "Redefinir senha", f"Senha temporária definida para {usuario.login}.\n"
                                          "No próximo acesso ele vai cadastrar uma nova senha.")


class UsuarioEditDialog(BaseDialog):
    """Novo usuário (com senha temporária) ou edição de nome/permissões/ativo."""

    def __init__(self, usuario: Usuario | None, parent: QWidget | None = None) -> None:
        novo = usuario is None
        super().__init__("Novo usuário" if novo else f"Editar {usuario.login}",
                         "O login não pode ser alterado depois." if novo else "", parent)
        self.original = usuario or Usuario(0, "", "")
        self.usuario = self.original
        self.senha = ""
        self.setMinimumWidth(580)

        frame, layout = card()
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.txt_login = UpperLineEdit(self.original.login)
        self.txt_login.setMaxLength(30)
        self.txt_login.setReadOnly(not novo)
        self.txt_nome = UpperLineEdit(self.original.nome)
        self.txt_nome.setMaxLength(60)
        self.txt_nome.setPlaceholderText("Nome que aparece como Responsável")
        form.addRow("Login:", self.txt_login)
        form.addRow("Nome:", self.txt_nome)
        self.txt_senha = QLineEdit()
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_senha.setPlaceholderText(f"Temporária, mínimo {SENHA_MINIMA} caracteres")
        if novo:
            form.addRow("Senha inicial:", self.txt_senha)
        layout.addLayout(form)

        layout.addWidget(label("Permissões", "SectionTitle"))
        caixas = QVBoxLayout()
        self.chk: dict[str, QCheckBox] = {}
        for campo, titulo, descricao in _PERMISSOES:
            chk = QCheckBox(titulo)
            chk.setChecked(getattr(self.original, campo))
            chk.setToolTip(descricao)
            caixas.addWidget(chk)
            desc = label(descricao, "Muted")
            desc.setWordWrap(True)
            desc.setContentsMargins(24, 0, 0, 4)
            caixas.addWidget(desc)
            self.chk[campo] = chk
        self.chk_ativo = QCheckBox("Usuário ativo (pode entrar no sistema)")
        self.chk_ativo.setChecked(self.original.ativo)
        caixas.addSpacing(6)
        caixas.addWidget(self.chk_ativo)
        layout.addLayout(caixas)
        self.body.addWidget(frame)
        self.lb_erro = label("", "Error")
        self.body.addWidget(self.lb_erro)

        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        bt_ok = button("Salvar", "primary")
        bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(bt_ok)
        (self.txt_login if novo else self.txt_nome).setFocus()

    def _ok(self) -> None:
        if not self.txt_login.text().strip():
            self.lb_erro.setText("Informe o login.")
            return
        if self.original.id == 0 and len(self.txt_senha.text()) < SENHA_MINIMA:
            self.lb_erro.setText(f"A senha inicial deve ter pelo menos {SENHA_MINIMA} caracteres.")
            return
        self.usuario = replace(
            self.original, login=self.txt_login.text().strip(), nome=self.txt_nome.text().strip(),
            ativo=self.chk_ativo.isChecked(), **{campo: chk.isChecked() for campo, chk in self.chk.items()},
        )
        self.senha = self.txt_senha.text()
        self.accept()


class SenhaTemporariaDialog(BaseDialog):
    def __init__(self, usuario: Usuario, parent: QWidget | None = None) -> None:
        super().__init__("Redefinir senha", f"Senha temporária para {usuario.login}. "
                                            "Ele vai cadastrar uma nova no próximo acesso.", parent)
        self.senha = ""
        self.setMinimumWidth(440)
        frame, layout = card()
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.txt_senha = QLineEdit()
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_conf = QLineEdit()
        self.txt_conf.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Senha temporária:", self.txt_senha)
        form.addRow("Confirmar:", self.txt_conf)
        layout.addLayout(form)
        self.body.addWidget(frame)
        self.lb_erro = label("", "Error")
        self.body.addWidget(self.lb_erro)
        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        bt_ok = button("Definir senha", "primary")
        bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(bt_ok)
        self.txt_senha.setFocus()

    def _ok(self) -> None:
        if self.txt_senha.text() != self.txt_conf.text():
            self.lb_erro.setText("As senhas não conferem.")
            return
        if len(self.txt_senha.text()) < SENHA_MINIMA:
            self.lb_erro.setText(f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres.")
            return
        self.senha = self.txt_senha.text()
        self.accept()

