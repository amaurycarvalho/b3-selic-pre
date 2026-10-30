"""Painel de gráfico da sub-aba Dólar e Ouro."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from b3_selic_pre.presentation.gui.tesouro_chart_panel import ChartPanel

Widget = Any
StatusCallback = Callable[[str, str], None]


def _no_status(message: str, msg_type: str) -> None:
    return None


class MarketChartPanel(ChartPanel):
    """Reuse the existing chart panel with a taller market figure."""

    def __init__(
        self: MarketChartPanel,
        parent: Widget,
        *,
        icons: dict[str, Any],
        on_status: StatusCallback = _no_status,
    ) -> None:
        """Create the panel with the shared toolbar, copy and hover."""
        super().__init__(parent, icons=icons, on_status=on_status)
        self.figure.set_size_inches(8, 6)
