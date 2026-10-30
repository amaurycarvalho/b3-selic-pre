"""Bucketing temporal e derivação do ouro em R$/g."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime

from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    METODO_DERIVADO,
    OUNCES_PER_GRAM,
    UNIDADE_OURO,
    Bucket,
    MarketQuote,
    MarketSeries,
    Resolution,
)


def _parse(value: str) -> date:
    return date.fromisoformat(value)


def troy_ounce_to_grams(value: float) -> float:
    """Convert a troy-ounce price into a per-gram price."""
    return value / OUNCES_PER_GRAM


def gold_brl_per_gram(xau_usd: float, usd_brl: float) -> float:
    """Return gold in BRL per gram from XAU/USD and USD/BRL."""
    return troy_ounce_to_grams(xau_usd * usd_brl)


def derive_gold(xau: MarketQuote, usd: MarketQuote) -> MarketQuote:
    """Derive one gold quote in BRL/g from XAU/USD and USD/BRL."""
    return MarketQuote(
        data=xau.data,
        ativo=ATIVO_OURO,
        valor=gold_brl_per_gram(xau.valor, usd.valor),
        unidade=UNIDADE_OURO,
        origem=f"{xau.origem} x {usd.origem}",
        metodo=METODO_DERIVADO,
        extraido_em=xau.extraido_em,
        defasagem_horas=xau.defasagem_horas,
    )


def stale_gold(
    last: MarketQuote,
    reference: datetime | None = None,
) -> MarketQuote:
    """Return a cached gold quote marked as stale with its age in hours."""
    reference = reference or datetime.now().astimezone()
    try:
        extracted = datetime.fromisoformat(last.extraido_em)
    except (TypeError, ValueError):
        return last
    if extracted.tzinfo is None:
        extracted = extracted.astimezone()
    age = max(0.0, (reference - extracted).total_seconds() / 3600)
    return MarketQuote(
        data=last.data,
        ativo=last.ativo,
        valor=last.valor,
        unidade=last.unidade,
        origem=last.origem,
        metodo="cache_defasado",
        extraido_em=last.extraido_em,
        defasagem_horas=age,
    )


def resolution_for(
    point_date: str, reference: date, config: MarketConfig
) -> Resolution:
    """Return the layered resolution for one date relative to a reference."""
    age = (reference - _parse(point_date)).days
    if age <= config.resolucao.diario_dias:
        return Resolution.DIA
    if age <= config.resolucao.semanal_dias:
        return Resolution.SEMANA
    return Resolution.MES


def _sort(points: Iterable[MarketQuote]) -> list[MarketQuote]:
    return sorted(points, key=lambda point: point.data)


def _bucket_key(point_date: str, resolution: Resolution) -> tuple[int, int]:
    parsed = _parse(point_date)
    if resolution == Resolution.SEMANA:
        iso = parsed.isocalendar()
        return iso.year, iso.week
    if resolution == Resolution.MES:
        return parsed.year, parsed.month
    return parsed.year, parsed.toordinal()


def bucket_points(
    points: Sequence[MarketQuote], resolution: Resolution
) -> list[Bucket]:
    """Group sorted points into OHLC buckets for ``resolution``."""
    if resolution == Resolution.AUTO:
        resolution = Resolution.DIA
    groups: dict[tuple[int, int], list[MarketQuote]] = {}
    for point in _sort(points):
        groups.setdefault(_bucket_key(point.data, resolution), []).append(point)
    buckets: list[Bucket] = []
    for key in sorted(groups):
        group = groups[key]
        values = [point.valor for point in group]
        buckets.append(
            Bucket(
                inicio=group[0].data,
                fim=group[-1].data,
                abertura=group[0].valor,
                minimo=min(values),
                maximo=max(values),
                fechamento=group[-1].valor,
                ultimo=group[-1].valor,
            )
        )
    return buckets


def layered_buckets(
    points: Sequence[MarketQuote],
    reference: str,
    config: MarketConfig,
) -> list[Bucket]:
    """Bucket a full series using the layered daily/weekly/monthly rule."""
    reference_date = _parse(reference)
    layered: list[Bucket] = []
    for resolution in (Resolution.MES, Resolution.SEMANA, Resolution.DIA):
        selected = [
            point
            for point in points
            if resolution_for(point.data, reference_date, config) == resolution
        ]
        layered.extend(bucket_points(selected, resolution))
    return sorted(layered, key=lambda bucket: bucket.fim)


def series_from_quotes(
    ativo: str,
    unidade: str,
    quotes: Sequence[MarketQuote],
    resolution: Resolution = Resolution.AUTO,
) -> MarketSeries:
    """Build a :class:`MarketSeries` preserving each point's own date."""
    ordered = tuple(_sort(quotes))
    extraido_em = ordered[-1].extraido_em if ordered else ""
    origem = ordered[-1].origem if ordered else ""
    metodo = ordered[-1].metodo if ordered else "oficial"
    if resolution == Resolution.AUTO and ordered:
        resolution = Resolution.DIA
    return MarketSeries(
        ativo=ativo,
        unidade=unidade,
        resolucao=resolution,
        pontos=ordered,
        origem=origem,
        metodo=metodo,
        extraido_em=extraido_em,
    )


def filter_window(
    quotes: Sequence[MarketQuote], inicio: str, fim: str
) -> list[MarketQuote]:
    """Return quotes whose dates fall inside ``inicio`` and ``fim``."""
    return [
        quote for quote in _sort(quotes) if inicio <= quote.data <= fim
    ]
