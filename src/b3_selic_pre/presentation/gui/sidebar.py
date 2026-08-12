"""Mixin de construção e atualização do painel de análise lateral."""

from __future__ import annotations

from typing import Any

from b3_selic_pre.application.analyze import (
    EvolutionReport,
    analyze,
    analyze_evolution,
)
from b3_selic_pre.application.analyze._config import CurvaJurosConfig
from b3_selic_pre.application.analyze._texto_evolucao import montar_evolucao_resumo

App = Any
Widget = Any


class SidebarMixin:
    """Gerencia o painel lateral com a análise textual da curva."""

    def _build_sidebar(self: App, parent: Widget) -> None:
        """Constrói o widget de texto rolável do painel de análise."""
        text_frame = self.ttk.Frame(parent)
        text_frame.pack(fill=self.tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.sidebar_text = self.tk.Text(
            text_frame, wrap=self.tk.WORD, state=self.tk.DISABLED,
            width=36, font=("TkDefaultFont", 9),
        )
        self.sidebar_text.tag_configure("header", font=("TkDefaultFont", 9, "bold"))
        self.sidebar_text.tag_configure("conf_high", foreground="green")
        self.sidebar_text.tag_configure("conf_mid", foreground="orange")
        self.sidebar_text.tag_configure("conf_low", foreground="red")
        self.sidebar_text.tag_configure("positive", foreground="green")
        self.sidebar_text.tag_configure("negative", foreground="red")
        scrollbar = self.ttk.Scrollbar(
            text_frame, orient=self.tk.VERTICAL,
            command=self.sidebar_text.yview,
        )
        self.sidebar_text.configure(yscrollcommand=scrollbar.set)
        self.sidebar_text.pack(side=self.tk.LEFT, fill=self.tk.BOTH, expand=True)
        scrollbar.pack(side=self.tk.RIGHT, fill=self.tk.Y)

    def _toggle_sidebar(self: App) -> None:
        """Exibe ou oculta o painel de análise conforme o checkbox correspondente."""
        self.settings["sidebar"] = self.sidebar_var.get()
        if self.sidebar_var.get():
            self.pane.add(self.sidebar_frame, weight=0)
            self._update_analysis()
        else:
            self.pane.forget(self.sidebar_frame)

    def _update_analysis(self: App) -> None:
        """Reconstrói o texto do painel de análise a partir dos dados atuais."""
        if not self.sidebar_var.get():
            return
        report = analyze(
            records=self.records,
            historical_data=self.historical_data,
            view_mode=self.view_var.get(),
            evolution_active=self.evolution_var.get(),
        )
        self.sidebar_text.configure(state=self.tk.NORMAL)
        self.sidebar_text.delete("1.0", self.tk.END)
        self._render_paragraphs(self.sidebar_text, report.statements)
        evolution_report = self._build_evolution_report()
        if evolution_report is not None:
            self.sidebar_text.insert(self.tk.END, "\n─╌─╌─╌─╌─╌─╌─╌─╌─╌╌\n\n")
            self.sidebar_text.insert(
                self.tk.END, "Evolução da Curva\n\n", "header"
            )
            config = CurvaJurosConfig.from_settings()
            blocos = montar_evolucao_resumo(evolution_report, config.evolucao)
            self._render_paragraphs(self.sidebar_text, blocos)
        self.sidebar_text.configure(state=self.tk.DISABLED)

    def _build_evolution_report(self: App) -> EvolutionReport | None:
        """Devolve o relatório de evolução quando há duas ou mais datas."""
        if not (self.evolution_var.get() and self.historical_data):
            return None
        sorted_dates = sorted(self.historical_data.keys())
        if len(sorted_dates) < 2:
            return None
        previous_date = sorted_dates[-2]
        previous_records = self.historical_data[previous_date]
        return analyze_evolution(self.records, previous_records, config=None)

    def _render_paragraphs(self: App, text: Widget, paragraphs: list[str]) -> None:
        """Insere parágrafos formatados no widget de texto do painel."""
        for i, paragraph in enumerate(paragraphs):
            for j, line in enumerate(paragraph.split("\n")):
                if not line.strip():
                    continue
                if j == 0:
                    tag = "header"
                elif line.startswith("▲"):
                    tag = "positive"
                elif line.startswith("▼"):
                    tag = "negative"
                else:
                    tag = None
                self._insert_line(text, line, tag)
            if i < len(paragraphs) - 1:
                text.insert(self.tk.END, "\n")

    def _insert_line(self: App, text: Widget, line: str, tag: str | None) -> None:
        """Insere uma única linha no widget de texto, com a tag quando houver."""
        if tag is None:
            text.insert(self.tk.END, line + "\n")
        else:
            text.insert(self.tk.END, line + "\n", tag)
