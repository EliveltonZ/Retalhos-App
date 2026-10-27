"""Baixa por consumo: não apaga; registra data/hora e responsável e oculta o retalho do sistema."""
import pytest

from retalhos.db import Database
from retalhos.models import Usuario
from retalhos.services import EstoqueService, RegraDeNegocioError
from tests.conftest import _create_db
from tests.test_consumo import _peca, _plano, _program


def _linha_bruta(settings, rid):
    with Database(settings.database_path).session() as s:
        return s.query_one("SELECT id, Reserva, DataBaixa, ResponsavelBaixa FROM tblRetalhos WHERE id = ?", (rid,))


def test_baixa_registra_e_oculta(settings, tmp_path):
    svc = EstoqueService(settings)
    consumido = svc.lancar_retalho(10, 1000, 500)
    outro = svc.lancar_retalho(10, 800, 400)
    svc.reservar("1206", [r for r in svc.listar_retalhos() if r.id == consumido], gerar_planilha=False)

    settings.usuario = Usuario(4, "PROD", "PRODUCAO")
    assert svc.dar_baixa("1206") == 1

    # continua no banco, com data/hora e responsável da baixa
    rid, reserva, data_baixa, responsavel = _linha_bruta(settings, consumido)
    assert rid == consumido and reserva == "1206" and data_baixa is not None and responsavel == "PRODUCAO"
    # ...mas some de todo o sistema
    assert [r.id for r in svc.listar_retalhos()] == [outro]
    assert svc.retalhos_reservados("1206") == []
    assert svc.dar_baixa("1206") == 0  # não "dá baixa" duas vezes
    (svc.arquivos.ped_dir / "PED01206.TAB").write_text("1 a b c d 10\n")
    assert [r.id for r in svc.retalhos_para_projeto("1206")] == [outro]

    plano = _plano(tmp_path, "1206_x.cutplanning", {10: [_program(True, 1000, 500, 1, (_peca("1206"),))]})
    analise = svc.analisar_planos([plano])
    assert not analise.retalhos[0].encontrado  # o consumo do plano não acha retalho já baixado

    settings.usuario = Usuario(1, "ADM", "ADM", admin=True)
    svc.recriar_arquivos()
    assert [linha.split(",")[0] for linha in svc.arquivos.arquivo_retalho(10).read_text().splitlines()] == [str(outro)]


def test_baixa_exige_login(settings):
    svc = EstoqueService(settings)
    settings.usuario = None
    with pytest.raises(RegraDeNegocioError, match="logado"):
        svc.dar_baixa("1206")


@pytest.mark.parametrize("dialeto", ["sqlite", "access"])
def test_migracao_do_banco_antigo(dialeto, tmp_path, settings):
    import os
    if dialeto == "access" and not os.getenv("RETALHOS_TEST_ACCDB"):
        pytest.skip("sem modelo .accdb")
    pasta = tmp_path / dialeto
    pasta.mkdir()
    antigo = _create_db(dialeto, pasta)  # estrutura antiga, sem as colunas de baixa
    with Database(str(antigo)).session() as s:
        s.execute("INSERT INTO tblRetalhos (Cod_Material, Largura, Altura) VALUES (?, ?, ?)", (10, 1000, 500))
    settings.database_path = str(antigo)
    svc = EstoqueService(settings)

    backup = svc.preparar_banco(pasta_backup=pasta / "bk")
    if dialeto == "access":
        assert backup is not None and backup.is_file()  # cópia do banco antes de alterar
    with Database(str(antigo)).session() as s:
        assert {"databaixa", "responsavelbaixa", "dataexclusao", "responsavelexclusao",
                "responsavelreserva"} <= s.colunas("tblRetalhos")
        assert s.tabela_existe("tblHistorico")
    assert len(svc.listar_retalhos()) == 1  # dados preservados e visíveis
    assert svc.preparar_banco(pasta_backup=pasta / "bk") is None  # 2ª vez: nada a fazer
