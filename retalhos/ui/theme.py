"""Tema visual: paletas clara e escura + folha de estilo Qt.

O tema é trocado em tempo de execução por :func:`apply_theme`. As cores de linha
(``ROW_*``) são objetos ``QColor`` alterados no lugar, por isso quem os importou
passa a usar as cores do tema novo automaticamente.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QWidget

THEME_LIGHT = "Claro"
THEME_DARK = "Escuro"
THEME_AUTO = "Automático"
THEMES = (THEME_LIGHT, THEME_DARK, THEME_AUTO)

# cores de destaque (iguais nos dois temas)
PRIMARY = "#2563eb"
PRIMARY_HOVER = "#1d4ed8"
DANGER = "#dc2626"
SUCCESS = "#16a34a"
WARNING = "#d97706"


@dataclass(frozen=True)
class Palette:
    dark: bool
    bg: str
    surface: str
    border: str
    dialog_border: str
    text: str
    muted: str
    header_bg: str
    header_text: str
    grid: str
    alternate: str
    hover: str
    pressed: str
    selection: str
    disabled_bg: str
    disabled_text: str
    readonly_bg: str
    invalid_bg: str
    danger_border: str
    danger_hover: str
    primary_disabled: str
    scrollbar: str
    scrollbar_hover: str
    ok: str
    fail: str
    row_reserved: str
    row_full_sheet: str
    row_inactive: str
    row_error: str


LIGHT = Palette(
    dark=False, bg="#f3f5f9", surface="#ffffff", border="#dde2ea", dialog_border="#cfd6e1",
    text="#1f2937", muted="#6b7280", header_bg="#f7f9fc", header_text="#374151", grid="#eef1f5",
    alternate="#fafbfd", hover="#eef2f7", pressed="#e2e8f0", selection="#dbe7ff",
    disabled_bg="#f1f3f6", disabled_text="#a0a7b4", readonly_bg="#f1f3f6", invalid_bg="#fff5f5",
    danger_border="#f3b4b4", danger_hover="#fdecec", primary_disabled="#9db6ee",
    scrollbar="#c9d0db", scrollbar_hover="#aab3c2", ok="#16a34a", fail="#dc2626",
    row_reserved="#fff3bf", row_full_sheet="#ffd8b5", row_inactive="#e5e7eb", row_error="#fde2e2",
)

DARK = Palette(
    dark=True, bg="#15171c", surface="#1e2128", border="#2f343e", dialog_border="#3a404c",
    text="#e5e7eb", muted="#9aa3b2", header_bg="#252932", header_text="#cfd5df", grid="#2a2e37",
    alternate="#1b1e24", hover="#2a2f3a", pressed="#333946", selection="#2b3d63",
    disabled_bg="#22252c", disabled_text="#5f6673", readonly_bg="#22252c", invalid_bg="#3a1f22",
    danger_border="#7f2d2d", danger_hover="#3a1f22", primary_disabled="#2c3e66",
    scrollbar="#3a404c", scrollbar_hover="#4b5260", ok="#4ade80", fail="#f87171",
    row_reserved="#4a4016", row_full_sheet="#56331a", row_inactive="#30333a", row_error="#5a2428",
)

# cores de linha das tabelas (atualizadas no lugar ao trocar o tema)
ROW_RESERVED = QColor(LIGHT.row_reserved)
ROW_FULL_SHEET = QColor(LIGHT.row_full_sheet)
ROW_INACTIVE = QColor(LIGHT.row_inactive)
ROW_ERROR = QColor(LIGHT.row_error)


# sobras que passam de um projeto do lote para outro (mesma ordem/nome de CORES_SOBRAS da capa)
_SOBRA_ESCURO = ["#4A4016", "#1F4D2E", "#1E3A5F", "#5A3A12", "#3B2F63", "#5A2440", "#3A3F47"]


def cor_sobra(indice: int) -> QColor:
    """Cor da n-ésima passagem de sobra entre projetos, no tema atual."""
    from ..services.capa_lote import CORES_SOBRAS  # cores claras são as mesmas da capa impressa

    if _current.dark:
        return QColor(_SOBRA_ESCURO[indice % len(_SOBRA_ESCURO)])
    return QColor("#" + CORES_SOBRAS[indice % len(CORES_SOBRAS)][1])


class _ThemeEvents(QObject):
    changed = Signal()


events = _ThemeEvents()
_current: Palette = LIGHT
_mode: str = THEME_LIGHT


def current() -> Palette:
    return _current


def current_mode() -> str:
    return _mode


def build_stylesheet(p: Palette) -> str:
    return f"""
* {{ font-family: "Segoe UI"; font-size: 10pt; color: {p.text}; }}
QMainWindow {{ background: {p.bg}; }}
QDialog {{ background: transparent; }}
QFrame#DialogFrame {{ background: {p.bg}; border: 1px solid {p.dialog_border}; border-radius: 12px; }}
QToolButton#TitleClose {{
    border: none; border-radius: 6px; min-width: 28px; min-height: 28px;
    color: {p.muted}; font-size: 11pt; background: transparent;
}}
QToolButton#TitleClose:hover {{ background: {p.danger_hover}; color: {DANGER}; }}
QToolButton#ThemeToggle {{
    border: 1px solid {p.border}; border-radius: 8px; background: {p.surface};
    min-width: 34px; min-height: 34px; font-size: 13pt;
}}
QToolButton#ThemeToggle:hover {{ background: {p.hover}; }}
QPlainTextEdit {{
    background: {p.surface}; border: 1px solid {p.border}; border-radius: 6px;
    font-family: Consolas; font-size: 9pt;
}}
QToolTip {{ background: {p.text}; color: {p.bg}; border: none; padding: 4px 8px; }}

QLabel#Title {{ font-size: 17pt; font-weight: 600; }}
QLabel#Subtitle, QLabel#Muted, QLabel#StatLabel {{ color: {p.muted}; }}
QLabel#StatLabel {{ font-size: 9pt; }}
QLabel#SectionTitle {{ font-size: 11pt; font-weight: 600; }}
QLabel#StatValue {{ font-size: 18pt; font-weight: 600; }}
QLabel#Error {{ color: {p.fail}; }}
QLabel#Ok {{ color: {p.ok}; font-weight: 600; }}
QLabel#Fail {{ color: {p.fail}; font-weight: 600; }}
QLabel#Alert {{ color: {p.fail}; }}

QFrame#Card {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 10px; }}

QPushButton {{
    background: {p.surface}; border: 1px solid {p.border}; border-radius: 6px;
    padding: 6px 14px; min-height: 22px;
}}
QPushButton:hover {{ background: {p.hover}; }}
QPushButton:pressed {{ background: {p.pressed}; }}
QPushButton:disabled {{ color: {p.disabled_text}; background: {p.disabled_bg}; }}
QPushButton[variant="primary"] {{ background: {PRIMARY}; border-color: {PRIMARY}; color: white; font-weight: 600; }}
QPushButton[variant="primary"]:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton[variant="primary"]:disabled {{
    background: {p.primary_disabled}; border-color: {p.primary_disabled}; color: {"#8a9bbf" if p.dark else "white"};
}}
QPushButton[variant="danger"] {{ background: {p.surface}; border-color: {p.danger_border}; color: {p.fail}; }}
QPushButton[variant="danger"]:hover {{ background: {p.danger_hover}; }}
QPushButton[variant="danger"]:disabled {{ color: {p.disabled_text}; border-color: {p.border}; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {p.surface}; border: 1px solid {p.border}; border-radius: 6px;
    padding: 5px 8px; min-height: 22px; selection-background-color: {PRIMARY}; selection-color: white;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {PRIMARY}; }}
QLineEdit:read-only {{ background: {p.readonly_bg}; color: {p.muted}; }}
QLineEdit[invalid="true"] {{ border: 1px solid {DANGER}; background: {p.invalid_bg}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {p.surface}; border: 1px solid {p.border}; selection-background-color: {p.selection};
    selection-color: {p.text};
}}

QTableView {{
    background: {p.surface}; border: 1px solid {p.border}; border-radius: 8px;
    gridline-color: {p.grid}; selection-background-color: {p.selection}; selection-color: {p.text};
    alternate-background-color: {p.alternate};
}}
QTableView::item {{ padding: 2px 6px; }}
QTableCornerButton::section {{ background: {p.header_bg}; border: none; }}
QHeaderView::section {{
    background: {p.header_bg}; border: none; border-bottom: 1px solid {p.border};
    border-right: 1px solid {p.grid}; padding: 6px; font-weight: 600; color: {p.header_text};
}}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle {{ background: {p.scrollbar}; border-radius: 4px; min-height: 30px; min-width: 30px; }}
QScrollBar::handle:hover {{ background: {p.scrollbar_hover}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenuBar {{ background: {p.surface}; border-bottom: 1px solid {p.border}; padding: 2px; }}
QMenuBar::item {{ padding: 5px 10px; border-radius: 4px; background: transparent; }}
QMenuBar::item:selected {{ background: {p.hover}; }}
QMenu {{ background: {p.surface}; border: 1px solid {p.border}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {p.selection}; }}
QMenu::item:disabled {{ color: {p.disabled_text}; }}
QMenu::separator {{ height: 1px; background: {p.border}; margin: 4px 6px; }}

QStatusBar {{ background: {p.surface}; border-top: 1px solid {p.border}; }}
QStatusBar QLabel {{ color: {p.muted}; padding: 0 8px; }}
QStatusBar QLabel#Alert {{ color: {p.fail}; }}

QProgressBar {{
    border: 1px solid {p.border}; border-radius: 6px; background: {p.surface};
    text-align: center; min-height: 18px;
}}
QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 5px; }}

QTabWidget::pane {{ border: none; top: -1px; }}
QTabBar::tab {{
    background: transparent; border: none; border-bottom: 2px solid transparent;
    padding: 7px 16px; margin-right: 4px; color: {p.muted}; font-weight: 600;
}}
QTabBar::tab:selected {{ color: {PRIMARY}; border-bottom: 2px solid {PRIMARY}; }}
QTabBar::tab:hover:!selected {{ color: {p.text}; }}

QSplitter::handle {{ background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; }}
"""


def _qpalette(p: Palette) -> QPalette:
    """Paleta Qt para o que a folha de estilo não cobre (caixas de seleção, itens nativos)."""
    pal = QPalette()
    role = QPalette.ColorRole
    for r, color in (
        (role.Window, p.bg), (role.WindowText, p.text), (role.Base, p.surface),
        (role.AlternateBase, p.alternate), (role.Text, p.text), (role.Button, p.surface),
        (role.ButtonText, p.text), (role.Highlight, PRIMARY), (role.HighlightedText, "#ffffff"),
        (role.ToolTipBase, p.text), (role.ToolTipText, p.bg), (role.PlaceholderText, p.muted),
        (role.Mid, p.border), (role.Midlight, p.hover), (role.Dark, p.border), (role.Light, p.surface),
    ):
        pal.setColor(r, QColor(color))
    for r in (role.Text, role.WindowText, role.ButtonText):
        pal.setColor(QPalette.ColorGroup.Disabled, r, QColor(p.disabled_text))
    return pal


def system_is_dark(app: QApplication) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:  # Qt < 6.5
        return False


def resolve(app: QApplication, mode: str) -> Palette:
    if mode == THEME_DARK:
        return DARK
    if mode == THEME_AUTO:
        return DARK if system_is_dark(app) else LIGHT
    return LIGHT


def apply_theme(app: QApplication, mode: str = THEME_LIGHT) -> None:
    """Aplica o tema (``Claro``, ``Escuro`` ou ``Automático``) em toda a aplicação."""
    global _current, _mode
    first = app.property("retalhos_theme_ready") is None
    if first:
        app.setStyle("Fusion")
        app.setFont(QFont("Segoe UI", 10))
        app.setProperty("retalhos_theme_ready", True)
        app.installEventFilter(_barra_titulo)
        try:  # no modo Automático, acompanha a troca de tema do Windows
            app.styleHints().colorSchemeChanged.connect(
                lambda *_: apply_theme(app, _mode) if _mode == THEME_AUTO else None
            )
        except AttributeError:
            pass

    _mode = mode if mode in THEMES else THEME_LIGHT
    _current = resolve(app, _mode)
    for color, value in ((ROW_RESERVED, _current.row_reserved), (ROW_FULL_SHEET, _current.row_full_sheet),
                         (ROW_INACTIVE, _current.row_inactive), (ROW_ERROR, _current.row_error)):
        color.setRgba(QColor(value).rgba())
    app.setPalette(_qpalette(_current))
    app.setStyleSheet(build_stylesheet(_current))
    for widget in app.allWidgets():
        QWidget.update(widget)  # chamada explícita: tabelas têm uma sobrecarga update(index)
    for janela in app.topLevelWidgets():
        if janela.isVisible():
            ajustar_barra_titulo(janela)
    events.changed.emit()


# atributos do DWM para a barra de título escura (20 no Windows 10 20H1+ e 11; 19 nos builds anteriores)
_DWMWA_DARK_MODE = (20, 19)
_SWP_FRAME = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020  # NOSIZE|NOMOVE|NOZORDER|NOACTIVATE|FRAMECHANGED
_WM_NCACTIVATE = 0x0086


def ajustar_barra_titulo(janela: QWidget) -> None:
    """Deixa a barra de título nativa do Windows (minimizar/fechar) no tema do app e redesenha na hora.

    Sem isso o Windows só repinta a barra quando a janela é redimensionada.
    """
    import sys
    if sys.platform != "win32" or janela.windowFlags() & Qt.WindowType.FramelessWindowHint:
        return
    import ctypes
    from ctypes import wintypes

    hwnd = wintypes.HWND(int(janela.winId()))
    valor = ctypes.c_int(1 if _current.dark else 0)
    try:
        dwm = ctypes.windll.dwmapi
        user32 = ctypes.windll.user32
    except OSError:
        return
    for atributo in _DWMWA_DARK_MODE:
        if dwm.DwmSetWindowAttribute(hwnd, atributo, ctypes.byref(valor), ctypes.sizeof(valor)) == 0:
            break
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, _SWP_FRAME)
    # o Windows 10 só repinta a legenda ao trocar o estado ativo/inativo: alterna e volta
    ativa = janela.isActiveWindow()
    user32.SendMessageW(hwnd, _WM_NCACTIVATE, not ativa, 0)
    user32.SendMessageW(hwnd, _WM_NCACTIVATE, ativa, 0)


class _BarraTituloAoExibir(QObject):
    """Janela nova (principal, atualizador) já abre com a barra de título no tema atual."""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.Show and isinstance(obj, QWidget) and obj.isWindow():
            ajustar_barra_titulo(obj)
        return False


_barra_titulo = _BarraTituloAoExibir()
