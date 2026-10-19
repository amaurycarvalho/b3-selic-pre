"""Mixin de desenho e atualização dos gráficos da aplicação."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from b3_selic_pre.application.use_cases import nearest_business_day
from b3_selic_pre.presentation.charts import (
    render_3d_evolution,
    render_chart,
    render_curve_evolution,
    render_detailed_evolution,
)
from b3_selic_pre.presentation.view_model import ChartMode, GuiViewModel

App = Any


class ChartMixin:
    """Gerencia o redesenho dos gráficos e os estados de visualização."""

    def _view_model(self: App) -> GuiViewModel:
        """Monta o view-model headless a partir do estado atual da janela."""
        return GuiViewModel(
            records=self.records,
            historical_data=self.historical_data,
            view_mode=self.view_var.get(),
            evolution_active=self.evolution_var.get(),
            show_3d=self.var_3d.get(),
            reference_date=self.date_var.get().strip(),
        )

    def _update_stats(self: App) -> None:
        """Atualiza o rótulo de estatísticas com a data e as taxas extremas."""
        self.stats_label.configure(text=self._view_model().stats_text)

    def _update_button_states(self: App) -> None:
        """Habilita ou desabilita os botões conforme os dados disponíveis."""
        controls = self._view_model().controls
        copy_state = self.tk.NORMAL if controls.copy_enabled else self.tk.DISABLED
        self.data_button.configure(state=copy_state)
        self.copy_toolbar_btn.configure(state=copy_state)
        view_state = self.tk.NORMAL if controls.view_enabled else self.tk.DISABLED
        self.view_consolidated_rb.configure(state=view_state)
        self.view_raw_rb.configure(state=view_state)
        self.evolution_cb.configure(state=view_state)
        analysis_state = self.tk.NORMAL if controls.analysis_enabled else self.tk.DISABLED
        self.sidebar_cb.configure(state=analysis_state)

    def _redraw_chart(self: App) -> None:
        """Redesenha o gráfico conforme o modo calculado pelo view-model."""
        mode = self._view_model().chart_mode
        if mode == ChartMode.EVOLUTION_3D_CONSOLIDATED:
            render_3d_evolution(self.figure, self.historical_data, consolidated=True)
            self.figure.gca().set_title(
                "Evolução 3D da Curva Longa (SELIC Pré)", fontsize=14, y=1.06,
                ha="center")
        elif mode == ChartMode.EVOLUTION_3D_DETAILED:
            render_3d_evolution(self.figure, self.historical_data, consolidated=False)
            self.figure.gca().set_title(
                "Evolução 3D da Curva Curta (SELIC Pré)", fontsize=14, y=1.06,
                ha="center")
        elif mode == ChartMode.EVOLUTION_CURVE:
            render_curve_evolution(self.figure, self.historical_data)
            self.figure.gca().set_title(
                "Evolução da Curva Longa (SELIC Pré)", fontsize=14, y=0.92)
        elif mode == ChartMode.EVOLUTION_DETAILED:
            render_detailed_evolution(self.figure, self.historical_data)
            self.figure.gca().set_title(
                "Evolução da Curva Curta (SELIC Pré)", fontsize=14, y=0.92)
        elif mode == ChartMode.CONSOLIDATED:
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
        controls = self._view_model().controls
        if controls.three_d_enabled:
            self.cb_3d.configure(state=self.tk.NORMAL)
            if self.historical_data:
                self._redraw_chart()
            else:
                today = nearest_business_day(
                    datetime.now(timezone.utc).date().isoformat()
                )
                if self.date_var.get().strip() != today:
                    self.date_var.set(today)
                self._fetch_historical_rates(today)
        else:
            self.var_3d.set(False)
            self.settings["show_3d"] = False
            self.cb_3d.configure(state=self.tk.DISABLED)
            self._redraw_chart()
