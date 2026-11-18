"""Publica a versão atual do Retalhos para as máquinas encontrarem em Ajuda › Procurar atualizações.

Uso (na raiz do projeto):  ferramentas\\publicar_versao.bat   [--sem-build] [--so-rede] [--so-internet]

1. Gera o instalador (ferramentas\\gerar_instalador.bat), a não ser com --sem-build.
2. Escreve dist\\instalador\\versao.json (versão, SHA-256, tamanho, data e as notas de instalador\\novidades.md).
3. Internet: cria a Release v<versão> no repositório público (RepoAtualizacao do Settings.json) com o
   instalador e o versao.json. Precisa do GitHub CLI logado (gh auth login).
4. Rede: copia o instalador e o versao.json para a pasta do local_zip (ex.: \\\\GDD02\\sistema\\Developer).

A versão vem de retalhos/__init__.py: suba o número antes de publicar uma versão nova.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from retalhos import __version__  # noqa: E402
from retalhos.config import Settings  # noqa: E402
from retalhos.services.atualizacao import MANIFESTO, pasta_rede  # noqa: E402

NOVIDADES = RAIZ / "instalador" / "novidades.md"
SAIDA = RAIZ / "dist" / "instalador"


def sha256(arquivo: Path) -> str:
    h = hashlib.sha256()
    with open(arquivo, "rb") as fp:
        while bloco := fp.read(1024 * 1024):
            h.update(bloco)
    return h.hexdigest()


def passo(texto: str) -> None:
    print(f"\n=== {texto}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Publica a versão atual do Retalhos")
    ap.add_argument("--sem-build", action="store_true", help="usa o instalador já gerado")
    ap.add_argument("--so-rede", action="store_true", help="publica só na pasta da rede")
    ap.add_argument("--so-internet", action="store_true", help="publica só no GitHub")
    args = ap.parse_args()

    settings = Settings.load(RAIZ / "Settings.json")
    versao = __version__
    instalador = SAIDA / f"Retalhos_Setup_{versao}.exe"
    print(f"Retalhos {versao}")

    if not NOVIDADES.is_file() or not NOVIDADES.read_text(encoding="utf-8").strip():
        print(f"Escreva o que mudou nesta versão em {NOVIDADES} (aparece para o usuário) e rode de novo.")
        return 1
    notas = NOVIDADES.read_text(encoding="utf-8").strip()

    sujo = subprocess.run(["git", "status", "--porcelain", "--", "retalhos"], cwd=RAIZ,
                          capture_output=True, text=True).stdout.strip()
    if sujo:
        print("Atenção: há alterações no código ainda sem commit (a versão publicada vai incluí-las).")

    if not args.sem_build:
        passo("Gerando o instalador")
        if subprocess.run(["cmd", "/c", str(RAIZ / "ferramentas" / "gerar_instalador.bat")], cwd=RAIZ).returncode:
            print("Falha ao gerar o instalador.")
            return 1
    if not instalador.is_file():
        print(f"Instalador não encontrado: {instalador}")
        return 1

    manifesto = SAIDA / MANIFESTO
    manifesto.write_text(json.dumps({
        "versao": versao,
        "instalador": instalador.name,
        "sha256": sha256(instalador),
        "tamanho": instalador.stat().st_size,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "notas": notas,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{manifesto.name} gravado")

    erros = 0
    if not args.so_rede:
        passo(f"Internet: Release v{versao} em {settings.update_repo}")
        gh = shutil.which("gh")
        if gh is None:  # recém-instalado: o PATH só atualiza em um terminal novo
            padrao = Path(r"C:\Program Files\GitHub CLI\gh.exe")
            gh = str(padrao) if padrao.is_file() else None
        if gh is None:
            print("GitHub CLI não encontrado. Instale com: winget install GitHub.cli  e depois: gh auth login")
            erros += 1
        else:
            r = subprocess.run([gh, "release", "create", f"v{versao}", str(instalador), str(manifesto),
                                "--repo", settings.update_repo, "--title", f"Retalhos {versao}",
                                "--notes", notas, "--latest"], cwd=RAIZ)
            if r.returncode:
                print("Falha ao publicar no GitHub (essa versão já foi publicada? suba o número da versão).")
                erros += 1
            else:
                print("Publicado no GitHub.")

    if not args.so_internet:
        pasta = pasta_rede(settings)
        passo(f"Rede: {pasta or '(local_zip não configurado)'}")
        if not pasta or not Path(pasta).is_dir():
            print("Pasta da rede indisponível; publicação na rede ignorada.")
            erros += 1
        else:
            destino = Path(pasta)
            shutil.copy2(instalador, destino / instalador.name)  # instalador antes: o versao.json só aparece
            shutil.copy2(manifesto, destino / f"{MANIFESTO}.tmp")  # quando o instalador já está inteiro lá
            (destino / f"{MANIFESTO}.tmp").replace(destino / MANIFESTO)
            for antigo in destino.glob("Retalhos_Setup_*.exe"):
                if antigo.name != instalador.name:
                    antigo.unlink(missing_ok=True)
            print("Copiado para a rede.")

    print("\nPronto." if not erros else "\nTerminado com avisos (veja acima).")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
