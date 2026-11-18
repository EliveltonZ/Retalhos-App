"""Atualização do sistema: procura uma versão nova na internet (GitHub) e na pasta da rede.

Cada versão publicada tem um ``versao.json`` ao lado do instalador::

    {"versao": "2.2.0", "instalador": "Retalhos_Setup_2.2.0.exe", "sha256": "...", "tamanho": 89212878,
     "data": "18/11/2026", "notas": "texto livre (o que mudou)"}

- Internet: Releases do repositório público ``RepoAtualizacao`` do Settings.json (só instaladores; o código fica no privado).
  O ``versao.json`` é baixado de ``releases/latest/download/``, que não entra no limite de consultas da API.
- Rede: a pasta do ``local_zip`` do Settings.json (ex.: ``\\\\GDD02\\sistema\\Developer\\``).

Sem internet e sem rede, a procura falha em silêncio. Se as duas fontes têm a mesma versão, usa a rede
(baixa mais rápido). O instalador baixado é conferido pelo SHA-256 antes de ser executado.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .. import __version__
from ..config import Settings

MANIFESTO = "versao.json"
_TIMEOUT = 8
_BLOCO = 256 * 1024
_USER_AGENT = f"Retalhos/{__version__}"


@dataclass(frozen=True)
class NovaVersao:
    versao: str
    instalador: str  # nome do arquivo
    sha256: str
    tamanho: int
    data: str
    notas: str
    origem: str  # URL ou pasta de onde baixar o instalador

    @property
    def da_rede(self) -> bool:
        return not self.origem.lower().startswith("http")

    @property
    def endereco(self) -> str:
        if self.da_rede:
            return str(Path(self.origem) / self.instalador)
        return f"{self.origem.rstrip('/')}/{self.instalador}"


def versao_tupla(texto: str) -> tuple[int, ...]:
    """``"v2.10.1"`` -> ``(2, 10, 1)``; partes não numéricas viram 0."""
    partes = []
    for parte in texto.strip().lstrip("vV").split("."):
        digitos = "".join(c for c in parte if c.isdigit())
        partes.append(int(digitos) if digitos else 0)
    while len(partes) > 1 and partes[-1] == 0:
        partes.pop()
    return tuple(partes)


def ler_manifesto(dados: dict, origem: str) -> NovaVersao:
    versao = str(dados["versao"]).strip()
    instalador = Path(str(dados["instalador"])).name  # só o nome: nunca um caminho vindo de fora
    if not versao or not instalador.lower().endswith(".exe"):
        raise ValueError("versao.json inválido")
    return NovaVersao(versao, instalador, str(dados.get("sha256", "")).lower(), int(dados.get("tamanho") or 0),
                      str(dados.get("data", "")), str(dados.get("notas", "")), origem)


def _abrir_url(url: str, timeout: float):
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 - só https do GitHub


def _da_internet(repo: str, timeout: float) -> NovaVersao | None:
    if not repo:
        return None
    base = f"https://github.com/{repo}/releases"
    try:
        with _abrir_url(f"{base}/latest/download/{MANIFESTO}", timeout) as resp:
            nova = ler_manifesto(json.loads(resp.read(64 * 1024).decode("utf-8-sig")), "")
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return NovaVersao(**{**nova.__dict__, "origem": f"{base}/download/v{nova.versao}"})


def _da_rede(pasta: str) -> NovaVersao | None:
    if not pasta:
        return None
    try:
        arquivo = Path(pasta) / MANIFESTO
        nova = ler_manifesto(json.loads(arquivo.read_text(encoding="utf-8-sig")), str(Path(pasta)))
        return nova if (Path(pasta) / nova.instalador).is_file() else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def pasta_rede(settings: Settings) -> str:
    """Pasta da rede com as versões: a mesma do antigo ``Retalhos.zip`` (chave ``local_zip``)."""
    caminho = settings.update_zip.strip()
    if not caminho:
        return ""
    return str(Path(caminho).parent) if Path(caminho).suffix else caminho


def buscar_atualizacao(settings: Settings, versao_atual: str = __version__,
                       timeout: float = _TIMEOUT) -> NovaVersao | None:
    """A versão mais nova que a instalada, ou ``None`` (inclusive sem internet e sem rede)."""
    atual = versao_tupla(versao_atual)
    candidatas = [v for v in (_da_rede(pasta_rede(settings)), _da_internet(settings.update_repo, timeout))
                  if v is not None and versao_tupla(v.versao) > atual]
    if not candidatas:
        return None
    # a mais nova; no empate, a da rede (vem primeiro na lista e max() mantém a primeira)
    return max(candidatas, key=lambda v: versao_tupla(v.versao))


def baixar_instalador(nova: NovaVersao, pasta: Path,
                      progresso: Callable[[int, int], None] | None = None) -> Path:
    """Copia/baixa o instalador para ``pasta`` e confere o SHA-256. Reaproveita um download já feito."""
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nova.instalador
    if destino.is_file() and nova.sha256 and _sha256(destino) == nova.sha256:
        return destino
    for antigo in pasta.glob("Retalhos_Setup_*.exe"):  # versões baixadas antes
        antigo.unlink(missing_ok=True)
    parcial = destino.with_suffix(".parcial")
    try:
        if nova.da_rede:
            with open(nova.endereco, "rb") as origem, open(parcial, "wb") as saida:
                _copiar(origem, saida, nova.tamanho, progresso)
        else:
            with _abrir_url(nova.endereco, 60) as resp, open(parcial, "wb") as saida:
                total = int(resp.headers.get("Content-Length") or nova.tamanho or 0)
                _copiar(resp, saida, total, progresso)
        if nova.sha256 and _sha256(parcial) != nova.sha256:
            raise ValueError("O arquivo baixado está corrompido ou incompleto. Tente de novo.")
        parcial.replace(destino)
    finally:
        parcial.unlink(missing_ok=True)
    return destino


def _copiar(origem, saida, total: int, progresso: Callable[[int, int], None] | None) -> None:
    feito = 0
    while bloco := origem.read(_BLOCO):
        saida.write(bloco)
        feito += len(bloco)
        if progresso:
            progresso(feito, max(total, feito))


def _sha256(arquivo: Path) -> str:
    h = hashlib.sha256()
    with open(arquivo, "rb") as fp:
        while bloco := fp.read(1024 * 1024):
            h.update(bloco)
    return h.hexdigest()


def executar_instalador(instalador: Path) -> None:
    """Instala sem perguntas; o instalador fecha o Retalhos que estiver aberto e o abre de novo no fim."""
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # sobrevive ao app fechar
    subprocess.Popen(  # noqa: S603
        [str(instalador), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/REABRIR"],
        creationflags=flags, close_fds=True,
    )


def limpar_downloads(pasta: Path) -> None:
    """Depois de atualizado, o instalador baixado não serve mais."""
    shutil.rmtree(pasta, ignore_errors=True)
