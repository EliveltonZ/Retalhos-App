import openpyxl
import pytest

from retalhos.models import Chapa, Sobra, Usuario
from retalhos.services import EstoqueService, RegraDeNegocioError


def _linhas(service, codigo):
    arquivo = service.arquivos.arquivo_retalho(codigo)
    return arquivo.read_text().splitlines() if arquivo.exists() else []


def _por_id(service, rid):
    return next(r for r in service.listar_retalhos() if r.id == rid)


def test_lancar_e_excluir(settings):
    svc = EstoqueService(settings)
    rid = svc.lancar_retalho(10, 1000, 500, "corte")
    r = _por_id(svc, rid)
    assert (r.codigo, r.largura, r.altura, r.descricao, r.responsavel) == (10, 1000, 500, "BRANCO TX", "TESTE")
    assert r.data_entrada is not None and not r.reservado
    assert _linhas(svc, 10) == [f"{rid},+,1,1000.0,500.0, ,{rid},"]

    svc.excluir_retalho(r)
    assert svc.listar_retalhos() == []
    assert _linhas(svc, 10) == []


def test_validacoes(settings):
    svc = EstoqueService(settings)
    with pytest.raises(RegraDeNegocioError):
        svc.lancar_retalho(10, 100, 500)  # abaixo do mínimo
    with pytest.raises(RegraDeNegocioError):
        svc.lancar_retalho(999, 1000, 500)  # material inexistente
    assert svc.listar_retalhos() == []


def test_falha_no_arquivo_desfaz_banco(settings, monkeypatch):
    svc = EstoqueService(settings)

    def falha(*a, **k):
        raise OSError("disco")
    monkeypatch.setattr(svc.arquivos, "adicionar", falha)
    with pytest.raises(OSError):
        svc.lancar_retalho(10, 1000, 500)
    assert svc.listar_retalhos() == []


def test_fluxo_reserva(settings):
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 2740, 1840)
    b = svc.lancar_retalho(20, 1000, 600, "S1")
    svc.lancar_retalho(30, 900, 900)  # material fora do pedido
    (svc.arquivos.ped_dir / "PED01206.TAB").write_text("1 a b c d 10\n2 a b c d 20\n")

    candidatos = svc.retalhos_para_projeto("1206")
    assert sorted(r.id for r in candidatos) == sorted([a, b])
    assert svc.corte_gerado("1206") is False

    resultado = svc.reservar("1206", candidatos)
    assert resultado.reservados == 2
    assert _linhas(svc, 10) == [] and _linhas(svc, 20) == []
    assert _por_id(svc, a).reserva == "1206" and _por_id(svc, a).data_reserva

    ws = openpyxl.load_workbook(resultado.planilha).active
    linhas = {row[2]: row for row in ws.iter_rows(values_only=True)}
    linha = linhas["LORD SETHOS (ARAUCO)"]
    assert linha[:11] == ("S1", "18", "LORD SETHOS (ARAUCO)", None, None, None, None,
                         "1000.0", "x", "600.0", "1206")

    # continua aparecendo para o mesmo projeto
    assert len(svc.retalhos_para_projeto("1206")) == 2
    with pytest.raises(RegraDeNegocioError):
        svc.excluir_retalho(_por_id(svc, a))

    assert svc.cancelar_reservas("1206", [_por_id(svc, a)]) == 1
    assert _por_id(svc, a).reserva == ""
    assert _linhas(svc, 10) == [f"{a},+,1,2740.0,1840.0, ,{a},"]

    assert [r.id for r in svc.retalhos_reservados("1206")] == [b]
    assert svc.dar_baixa("1206") == 1
    assert {r.id for r in svc.listar_retalhos()} == {a, a + 2}


def test_liberar_reserva_e_permissao(settings):
    svc = EstoqueService(settings)
    rid = svc.lancar_retalho(10, 1000, 500)
    original = _por_id(svc, rid)
    svc.reservar("77", [_por_id(svc, rid)])

    settings.usuario = Usuario(2, "OUTRA", "OUTRA MAQUINA", admin=True)  # quem libera não vira o responsável
    svc.liberar_reserva(_por_id(svc, rid))
    liberado = _por_id(svc, rid)
    assert not liberado.reservado and liberado.data_reserva == ""
    assert liberado.data_entrada == original.data_entrada  # data de lançamento preservada
    assert liberado.responsavel == original.responsavel == "TESTE"
    assert len(_linhas(svc, 10)) == 1

    svc.reservar("77", [_por_id(svc, rid)])
    settings.usuario = Usuario(3, "SEMPERM", "SEM PERMISSAO")  # usuário sem "remover reserva"
    with pytest.raises(RegraDeNegocioError):
        svc.liberar_reserva(_por_id(svc, rid))


def test_sobras_e_recriar(settings):
    svc = EstoqueService(settings)
    with pytest.raises(RegraDeNegocioError):
        svc.lancar_sobras([Sobra(10, 500, 400)], "")
    assert svc.lancar_sobras([Sobra(10, 500, 400), Sobra(20, 600, 450)], "55") == 2
    reservados = svc.retalhos_reservados("55")
    assert len(reservados) == 2
    assert _linhas(svc, 10)[0].split(",")[5] == "55"

    livre = svc.lancar_retalho(10, 1000, 500)
    (svc.arquivos.ret_dir / "RET00999.TAB").write_text("lixo\n")
    assert svc.recriar_arquivos() == 1
    assert _linhas(svc, 10) == [f"{livre},+,1,1000.0,500.0, ,{livre},"]
    assert not (svc.arquivos.ret_dir / "RET00999.TAB").exists()


def test_materiais(settings):
    svc = EstoqueService(settings)
    assert svc.salvar_material(Chapa(40, "25", "CARVALHO", True)) is True
    assert svc.salvar_material(Chapa(40, "25", "CARVALHO HANOVER", False)) is False
    m = svc.buscar_material(40)
    assert (m.descricao, m.ativo, m.espessura) == ("CARVALHO HANOVER", False, "25")
    assert [c.codigo for c in svc.listar_materiais()][:2] == [10, 40]
    assert set(svc.buscar_materiais([10, 30, 999])) == {10, 30}
