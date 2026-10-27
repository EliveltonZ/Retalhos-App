"""Prévia da capa do lote com dados de exemplo, para testar cores e layout.

Uso (na pasta do projeto)::

    .venv\\Scripts\\python -m retalhos.previa_capa

Gera ``teste_lote\\PREVIA_CAPA.xlsx`` e ``.pdf`` e abre o PDF. Não usa banco nem rede.
As cores ficam no bloco "CORES DA CAPA" de ``retalhos/services/capa_lote.py``.
"""
from __future__ import annotations

import os
from datetime import datetime

from .paths import app_dir
from .services.capa_lote import (
    CapaLote, ChapaLote, ProjetoLote, RetalhoLote, exportar_pdf, gerar_capa, texto_passagens,
)


def capa_exemplo() -> CapaLote:
    return CapaLote(
        "2566", datetime.now(),
        projetos=[
            ProjetoLote("13955", "5479", "SOLTEIRO", "GABRIELA AGOSTINETO GIACON", "18/11/2026"),
            ProjetoLote("13956", "5480", "BANHO SUITE CASAL", "GABRIELA AGOSTINETO GIACON", "18/11/2026"),
            ProjetoLote("13957", "5481", "BANHO SOCIAL", "GABRIELA AGOSTINETO GIACON", "20/11/2026"),
        ],
        chapas=[
            ChapaLote("BRANCO TX", "6", 3, "2740 x 1840"), ChapaLote("BRANCO TX", "15", 7, "2740 x 1820"),
            ChapaLote("FRAPE MATT (ARAUCO)", "18", 2, "2740 x 1840"),
            ChapaLote("ITAPUA ESSENCIAL (DURATEX)", "15", 6, "2740 x 1840"),
        ],
        retalhos=[
            RetalhoLote("3", "15", "ITAPUA ESSENCIAL (DURATEX)", "2460 x 426", "13955"),
            RetalhoLote("12", "15", "ITAPUA ESSENCIAL (DURATEX)", "2340 x 890", "13955"),
            RetalhoLote("5", "15", "BRANCO TX", "1320 x 600", "13956", passagem=0),
            RetalhoLote("7", "18", "CARVALHO MALVA NATURALE TRAMATO (GUARARAPES)", "2740 x 390", "13956"),
            RetalhoLote("", "15", "BRANCO TX", "980 x 450", "13957", encontrado=False, passagem=1),
            RetalhoLote("", "15", "FRAPE MATT (ARAUCO)", "2740 x 660", "13957", encontrado=False),
        ],
        passagens=[("13955", "13956"), ("13956", "13957")],
        observacoes=texto_passagens([("13955", "13956"), ("13956", "13957")])
        + "\nPrévia com dados de exemplo para testar cores e layout.",
    )


def main() -> None:
    destino = app_dir() / "teste_lote" / "PREVIA_CAPA.xlsx"
    try:
        xlsx = gerar_capa(capa_exemplo(), destino)
    except PermissionError:
        print(f"Feche o arquivo {destino.name} no Excel e rode de novo.")
        return
    try:
        arquivo = exportar_pdf(xlsx)
    except PermissionError:
        print(f"Feche o {destino.with_suffix('.pdf').name} no leitor de PDF e rode de novo.")
        return
    except RuntimeError as exc:
        print(f"{exc}\nAbrindo o Excel no lugar do PDF.")
        arquivo = xlsx
    print(f"Prévia gerada: {arquivo}")
    os.startfile(arquivo)  # noqa: S606 - Windows


if __name__ == "__main__":
    main()
