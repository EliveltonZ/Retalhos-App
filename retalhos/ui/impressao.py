"""Lista de conferência de estoque em PDF (A4), feita a partir do que está filtrado na tela principal.

Cada linha tem uma caixa para marcar à mão e espaço para anotação. O cabeçalho da tabela se repete
em todas as páginas e o rodapé numera as páginas.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from html import escape
from pathlib import Path

from PySide6.QtCore import QMarginsF, QRectF, QSizeF
from PySide6.QtGui import QFont, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument

from ..models import Retalho

_CSS = """
body { font-family: 'Segoe UI'; font-size: 8.5pt; color: #111; }
h1 { font-size: 14pt; margin: 0; }
p.info { color: #444; margin: 2px 0 8px 0; }
table { border-collapse: collapse; }
th { background: #e8eef7; font-weight: 600; padding: 4px 5px; border: 1px solid #9aa3b2; }
td { padding: 4px 5px; border: 1px solid #b8c0cc; }
td.c { text-align: center; }
td.box { text-align: center; font-size: 11pt; color: #555; }
tr.res td { background: #fff7d6; }
"""


def _ordem_setor(setor: str) -> tuple:
    return (0, int(setor), "") if setor.isdigit() else (1, 0, setor)


def montar_html(retalhos: Sequence[Retalho], filtro: str, usuario: str, quando: datetime) -> str:
    setores = sorted({r.setor or "—" for r in retalhos}, key=_ordem_setor)
    reservados = sum(r.reservado for r in retalhos)
    linhas = []
    for r in retalhos:
        linhas.append(
            f"<tr{' class=res' if r.reservado else ''}>"
            f"<td class=box>☐</td><td class=c>{r.id}</td><td class=c>{escape(r.setor)}</td>"
            f"<td class=c>{r.codigo}</td><td class=c>{escape(r.espessura)}</td><td>{escape(r.descricao)}</td>"
            f"<td class=c>{r.largura:g} x {r.altura:g}</td><td class=c>{escape(r.reserva)}</td><td></td></tr>"
        )
    return f"""<html><head><style>{_CSS}</style></head><body>
<h1>Conferência de estoque de retalhos</h1>
<p class=info>
  {quando:%d/%m/%Y %H:%M} · emitido por {escape(usuario or '—')}<br>
  Filtro: {escape(filtro)}<br>
  <b>{len(retalhos)} retalho(s)</b> · {reservados} reservado(s) · setor(es): {escape(', '.join(setores)) or '—'}
</p>
<table width=100% cellspacing=0>
<thead><tr>
  <th width=4%>OK</th><th width=7%>ID</th><th width=7%>Setor</th><th width=6%>Cód.</th><th width=5%>Esp.</th>
  <th>Material</th><th width=12%>Medida</th><th width=9%>Reserva</th><th width=16%>Observação</th>
</tr></thead>
{''.join(linhas)}
</table>
<p class=info>Conferido por: ______________________________ &nbsp;&nbsp; Data: ____/____/______</p>
</body></html>"""


def gerar_pdf_conferencia(retalhos: Sequence[Retalho], filtro: str, usuario: str, destino: str | Path) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    quando = datetime.now()

    writer = QPdfWriter(str(destino))
    writer.setTitle("Conferência de estoque de retalhos")
    writer.setResolution(300)
    margem_mm = 12
    writer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait,
                                     QMarginsF(margem_mm, margem_mm, margem_mm, margem_mm + 4),
                                     QPageLayout.Unit.Millimeter))

    doc = QTextDocument()
    doc.setDefaultFont(QFont("Segoe UI", 9))
    doc.setDocumentMargin(0)
    doc.setHtml(montar_html(retalhos, filtro, usuario, quando))
    tabela = doc.rootFrame().childFrames()[0] if doc.rootFrame().childFrames() else None
    if tabela is not None:  # cabeçalho da tabela repetido em todas as páginas
        fmt = tabela.frameFormat().toTableFormat()
        fmt.setHeaderRowCount(1)
        tabela.setFrameFormat(fmt)

    # página em "pontos" do documento: largura útil do A4 a 300 dpi, desenhada em escala
    area = writer.pageLayout().paintRectPixels(writer.resolution())
    escala = writer.resolution() / 96  # o QTextDocument trabalha em 96 dpi
    pagina = QSizeF(area.width() / escala, area.height() / escala)
    doc.setPageSize(pagina)
    total = doc.pageCount()

    p = QPainter(writer)
    rodape = QFont("Segoe UI", 7)
    try:
        for i in range(total):
            if i:
                writer.newPage()
            p.save()
            p.scale(escala, escala)
            p.translate(0, -i * pagina.height())
            doc.drawContents(p, QRectF(0, i * pagina.height(), pagina.width(), pagina.height()))
            p.restore()
            p.setFont(rodape)
            p.drawText(QRectF(0, area.height() + 8, area.width(), 60), 0x0084,  # AlignRight | AlignVCenter
                       f"Emitido em {quando:%d/%m/%Y %H:%M}  ·  Página {i + 1} de {total}")
    finally:
        p.end()
    return destino
