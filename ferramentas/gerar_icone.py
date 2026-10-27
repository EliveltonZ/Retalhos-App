"""Gera o ícone do sistema: chapa de MDF com plano de corte e o retalho (âmbar) sendo reaproveitado.

Cada tamanho é desenhado separadamente (fica nítido de 16 a 256 px). Uso, na pasta do projeto::

    .venv\\Scripts\\python ferramentas\\gerar_icone.py            # grava retalhos\\resources\\icon_retalho.ico
    .venv\\Scripts\\python ferramentas\\gerar_icone.py --previa   # só gera ferramentas\\icone_previa.png

Requer Pillow (``requirements-dev.txt``). As cores ficam no bloco CORES abaixo.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPen  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "retalhos" / "resources" / "icon_retalho.ico"
TAMANHOS = [16, 20, 24, 32, 40, 48, 64, 128, 256]

# ---------------------------------------------------------------- CORES
FUNDO_TOPO, FUNDO_BASE = "#3B82F6", "#1D4ED8"         # azul do app
CHAPA, CHAPA_BORDA, CORTE = "#F3DFB8", "#C08A4A", "#B9894C"  # MDF cru, espessura e linhas de corte
RETALHO_TOPO, RETALHO_BASE = "#FCD34D", "#F59E0B"     # retalho destacado (âmbar)


def _gradiente(y0: float, y1: float, c0: str, c1: str) -> QLinearGradient:
    g = QLinearGradient(0, y0, 0, y1)
    g.setColorAt(0, QColor(c0))
    g.setColorAt(1, QColor(c1))
    return g


def desenhar(tamanho: int) -> QImage:
    img = QImage(tamanho, tamanho, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    u = tamanho / 64  # desenho numa grade de 64 x 64
    detalhe = tamanho >= 32
    linha = max(1.0, 1.5 * u)

    # fundo arredondado
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(_gradiente(0, tamanho, FUNDO_TOPO, FUNDO_BASE))
    p.drawRoundedRect(QRectF(1 * u, 1 * u, 62 * u, 62 * u), 14 * u, 14 * u)

    # chapa de MDF (com espessura embaixo e sombra)
    chapa = QRectF(9 * u, 12 * u, 46 * u, 31 * u)
    p.setBrush(QColor(0, 0, 0, 55))
    p.drawRoundedRect(chapa.translated(0, 4 * u), 2.5 * u, 2.5 * u)
    p.setBrush(QColor(CHAPA_BORDA))
    p.drawRoundedRect(chapa.translated(0, 2.5 * u), 2.5 * u, 2.5 * u)
    p.setBrush(QColor(CHAPA))
    p.drawRoundedRect(chapa, 2.5 * u, 2.5 * u)

    # plano de corte (peças)
    pen = QPen(QColor(CORTE), linha)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    p.setPen(pen)
    p.drawLine(QPointF(31 * u, 12 * u), QPointF(31 * u, 43 * u))
    if detalhe:
        p.drawLine(QPointF(9 * u, 27 * u), QPointF(31 * u, 27 * u))
        p.drawLine(QPointF(20 * u, 27 * u), QPointF(20 * u, 43 * u))
        p.drawLine(QPointF(31 * u, 24 * u), QPointF(55 * u, 24 * u))

    # lugar de onde o retalho saiu (tracejado)
    vazio = QRectF(36 * u, 29 * u, 19 * u, 14 * u)
    if detalhe:
        tracejado = QPen(QColor(CORTE), linha, Qt.PenStyle.DashLine)
        p.setPen(tracejado)
        p.setBrush(QColor("#E7CFA0"))
        p.drawRect(vazio)

    # retalho destacado, deslocado para fora da chapa
    retalho = vazio.translated(5 * u, 9 * u)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(0, 0, 0, 70))
    p.drawRoundedRect(retalho.translated(1.2 * u, 1.8 * u), 1.8 * u, 1.8 * u)
    p.setBrush(_gradiente(retalho.top(), retalho.bottom(), RETALHO_TOPO, RETALHO_BASE))
    p.setPen(QPen(QColor("#FFFFFF"), max(1.0, 1.6 * u)))
    p.drawRoundedRect(retalho, 1.8 * u, 1.8 * u)
    if tamanho >= 48:  # veios de madeira no retalho
        veio = QPen(QColor(180, 83, 9, 90), max(1.0, 0.9 * u))
        p.setPen(veio)
        for dy in (4.0, 7.0, 10.0):
            y = retalho.top() + dy * u
            p.drawLine(QPointF(retalho.left() + 3 * u, y), QPointF(retalho.right() - 3 * u, y - 0.8 * u))
    p.end()
    return img


def _para_pil(img: QImage) -> Image.Image:
    dados = QByteArray()
    buf = QBuffer(dados)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(dados))).convert("RGBA")


def main() -> None:
    QGuiApplication.instance() or QGuiApplication(sys.argv)
    imagens = {t: _para_pil(desenhar(t)) for t in TAMANHOS}

    # prévia lado a lado (fundo claro e escuro) para conferir
    largura = sum(TAMANHOS) + 20 * len(TAMANHOS) + 20
    previa = Image.new("RGBA", (largura, 2 * 276 + 20), "#F3F5F9")
    previa.paste(Image.new("RGBA", (largura, 286), "#1E2128"), (0, 286))
    x = 20
    for t in TAMANHOS:
        for y in (10 + (256 - t), 296 + (256 - t)):
            previa.alpha_composite(imagens[t], (x, y))
        x += t + 20
    previa.save(RAIZ / "ferramentas" / "icone_previa.png")

    if "--previa" in sys.argv:
        print("Prévia: ferramentas/icone_previa.png")
        return
    antigo = RAIZ / "ferramentas" / "icon_retalho_antigo.ico"
    if DESTINO.exists() and not antigo.exists():
        DESTINO.replace(antigo)  # guarda o ícone anterior uma única vez (fora de resources: não vai para o .exe)
    base = imagens[256]
    base.save(DESTINO, format="ICO", sizes=[(t, t) for t in TAMANHOS],
              append_images=[imagens[t] for t in TAMANHOS if t != 256])
    print(f"Ícone gravado: {DESTINO}")


if __name__ == "__main__":
    main()
