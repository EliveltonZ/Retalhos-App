"""Controles: quem lançou, reservou, liberou, deu baixa e excluiu (colunas + tblHistorico)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from retalhos.db import Database  # noqa: E402
from retalhos.models import Sobra, Usuario  # noqa: E402
from retalhos.services import EstoqueService  # noqa: E402
from tests.test_consumo import _peca, _plano, _program  # noqa: E402


def _por_id(svc, rid):
    return next(r for r in svc.listar_retalhos() if r.id == rid)


def _como(settings, nome):
    settings.usuario = Usuario(hash(nome) % 1000, nome, nome, admin=True)


def _acoes(svc, rid):
    return [(m.acao, m.usuario) for m in svc.historico(rid)]


def test_ciclo_completo_registrado(settings):
    svc = EstoqueService(settings)
    _como(settings, "ANA")
    rid = svc.lancar_retalho(10, 1000, 500, "5")

    _como(settings, "BETO")
    svc.reservar_manual("14010", [_por_id(svc, rid)])
    r = _por_id(svc, rid)
    assert (r.responsavel, r.reservado_por) == ("ANA", "BETO")  # quem lançou x quem reservou

    _como(settings, "CARLA")
    svc.liberar_reserva(_por_id(svc, rid))
    assert _por_id(svc, rid).reservado_por == ""  # reserva atual limpa...
    _como(settings, "BETO")
    svc.reservar("1206", [_por_id(svc, rid)], gerar_planilha=False)
    _como(settings, "DANI")
    svc.dar_baixa("1206")

    historico = svc.historico(rid)
    assert [(m.acao, m.usuario) for m in historico] == [
        ("LANÇAMENTO", "ANA"), ("RESERVA", "BETO"), ("LIBERAÇÃO", "CARLA"), ("RESERVA", "BETO"), ("BAIXA", "DANI"),
    ]
    assert historico[1].detalhe == "p/ 14010 (manual)"
    assert historico[2].detalhe == "estava reservado p/ 14010 (por BETO)"  # ...mas o histórico guarda
    assert historico[4].detalhe == "consumido no projeto 1206"
    assert all(m.data_hora is not None for m in historico)


def test_exclusao_registrada_e_oculta(settings):
    svc = EstoqueService(settings)
    rid = svc.lancar_retalho(10, 1000, 500)
    _como(settings, "EDU")
    svc.excluir_retalho(_por_id(svc, rid))
    assert svc.listar_retalhos() == []  # some do sistema
    with Database(settings.database_path).session() as s:  # mas continua no banco
        row = s.query_one("SELECT DataExclusao, ResponsavelExclusao FROM tblRetalhos WHERE id = ?", (rid,))
    assert row[0] is not None and row[1] == "EDU"
    assert _acoes(svc, rid)[-1] == ("EXCLUSÃO", "EDU")
    assert svc.arquivos.arquivo_retalho(10).read_text() == ""


def test_sobra_e_reserva_pelo_plano_e_cancelamento(settings, tmp_path):
    svc = EstoqueService(settings)
    _como(settings, "FABI")
    svc.lancar_sobras([Sobra(10, 700, 600)], "300")
    sobra = svc.listar_retalhos()[0]
    assert sobra.reservado_por == "FABI"
    assert _acoes(svc, sobra.id) == [("SOBRA LANÇADA", "FABI")]

    _como(settings, "GUI")
    livre = svc.lancar_retalho(10, 1500, 900)
    plano = _plano(tmp_path, "200_x.cutplanning", {10: [_program(True, 1500, 900, 1, (_peca("200"),))]})
    svc.reservar_do_plano(svc.analisar_planos([plano]))
    assert _por_id(svc, livre).reservado_por == "GUI"
    assert svc.historico(livre)[-1].detalhe == "p/ 200 (plano de corte)"

    _como(settings, "HUGO")
    svc.cancelar_reservas("200", [_por_id(svc, livre)])
    assert _acoes(svc, livre)[-1] == ("CANCELAMENTO", "HUGO")


def test_falha_desfaz_alteracao_e_historico(settings, monkeypatch):
    svc = EstoqueService(settings)
    rid = svc.lancar_retalho(10, 1000, 500)

    def quebra(*a, **k):
        raise OSError("rede caiu")
    monkeypatch.setattr(svc.arquivos, "remover", quebra)
    try:
        svc.reservar("1", [_por_id(svc, rid)], gerar_planilha=False)
    except OSError:
        pass
    assert not _por_id(svc, rid).reservado
    assert [m.acao for m in svc.historico(rid)] == ["LANÇAMENTO"]  # nada de reserva "pela metade"


def test_tela_de_historico(settings):
    from retalhos.app import create_app
    from retalhos.ui.dialogs import HistoricoDialog
    from retalhos.ui.widgets import DataTable
    create_app()
    svc = EstoqueService(settings)
    rid = svc.lancar_retalho(10, 1000, 500)
    svc.reservar_manual("X1", [_por_id(svc, rid)])
    dlg = HistoricoDialog(svc, _por_id(svc, rid))
    tabela = dlg.findChildren(DataTable)[0]
    assert [m.acao for m in tabela.source.rows()] == ["LANÇAMENTO", "RESERVA"]
