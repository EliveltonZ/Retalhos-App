"""Reserva manual: guardar retalho para um projeto que ainda será feito (sem PED nem plano)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtCore import QItemSelectionModel  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from retalhos.models import Usuario  # noqa: E402
from retalhos.services import EstoqueService, RegraDeNegocioError  # noqa: E402


def _por_id(svc, rid):
    return next(r for r in svc.listar_retalhos() if r.id == rid)


def _linhas_ret(svc, codigo):
    arquivo = svc.arquivos.arquivo_retalho(codigo)
    return arquivo.read_text().splitlines() if arquivo.exists() else []


def test_reserva_livre_sem_planilha(settings):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500)
    b = svc.lancar_retalho(10, 800, 400)
    r = svc.reservar("joao-cozinha", [_por_id(svc, a), _por_id(svc, b)], gerar_planilha=False)
    assert r.reservados == 2 and r.planilha is None
    assert _por_id(svc, a).reserva == "JOAO-COZINHA" and _por_id(svc, a).data_reserva
    assert _linhas_ret(svc, 10) == []  # saíram dos disponíveis do Corte Certo
    # nenhuma PRJ_*.xlsx gerada (não sobrescreve a planilha de um projeto existente)
    assert not os.path.isdir(settings.sheets_dir) or not os.listdir(settings.sheets_dir)

    svc.liberar_reserva(_por_id(svc, a))  # desfaz pelo "Liberar reserva" de sempre
    assert not _por_id(svc, a).reservado and len(_linhas_ret(svc, 10)) == 1


def test_nao_toma_retalho_reservado_por_outra_maquina(settings):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500)
    b = svc.lancar_retalho(10, 800, 400)
    tela = [_por_id(svc, a), _por_id(svc, b)]  # o que a tela tinha carregado
    svc.reservar("999", [_por_id(svc, b)], gerar_planilha=False)  # outra máquina reserva o "b"
    with pytest.raises(RegraDeNegocioError, match="acabou de ser reservado"):
        svc.reservar("14010", tela, gerar_planilha=False)
    # nada foi gravado: o "a" continua livre e no RET
    assert not _por_id(svc, a).reservado
    assert [linha.split(",")[0] for linha in _linhas_ret(svc, 10)] == [str(a)]


def test_reserva_manual_exige_permissao(settings):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500)
    settings.usuario = Usuario(5, "OPERADOR", "OPERADOR")  # sem a permissão "reservar manual"
    assert settings.allow_manual_reserve is False
    with pytest.raises(RegraDeNegocioError, match="permissão"):
        svc.reservar_manual("14010", [_por_id(svc, a)])
    assert not _por_id(svc, a).reservado

    settings.usuario = Usuario(5, "OPERADOR", "OPERADOR", reservar_manual=True)
    r = svc.reservar_manual("14010", [_por_id(svc, a)])
    assert r.reservados == 1 and r.planilha is None and _por_id(svc, a).reserva == "14010"


def test_chave_antiga_do_json_nao_libera_mais(tmp_path):
    import json

    from retalhos.config import Settings
    arquivo = tmp_path / "Settings.json"
    arquivo.write_text(json.dumps({"ReservarManual": "Ativado", "Remover": "Ativado"}), encoding="utf-8")
    s = Settings.load(arquivo)
    assert s.allow_manual_reserve is False and s.allow_remove_reserve is False  # sem usuário logado
    s.usuario = Usuario(1, "A", "A", reservar_manual=True)
    assert s.allow_manual_reserve is True and s.allow_remove_reserve is False


def test_projeto_obrigatorio_e_limite(settings):
    svc = EstoqueService(settings)
    a = _por_id(svc, svc.lancar_retalho(10, 1000, 500))
    with pytest.raises(RegraDeNegocioError):
        svc.reservar("   ", [a], gerar_planilha=False)
    with pytest.raises(RegraDeNegocioError):
        svc.reservar("X" * 51, [a], gerar_planilha=False)


def test_botao_reservar_na_tela_principal(settings):
    from retalhos.app import create_app
    from retalhos.ui.main_window import MainWindow

    create_app()
    svc = EstoqueService(settings)
    livres = [svc.lancar_retalho(10, 1000 + i, 500) for i in range(2)]
    reservado = svc.lancar_retalho(10, 900, 400)
    svc.reservar("1", [_por_id(svc, reservado)], gerar_planilha=False)

    # sem permissão: o botão nem aparece
    settings.usuario = Usuario(9, "SEM", "SEM PERMISSAO")
    settings.save()
    sem = MainWindow(settings)
    sem.show()
    QApplication.processEvents()
    assert not sem.bt_reserve.isVisible() and not sem.act_reserve.isEnabled()
    sem.refresh_timer.stop()
    sem.close()

    settings.usuario = Usuario(9, "COM", "COM PERMISSAO", reservar_manual=True, remover_reserva=True)
    w = MainWindow(settings)
    w.show()
    QApplication.processEvents()
    assert w.bt_reserve.isVisible()

    def selecionar(ids):
        sel = w.table.selectionModel()
        sel.clearSelection()
        for row in range(w.table.proxy.rowCount()):
            if w.table.proxy.source_row(row).id in ids:
                sel.select(w.table.proxy.index(row, 0),
                           QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
        QApplication.processEvents()

    selecionar(livres)
    assert w.act_reserve.isEnabled() and w.bt_reserve.text() == "Reservar 2…"
    assert not w.act_delete.isEnabled()  # excluir: só com um selecionado
    selecionar([livres[0], reservado])
    assert not w.act_reserve.isEnabled()  # já reservado não entra
    selecionar([reservado])
    assert w.act_release.isEnabled()
    w.refresh_timer.stop()
    w.close()
