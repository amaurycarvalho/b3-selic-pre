"""Dataclasses de saída do gráfico de câmbio e ouro."""

from __future__ import annotations

from dataclasses import dataclass

FIBONACCI_LEVELS = (23.6, 38.2, 50.0, 61.8, 78.6)
ASSET_LABELS = {"usd": "Dólar (BRL/USD)", "ouro": "Ouro (R$/g)"}


@dataclass(frozen=True)
class ChartBand:
    """One forecast band for a chart panel."""

    nivel: int
    inferiores: tuple[float, ...]
    superiores: tuple[float, ...]


@dataclass(frozen=True)
class ChartPanelData:
    """Historical range, forecast and Fibonacci levels for one asset."""

    ativo: str
    label: str
    unidade: str
    datas: tuple[str, ...]
    valores: tuple[float, ...]
    minimos: tuple[float, ...]
    maximos: tuple[float, ...]
    previsao_datas: tuple[str, ...] = ()
    previsao_centro: tuple[float, ...] = ()
    bandas: tuple[ChartBand, ...] = ()
    fibonacci: dict[float, float] | None = None


@dataclass(frozen=True)
class MarketChartData:
    """Complete chart payload consumed only by the matplotlib renderer."""

    paineis: tuple[ChartPanelData, ...]
    hoje: str
    base100: bool
    indicadores_texto: str
    vazio: bool = False
    mensagem: str = ""

    def painel(self: MarketChartData, ativo: str) -> ChartPanelData | None:
        """Return the panel for ``ativo`` when present."""
        for panel in self.paineis:
            if panel.ativo == ativo:
                return panel
        return None
