"""Transferência de setor em lote (com histórico) e filtro por coluna."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from retalhos.models import Usuario  # noqa: E402
from retalhos.services import EstoqueService, RegraDeNegocioError  # noqa: E402


def _por_id(svc, ids):
    return [r for r in svc.listar_retalhos() if r.id in ids]


def test_transfere_varios_e_registra_historico(settings):
    settings.usuario = Usuario(1, "ANA", "ANA", admin=True)
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500, "5")
    b = svc.lancar_retalho(10, 800, 400)          # sem setor
    c = svc.lancar_retalho(20, 700, 400, "ESTOQUE")
    svc.reservar_manual("14078", _por_id(svc, {c}))  # reservado também pode mudar de lugar

    settings.usuario = Usuario(2, "BETO", "BETO")
    assert svc.transferir_setor(_por_id(svc, {a, b, c}), " 12 ") == 3
    assert {r.id: r.setor for r in svc.listar_retalhos()} == {a: "12", b: "12", c: "12"}
    assert next(r for r in svc.listar_retalhos() if r.id == c).reserva == "14078"  # reserva intacta

    ultimo = {rid: svc.historico(rid)[-1] for rid in (a, b, c)}
    assert all(m.acao == "TRANSFERÊNCIA" and m.usuario == "BETO" for m in ultimo.values())
    assert ultimo[a].detalhe == "setor 5 → 12"
    assert ultimo[b].detalhe == "setor (sem setor) → 12"
    assert ultimo[c].detalhe == "setor ESTOQUE → 12"

    # em cascata: um segundo lote, ignorando quem já está no destino
    assert svc.transferir_setor(_por_id(svc, {a, b}), "a") == 2
    assert svc.transferir_setor(_por_id(svc, {a, c}), "A") == 1
    assert [m.detalhe for m in svc.historico(a) if m.acao == "TRANSFERÊNCIA"] == ["setor 5 → 12", "setor 12 → A"]


def test_regras(settings):
    svc = EstoqueService(settings)
    r = svc.lancar_retalho(10, 1000, 500, "5")
    retalhos = svc.listar_retalhos()
    with pytest.raises(RegraDeNegocioError, match="destino"):
        svc.transferir_setor(retalhos, "  ")
    with pytest.raises(RegraDeNegocioError, match="no máximo"):
        svc.transferir_setor(retalhos, "X" * 21)
    with pytest.raises(RegraDeNegocioError, match="ao menos um"):
        svc.transferir_setor([], "1")

    svc.excluir_retalho(retalhos[0])  # removido em outra máquina depois da tela carregar
    with pytest.raises(RegraDeNegocioError, match=f"{r} não está mais"):
        svc.transferir_setor(retalhos, "1")

    settings.usuario = None
    with pytest.raises(RegraDeNegocioError, match="logado"):
        svc.transferir_setor(retalhos, "1")


def test_lote_com_removido_nao_grava_nada(settings):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500, "5")
    b = svc.lancar_retalho(10, 800, 400, "5")
    lista = svc.listar_retalhos()
    svc.excluir_retalho(next(r for r in lista if r.id == b))
    with pytest.raises(RegraDeNegocioError):
        svc.transferir_setor(lista, "9")
    assert next(r for r in svc.listar_retalhos() if r.id == a).setor == "5"  # nada pela metade


def test_tela_principal_filtro_por_coluna_e_transferencia(settings, monkeypatch):
    from retalhos.app import create_app
    from retalhos.ui import main_window
    create_app()
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500, "5")
    b = svc.lancar_retalho(10, 800, 400, "15")
    w = main_window.MainWindow(settings)
    w.reload()

    # "5" em todas as colunas acha os dois (setor 15, medidas…); só na coluna Setor, acha o setor 5 exato e o 15
    w.txt_filter.setText("5")
    w._apply_filter()  # sem esperar a pausa de digitação
    assert len(w.table.visible_rows()) == 2
    w.cb_coluna.setCurrentIndex(w.cb_coluna.findText("ID"))
    assert w.table.visible_rows() == []
    w.cb_coluna.setCurrentIndex(w.cb_coluna.findText("Setor"))
    assert {r.id for r in w.table.visible_rows()} == {a, b}
    w.txt_filter.setText("15")
    w._apply_filter()
    assert [r.id for r in w.table.visible_rows()] == [b]
    assert "setor" in w.txt_filter.placeholderText().lower()
    assert w.cb_coluna.findText("x") == -1  # coluna separadora não entra na lista
    w.txt_filter.clear()
    w._apply_filter()

    w.table.selectAll()
    assert w.bt_transferir.isEnabled() and w.bt_transferir.text() == "Transferir 2…"

    class Falso:
        setor = "ESTOQUE"

        def __init__(self, retalhos, setores, parent):
            assert len(retalhos) == 2 and "15" in setores

        def exec(self):
            return True

    monkeypatch.setattr(main_window, "TransferenciaDialog", Falso)
    w.transfer_selected()
    assert {r.setor for r in svc.listar_retalhos()} == {"ESTOQUE"}
    w.close()


def test_tela_transferencia(settings):
    from retalhos.app import create_app
    from retalhos.ui.dialogs import TransferenciaDialog
    create_app()
    svc = EstoqueService(settings)
    svc.lancar_retalho(10, 1000, 500, "5")
    dlg = TransferenciaDialog(svc.listar_retalhos(), ["10", "2", "ESTOQUE", "", "2", "1"])
    assert [dlg.cb_setor.itemText(i) for i in range(dlg.cb_setor.count())] == ["1", "2", "10", "ESTOQUE"]
    assert not dlg.bt_ok.isEnabled()
    dlg.cb_setor.setEditText("b3")
    dlg._ok()
    assert dlg.setor == "B3"


def test_busca_nao_emenda_colunas_e_nao_refiltra_sem_mudanca():
    from retalhos.app import create_app
    from retalhos.ui.widgets import Column, FilterProxy, ObjectTableModel
    create_app()
    m = ObjectTableModel([Column("A", lambda x: x[0]), Column("B", lambda x: x[1])])
    m.set_rows([("12", "34"), ("1", "234")])
    proxy = FilterProxy()
    proxy.setSourceModel(m)
    proxy.set_text("23")
    assert proxy.rowCount() == 1  # "12"+"34" não forma "23"; só a linha com "234"
    proxy.set_column(0)
    assert proxy.rowCount() == 0
    chamadas = []
    proxy.invalidateFilter = lambda: chamadas.append(1)
    proxy.set_filter("23", 0, None)  # nada mudou
    assert chamadas == []
