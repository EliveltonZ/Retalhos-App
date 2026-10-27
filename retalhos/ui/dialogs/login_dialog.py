"""Entrada no sistema: login, cadastro do primeiro administrador e troca de senha."""
from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from ...config import Settings
from ...models import Usuario
from ...services import RegraDeNegocioError, UsuarioService
from ...services.usuarios import SENHA_MINIMA
from ..widgets import BaseDialog, UpperLineEdit, busy, button, card, label, show_exception


def _senha(placeholder: str = "") -> QLineEdit:
    campo = QLineEdit()
    campo.setEchoMode(QLineEdit.EchoMode.Password)
    campo.setPlaceholderText(placeholder)
    return campo


def _form() -> tuple[QWidget, QFormLayout]:
    frame, layout = card()
    form = QFormLayout()
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    form.setSpacing(10)
    layout.addLayout(form)
    return frame, form


class _ComMensagem(BaseDialog):
    """Diálogo com uma linha de erro em vermelho acima dos botões."""

    def _montar_mensagem(self) -> None:
        self.lb_erro = label("", "Error")
        self.lb_erro.setWordWrap(True)
        self.body.addWidget(self.lb_erro)

    def erro(self, texto: str) -> None:
        self.lb_erro.setText(texto)


class LoginDialog(_ComMensagem):
    def __init__(self, service: UsuarioService, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__("Retalhos", "Entre com seu usuário e senha.", parent)
        self.service = service
        self.settings = settings
        self.usuario: Usuario | None = None
        self.setMinimumWidth(420)

        frame, form = _form()
        self.txt_login = UpperLineEdit(settings.last_login)
        self.txt_login.setPlaceholderText("Usuário")
        self.txt_senha = _senha("Senha")
        form.addRow("Usuário:", self.txt_login)
        form.addRow("Senha:", self.txt_senha)
        self.body.addWidget(frame)
        self._montar_mensagem()

        bt_sair = button("Sair")
        bt_sair.clicked.connect(self.reject)
        self.bt_entrar = button("Entrar", "primary")
        self.bt_entrar.setDefault(True)  # Enter entra
        self.bt_entrar.clicked.connect(self._entrar)
        self.footer.addStretch()
        self.footer.addWidget(bt_sair)
        self.footer.addWidget(self.bt_entrar)
        (self.txt_senha if self.txt_login.text() else self.txt_login).setFocus()

    def _entrar(self) -> None:
        login, senha = self.txt_login.text().strip(), self.txt_senha.text()
        if not login or not senha:
            self.erro("Informe usuário e senha.")
            return
        try:
            with busy():
                usuario = self.service.autenticar(login, senha)
        except RegraDeNegocioError as exc:
            self.erro(str(exc))
            self.txt_senha.clear()
            self.txt_senha.setFocus()
            return
        except Exception as exc:  # noqa: BLE001 - banco fora do ar etc.
            show_exception(self, "Login", exc)
            return
        if usuario.trocar_senha:
            # senha temporária (definida pelo administrador): obriga a cadastrar a própria
            if not TrocarSenhaDialog(self.service, usuario, obrigatoria=True, parent=self).exec():
                self.erro("É preciso cadastrar uma nova senha para continuar.")
                self.txt_senha.clear()
                return
        self.usuario = usuario
        self.settings.last_login = usuario.login
        try:
            self.settings.save()
        except OSError:
            pass  # só serve para sugerir o usuário na próxima vez
        self.accept()


class PrimeiroAdminDialog(_ComMensagem):
    """Aparece uma única vez: banco sem nenhum usuário cadastrado."""

    def __init__(self, service: UsuarioService, parent: QWidget | None = None) -> None:
        super().__init__(
            "Primeiro acesso",
            "Nenhum usuário cadastrado ainda. Crie o administrador do sistema: ele terá todas as "
            "permissões e poderá cadastrar os demais usuários.",
            parent,
        )
        self.service = service
        self.usuario: Usuario | None = None
        self.setMinimumWidth(480)
        frame, form = _form()
        self.txt_login = UpperLineEdit()
        self.txt_login.setMaxLength(30)
        self.txt_nome = UpperLineEdit()
        self.txt_nome.setMaxLength(60)
        self.txt_nome.setPlaceholderText("Nome que aparece como Responsável")
        self.txt_senha = _senha(f"Mínimo {SENHA_MINIMA} caracteres")
        self.txt_conf = _senha()
        form.addRow("Login:", self.txt_login)
        form.addRow("Nome:", self.txt_nome)
        form.addRow("Senha:", self.txt_senha)
        form.addRow("Confirmar senha:", self.txt_conf)
        self.body.addWidget(frame)
        self._montar_mensagem()
        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        bt_ok = button("Criar administrador", "primary")
        bt_ok.setDefault(True)
        bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(bt_ok)
        self.txt_login.setFocus()

    def _ok(self) -> None:
        if self.txt_senha.text() != self.txt_conf.text():
            self.erro("As senhas não conferem.")
            return
        try:
            with busy():
                self.usuario = self.service.criar_primeiro_admin(
                    self.txt_login.text(), self.txt_nome.text() or self.txt_login.text(), self.txt_senha.text())
        except RegraDeNegocioError as exc:
            self.erro(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Primeiro acesso", exc)
            return
        self.accept()


class TrocarSenhaDialog(_ComMensagem):
    def __init__(self, service: UsuarioService, usuario: Usuario, obrigatoria: bool = False,
                 parent: QWidget | None = None) -> None:
        super().__init__(
            "Nova senha" if obrigatoria else "Trocar senha",
            f"{usuario.login}: cadastre uma senha pessoal para continuar (a atual é temporária)."
            if obrigatoria else f"Trocar a senha de {usuario.login}.",
            parent,
        )
        self.service = service
        self.usuario = usuario
        self.obrigatoria = obrigatoria
        self.setMinimumWidth(440)
        frame, form = _form()
        self.txt_atual = _senha()
        self.txt_nova = _senha(f"Mínimo {SENHA_MINIMA} caracteres")
        self.txt_conf = _senha()
        if not obrigatoria:
            form.addRow("Senha atual:", self.txt_atual)
        form.addRow("Nova senha:", self.txt_nova)
        form.addRow("Confirmar:", self.txt_conf)
        self.body.addWidget(frame)
        self._montar_mensagem()
        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        bt_ok = button("Salvar senha", "primary")
        bt_ok.setDefault(True)
        bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(bt_ok)
        (self.txt_nova if obrigatoria else self.txt_atual).setFocus()

    def _ok(self) -> None:
        if self.txt_nova.text() != self.txt_conf.text():
            self.erro("As senhas não conferem.")
            return
        try:
            with busy():
                self.service.trocar_senha(self.usuario, None if self.obrigatoria else self.txt_atual.text(),
                                          self.txt_nova.text())
        except RegraDeNegocioError as exc:
            self.erro(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Trocar senha", exc)
            return
        self.accept()
