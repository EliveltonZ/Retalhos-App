"""Procura de versão nova (internet e pasta da rede), download conferido e aviso na janela principal."""
import hashlib
import io
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from retalhos.config import Settings  # noqa: E402
from retalhos.services import atualizacao as at  # noqa: E402


def _publicar(pasta, versao, conteudo=b"instalador", sha=None):
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"Retalhos_Setup_{versao}.exe"
    (pasta / nome).write_bytes(conteudo)
    (pasta / "versao.json").write_text(json.dumps({
        "versao": versao, "instalador": nome, "sha256": sha or hashlib.sha256(conteudo).hexdigest(),
        "tamanho": len(conteudo), "data": "18/11/2026", "notas": "- novidade",
    }), encoding="utf-8")
    return nome


def _settings(tmp_path, repo=""):
    return Settings(update_zip=str(tmp_path / "rede" / "Retalhos.zip"), update_repo=repo)


class _Resposta(io.BytesIO):
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _internet(monkeypatch, versao, conteudo=b"da internet"):
    pedidos = []

    def abrir(url, timeout):
        pedidos.append(url)
        if url.endswith("versao.json"):
            return _Resposta(json.dumps({"versao": versao, "instalador": f"Retalhos_Setup_{versao}.exe",
                                         "sha256": hashlib.sha256(conteudo).hexdigest()}).encode())
        return _Resposta(conteudo)

    monkeypatch.setattr(at, "_abrir_url", abrir)
    return pedidos


def test_versao_tupla():
    assert at.versao_tupla("v2.10.0") > at.versao_tupla("2.9.9")
    assert at.versao_tupla("2.1") == at.versao_tupla("2.1.0")
    assert at.versao_tupla("2.1.0") > at.versao_tupla("2.0.0")


def test_rede_mais_nova(tmp_path):
    _publicar(tmp_path / "rede", "2.2.0")
    nova = at.buscar_atualizacao(_settings(tmp_path), "2.1.0")
    assert nova is not None and nova.versao == "2.2.0" and nova.da_rede and nova.notas == "- novidade"
    assert at.buscar_atualizacao(_settings(tmp_path), "2.2.0") is None  # já atualizado
    assert at.buscar_atualizacao(_settings(tmp_path), "2.3.0") is None  # mais novo que o publicado


def test_rede_sem_instalador_ou_manifesto_quebrado(tmp_path):
    nome = _publicar(tmp_path / "rede", "2.2.0")
    (tmp_path / "rede" / nome).unlink()
    assert at.buscar_atualizacao(_settings(tmp_path), "2.1.0") is None  # versao.json sem o instalador
    (tmp_path / "rede" / "versao.json").write_text("{lixo", encoding="utf-8")
    assert at.buscar_atualizacao(_settings(tmp_path), "2.1.0") is None


def test_sem_internet_e_sem_rede_nao_quebra(tmp_path, monkeypatch):
    def sem_rede(url, timeout):
        raise OSError("sem internet")

    monkeypatch.setattr(at, "_abrir_url", sem_rede)
    assert at.buscar_atualizacao(_settings(tmp_path, "dono/repo"), "2.1.0") is None


def test_internet_e_rede_escolhe_a_mais_nova_e_no_empate_a_rede(tmp_path, monkeypatch):
    _publicar(tmp_path / "rede", "2.2.0")
    pedidos = _internet(monkeypatch, "2.3.0")
    nova = at.buscar_atualizacao(_settings(tmp_path, "dono/repo"), "2.1.0")
    assert nova.versao == "2.3.0" and not nova.da_rede
    assert pedidos == ["https://github.com/dono/repo/releases/latest/download/versao.json"]
    assert nova.endereco == "https://github.com/dono/repo/releases/download/v2.3.0/Retalhos_Setup_2.3.0.exe"

    _internet(monkeypatch, "2.2.0")
    assert at.buscar_atualizacao(_settings(tmp_path, "dono/repo"), "2.1.0").da_rede


def test_manifesto_nao_aceita_caminho_no_nome():
    nova = at.ler_manifesto({"versao": "2.2.0", "instalador": r"..\..\Windows\x.exe"}, "pasta")
    assert nova.instalador == "x.exe"
    with pytest.raises(ValueError):
        at.ler_manifesto({"versao": "2.2.0", "instalador": "virus.bat"}, "pasta")


def test_baixar_da_rede_confere_sha_e_reaproveita(tmp_path):
    _publicar(tmp_path / "rede", "2.2.0", b"x" * 1000)
    nova = at.buscar_atualizacao(_settings(tmp_path), "2.1.0")
    pasta = tmp_path / "baixados"
    (pasta).mkdir()
    (pasta / "Retalhos_Setup_2.0.0.exe").write_bytes(b"velho")
    progresso = []
    arq = at.baixar_instalador(nova, pasta, lambda f, t: progresso.append((f, t)))
    assert arq.read_bytes() == b"x" * 1000 and progresso[-1] == (1000, 1000)
    assert sorted(p.name for p in pasta.iterdir()) == ["Retalhos_Setup_2.2.0.exe"]  # o velho foi apagado
    assert at.baixar_instalador(nova, pasta) == arq  # já baixado e íntegro: não baixa de novo


def test_baixar_corrompido_nao_deixa_arquivo(tmp_path):
    _publicar(tmp_path / "rede", "2.2.0", b"conteudo", sha="0" * 64)
    nova = at.buscar_atualizacao(_settings(tmp_path), "2.1.0")
    with pytest.raises(ValueError, match="corrompido"):
        at.baixar_instalador(nova, tmp_path / "baixados")
    assert list((tmp_path / "baixados").iterdir()) == []


def test_baixar_da_internet(tmp_path, monkeypatch):
    _internet(monkeypatch, "2.3.0", b"bytes do github")
    nova = at.buscar_atualizacao(_settings(tmp_path, "dono/repo"), "2.1.0")
    assert at.baixar_instalador(nova, tmp_path / "b").read_bytes() == b"bytes do github"


def test_pasta_rede_aceita_zip_antigo_ou_pasta():
    assert at.pasta_rede(Settings(update_zip=r"\\GDD02\sistema\Developer\Retalhos.zip")) == r"\\GDD02\sistema\Developer"
    assert at.pasta_rede(Settings(update_zip=r"\\GDD02\sistema\Developer")) == r"\\GDD02\sistema\Developer"
    assert at.pasta_rede(Settings()) == ""


def test_repo_padrao_e_gravado_no_settings(tmp_path):
    s = Settings(path=tmp_path / "Settings.json")
    assert s.update_repo == "EliveltonZ/Retalhos-Releases"
    s.save()
    assert json.loads((tmp_path / "Settings.json").read_text(encoding="utf-8"))["RepoAtualizacao"] == s.update_repo


def test_janela_avisa_na_barra_e_pergunta_uma_vez(settings, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QApplication

    from retalhos.app import create_app
    from retalhos.ui import main_window
    create_app()
    perguntas = []
    monkeypatch.setattr(main_window.AtualizacaoDialog, "exec", lambda self: perguntas.append(self.nova.versao))
    monkeypatch.setattr(main_window, "pasta_downloads", lambda: tmp_path / "baixados")
    _publicar(tmp_path / "rede", "9.0.0")
    settings.update_zip = str(tmp_path / "rede" / "Retalhos.zip")
    w = main_window.MainWindow(settings)
    w.show()
    QApplication.processEvents()

    w._procurar_em_segundo_plano()
    w._update_worker.wait(10_000)
    QApplication.processEvents()
    assert w.bt_nova_versao.isVisible() and "9.0.0" in w.bt_nova_versao.text()
    assert perguntas == ["9.0.0"]

    w._procurar_em_segundo_plano()  # 4 h depois: a mesma versão não pergunta de novo, só fica o aviso
    w._update_worker.wait(10_000)
    QApplication.processEvents()
    assert perguntas == ["9.0.0"] and w.bt_nova_versao.isVisible()

    w.bt_nova_versao.click()  # clicar no aviso pergunta de novo
    assert perguntas == ["9.0.0", "9.0.0"]

    (tmp_path / "rede" / "versao.json").unlink()  # já atualizado: o aviso some
    w._procurar_em_segundo_plano()
    w._update_worker.wait(10_000)
    QApplication.processEvents()
    assert not w.bt_nova_versao.isVisible()
    w.update_timer.stop()
    w.refresh_timer.stop()
    w.close()
