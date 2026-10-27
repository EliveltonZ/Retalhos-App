import json
from pathlib import Path

import pytest

from retalhos.config import Settings
from retalhos.services import ArquivosCorteCerto, PedidoNaoEncontrado, ler_codigo_barras, nome_arquivo
from retalhos.services.etiquetas import ler_plano_de_corte

DADOS = Path(__file__).resolve().parent / "dados"  # planos de corte reais para teste


def test_nome_arquivo():
    assert nome_arquivo(123) == "RET00123.TAB"
    assert nome_arquivo("1206", prefixo="PED") == "PED01206.TAB"
    assert nome_arquivo("123456") == "RET123456.TAB"


def test_codigo_barras():
    sobra = ler_codigo_barras("0000123X2740.0 0550.0")
    assert (sobra.codigo, sobra.largura, sobra.altura) == (123, 2740.0, 550.0)
    with pytest.raises(ValueError):
        ler_codigo_barras("123")


def test_plano_de_corte_exemplo():
    exemplos = list(DADOS.glob("*.cutplanning"))
    if not exemplos:
        pytest.skip("sem arquivo de exemplo")
    sobras = ler_plano_de_corte(exemplos[0])
    assert all(s.codigo > 0 and s.largura > 0 and s.altura > 0 for s in sobras)


def test_settings_preserva_chaves(tmp_path):
    original = {"Directory_cc": "\\\\X\\cc\\", "Menu": "Desativado", "Remover": "Ativado",
                "Password": 1, "Largura": 2740, "chave_extra": "mantida"}
    arquivo = tmp_path / "Settings.json"
    arquivo.write_text(json.dumps(original), encoding="utf-8")

    s = Settings.load(arquivo)
    # permissões agora vêm do usuário logado: as chaves antigas do JSON não liberam nada
    assert s.menu_pcp_enabled is False and s.allow_remove_reserve is False and s.user == ""
    assert s.database_password == "1" and s.max_width == 2740.0
    s.last_login = "MAQ1"
    s.save()

    salvo = json.loads(arquivo.read_text(encoding="utf-8"))
    assert salvo["chave_extra"] == "mantida"
    assert salvo["Menu"] == "Desativado" and salvo["Password"] == 1 and salvo["Largura"] == 2740  # preservadas
    assert salvo["UltimoLogin"] == "MAQ1"
    assert "usuario" not in salvo and "User" not in salvo  # a sessão nunca vai para o JSON


def test_adicionar_remover_sem_duplicar(settings):
    arq = ArquivosCorteCerto(settings)
    arq.adicionar(10, 1, 1000, 500)
    arq.adicionar(10, 2, 800, 400, "1206")
    arq.adicionar(10, 1, 1000, 500)  # repetido: não duplica
    linhas = arq.arquivo_retalho(10).read_text().splitlines()
    assert linhas == ["2,+,1,800.0,400.0,1206,2,", "1,+,1,1000.0,500.0, ,1,"]

    assert arq.remover(10, 2) is True
    assert arq.remover(10, 2) is False
    assert arq.remover(99, 1) is False  # arquivo inexistente não é erro
    assert arq.arquivo_retalho(10).read_text().splitlines() == ["1,+,1,1000.0,500.0, ,1,"]


def test_codigos_do_pedido(settings):
    arq = ArquivosCorteCerto(settings)
    (arq.ped_dir / "PED01206.TAB").write_text(
        "1 A  2 3 4 10 x\n2 B 2 3 4  20 y\n3 C 2 3 4 10 z\ncurta\n", encoding="latin-1"
    )
    assert arq.codigos_do_pedido("1206") == [10, 20]
    # o arquivo do Corte Certo não é modificado
    assert "  " in (arq.ped_dir / "PED01206.TAB").read_text(encoding="latin-1")
    with pytest.raises(PedidoNaoEncontrado):
        arq.codigos_do_pedido("999")
