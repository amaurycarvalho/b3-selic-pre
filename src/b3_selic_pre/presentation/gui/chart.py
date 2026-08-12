"""Mixin de desenho e atualização dos gráficos da aplicação."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from b3_selic_pre.presentation.charts import (
    render_3d_evolution,
    render_chart,
    render_curve_evolution,
    render_detailed_evolution,
)

App = Any


class ChartMixin:
    """Gerencia o redesenho dos gráficos e os estados de visualização."""

    def _update_stats(self: App) -> None:
        """Atualiza o rótulo de estatísticas com a data e as taxas extremas."""
        if not self.records:
            self.stats_label.configure(text="")
            return
        rates = [float(r.rate.replace(",", ".")) for r in self.records]
        date_str = self.date_var.get().strip()
        self.stats_label.configure(
            text=f"Data: {date_str} | Maior: {max(rates):.2f}% | "
                 f"Menor: {min(rates):.2f}%"
        )

    def _update_button_states(self: App) -> None:
        """Habilita ou desabilita os botões conforme os dados disponíveis."""
        has_single = bool(self.records)
        has_historical = bool(self.historical_data)
        has_any = has_single or has_historical
        copy_state = self.tk.NORMAL if has_any else self.tk.DISABLED
        self.data_button.configure(state=copy_state)
        self.copy_toolbar_btn.configure(state=copy_state)
        consolidated_state = self.tk.NORMAL if has_single else self.tk.DISABLED
        self.view_consolidated_rb.configure(state=consolidated_state)
        self.view_raw_rb.configure(state=consolidated_state)
        self.evolution_cb.configure(state=consolidated_state)
        analysis_state = self.tk.NORMAL if has_single else self.tk.DISABLED
        self.sidebar_cb.configure(state=analysis_state)

    def _redraw_chart(self: App) -> None:
        """Redesenha o gráfico conforme o modo de visualização selecionado."""
        show_evolution = self.evolution_var.get()
        show_3d = self.var_3d.get()
        view = self.view_var.get()
        if show_evolution and self.historical_data:
            if show_3d:
                c = view == "consolidated"
                render_3d_evolution(self.figure, self.historical_data, consolidated=c)
                mode = "Longa" if c else "Curta"
                self.figure.gca().set_title(
                    f"Evolução 3D da Curva {mode} (SELIC Pré)", fontsize=14, y=1.06,
                    ha="center")
            elif view == "consolidated":
                render_curve_evolution(self.figure, self.historical_data)
                self.figure.gca().set_title(
                    "Evolução da Curva Longa (SELIC Pré)", fontsize=14, y=0.92)
            else:
                render_detailed_evolution(self.figure, self.historical_data)
                self.figure.gca().set_title(
                    "Evolução da Curva Curta (SELIC Pré)", fontsize=14, y=0.92)
        elif view == "consolidated":
            render_chart(self.figure, self.records, consolidated=True)
            self.figure.gca().set_title(
                "Curva Longa (SELIC Pré)", fontsize=14, y=0.92)
        else:
            render_chart(self.figure, self.records, consolidated=False)
            self.figure.gca().set_title(
                "Curva Curta (SELIC Pré)", fontsize=14, y=0.92)
        self.canvas.draw_idle()
        self._update_analysis()

    def toggle_view(self: App) -> None:
        """Alterna entre as visualizações de curva curta e curva longa."""
        self.settings["view_mode"] = self.view_var.get()
        self._redraw_chart()

    def toggle_evolution(self: App) -> None:
        """Ativa ou desativa o modo de evolução da curva."""
        self.settings["evolution"] = self.evolution_var.get()
        if self.evolution_var.get():
            self.cb_3d.configure(state=self.tk.NORMAL)
            if self.historical_data:
                self._redraw_chart()
            else:
                today = self._nearest_business_day(datetime.now(timezone.utc).date().isoformat())
                if self.date_var.get().strip() != today:
                    self.date_var.set(today)
                self._fetch_historical_rates(today)
        else:
            self.var_3d.set(False)
            self.settings["show_3d"] = False
            self.cb_3d.configure(state=self.tk.DISABLED)
            self._redraw_chart()
