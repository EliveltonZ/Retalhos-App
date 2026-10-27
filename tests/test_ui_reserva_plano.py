"""Tela de conferência da reserva pelo plano de corte (sem exibir na tela)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from retalhos.app import create_app  # noqa: E402
from retalhos.services import EstoqueService  # noqa: E402
from tests.test_consumo import _peca, _plano, _program  # noqa: E402


def test_conferencia_marca_so_os_disponiveis(settings, tmp_path):
    create_app()
    from retalhos.ui.dialogs.consumo_dialog import ReservaPlanoDialog, _status_reserva

    svc = EstoqueService(settings)
    livre = svc.lancar_retalho(10, 1500, 900)
    ja = svc.lancar_retalho(10, 700, 600)
    outro = svc.lancar_retalho(20, 800, 600)
    svc.reservar("100", [r for r in svc.listar_retalhos() if r.id == ja])
    svc.reservar("999", [r for r in svc.listar_retalhos() if r.id == outro])
    arquivo = _plano(tmp_path, "100_x.cutplanning", {
        10: [_program(True, 1500, 900, 1, (_peca("100"),)), _program(True, 700, 600, 1, (_peca("100"),)),
             _program(True, 333, 333, 1, (_peca("100"),))],
        20: [_program(True, 800, 600, 1, (_peca("100"),))],
    })
    analise = svc.analisar_planos([arquivo])

    dlg = ReservaPlanoDialog(analise)
    status = sorted(_status_reserva(r) for r in dlg.model.rows())
    assert status == ["Já reservado p/ 100", "Não encontrado no estoque", "Reservado p/ outro projeto (999)",
                      "Reservar p/ 100"]
    marcados = dlg.model.checked_rows()
    assert [r.retalho.id for r in marcados] == [livre]  # só o disponível vem marcado e pode ser marcado
    dlg.model.set_all_checked(True)
    assert len(dlg.model.checked_rows()) == 1
    dlg._ok()
    assert [r.retalho.id for r in dlg.escolhidos] == [livre]
