"""Mixin de ações de cópia e atalhos da interface gráfica."""

from __future__ import annotations

import io
from typing import Any

from b3_selic_pre.application.formatting import (
    format_cli_rows,
    format_evolution_csv,
    format_yearly_rows,
)
from b3_selic_pre.application.use_cases import consolidate_by_year
from b3_selic_pre.infrastructure.desktop import create_shortcut
from b3_selic_pre.presentation.gui.tooltip import Tooltip

App = Any


class ActionsMixin:
    """Gerencia cópia de dados/gráfico, atalhos de teclado e dicas de tela."""

    def _setup_shortcuts(self: App) -> None:
        """Registra os atalhos de teclado da janela principal."""
        self.root.bind("<Control-d>", lambda e: self.copy_data())
        self.root.bind("<Control-Shift-C>", lambda e: self.copy_chart())
        self.root.bind("<F5>", lambda e: self.fetch_rates())
        self.root.bind("<Control-e>", lambda e: self.evolution_cb.invoke())
        self.root.bind("<Control-l>", lambda e: self.sidebar_cb.invoke())

    def _setup_tooltips(self: App) -> None:
        """Vincula dicas de texto aos principais controles da janela."""
        tooltips = {
            self.date_entry: "Digite a data no formato AAAA-MM-DD",
            self.today_button: "Define a data atual e busca automaticamente",
            self.fetch_button: "Busca as taxas para a data informada",
            self.data_button: "Copia os dados para a área de transferência",
            self.copy_toolbar_btn: "Copia o gráfico como imagem",
            self.view_raw_rb: "Exibe todos os vencimentos disponíveis",
            self.view_consolidated_rb: "Agrupa os vencimentos por ano",
            self.evolution_cb: "Carrega automaticamente os últimos 7 pregões",
            self.cb_3d: "Exibe a evolução temporal em três dimensões",
            self.sidebar_cb: "Exibe painel com análise da curva",
        }
        for widget, text in tooltips.items():
            Tooltip(widget, text)

    def _create_shortcut(self: App) -> None:
        """Cria o atalho desktop e esconde o botão de criação."""
        create_shortcut()
        if self.shortcut_button:
            self.shortcut_button.pack_forget()
            self.shortcut_button = None
        self.set_status("Atalho criado em ~/Desktop/ e ~/.local/share/applications/.", msg_type="success")

    def _has_data(self: App) -> bool:
        return bool(self.records)

    def copy_chart(self: App) -> None:
        """Copia o gráfico atual como imagem para a área de transferência."""
        if not self._has_data():
            return
        prior_text = self.status_var.get()
        prior_color = self.statusbar_label.cget("foreground")
        import pyxclip
        from PIL import Image
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", dpi=150)
        img = Image.open(buf).convert("RGBA")
        try:
            pyxclip.copy((img.width, img.height, img.tobytes()))
            self.set_status("Gráfico copiado para a área de transferência.", msg_type="success")
            self._schedule_restore(prior_text, prior_color)
        except pyxclip.ClipboardError:
            self.set_status("Use o botão Salvar do toolbar para salvar o gráfico.", msg_type="warning")

    def copy_data(self: App) -> None:
        """Copia os dados da tabela atual para a área de transferência."""
        if not self._has_data():
            return
        prior_text = self.status_var.get()
        prior_color = self.statusbar_label.cget("foreground")
        if self.evolution_var.get() and self.historical_data:
            csv_text = format_evolution_csv(self.historical_data)
        elif self.view_var.get() == "consolidated":
            consolidated = consolidate_by_year(self.records)
            csv_text = format_yearly_rows(consolidated)
        else:
            csv_text = format_cli_rows(self.records)
        self.root.clipboard_clear()
        self.root.clipboard_append(csv_text)
        self.set_status("Dados copiados para a área de transferência.", msg_type="success")
        self._schedule_restore(prior_text, prior_color)
