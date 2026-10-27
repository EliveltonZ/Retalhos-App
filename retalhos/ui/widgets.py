"""Componentes reutilizáveis da interface."""
from __future__ import annotations

import logging
import traceback
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

from PySide6.QtCore import (
    QAbstractTableModel, QEvent, QModelIndex, QObject, QRectF, QSortFilterProxyModel, Qt, QThread,
    Signal,
)
from PySide6.QtGui import (
    QBrush, QColor, QIcon, QKeySequence, QMouseEvent, QPainter, QPaintEvent, QPen, QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizeGrip, QTableView, QToolButton, QVBoxLayout, QWidget,
)

from ..db import DatabaseError
from ..paths import resource_path
from ..services import CorteCertoError, RegraDeNegocioError
from . import theme

log = logging.getLogger(__name__)
T = TypeVar("T")

ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
SORT_ROLE = Qt.ItemDataRole.UserRole + 1

# Erros esperados: mostrados sem detalhes técnicos
EXPECTED_ERRORS = (RegraDeNegocioError, CorteCertoError, DatabaseError, ValueError)


def app_icon() -> QIcon:
    return QIcon(str(resource_path("icon_retalho.ico")))


# ================================================================ mensagens
_OK = (("ok", "OK", "primary"),)


def choose(parent: QWidget | None, title: str, text: str, buttons: Sequence[tuple[str, str, str]],
           default: str | None = None, kind: str = "info", details: str = "") -> str | None:
    """Mostra uma mensagem com botões ``(chave, texto, variante)``; retorna a chave clicada."""
    dlg = MessageDialog(parent, title, text, kind, buttons, default, details)
    dlg.exec()
    return dlg.result_key


def info(parent: QWidget | None, title: str, text: str) -> None:
    choose(parent, title, text, _OK, "ok", "info")


def warning(parent: QWidget | None, title: str, text: str) -> None:
    choose(parent, title, text, _OK, "ok", "warning")


def error(parent: QWidget | None, title: str, text: str, details: str = "") -> None:
    choose(parent, title, text, _OK, "ok", "error", details)


def confirm(parent: QWidget | None, title: str, text: str, default_yes: bool = True) -> bool:
    buttons = (("no", "Não", ""), ("yes", "Sim", "primary"))
    return choose(parent, title, text, buttons, "yes" if default_yes else "no", "question") == "yes"


def show_exception(parent: QWidget | None, title: str, exc: BaseException) -> None:
    if isinstance(exc, EXPECTED_ERRORS):
        warning(parent, title, str(exc))
    else:
        log.exception("Erro inesperado: %s", title, exc_info=exc)
        error(parent, title, f"Ocorreu um erro inesperado:\n{exc}",
              "".join(traceback.format_exception(exc)))


@contextmanager
def busy() -> Iterator[None]:
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


# ================================================================== widgets
def button(text: str, variant: str = "", icon: str = "", tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    if variant:
        btn.setProperty("variant", variant)
    if icon:
        btn.setIcon(QIcon(str(resource_path(icon))))
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setAutoDefault(False)  # Enter em campos de texto não dispara botões
    return btn


def label(text: str = "", name: str = "") -> QLabel:
    lbl = QLabel(text)
    if name:
        lbl.setObjectName(name)
    return lbl


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    return frame, layout


class StatCard(QFrame):
    def __init__(self, title: str, accent: str = "") -> None:
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(0)
        self.value = label("–", "StatValue")
        if accent:
            self.value.setStyleSheet(f"color: {accent};")
        layout.addWidget(self.value)
        layout.addWidget(label(title, "StatLabel"))

    def set(self, value: int) -> None:
        self.value.setText(f"{value:,}".replace(",", "."))


def set_invalid(widget: QWidget, invalid: bool) -> None:
    widget.setProperty("invalid", "true" if invalid else "false")
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class UpperLineEdit(QLineEdit):
    """Campo que converte o texto digitado para maiúsculas mantendo o cursor."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.textEdited.connect(self._upper)

    def _upper(self, text: str) -> None:
        if text != text.upper():
            pos = self.cursorPosition()
            self.setText(text.upper())
            self.setCursorPosition(pos)


def parse_float(text: str) -> float:
    """Aceita vírgula ou ponto decimal."""
    return float(text.strip().replace(",", "."))


# ========================================================= modelo de tabela
@dataclass
class Column(Generic[T]):
    title: str
    value: Callable[[T], Any]
    align: Qt.AlignmentFlag = ALIGN_CENTER
    width: int | None = None
    stretch: bool = False


def _display(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _sort_key(value: Any) -> Any:
    if value is None or value == "":
        return -1e18
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, (int, float)):
        return float(value)
    return str(value).lower()


class ObjectTableModel(QAbstractTableModel):
    """Modelo de tabela sobre uma lista de objetos, com coluna de seleção opcional."""

    def __init__(
        self,
        columns: Sequence[Column[T]],
        checkable: bool = False,
        row_color: Callable[[T], QColor | None] | None = None,
        can_check: Callable[[T], bool] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.columns = list(columns)
        self.checkable = checkable
        self.row_color = row_color
        self.can_check = can_check or (lambda _: True)
        self._rows: list[T] = []
        self._checked: set[int] = set()

    # --- dados
    def set_rows(self, rows: Sequence[T], checked: Callable[[T], bool] | None = None) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self._checked = {i for i, r in enumerate(self._rows) if checked and checked(r) and self.can_check(r)}
        self.endResetModel()

    def rows(self) -> list[T]:
        return list(self._rows)

    def row(self, index: int) -> T:
        return self._rows[index]

    def checked_rows(self) -> list[T]:
        return [self._rows[i] for i in sorted(self._checked)]

    def set_all_checked(self, checked: bool) -> None:
        self._checked = {i for i, r in enumerate(self._rows) if self.can_check(r)} if checked else set()
        if self._rows:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._rows) - 1, 0))

    # --- Qt
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self.columns) + (1 if self.checkable else 0)

    def _column(self, col: int) -> Column[T] | None:
        if self.checkable:
            return None if col == 0 else self.columns[col - 1]
        return self.columns[col]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        column = self._column(section)
        return "" if column is None else column.title

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        obj = self._rows[index.row()]
        column = self._column(index.column())

        if role == Qt.ItemDataRole.BackgroundRole and self.row_color:
            color = self.row_color(obj)
            return QBrush(color) if color else None

        if column is None:  # coluna de seleção
            if role == Qt.ItemDataRole.CheckStateRole and self.can_check(obj):
                checked = index.row() in self._checked
                return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            if role == SORT_ROLE:
                return 1 if index.row() in self._checked else 0
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return _display(column.value(obj))
        if role == SORT_ROLE:
            return _sort_key(column.value(obj))
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return int(column.align)
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if self.checkable and index.column() == 0 and role == Qt.ItemDataRole.CheckStateRole:
            if Qt.CheckState(value) == Qt.CheckState.Checked:
                self._checked.add(index.row())
            else:
                self._checked.discard(index.row())
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if self.checkable and index.column() == 0 and self.can_check(self._rows[index.row()]):
            base |= Qt.ItemFlag.ItemIsUserCheckable
        return base


class FilterProxy(QSortFilterProxyModel):
    """Filtro por texto (todas as colunas) + predicado opcional."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.setSortRole(SORT_ROLE)
        self._text = ""
        self._predicate: Callable[[Any], bool] | None = None

    def set_text(self, text: str) -> None:
        self._text = text.strip().lower()
        self.invalidateFilter()

    def set_predicate(self, predicate: Callable[[Any], bool] | None) -> None:
        self._predicate = predicate
        self.invalidateFilter()

    def source_row(self, proxy_row: int) -> Any:
        model: ObjectTableModel = self.sourceModel()  # type: ignore[assignment]
        return model.row(self.mapToSource(self.index(proxy_row, 0)).row())

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: ObjectTableModel = self.sourceModel()  # type: ignore[assignment]
        if self._predicate and not self._predicate(model.row(source_row)):
            return False
        if not self._text:
            return True
        for col in range(model.columnCount()):
            value = model.data(model.index(source_row, col), Qt.ItemDataRole.DisplayRole)
            if value and self._text in str(value).lower():
                return True
        return False


class DataTable(QTableView):
    """Tabela pronta para uso com :class:`ObjectTableModel` + filtro/ordenação."""

    rowActivated = Signal(object)

    def __init__(self, model: ObjectTableModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.source = model
        self.proxy = FilterProxy(self)
        self.proxy.setSourceModel(model)
        self.setModel(self.proxy)

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(model.row_color is None)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(30)
        header = self.horizontalHeader()
        header.setHighlightSections(False)
        header.setDefaultAlignment(ALIGN_CENTER)
        header.setStretchLastSection(False)

        offset = 1 if model.checkable else 0
        if model.checkable:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            self.setColumnWidth(0, 36)
        for i, column in enumerate(model.columns):
            if column.stretch:
                header.setSectionResizeMode(i + offset, QHeaderView.ResizeMode.Stretch)
            elif column.width:
                self.setColumnWidth(i + offset, column.width)
        self.sortByColumn(-1, Qt.SortOrder.AscendingOrder)

        self.doubleClicked.connect(self._on_double_click)
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, self._activate_current,
                  context=Qt.ShortcutContext.WidgetShortcut)

    def _on_double_click(self, index: QModelIndex) -> None:
        if self.source.checkable and index.column() == 0:
            return
        self.rowActivated.emit(self.proxy.source_row(index.row()))

    def _activate_current(self) -> None:
        obj = self.selected()
        if obj is not None:
            self.rowActivated.emit(obj)

    def selected(self) -> Any | None:
        rows = self.selectionModel().selectedRows()
        if not rows:
            return None
        return self.proxy.source_row(rows[0].row())

    def selected_rows(self) -> list[Any]:
        """Todas as linhas selecionadas (na ordem da tela)."""
        rows = sorted(i.row() for i in self.selectionModel().selectedRows())
        return [self.proxy.source_row(r) for r in rows]

    def set_multi_selection(self, multipla: bool = True) -> None:
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection if multipla
                              else QAbstractItemView.SelectionMode.SingleSelection)

    def visible_rows(self) -> list[Any]:
        return [self.proxy.source_row(i) for i in range(self.proxy.rowCount())]


# ================================================================ diálogos
class RoundedDialog(QDialog):
    """Popup sem a moldura do Windows: cantos arredondados, sombra suave e cabeçalho arrastável."""

    RADIUS = 12
    SHADOW = 12

    def __init__(self, title: str, parent: QWidget | None = None, resizable: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowIcon(app_icon())
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        s = self.SHADOW
        outer.setContentsMargins(s, s - 4, s, s + 4)  # sombra levemente deslocada para baixo
        self.frame = QFrame()
        self.frame.setObjectName("DialogFrame")
        outer.addWidget(self.frame)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(20, 14, 14, 18)
        layout.setSpacing(14)
        self.header = QWidget()
        head = QHBoxLayout(self.header)
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        self.header_text = QVBoxLayout()
        self.header_text.setSpacing(2)
        head.addLayout(self.header_text, 1)
        bt_close = QToolButton()
        bt_close.setObjectName("TitleClose")
        bt_close.setText("✕")
        bt_close.setToolTip("Fechar (Esc)")
        bt_close.setCursor(Qt.CursorShape.PointingHandCursor)
        bt_close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        bt_close.clicked.connect(self.reject)
        head.addWidget(bt_close, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.header)

        self.content = QVBoxLayout()
        self.content.setContentsMargins(0, 0, 6, 0)  # compensa a margem menor do botão fechar
        self.content.setSpacing(12)
        layout.addLayout(self.content, 1)

        self._grip: QSizeGrip | None = None
        if resizable:
            self._grip = QSizeGrip(self.frame)
            self._grip.setFixedSize(16, 16)
            self.frame.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if obj is self.frame and event.type() == QEvent.Type.Resize and self._grip:
            self._grip.move(self.frame.width() - 18, self.frame.height() - 18)
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        pos = self.frame.mapFrom(self, event.position().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and self.header.geometry().contains(pos):
            self.windowHandle().startSystemMove()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(self.frame.geometry()).translated(0, 2)
        # no fundo escuro a sombra precisa ser mais forte para aparecer
        (r, g, b), intensity = ((0, 0, 0), 70) if theme.current().dark else ((15, 23, 42), 26)
        for i in range(1, self.SHADOW + 1):
            alpha = int(intensity * (1 - i / (self.SHADOW + 1)) ** 2)
            painter.setPen(QPen(QColor(r, g, b, alpha), 1.0))
            painter.drawRoundedRect(rect.adjusted(-i, -i, i, i), self.RADIUS + i, self.RADIUS + i)


class BaseDialog(RoundedDialog):
    """Diálogo com cabeçalho (título/subtítulo), corpo e rodapé de botões."""

    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None,
                 resizable: bool = False) -> None:
        super().__init__(title, parent, resizable)
        self.header_text.addWidget(label(title, "Title"))
        if subtitle:
            sub = label(subtitle, "Subtitle")
            sub.setWordWrap(True)
            self.header_text.addWidget(sub)
        self.body = QVBoxLayout()
        self.body.setSpacing(12)
        self.content.addLayout(self.body, 1)
        self.footer = QHBoxLayout()
        self.footer.setSpacing(8)
        self.content.addLayout(self.footer)
        self.changed = False  # indica à janela principal que deve recarregar


_MESSAGE_ICONS = {
    "info": ("i", "#2563eb"),
    "question": ("?", "#2563eb"),
    "warning": ("!", "#d97706"),
    "error": ("✕", "#dc2626"),
}


class MessageDialog(RoundedDialog):
    """Caixa de mensagem no mesmo visual dos diálogos. ``result_key`` = botão clicado (``None`` se fechada)."""

    def __init__(self, parent: QWidget | None, title: str, text: str, kind: str,
                 buttons: Sequence[tuple[str, str, str]], default: str | None, details: str = "") -> None:
        super().__init__(title, parent)
        self.result_key: str | None = None
        self.header_text.addWidget(label(title, "SectionTitle"))

        row = QHBoxLayout()
        row.setSpacing(14)
        symbol, color = _MESSAGE_ICONS.get(kind, _MESSAGE_ICONS["info"])
        icon = QLabel(symbol)
        icon.setFixedSize(34, 34)
        icon.setAlignment(ALIGN_CENTER)
        icon.setStyleSheet(
            f"background: {color}; color: white; border-radius: 17px; font-size: 14pt; font-weight: 700;"
        )
        row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setMinimumWidth(320)
        msg.setMaximumWidth(560)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(msg, 1)
        self.content.addLayout(row)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        if details:
            box = QPlainTextEdit(details)
            box.setReadOnly(True)
            box.setMinimumHeight(180)
            box.setVisible(False)
            self.content.addWidget(box)
            bt_details = button("Detalhes")
            bt_details.clicked.connect(lambda: (box.setVisible(not box.isVisible()), self.adjustSize()))
            footer.addWidget(bt_details)
        footer.addStretch()
        for key, text_, variant in buttons:
            btn = button(text_, variant)
            btn.clicked.connect(lambda _=False, k=key: self._finish(k))
            footer.addWidget(btn)
            if key == default:
                btn.setDefault(True)
                btn.setFocus()
        self.content.addLayout(footer)

    def _finish(self, key: str) -> None:
        self.result_key = key
        self.accept()


# =============================================================== threads
class Worker(QThread):
    """Executa ``fn(progress)`` fora da thread da interface."""

    progress = Signal(int, int)
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, fn: Callable[[Callable[[int, int], None]], Any], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            result = self._fn(self.progress.emit)
        except Exception as exc:  # noqa: BLE001 - repassado para a interface
            self.failed.emit(exc)
        else:
            self.succeeded.emit(result)
