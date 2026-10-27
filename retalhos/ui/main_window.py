from __future__ import annotations

import subprocess
from datetime import datetime
from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QToolButton, QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, __version__
from ..config import Settings
from ..models import Retalho
from ..paths import app_dir
from ..services import EstoqueService, UsuarioService
from ..services.atualizacao import UPDATER_EXE, atualizar_atualizador
from .columns import retalho_columns, retalho_row_color
from .dialogs import (
    BaixaDialog, CadastroDialog, ConfigDialog, ConsumoDialog, LeitorXmlDialog, MateriaisDialog, NovoRetalhoDialog,
    ReservaDialog, ReservaManualDialog, LoginDialog, TrocarSenhaDialog, UsuariosDialog, HistoricoDialog,
    RemovidosDialog,
)
from . import theme
from .widgets import (
    BaseDialog, DataTable, ObjectTableModel, StatCard, Worker, app_icon, busy, button, card, confirm, info,
    label, show_exception, warning,
)

_FILTROS: dict[str, Callable[[Retalho], bool] | None] = {
    "Todos": None,
    "Disponíveis": lambda r: not r.reservado,
    "Reservados": lambda r: r.reservado,
}


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.service = EstoqueService(settings)
        self.setWindowTitle(f"{APP_NAME} — Controle de Retalhos")
        self.setWindowIcon(app_icon())
        self.resize(1360, 800)

        self._build_actions()
        self._build_menu()
        self._build_body()
        self._build_status()
        self.apply_settings()
        theme.events.changed.connect(self._on_theme_changed)
        self._on_theme_changed()
        self._refresh_worker: Worker | None = None
        self._refresh_text = ""
        self._ultimo_intervalo = settings.auto_refresh_minutes or 3.0
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_reload)
        self.act_auto_refresh.blockSignals(True)  # estado inicial vem do Settings, sem gravar de novo
        self._setup_auto_refresh()
        self.act_auto_refresh.blockSignals(False)
        QTimer.singleShot(0, self.reload)

    # =============================================================== layout
    def _action(self, text: str, slot: Callable[[], None], shortcut: str | QKeySequence = "",
                tip: str = "") -> QAction:
        act = QAction(text, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if tip:
            act.setStatusTip(tip)
        self.addAction(act)  # atalho ativo mesmo fora do menu
        return act

    def _build_actions(self) -> None:
        self.act_reload = self._action("Atualizar lista", self.reload, "F5")
        self.act_new = self._action("Novo retalho…", self.new_retalho, "Ctrl+N")
        self.act_delete = self._action("Excluir retalho", self.delete_selected, "Del")
        self.act_release = self._action("Liberar reserva", self.release_selected, "Ctrl+L")
        self.act_historico = self._action("Histórico do retalho…", self.show_historico, "Ctrl+H",
                                          "Quem lançou, reservou, liberou, deu baixa ou excluiu, e quando")
        self.act_reserve = self._action("Reservar retalho(s)…", self.reserve_selected, "Ctrl+Shift+R",
                                        "Reserva manual para um projeto (inclusive um que ainda será feito)")
        self.act_config = self._action("Configurações…", self.open_config)
        self.act_usuarios = self._action("Usuários…", self.open_usuarios)
        self.act_trocar_senha = self._action("Trocar minha senha…", self.trocar_senha)
        self.act_trocar_usuario = self._action("Trocar usuário…", self.trocar_usuario)
        self.act_quit = self._action("Sair", self.close, "Ctrl+Q")
        self.act_xml = self._action("Leitor de plano de corte…", lambda: self._open(LeitorXmlDialog))
        self.act_reserva = self._action("Reserva por projeto…", lambda: self._open(ReservaDialog))
        self.act_consumo = self._action(
            "Consumo do plano de corte (compras)…", lambda: self._open(ConsumoDialog), "Ctrl+K",
            "Chapas inteiras por material e retalhos usados em arquivos .cutplanning",
        )
        self.act_cadastro = self._action("Cadastro de cores…", lambda: self._open(CadastroDialog))
        self.act_materiais = self._action("Materiais…", lambda: self._open(MateriaisDialog))
        self.act_baixa = self._action("Baixa de reservas…", lambda: self._open(BaixaDialog))
        self.act_removidos = self._action("Retalhos removidos…", lambda: self._open(RemovidosDialog))
        self.act_rebuild = self._action(
            "Recriar arquivos do Corte Certo", self.rebuild_files, "Ctrl+R",
            "Apaga os RET*.TAB e recria a partir dos retalhos disponíveis no banco",
        )
        self.act_update = self._action("Atualizar sistema…", self.start_updater)
        self.act_update_updater = self._action("Atualizar o atualizador", self.update_updater, "Ctrl+U")
        self.act_about = self._action("Sobre", self.about)
        self.act_filter = self._action("Filtrar", lambda: self.txt_filter.setFocus(), "Ctrl+F")
        self.act_toggle_theme = self._action("Alternar claro/escuro", self.toggle_theme, "Ctrl+Shift+T")
        self.act_auto_refresh = QAction("Atualizar a lista automaticamente", self, checkable=True)
        self.act_auto_refresh.toggled.connect(self.toggle_auto_refresh)

    def _build_menu(self) -> None:
        bar = self.menuBar()
        m = bar.addMenu("&Arquivo")
        m.addActions([self.act_reload, self.act_new])
        m.addSeparator()
        m.addActions([self.act_trocar_senha, self.act_trocar_usuario])
        m.addSeparator()
        m.addAction(self.act_quit)

        self.menu_pcp = bar.addMenu("&PCP")
        self.menu_pcp.addActions([self.act_xml, self.act_consumo, self.act_reserva])
        self.menu_pcp.addSeparator()
        self.menu_pcp.addAction(self.act_cadastro)

        m = bar.addMenu("P&rodução")
        m.addActions([self.act_materiais, self.act_baixa, self.act_removidos])

        m = bar.addMenu("&Ferramentas")
        m.addAction(self.act_rebuild)
        m.addSeparator()
        m.addActions([self.act_update, self.act_update_updater])

        self.menu_admin = bar.addMenu("A&dministração")  # só aparece para administradores
        self.menu_admin.addActions([self.act_usuarios, self.act_config])

        m = bar.addMenu("&Exibir")
        tema = m.addMenu("Tema")
        self.theme_actions: dict[str, QAction] = {}
        group = QActionGroup(self)
        for mode in theme.THEMES:
            act = QAction(mode, self, checkable=True)
            act.triggered.connect(lambda _=False, md=mode: self.set_theme(md))
            group.addAction(act)
            tema.addAction(act)
            self.theme_actions[mode] = act
        m.addSeparator()
        m.addAction(self.act_toggle_theme)
        m.addSeparator()
        m.addAction(self.act_auto_refresh)

        m = bar.addMenu("A&juda")
        m.addAction(self.act_about)

    def _build_body(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(14)

        # cabeçalho + indicadores
        head = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(label("Controle de Retalhos", "Title"))
        self.lb_subtitle = label("", "Subtitle")
        titles.addWidget(self.lb_subtitle)
        head.addLayout(titles)
        head.addStretch()
        self.st_total = StatCard("Retalhos em estoque")
        self.st_free = StatCard("Disponíveis", "#16a34a")
        self.st_reserved = StatCard("Reservados", "#b45309")
        self.st_full = StatCard("Chapas inteiras", "#c2410c")
        for st in (self.st_total, self.st_free, self.st_reserved, self.st_full):
            st.setMinimumWidth(140)
            head.addWidget(st)
        self.bt_theme = QToolButton()
        self.bt_theme.setObjectName("ThemeToggle")
        self.bt_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bt_theme.clicked.connect(self.toggle_theme)
        head.addWidget(self.bt_theme, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(head)

        frame, layout = card()
        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Filtrar por material, código, setor, projeto…  (Ctrl+F)")
        self.txt_filter.setClearButtonEnabled(True)
        self.txt_filter.setMinimumWidth(340)
        tools.addWidget(self.txt_filter, 1)
        self.cb_status = QComboBox()
        self.cb_status.addItems(list(_FILTROS))
        tools.addWidget(self.cb_status)
        tools.addSpacing(12)

        self.bt_reload = button("Atualizar", icon="Infor_Icon.png", tooltip="Recarregar (F5)")
        self.bt_reload.clicked.connect(self.reload)
        self.bt_historico = button("Histórico", tooltip="Movimentação do retalho selecionado (Ctrl+H)")
        self.bt_historico.clicked.connect(self.show_historico)
        self.bt_reserve = button("Reservar…", tooltip="Reservar os retalhos selecionados para um projeto, "
                                                     "mesmo que ainda não exista (Ctrl+Shift+R)")
        self.bt_reserve.clicked.connect(self.reserve_selected)
        self.bt_release = button("Liberar reserva", tooltip="Devolve o retalho reservado ao estoque (Ctrl+L)")
        self.bt_release.clicked.connect(self.release_selected)
        self.bt_delete = button("Excluir", "danger", "Remove_Icon.png", "Excluir retalho selecionado (Del)")
        self.bt_delete.clicked.connect(self.delete_selected)
        self.bt_new = button("Novo retalho", "primary", "Add_Icon.png", "Lançar novo retalho (Ctrl+N)")
        self.bt_new.clicked.connect(self.new_retalho)
        for b in (self.bt_reload, self.bt_historico, self.bt_reserve, self.bt_release, self.bt_delete, self.bt_new):
            tools.addWidget(b)
        layout.addLayout(tools)

        self.model = ObjectTableModel(retalho_columns(), row_color=retalho_row_color(self.settings))
        self.table = DataTable(self.model)
        self.table.set_multi_selection()  # Ctrl/Shift para reservar vários de uma vez
        self.table.rowActivated.connect(self._on_activate)
        self.table.selectionModel().selectionChanged.connect(self._update_buttons)
        layout.addWidget(self.table, 1)

        legend = QHBoxLayout()
        legend.setSpacing(16)
        self._chips: list[tuple[QLabel, QColor]] = []
        for color, text in ((theme.ROW_RESERVED, "Reservado"), (theme.ROW_FULL_SHEET, "Chapa inteira"),
                            (theme.ROW_INACTIVE, "Material inativo")):
            legend.addWidget(self._legend_item(color, text))
        legend.addStretch()
        self.lb_shown = label("", "Muted")
        legend.addWidget(self.lb_shown)
        layout.addLayout(legend)
        root.addWidget(frame, 1)

        self.txt_filter.textChanged.connect(self._apply_filter)
        self.cb_status.currentTextChanged.connect(self._apply_filter)
        self.setCentralWidget(central)

    def _legend_item(self, color: QColor, text: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        chip = QLabel()
        chip.setFixedSize(14, 14)
        self._chips.append((chip, color))
        h.addWidget(chip)
        h.addWidget(label(text, "Muted"))
        return w

    # ================================================================ tema
    def set_theme(self, mode: str) -> None:
        theme.apply_theme(QApplication.instance(), mode)  # type: ignore[arg-type]
        if self.settings.theme != mode:
            self.settings.theme = mode
            try:
                self.settings.save()
            except OSError:
                pass  # a escolha vale nesta sessão mesmo sem gravar

    def toggle_theme(self) -> None:
        self.set_theme(theme.THEME_LIGHT if theme.current().dark else theme.THEME_DARK)

    def _on_theme_changed(self) -> None:
        p = theme.current()
        for chip, color in self._chips:
            chip.setStyleSheet(f"background: {color.name()}; border: 1px solid {p.border}; border-radius: 3px;")
        self.bt_theme.setText("☀" if p.dark else "🌙")
        self.bt_theme.setToolTip("Mudar para tema claro (Ctrl+Shift+T)" if p.dark
                                 else "Mudar para tema escuro (Ctrl+Shift+T)")
        for mode, act in self.theme_actions.items():
            act.setChecked(mode == theme.current_mode())

    @staticmethod
    def _set_alert(lbl: QLabel, alert: bool) -> None:
        lbl.setObjectName("Alert" if alert else "")
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    def _build_status(self) -> None:
        self.lb_db = QLabel()
        self.lb_cc = QLabel()
        sb = self.statusBar()
        sb.addWidget(self.lb_db)
        sb.addWidget(self.lb_cc)
        self.lb_refresh = QLabel()
        sb.addPermanentWidget(self.lb_refresh)
        sb.addPermanentWidget(QLabel(f"v{__version__}"))

    # ======================================================= estado/dados
    def apply_settings(self) -> None:
        """Aplica permissões e verifica o Corte Certo (após abrir ou alterar configurações)."""
        self.service = EstoqueService(self.settings)
        self.usuarios = UsuarioService(self.settings)
        self.model.row_color = retalho_row_color(self.settings)
        # permissões do usuário logado (tblUsuarios)
        self.menu_pcp.menuAction().setVisible(self.settings.menu_pcp_enabled)
        for act in (self.act_xml, self.act_consumo, self.act_reserva, self.act_cadastro):
            act.setEnabled(self.settings.menu_pcp_enabled)
        admin = self.settings.is_admin
        self.menu_admin.menuAction().setVisible(admin)
        for act in (self.act_usuarios, self.act_config, self.act_update_updater):
            act.setEnabled(admin)
        self.cc_ok = self.service.arquivos.instalado()
        usuario = self.settings.usuario
        papel = "  ·  administrador" if admin else ""
        self.lb_subtitle.setText(f"Usuário: {usuario.exibicao if usuario else '—'}{papel}")
        self.lb_cc.setText(
            "Corte Certo: conectado" if self.cc_ok else "⚠ Corte Certo não encontrado — lançamentos bloqueados"
        )
        self._set_alert(self.lb_cc, not self.cc_ok)
        self._update_buttons()

    def reload(self) -> None:
        """Atualização manual (botão/F5): mostra erro em janela se o banco falhar."""
        try:
            with busy():
                retalhos = self.service.listar_retalhos()
        except Exception as exc:  # noqa: BLE001
            self.model.set_rows([])
            self.lb_db.setText("⚠ Banco de dados indisponível")
            self._set_alert(self.lb_db, True)
            self._update_stats()
            show_exception(self, "Banco de dados", exc)
            return
        self._apply_rows(retalhos)

    def _apply_rows(self, retalhos: list[Retalho]) -> None:
        """Troca os dados da tabela mantendo filtro, seleção e posição da rolagem."""
        selected = self.table.selected()
        rolagem = self.table.verticalScrollBar().value()
        self.lb_db.setText(f"Banco: {self.settings.database_path}")
        self._set_alert(self.lb_db, False)
        self.model.set_rows(retalhos)
        self._update_stats()
        if selected is not None:
            self._select_id(selected.id)
        self.table.verticalScrollBar().setValue(rolagem)
        self._update_refresh_label(f"Atualizado às {datetime.now():%H:%M}")

    # ============================================ atualização automática
    def _setup_auto_refresh(self) -> None:
        minutos = self.settings.auto_refresh_minutes
        if minutos > 0:
            self.refresh_timer.start(int(minutos * 60_000))
        else:
            self.refresh_timer.stop()
        self.act_auto_refresh.setChecked(minutos > 0)
        self.act_auto_refresh.setText(
            f"Atualizar a lista automaticamente (a cada {minutos:g} min)" if minutos > 0
            else "Atualizar a lista automaticamente"
        )
        self._update_refresh_label()

    def toggle_auto_refresh(self, ligado: bool) -> None:
        if ligado:
            self.settings.auto_refresh_minutes = self._ultimo_intervalo or 3.0
        else:
            self._ultimo_intervalo = self.settings.auto_refresh_minutes or self._ultimo_intervalo
            self.settings.auto_refresh_minutes = 0
        try:
            self.settings.save()
        except OSError:
            pass  # vale para esta sessão mesmo sem gravar
        self._setup_auto_refresh()

    def _auto_reload(self) -> None:
        """Atualização periódica em segundo plano; nunca interrompe quem está usando a tela."""
        if (self._refresh_worker is not None and self._refresh_worker.isRunning()) \
                or QApplication.activeModalWidget() is not None or not self.isVisible():
            return  # janela/diálogo aberto ou consulta anterior ainda rodando: tenta no próximo ciclo
        service = self.service
        self._refresh_worker = Worker(lambda _progress: service.listar_retalhos(), self)
        self._refresh_worker.succeeded.connect(self._auto_reload_ok)
        self._refresh_worker.failed.connect(self._auto_reload_falhou)
        self._refresh_worker.start()

    def _auto_reload_ok(self, retalhos: list[Retalho]) -> None:
        if QApplication.activeModalWidget() is not None:
            return  # um diálogo abriu enquanto a consulta rodava: não mexe na tela agora
        self._apply_rows(retalhos)

    def _auto_reload_falhou(self, _exc: Exception) -> None:
        # sem janela de erro a cada ciclo: só avisa na barra de status e tenta de novo depois
        self.lb_db.setText(f"⚠ Banco indisponível (tentativa automática às {datetime.now():%H:%M})")
        self._set_alert(self.lb_db, True)

    def _update_refresh_label(self, texto: str | None = None) -> None:
        if texto is not None:
            self._refresh_text = texto
        minutos = self.settings.auto_refresh_minutes
        sufixo = f"  ·  automático a cada {minutos:g} min" if minutos > 0 else ""
        self.lb_refresh.setText(f"{self._refresh_text}{sufixo}")

    def _select_id(self, retalho_id: int) -> None:
        for row in range(self.table.proxy.rowCount()):
            if self.table.proxy.source_row(row).id == retalho_id:
                self.table.selectRow(row)
                return

    def _apply_filter(self) -> None:
        self.table.proxy.set_text(self.txt_filter.text())
        self.table.proxy.set_predicate(_FILTROS[self.cb_status.currentText()])
        self._update_stats()

    def _update_stats(self) -> None:
        rows = self.model.rows()
        st = self.settings
        self.st_total.set(len(rows))
        self.st_reserved.set(sum(r.reservado for r in rows))
        self.st_free.set(sum(not r.reservado for r in rows))
        self.st_full.set(sum(r.chapa_inteira(st.max_width, st.max_height) for r in rows))
        self.lb_shown.setText(f"Exibindo {self.table.proxy.rowCount()} de {len(rows)}")
        self._update_buttons()

    def _update_buttons(self, *_: object) -> None:
        selecionados = self.table.selected_rows()
        # excluir/liberar: um retalho por vez (evita engano com vários selecionados)
        r = selecionados[0] if len(selecionados) == 1 else None
        self.act_new.setEnabled(self.cc_ok)
        self.act_rebuild.setEnabled(self.cc_ok and self.settings.is_admin)  # apaga e recria os RET*.TAB
        self.act_delete.setEnabled(self.cc_ok and r is not None and not r.reservado)
        self.act_release.setEnabled(
            self.cc_ok and r is not None and r.reservado and self.settings.allow_remove_reserve
        )
        self.act_reserve.setEnabled(
            self.settings.allow_manual_reserve and self.cc_ok and bool(selecionados)
            and not any(x.reservado for x in selecionados)
        )
        self.bt_new.setEnabled(self.act_new.isEnabled())
        self.bt_delete.setEnabled(self.act_delete.isEnabled())
        self.bt_release.setEnabled(self.act_release.isEnabled())
        self.bt_release.setVisible(self.settings.allow_remove_reserve)
        self.bt_reserve.setEnabled(self.act_reserve.isEnabled())
        self.act_historico.setEnabled(r is not None)
        self.bt_historico.setEnabled(r is not None)
        self.bt_reserve.setVisible(self.settings.allow_manual_reserve)  # sem permissão: nem aparece
        n = len(selecionados)
        self.bt_reserve.setText(f"Reservar {n}…" if n > 1 else "Reservar…")

    # ================================================================ ações
    def _open(self, dialog_cls: type[BaseDialog]) -> None:
        dlg = dialog_cls(self.service, parent=self)
        dlg.exec()
        if dlg.changed:
            self.reload()

    def _on_activate(self, retalho: Retalho) -> None:
        # duplo clique em retalho reservado libera a reserva (comportamento da versão anterior)
        if retalho.reservado and self.act_release.isEnabled():
            self.release_selected()

    def new_retalho(self) -> None:
        if self.act_new.isEnabled():
            self._open(NovoRetalhoDialog)

    def delete_selected(self) -> None:
        r = self.table.selected()
        if r is None or not self.act_delete.isEnabled():
            return
        if not confirm(self, "Excluir retalho",
                       f"Excluir o retalho {r.id} — {r.descricao} {r.largura:g} × {r.altura:g}?\n\n"
                       "Ele deixa de aparecer no sistema; a exclusão fica registrada com data/hora e usuário.",
                       default_yes=False):
            return
        try:
            self.service.excluir_retalho(r)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Excluir retalho", exc)
            return
        self.reload()
        self.statusBar().showMessage(f"Retalho {r.id} excluído.", 5000)

    def show_historico(self) -> None:
        selecionados = self.table.selected_rows()
        if len(selecionados) == 1:
            HistoricoDialog(self.service, selecionados[0], self).exec()

    def reserve_selected(self) -> None:
        """Reserva manual: projeto livre, sem depender de pedido (PED) ou plano de corte."""
        selecionados = self.table.selected_rows()
        if not selecionados or not self.act_reserve.isEnabled():
            return
        dlg = ReservaManualDialog(selecionados, self)
        if not dlg.exec():
            return
        try:
            with busy():
                resultado = self.service.reservar_manual(dlg.projeto, selecionados)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Reservar retalho", exc)
            self.reload()  # a lista pode estar desatualizada (ex.: outra máquina reservou)
            return
        self.reload()
        self.statusBar().showMessage(
            f"{resultado.reservados} retalho(s) reservado(s) para {dlg.projeto.upper()}.", 8000
        )

    def release_selected(self) -> None:
        r = self.table.selected()
        if r is None or not self.act_release.isEnabled():
            return
        if not confirm(self, "Liberar reserva",
                       f"Remover a reserva do projeto {r.reserva} e devolver o retalho {r.id} ao estoque?"):
            return
        try:
            self.service.liberar_reserva(r)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Liberar reserva", exc)
            return
        self.reload()
        info(self, "Liberar reserva", "Retalho disponível no estoque.")

    def rebuild_files(self) -> None:
        if not self.act_rebuild.isEnabled():
            return
        if not confirm(
            self, "Recriar arquivos",
            "Recriar os arquivos de retalho do Corte Certo a partir do banco de dados?\n\n"
            "Todos os arquivos RET*.TAB serão apagados e regravados apenas com os retalhos disponíveis.",
            default_yes=False,
        ):
            return
        try:
            with busy():
                total = self.service.recriar_arquivos()
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Recriar arquivos", exc)
            return
        info(self, "Recriar arquivos", f"Arquivos gerados com sucesso ({total} materiais).")

    def open_config(self) -> None:
        if not self.settings.is_admin:
            return
        dlg = ConfigDialog(self.settings, self)
        if dlg.exec():
            self.apply_settings()
            self.reload()

    # ============================================================== usuário
    def open_usuarios(self) -> None:
        if not self.settings.is_admin:
            return
        dlg = UsuariosDialog(self.usuarios, self.settings.usuario, self)
        dlg.exec()
        if dlg.changed:  # o admin alterou as próprias permissões/nome
            self.apply_settings()

    def trocar_senha(self) -> None:
        if self.settings.usuario is not None:
            if TrocarSenhaDialog(self.usuarios, self.settings.usuario, parent=self).exec():
                info(self, "Trocar senha", "Senha alterada.")

    def trocar_usuario(self) -> None:
        """Outro usuário entra nesta mesma janela; cancelar mantém o usuário atual."""
        dlg = LoginDialog(self.usuarios, self.settings, self)
        dlg.txt_login.clear()
        dlg.txt_login.setFocus()
        if dlg.exec() and dlg.usuario is not None:
            self.settings.usuario = dlg.usuario
            self.apply_settings()
            self.reload()
            self.statusBar().showMessage(f"Usuário: {dlg.usuario.exibicao}", 6000)

    def start_updater(self) -> None:
        exe = app_dir() / UPDATER_EXE
        if not exe.is_file():
            warning(self, "Atualização", f"Atualizador não encontrado:\n{exe}")
            return
        subprocess.Popen([str(exe)], cwd=str(app_dir()))  # noqa: S603

    def update_updater(self) -> None:
        if not confirm(self, "Atualização", "Atualizar o programa de atualização (Update.exe)?"):
            return
        try:
            destino = atualizar_atualizador(self.settings, app_dir())
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Atualização", exc)
            return
        info(self, "Atualização", f"Atualizador copiado para:\n{destino}")

    def about(self) -> None:
        info(
            self, "Sobre",
            f"{APP_NAME} {__version__}\n\nControle de estoque de retalhos integrado ao Corte Certo Plus.",
        )

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape and self.txt_filter.text():
            self.txt_filter.clear()
            return
        super().keyPressEvent(event)
