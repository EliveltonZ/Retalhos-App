"""Impressão de conferência: PDF com exatamente o que está filtrado (e na ordem) da tela principal."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import datetime  # noqa: E402

from retalhos.models import Retalho  # noqa: E402
from retalhos.services import EstoqueService  # noqa: E402


def _r(rid, setor="5", reserva="", desc="BRANCO TX"):
    return Retalho(rid, setor, 10, "15", desc, 1000, 500, datetime(2026, 11, 1), reserva, "", "ANA")


def test_html_tem_linhas_resumo_e_escapa_texto():
    from retalhos.ui.impressao import montar_html
    html = montar_html([_r(1, "12"), _r(2, "2", "14078"), _r(3, "", desc="A&B <X>")], "Setor contém \"1\"",
                       "BETO", datetime(2026, 11, 18, 9, 30))
    assert html.count("<tr") == 4  # cabeçalho + 3 retalhos
    assert "<b>3 retalho(s)</b> · 1 reservado(s) · setor(es): 2, 12, —" in html
    assert "A&amp;B &lt;X&gt;" in html and "18/11/2026 09:30 · emitido por BETO" in html
    assert "class=res" in html  # reservado destacado


def test_pdf_varias_paginas(tmp_path):
    from PySide6.QtPdf import QPdfDocument

    from retalhos.app import create_app
    from retalhos.ui.impressao import gerar_pdf_conferencia
    create_app()
    pdf = gerar_pdf_conferencia([_r(i) for i in range(120)], "Todos", "ANA", tmp_path / "x" / "c.pdf")
    doc = QPdfDocument()
    doc.load(str(pdf))
    assert doc.status() == QPdfDocument.Status.Ready and doc.pageCount() >= 3


def test_tela_principal_imprime_o_filtrado(settings, monkeypatch, tmp_path):
    from retalhos.app import create_app
    from retalhos.ui import main_window
    create_app()
    svc = EstoqueService(settings)
    a = svc.lancar_retalho(10, 1000, 500, "15")
    svc.lancar_retalho(20, 900, 400, "3")
    c = svc.lancar_retalho(10, 800, 400, "15")
    w = main_window.MainWindow(settings)
    w.reload()

    capturado = {}

    def falso_pdf(retalhos, filtro, usuario, destino):
        capturado.update(ids=[r.id for r in retalhos], filtro=filtro, destino=destino)
        return destino

    monkeypatch.setattr(main_window, "gerar_pdf_conferencia", falso_pdf)
    monkeypatch.setattr(main_window, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(main_window.os, "startfile", lambda arquivo: capturado.update(aberto=arquivo), raising=False)

    w.cb_coluna.setCurrentIndex(w.cb_coluna.findText("Setor"))
    w.txt_filter.setText("15")  # imprime na hora, sem esperar a pausa de digitação
    w.print_filtered()
    assert sorted(capturado["ids"]) == [a, c]
    assert capturado["filtro"].startswith('Setor contém "15"  ·  Todos')
    assert capturado["aberto"] == capturado["destino"] and capturado["destino"].parent == tmp_path / "conferencia"

    w.txt_filter.setText("999")
    w._apply_filter()
    assert not w.bt_imprimir.isEnabled()  # nada na tela, nada para imprimir
    w.close()
