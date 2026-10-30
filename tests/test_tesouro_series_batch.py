from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import (
    BUCKET_DIARIO,
    BUCKET_MENSAL,
    BUCKET_SEMANAL,
    CachedTesouroSeriesProvider,
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    FAMILIAS,
    SeriesKey,
    TesouroSeriesProvider,
    build_demanda_snapshot,
    build_estoque_snapshot,
    build_fluxo_snapshot,
    build_series_snapshots,
)
from b3_selic_pre.domain.models import (
    EstoqueTesouroDireto,
    ResgateTesouroDireto,
    VendaTesouroDireto,
)


def _estoque(titulo, mes, valor, vencimento="2029-01-02"):
    return EstoqueTesouroDireto(
        titulo,
        vencimento,
        mes,
        Decimal("1"),
        Decimal("1"),
        Decimal(valor),
    )


def _venda(titulo, data, valor, vencimento="2029-01-02"):
    return VendaTesouroDireto(
        titulo,
        vencimento,
        data,
        Decimal("1"),
        Decimal("1"),
        Decimal(valor),
    )


def _recompra(titulo, data, valor, vencimento="2029-01-02"):
    return ResgateTesouroDireto(
        "recompra",
        titulo,
        vencimento,
        data,
        None,
        Decimal("1"),
        Decimal(valor),
    )


def _records():
    return (
        [
            _venda("Tesouro Selic 2029", "2025-10-15", "30"),
            _venda("Tesouro Selic 2029", "2025-10-28", "20"),
            _venda("Tesouro IPCA+ 2035", "2025-10-15", "10"),
            _venda("Tesouro Selic 2029", "2026-08-03", "10"),
            _venda("Tesouro Selic 2029", "2026-09-30", "40"),
            _venda("Tesouro IPCA+ 2035", "2026-10-02", "40"),
            _venda("Tesouro Selic 2029", "2026-10-02", "60"),
        ],
        [
            _recompra("Tesouro Selic 2029", "2026-09-30", "5"),
            _recompra("Tesouro IPCA+ 2035", "2026-10-02", "20"),
        ],
        [
            _estoque("Tesouro Selic 2029", "2025-09", "50"),
            _estoque("Tesouro Selic 2029", "2025-10", "50"),
            _estoque("Tesouro IPCA+ 2035", "2025-10", "50"),
            _estoque("Tesouro Selic 2029", "2026-09", "60"),
            _estoque("Tesouro IPCA+ 2035", "2026-09", "40"),
            _estoque("Tesouro Selic 2029", "2026-10", "70"),
            _estoque("Tesouro IPCA+ 2035", "2026-10", "30"),
        ],
    )


def _providers():
    vendas, resgates, estoque = _records()
    snapshots = build_series_snapshots(vendas, resgates, estoque)
    cached = CachedTesouroSeriesProvider(
        estoque=snapshots["estoque"].points,
        demanda=snapshots["demanda"].points,
        fluxo=snapshots["fluxo"].points,
    )
    raw = TesouroSeriesProvider(
        vendas=vendas,
        resgates=resgates,
        estoque=estoque,
    )
    return snapshots, raw, cached


def _keys(vendas, estoque):
    titles = {item.tipo_titulo for item in vendas}
    titles.update(item.tipo_titulo for item in estoque)
    keys = [(DIMENSAO_FAMILIA, family) for family in FAMILIAS]
    keys.extend((DIMENSAO_PRODUTO, title) for title in sorted(titles))
    return keys


@pytest.mark.parametrize(
    ("start", "end", "bucket"),
    [
        ("2026-09-18", "2026-10-02", BUCKET_DIARIO),
        ("2026-09-30", "2026-10-02", BUCKET_SEMANAL),
        ("2025-10-20", "2026-10-02", BUCKET_MENSAL),
    ],
)
def test_cached_provider_matches_raw_provider(start, end, bucket):
    vendas, _resgates, estoque = _records()
    _snapshots, raw, cached = _providers()

    for dimension, key in _keys(vendas, estoque):
        expected = raw.fetch(SeriesKey(dimension, key), start, end, bucket)
        actual = cached.fetch(SeriesKey(dimension, key), start, end, bucket)
        assert actual == expected


def test_snapshots_carry_latest_date_and_titles():
    vendas, resgates, estoque = _records()

    snapshots = build_series_snapshots(vendas, resgates, estoque)

    assert set(snapshots) == {"estoque", "demanda", "fluxo"}
    assert snapshots["estoque"].latest_data_date == "2026-10"
    assert snapshots["demanda"].latest_data_date == "2026-10-02"
    assert snapshots["fluxo"].latest_data_date == "2026-10-02"
    assert snapshots["estoque"].titles == (
        "Tesouro IPCA+ 2035",
        "Tesouro Selic 2029",
    )


def test_snapshots_keep_decimal_and_have_no_future_periods():
    vendas, resgates, estoque = _records()

    snapshots = build_series_snapshots(vendas, resgates, estoque)

    assert snapshots["demanda"].points
    assert all(
        isinstance(point.value, Decimal)
        for point in snapshots["demanda"].points
    )
    assert max(
        point.period for point in snapshots["demanda"].points
    ) == "2026-10-02"
    assert max(
        point.period for point in snapshots["estoque"].points
    ) == "2026-10"


def test_empty_windows_and_unknown_titles():
    vendas, resgates, estoque = _records()
    snapshots = build_series_snapshots(vendas, resgates, estoque)
    cached = CachedTesouroSeriesProvider(
        estoque=snapshots["estoque"].points,
        demanda=snapshots["demanda"].points,
        fluxo=snapshots["fluxo"].points,
    )

    assert cached.fetch(
        SeriesKey(DIMENSAO_FAMILIA, "SELIC"),
        "2020-01-01",
        "2020-12-31",
        BUCKET_MENSAL,
    ) == []

    unknown_stock = [_estoque("Tesouro Novo 2050", "2026-09", "10")]
    snapshot = build_estoque_snapshot(unknown_stock)
    assert snapshot is not None
    keys = {point.key for point in snapshot.points}
    assert "OUTROS" in keys
    assert "Tesouro Novo 2050" in keys


def test_builders_return_none_without_records():
    assert build_estoque_snapshot([]) is None
    assert build_demanda_snapshot([]) is None
    assert build_fluxo_snapshot([], []) is None


def test_retention_is_three_years_from_latest_date():
    vendas = [
        _venda("Tesouro Selic 2029", "2020-01-02", "10"),
        _venda("Tesouro Selic 2029", "2026-10-02", "10"),
    ]

    snapshot = build_demanda_snapshot(vendas)

    assert snapshot is not None
    assert {point.period for point in snapshot.points} == {"2026-10-02"}
