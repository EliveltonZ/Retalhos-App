from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QPlainTextEdit, QProgressBar, QPushButton, QSplitter,
    QWidget,
)

from ...paths import app_dir
from ...services import EstoqueService
from ...services.capa_lote import CapaLote, avaliar_impressao, exportar_pdf, gerar_capa, nome_cor_passagem
from ...services.consumo import (
    SITUACAO_DISPONIVEL, SITUACAO_OUTRO, SITUACAO_PROJETO, AnaliseConsumo, ChapaInteira, RetalhoUsado,
    exportar_excel, resumo_chapas, resumo_retalhos,
)
from ...services.estoque import projeto_da_reserva
from ..theme import ROW_ERROR, ROW_FULL_SHEET, ROW_INACTIVE, cor_sobra
from ..widgets import (
    ALIGN_LEFT, BaseDialog, Column, DataTable, ObjectTableModel, Worker, busy, button, card, choose, confirm,
    label, show_exception, warning,
)

_EXT = ".cutplanning"
_ARQUIVO_ABERTO = ("Não foi possível salvar:\n{}\n\nO arquivo provavelmente está aberto no Excel. "
                   "Feche-o e tente novamente, ou salve com outro nome.")


class CapaLoteDialog(BaseDialog):
    """Confirma o número do lote e as observações antes de gerar a capa."""

    def __init__(self, capa: CapaLote, parent: QWidget | None = None) -> None:
        super().__init__(
            "Capa do lote",
            f"{len(capa.projetos)} projeto(s) · {capa.total_chapas} chapa(s) inteira(s) · "
            f"{len(capa.retalhos)} retalho(s)",
            parent,
        )
        self.capa = capa
        self.setMinimumWidth(520)
        frame, layout = card()
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.txt_lote = QLineEdit(capa.lote)
        self.txt_lote.setPlaceholderText("Número do lote")
        form.addRow("Lote:", self.txt_lote)
        projetos = label(", ".join(p.projeto for p in capa.projetos) or "—")
        projetos.setWordWrap(True)
        form.addRow(f"Projetos ({len(capa.projetos)}):", projetos)
        fora = [p.projeto for p in capa.projetos if not p.no_conf_folha]
        if fora:
            aviso = label(f"Fora do ConFolhaLote: {', '.join(fora)}. Pedido, ambiente e cliente vêm do plano "
                          "de corte; a data de entrega fica em branco.", "Muted")
            aviso.setWordWrap(True)
            form.addRow("", aviso)
        self.txt_obs = QPlainTextEdit(capa.observacoes)
        self.txt_obs.setPlaceholderText("Observações do lote (opcional)")
        self.txt_obs.setFixedHeight(90)
        form.addRow("Observações:", self.txt_obs)
        layout.addLayout(form)
        self.body.addWidget(frame)

        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        bt_ok = button("Gerar capa", "primary")
        bt_ok.clicked.connect(self._ok)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(bt_ok)
        self.txt_lote.setFocus()

    def _ok(self) -> None:
        self.capa.lote = self.txt_lote.text().strip()
        self.capa.observacoes = self.txt_obs.toPlainText().strip()
        self.accept()


def _status_reserva(r: RetalhoUsado) -> str:
    if r.retalho is None:
        return "Não encontrado no estoque"
    if r.situacao == SITUACAO_PROJETO:
        return f"Já reservado p/ {r.retalho.reserva}"
    if r.situacao == SITUACAO_OUTRO:
        return f"Reservado p/ outro projeto ({r.retalho.reserva})"
    return f"Reservar p/ {projeto_da_reserva(r)}"


def _cor_reserva(r: RetalhoUsado):
    if r.retalho is None:
        return ROW_ERROR
    if r.situacao == SITUACAO_OUTRO:
        return ROW_FULL_SHEET
    if r.situacao == SITUACAO_PROJETO:
        return ROW_INACTIVE
    return None


class ReservaPlanoDialog(BaseDialog):
    """Conferência antes de reservar os retalhos identificados no plano de corte."""

    def __init__(self, analise: AnaliseConsumo, parent: QWidget | None = None) -> None:
        super().__init__(
            "Reservar retalhos do plano",
            "Cada retalho fica reservado para um único projeto (o primeiro que o usa) e sai da lista de "
            "disponíveis do Corte Certo. Desmarque o que não quiser reservar.",
            parent,
            resizable=True,
        )
        self.escolhidos: list[RetalhoUsado] = []
        self.resize(980, 560)
        self.model = ObjectTableModel(
            [
                Column("Situação", _status_reserva, ALIGN_LEFT, width=220),
                Column("ID", lambda r: r.retalho.id if r.retalho else None, width=70),
                Column("Setor", lambda r: r.setor, width=90),
                Column("Esp.", lambda r: r.espessura, width=50),
                Column("Material", lambda r: r.descricao, ALIGN_LEFT, stretch=True),
                Column("Medida", lambda r: r.medida, width=105),
            ],
            checkable=True,
            row_color=_cor_reserva,
            can_check=lambda r: r.situacao == SITUACAO_DISPONIVEL,
        )
        self.model.set_rows(analise.retalhos, checked=lambda r: True)
        self.body.addWidget(DataTable(self.model), 1)
        self.body.addWidget(label(
            "Cinza: já reservado para o lote  ·  Laranja: reservado para outro projeto (não será tomado)  ·  "
            "Vermelho: não encontrado no estoque", "Muted"))

        self.lb_count = label("", "Muted")
        bt_cancel = button("Cancelar")
        bt_cancel.clicked.connect(self.reject)
        self.bt_ok = button("Reservar", "primary")
        self.bt_ok.clicked.connect(self._ok)
        self.footer.addWidget(self.lb_count)
        self.footer.addStretch()
        self.footer.addWidget(bt_cancel)
        self.footer.addWidget(self.bt_ok)
        self.model.dataChanged.connect(self._atualizar)
        self._atualizar()

    def _atualizar(self, *_: object) -> None:
        n = len(self.model.checked_rows())
        self.lb_count.setText(f"{n} marcado(s) para reservar")
        self.bt_ok.setText(f"Reservar {n} retalho(s)")
        self.bt_ok.setEnabled(n > 0)

    def _ok(self) -> None:
        self.escolhidos = self.model.checked_rows()
        self.accept()



class _Painel(QWidget):
    """Cartão com título, total em destaque, legenda, tabela e botão copiar."""

    def __init__(self, titulo: str, model: ObjectTableModel, legenda: str, copiar: Callable[[], str]) -> None:
        super().__init__()
        self._copiar = copiar
        frame, layout = card()
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(frame)

        head = QHBoxLayout()
        head.addWidget(label(titulo, "SectionTitle"))
        head.addStretch()
        self.total = label("0", "StatValue")
        head.addWidget(self.total)
        layout.addLayout(head)
        self.info = label("", "Muted")
        layout.addWidget(self.info)

        self.table = DataTable(model)
        layout.addWidget(self.table, 1)

        self.legenda = label(legenda, "Muted")  # linha própria: com várias cores de sobra o texto cresce
        self.legenda.setWordWrap(True)
        layout.addWidget(self.legenda)
        foot = QHBoxLayout()
        foot.addStretch(1)
        self.bt_copy: QPushButton = button("Copiar lista", tooltip="Copia a lista para colar em e-mail ou WhatsApp")
        self.bt_copy.clicked.connect(self._copy)
        foot.addWidget(self.bt_copy)
        layout.addLayout(foot)
        self.foot = foot

    def set(self, total: int, info: str, enabled: bool) -> None:
        self.total.setText(str(total))
        self.info.setText(info)
        self.bt_copy.setText("Copiar lista")
        self.bt_copy.setEnabled(enabled)

    def _copy(self) -> None:
        QGuiApplication.clipboard().setText(self._copiar())
        self.bt_copy.setText("✔ Copiado")


class ConsumoDialog(BaseDialog):
    """Chapas inteiras por material (compras) e retalhos usados em um ou mais planos de corte."""

    def __init__(self, service: EstoqueService, parent: QWidget | None = None) -> None:
        super().__init__(
            "Consumo do plano de corte",
            "Abra (ou arraste aqui) um ou mais arquivos .cutplanning. As chapas inteiras e os retalhos "
            "usados são listados separadamente.",
            parent,
            resizable=True,
        )
        self.service = service
        self.arquivos: list[str] = []
        self.analise: AnaliseConsumo | None = None
        self.worker: Worker | None = None
        self.setAcceptDrops(True)
        self.resize(1320, 740)

        top = QHBoxLayout()
        self.lb_files = label("Nenhum arquivo selecionado.", "Muted")
        self.lb_files.setWordWrap(True)
        top.addWidget(self.lb_files, 1)
        self.bt_clear = button("Limpar")
        self.bt_clear.clicked.connect(self._clear)
        bt_add = button("Adicionar arquivos…", "primary")
        bt_add.clicked.connect(self._browse)
        top.addWidget(self.bt_clear)
        top.addWidget(bt_add)
        self.body.addLayout(top)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.body.addWidget(self.progress)

        self.model_chapas = ObjectTableModel(
            [
                Column("Qtd", lambda c: c.quantidade, width=55),
                Column("Cód.", lambda c: c.codigo, width=65),
                Column("Material", lambda c: c.descricao, ALIGN_LEFT, stretch=True),
                Column("Esp.", lambda c: c.espessura, width=50),
                Column("Medida", lambda c: c.medida, width=105),
            ],
        )
        self.model_retalhos = ObjectTableModel(
            [
                Column("Cód.", lambda r: r.codigo, width=65),
                Column("Setor", lambda r: r.setor, width=100),
                Column("Esp.", lambda r: r.espessura, width=50),
                Column("Material", lambda r: r.descricao, ALIGN_LEFT, stretch=True),
                Column("Medida", lambda r: r.medida, width=105),
                Column("Projeto", lambda r: r.projeto, width=70),
                Column("ID estoque", lambda r: r.retalho.id if r.retalho else None, width=85),
            ],
            row_color=self._cor_retalho,
        )
        self.painel_chapas = _Painel(
            "Chapas inteiras (compras)", self.model_chapas, "",
            lambda: resumo_chapas(self.analise) if self.analise else "",
        )
        self.painel_retalhos = _Painel(
            "Retalhos usados", self.model_retalhos,
            "Vermelho: retalho não encontrado no estoque",
            lambda: resumo_retalhos(self.analise) if self.analise else "",
        )
        self.bt_reservar = button("Reservar retalhos do plano", "primary",
                                  tooltip="Reserva no estoque os retalhos que este plano vai cortar")
        self.bt_reservar.clicked.connect(self._reservar)
        self.painel_retalhos.foot.insertWidget(1, self.bt_reservar)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(12)
        splitter.addWidget(self.painel_chapas)
        splitter.addWidget(self.painel_retalhos)
        splitter.setSizes([520, 760])
        self.body.addWidget(splitter, 1)

        self.bt_export = button("Exportar Excel")
        self.bt_export.clicked.connect(self._export)
        self.bt_capa = button("Gerar capa do lote", "primary",
                              tooltip="Capa de produção do lote (A4) com projetos, chapas e retalhos")
        self.bt_capa.clicked.connect(self._capa)
        bt_close = button("Fechar")
        bt_close.clicked.connect(self.reject)
        self.footer.addStretch()
        self.footer.addWidget(bt_close)
        self.footer.addWidget(self.bt_export)
        self.footer.addWidget(self.bt_capa)
        self._show(None)

    # ------------------------------------------------------------ arquivos
    def _browse(self) -> None:
        start = str(Path(self.arquivos[-1]).parent) if self.arquivos else ""
        paths, _ = QFileDialog.getOpenFileNames(self, "Planos de corte", start, f"Corte Certo (*{_EXT})")
        self.add_files(paths)

    def add_files(self, paths: list[str]) -> None:
        novos = [os.path.normpath(p) for p in paths if p.lower().endswith(_EXT)]
        novos = [p for p in novos if p not in self.arquivos]
        if novos:
            self.arquivos += novos
            self._analyze()

    def _clear(self) -> None:
        self.arquivos = []
        self._show(None)

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if any(u.toLocalFile().lower().endswith(_EXT) for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        self.add_files([u.toLocalFile() for u in event.mimeData().urls()])

    # -------------------------------------------------------------- análise
    def _analyze(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        arquivos = list(self.arquivos)
        service = self.service
        self.progress.setVisible(True)
        self.worker = Worker(lambda _progress: service.analisar_planos(arquivos), self)
        self.worker.succeeded.connect(self._show)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(lambda: self.progress.setVisible(False))
        self.worker.start()

    def _failed(self, exc: Exception) -> None:
        # volta à lista da última análise bem-sucedida
        self.arquivos = [os.path.normpath(p.arquivo) for p in self.analise.planos] if self.analise else []
        show_exception(self, "Consumo do plano de corte", exc)

    def _show(self, analise: AnaliseConsumo | None) -> None:
        self.analise = analise
        chapas: list[ChapaInteira] = analise.chapas if analise else []
        retalhos: list[RetalhoUsado] = analise.retalhos if analise else []
        self.model_chapas.set_rows(chapas)
        self.model_retalhos.set_rows(retalhos)

        materiais = len({c.codigo for c in chapas})
        self.painel_chapas.set(
            analise.total_chapas if analise else 0,
            f"{materiais} material(is)" if analise else "",
            bool(chapas),
        )
        ignoradas = analise.texto_ignoradas if analise else ""
        self.painel_chapas.legenda.setText(f"⚠ Ignoradas (material sem cadastro): {ignoradas}" if ignoradas else "")
        self.painel_chapas.legenda.setToolTip(
            "Chapas de materiais que não existem em tblChapas não entram na lista de compras." if ignoradas else ""
        )
        nao_encontrados = analise.nao_encontrados if analise else 0
        a_reservar = sum(r.situacao == SITUACAO_DISPONIVEL for r in retalhos)
        ja_reservados = sum(r.situacao == SITUACAO_PROJETO for r in retalhos)
        info = ""
        if analise:
            info = f"{len(retalhos) - nao_encontrados} identificado(s) no estoque"
            if ja_reservados:
                info += f"  ·  {ja_reservados} já reservado(s) p/ o lote"
            if nao_encontrados:
                info += f"  ·  {nao_encontrados} não encontrado(s)"
        self.painel_retalhos.set(len(retalhos), info, bool(retalhos))
        legendas = [f"{nome_cor_passagem(i).capitalize()}: sobra {o} → {d}"
                    for i, (o, d) in enumerate(analise.passagens)] if analise else []
        legendas.append("Vermelho: não está no estoque")
        self.painel_retalhos.legenda.setText("  ·  ".join(legendas))
        self.bt_reservar.setEnabled(a_reservar > 0)
        self.bt_reservar.setText(f"Reservar {a_reservar} retalho(s)" if a_reservar else "Reservar retalhos do plano")

        if analise:
            nomes = [f"{p.projeto} ({p.arquivo.name})" for p in analise.planos]
            self.lb_files.setText(f"{len(nomes)} arquivo(s): " + "  ·  ".join(nomes))
        else:
            self.lb_files.setText("Nenhum arquivo selecionado.")
        self.bt_export.setEnabled(analise is not None)
        self.bt_capa.setEnabled(analise is not None)
        self.bt_clear.setEnabled(analise is not None)

    # ------------------------------------------------------------ exportar
    def _export(self) -> None:
        if not self.analise:
            return
        pasta = self.service.settings.sheets_dir or str(app_dir())
        nome = f"CONSUMO_{'_'.join(self.analise.projetos)}.xlsx"
        destino, _ = QFileDialog.getSaveFileName(self, "Exportar consumo", os.path.join(pasta, nome), "Excel (*.xlsx)")
        if not destino:
            return
        try:
            arquivo = exportar_excel(self.analise, destino)
        except PermissionError:
            warning(self, "Exportar", _ARQUIVO_ABERTO.format(destino))
            return
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Exportar", exc)
            return
        if choose(self, "Exportar", f"Planilha gerada (abas \"Chapas inteiras\" e \"Retalhos usados\"):\n{arquivo}",
                  [("open", "Abrir planilha", ""), ("ok", "OK", "primary")], default="ok") == "open":
            os.startfile(arquivo)  # noqa: S606 - Windows

    def _cor_retalho(self, r: RetalhoUsado):
        """Sobra de outro projeto do lote: cor da passagem; senão vermelho se não está no estoque."""
        indice = self.analise.indice_passagem(r) if self.analise else None
        if indice is not None:
            return cor_sobra(indice)
        return None if r.encontrado else ROW_ERROR

    def _reservar(self) -> None:
        if not self.analise:
            return
        dlg = ReservaPlanoDialog(self.analise, self)
        if not dlg.exec() or not dlg.escolhidos:
            return
        try:
            with busy():
                r = self.service.reservar_do_plano(self.analise, dlg.escolhidos)
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Reservar retalhos", exc)
            return
        self.changed = True  # a lista da tela principal precisa refletir as reservas

        linhas = [f"✔ {len(r.reservados)} retalho(s) reservado(s)."]
        por_projeto: dict[str, list[int]] = {}
        for rid, projeto in r.reservados:
            por_projeto.setdefault(projeto, []).append(rid)
        linhas += [f"    Projeto {p}: IDs {', '.join(map(str, sorted(ids)))}" for p, ids in por_projeto.items()]
        if r.ja_reservados:
            linhas.append(f"{r.ja_reservados} já estava(m) reservado(s) para o lote.")
        if r.conflitos:
            linhas.append("\nNão reservados (conferido no banco agora):")
            linhas += [f"  • {c}" for c in r.conflitos]
        choose(self, "Reservar retalhos", "\n".join(linhas), [("ok", "OK", "primary")], "ok",
               kind="warning" if r.conflitos else "info")
        self._reanalisar()

    def _reanalisar(self) -> None:
        """Refaz a análise com o estoque atualizado (situações e IDs na tela)."""
        if self.arquivos:
            self._analyze()

    def _capa(self) -> None:
        if not self.analise:
            return
        with busy():
            capa = self.service.capa_do_lote(self.analise)
        dlg = CapaLoteDialog(capa, self)
        if not dlg.exec():
            return
        pasta = self.service.settings.sheets_dir or str(app_dir())
        nome = f"LOTE_{capa.lote or '_'.join(self.analise.projetos)}.xlsx"
        destino, _ = QFileDialog.getSaveFileName(self, "Salvar capa do lote", os.path.join(pasta, nome),
                                                 "Excel (*.xlsx)")
        if not destino:
            return
        impressao = avaliar_impressao(capa)
        if impressao.avisos and not confirm(
            self, "Capa do lote",
            "\n".join(impressao.avisos) + "\n\nA letra pode ficar pequena. Gerar mesmo assim?", default_yes=True,
        ):
            return
        try:
            arquivo = gerar_capa(capa, destino)
        except PermissionError:
            warning(self, "Capa do lote", _ARQUIVO_ABERTO.format(destino))
            return
        except Exception as exc:  # noqa: BLE001
            show_exception(self, "Capa do lote", exc)
            return

        # PDF frente (pág. 1) e verso (pág. 2): é o jeito seguro de imprimir em duplex
        pdf, erro_pdf = None, ""
        try:
            with busy():
                pdf = exportar_pdf(arquivo)
        except PermissionError:
            erro_pdf = "O PDF não foi atualizado porque está aberto. Feche-o e gere novamente."
        except RuntimeError as exc:
            erro_pdf = str(exc).splitlines()[0]

        texto = f"Capa gerada:\n{arquivo}"
        if pdf:
            texto += f"\n\nPDF para impressão (frente e verso):\n{pdf}"
        elif erro_pdf:
            texto += f"\n\n{erro_pdf}\nNo Excel, imprima com \"Imprimir Pasta de Trabalho Inteira\" e frente e verso."
        if impressao.frente_compacta or impressao.verso_compacto:
            texto += "\n\nModo compacto aplicado para caber em uma folha."
        botoes = ([("pdf", "Abrir PDF", "primary")] if pdf else []) + [("xlsx", "Abrir Excel", ""), ("ok", "OK", "")]
        escolha = choose(self, "Capa do lote", texto, botoes, default="pdf" if pdf else "ok")
        if escolha in ("pdf", "xlsx"):
            os.startfile(pdf if escolha == "pdf" else arquivo)  # noqa: S606 - Windows

    def reject(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.wait(10000)
        super().reject()
