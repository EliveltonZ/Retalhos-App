"""Atualização automática da lista principal (janela real, sem exibir na tela)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402

from retalhos.config import Settings  # noqa: E402
from retalhos.services import EstoqueService  # noqa: E402


@pytest.fixture(scope="module")
def app():
    from retalhos.app import create_app
    return create_app()


@pytest.fixture
def janela(app, settings):
    from retalhos.ui.main_window import MainWindow
    settings.save()
    w = MainWindow(settings)
    w.show()
    QApplication.processEvents()  # executa o carregamento inicial agendado pela janela
    yield w
    w.refresh_timer.stop()
    w.close()


def _rodar_auto(w):
    w._auto_reload()
    if w._refresh_worker is not None:
        w._refresh_worker.wait(10_000)
    QApplication.processEvents()


def test_intervalo_padrao_3_minutos(janela):
    assert janela.refresh_timer.isActive() and janela.refresh_timer.interval() == 180_000
    assert janela.act_auto_refresh.isChecked()
    assert "automático a cada 3 min" in janela.lb_refresh.text()


def test_atualiza_mantendo_filtro_e_selecao(janela, settings):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500)
    svc.lancar_retalho(20, 900, 400)
    janela.reload()
    janela.txt_filter.setText("BRANCO")
    janela._select_id(a)
    assert janela.table.proxy.rowCount() == 1

    svc.lancar_retalho(10, 800, 400)  # outra máquina lança um retalho
    _rodar_auto(janela)

    assert len(janela.model.rows()) == 3
    assert janela.txt_filter.text() == "BRANCO" and janela.table.proxy.rowCount() == 2
    assert janela.table.selected().id == a
    assert janela.lb_refresh.text().startswith("Atualizado às")


def test_nao_atualiza_com_janela_aberta(janela, settings):
    dlg = QDialog(janela)
    dlg.setModal(True)
    dlg.show()
    QApplication.processEvents()
    try:
        EstoqueService(settings).lancar_retalho(10, 1000, 500)
        _rodar_auto(janela)
        assert len(janela.model.rows()) == 0  # pulou este ciclo
    finally:
        dlg.close()
    _rodar_auto(janela)
    assert len(janela.model.rows()) == 1


def test_falha_no_banco_so_avisa_na_barra(janela, settings):
    janela.service.db.path = str(settings.path.parent / "nao_existe.db")
    _rodar_auto(janela)  # não abre janela de erro (bloquearia o teste)
    assert "tentativa automática" in janela.lb_db.text() and janela.lb_db.objectName() == "Alert"


def test_liga_e_desliga(janela, settings):
    janela.act_auto_refresh.setChecked(False)
    assert not janela.refresh_timer.isActive()
    assert Settings.load(settings.path).auto_refresh_minutes == 0
    janela.act_auto_refresh.setChecked(True)
    assert janela.refresh_timer.interval() == 180_000
    assert Settings.load(settings.path).auto_refresh_minutes == 3
