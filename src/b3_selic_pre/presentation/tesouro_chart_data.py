"""Estruturas imutáveis consumidas pelos renderizadores do Tesouro."""

from __future__ import annotations

from dataclasses import dataclass

KIND_VISAO_GERAL = "visao-geral"
KIND_ESTOQUE = "estoque"
KIND_APETITE = "apetite"

SUB_TABS = (
    (KIND_VISAO_GERAL, "Visão geral"),
    (KIND_ESTOQUE, "Estoque"),
    (KIND_APETITE, "Apetite do mercado"),
)

WINDOW_LABELS = {
    "14d": "14 dias",
    "3m": "3 meses",
    "12m": "12 meses",
    "3a": "3 anos",
}


@dataclass(frozen=True)
class ShareChart:
    """Composição percentual por família com detalhe por título."""

    title: str
    families: tuple[str, ...]
    totals: dict[str, float]
    segments: dict[str, dict[str, float]]


@dataclass(frozen=True)
class ComparisonChart:
    """Comparação agrupada de estoque e apetite por família."""

    title: str
    families: tuple[str, ...]
    estoque: tuple[float, ...]
    apetite: tuple[float, ...]


@dataclass(frozen=True)
class EvolutionChart:
    """Série de evolução percentual empilhada por família."""

    title: str
    periods: tuple[str, ...]
    series: dict[str, tuple[float, ...]]
    vertical_grid: bool = False


@dataclass(frozen=True)
class GapChart:
    """Evolução do gap apetite menos estoque por família."""

    title: str
    periods: tuple[str, ...]
    series: dict[str, tuple[float, ...]]
