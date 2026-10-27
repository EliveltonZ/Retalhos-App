"""Reserva dos retalhos a partir do plano de corte (tela de Consumo)."""
from retalhos.services import EstoqueService
from tests.test_consumo import _peca, _plano, _program


def _linhas_ret(svc, codigo):
    arquivo = svc.arquivos.arquivo_retalho(codigo)
    return arquivo.read_text().splitlines() if arquivo.exists() else []


def _por_id(svc, rid):
    return next(r for r in svc.listar_retalhos() if r.id == rid)


def test_medidas_repetidas_reservam_um_retalho_por_ocorrencia(settings, tmp_path):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 700, 600)
    b = svc.lancar_retalho(10, 700, 600)  # mesma medida
    outro = svc.lancar_retalho(10, 900, 600)  # não usado pelo plano
    # o plano usa 3 retalhos de 700 x 600: há só 2 no estoque
    arquivo = _plano(tmp_path, "13955_x.cutplanning", {10: [_program(True, 700, 600, 3, (_peca("13955"),))]})
    analise = svc.analisar_planos([arquivo])

    r = svc.reservar_do_plano(analise)
    assert sorted(r.reservados) == [(a, "13955"), (b, "13955")]
    assert r.nao_encontrados == 1 and not r.conflitos
    assert _por_id(svc, a).reserva == "13955" and _por_id(svc, b).reserva == "13955"
    assert not _por_id(svc, outro).reservado
    # saíram do RET (o Corte Certo não oferece mais); o não usado continua
    assert [linha.split(",")[0] for linha in _linhas_ret(svc, 10)] == [str(outro)]

    # processar o mesmo plano de novo não reserva nada a mais
    r2 = svc.reservar_do_plano(svc.analisar_planos([arquivo]))
    assert r2.reservados == [] and r2.ja_reservados == 2 and r2.nao_encontrados == 1


def test_retalho_compartilhado_fica_com_o_primeiro_projeto(settings, tmp_path):
    svc = EstoqueService(settings)
    rid = svc.lancar_retalho(10, 1500, 900)
    arquivo = _plano(tmp_path, "x.cutplanning",
                     {10: [_program(True, 1500, 900, 1, (_peca("13958"), _peca("13956")))]})
    r = svc.reservar_do_plano(svc.analisar_planos([arquivo]))
    assert r.reservados == [(rid, "13956")]  # um projeto só: o primeiro (ordem numérica)


def test_nao_toma_retalho_reservado_por_outra_maquina(settings, tmp_path):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1500, 900)
    b = svc.lancar_retalho(20, 800, 600)
    arquivo = _plano(tmp_path, "100_x.cutplanning", {
        10: [_program(True, 1500, 900, 1, (_peca("100"),))],
        20: [_program(True, 800, 600, 1, (_peca("100"),))],
    })
    analise = svc.analisar_planos([arquivo])
    # entre a análise e o clique, outra máquina reserva o retalho "a" para outro projeto
    svc.reservar("999", [_por_id(svc, a)])

    r = svc.reservar_do_plano(analise)
    assert r.reservados == [(b, "100")]
    assert len(r.conflitos) == 1 and "999" in r.conflitos[0]
    assert _por_id(svc, a).reserva == "999"


def test_reservado_para_outro_projeto_na_analise_nao_e_tomado(settings, tmp_path):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1500, 900)
    svc.reservar("999", [_por_id(svc, a)])
    arquivo = _plano(tmp_path, "100_x.cutplanning", {10: [_program(True, 1500, 900, 1, (_peca("100"),))]})
    r = svc.reservar_do_plano(svc.analisar_planos([arquivo]))
    assert r.reservados == [] and len(r.conflitos) == 1
    assert _por_id(svc, a).reserva == "999"


def test_reserva_so_os_itens_escolhidos(settings, tmp_path):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1500, 900)
    svc.lancar_retalho(20, 800, 600)
    arquivo = _plano(tmp_path, "100_x.cutplanning", {
        10: [_program(True, 1500, 900, 1, (_peca("100"),))],
        20: [_program(True, 800, 600, 1, (_peca("100"),))],
    })
    analise = svc.analisar_planos([arquivo])
    escolhidos = [i for i in analise.retalhos if i.codigo == 10]
    assert svc.reservar_do_plano(analise, escolhidos).reservados == [(a, "100")]
