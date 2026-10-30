from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import (
    BUCKET_MENSAL,
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    METRICA_ESTOQUE_PCT,
    OUTROS,
    SELIC,
    SeriesKey,
    TesouroSeriesProvider,
    build_estoque_snapshot,
    classificar_familia,
    merge_estoque,
)
from b3_selic_pre.domain.models import (
    EstoqueMensalTitulo,
    EstoqueTesouroDireto,
)


def _ckan(titulo, mes, valor):
    return EstoqueTesouroDireto(
        titulo,
        "2029-01-02",
        mes,
        Decimal("1"),
        Decimal("1"),
        Decimal(valor),
    )


def _btd(titulo, mes, valor):
    return EstoqueMensalTitulo(titulo, mes, Decimal(valor))


def test_estoque_mensal_titulo_is_immutable_and_comparable():
    record = _btd("Tesouro Selic 2029", "2026-09", "100")

    assert record == EstoqueMensalTitulo(
        "Tesouro Selic 2029", "2026-09", Decimal("100")
    )
    with pytest.raises(AttributeError):
        record.mes = "2026-10"


def test_merge_adds_only_new_btd_pairs():
    ckan = [_ckan("Tesouro Selic 2029", "2026-08", "100")]
    btd = [
        _btd("Tesouro Selic 2029", "2026-08", "999"),
        _btd("Tesouro Selic 2029", "2026-09", "120"),
    ]

    merged = merge_estoque(ckan, btd)

    assert merged == (
        ckan[0],
        _btd("Tesouro Selic 2029", "2026-09", "120"),
    )


def test_merge_never_replaces_coincident_months():
    ckan = [_ckan("Tesouro Selic 2029", "2026-09", "100")]
    merged = merge_estoque(
        ckan, [_btd("Tesouro Selic 2029", "2026-09", "200")]
    )

    assert merged == (ckan[0],)


def test_merge_ignores_overlapping_aggregate_btd_titles():
    ckan = [_ckan("Tesouro Selic 2029", "2026-08", "100")]
    btd = [_btd("Tesouro Selic (LFT)", "2026-08", "100")]

    assert merge_estoque(ckan, btd) == (ckan[0],)


def test_merge_ignores_btd_gap_older_than_latest_ckan_month():
    ckan = [
        _ckan("Tesouro Selic 2029", "2026-08", "100"),
        _ckan("Tesouro Selic 2029", "2026-10", "120"),
    ]
    btd = [_btd("Tesouro Selic (LFT)", "2026-09", "110")]

    assert merge_estoque(ckan, btd) == tuple(ckan)


def test_merge_with_empty_btd_keeps_ckan():
    ckan = [_ckan("Tesouro Selic 2029", "2026-09", "100")]

    assert merge_estoque(ckan, []) == (ckan[0],)


def test_merge_preserves_unknown_title_and_classifies_as_outros():
    merged = merge_estoque(
        [], [_btd("Tesouro Futuro 2035", "2026-09", "50")]
    )

    assert merged[0].tipo_titulo == "Tesouro Futuro 2035"
    assert classificar_familia(merged[0].tipo_titulo).familia == OUTROS


def test_merge_does_not_duplicate_repeated_btd_pairs():
    btd = [
        _btd("Tesouro Selic 2029", "2026-09", "100"),
        _btd("Tesouro Selic 2029", "2026-09", "100"),
    ]

    assert len(merge_estoque([], btd)) == 1


def test_snapshot_and_provider_accept_aggregated_btd_records():
    records = merge_estoque(
        [
            _ckan("Tesouro Selic 2029", "2026-08", "60"),
            _ckan("Tesouro IPCA+ 2035", "2026-08", "40"),
        ],
        [
            _btd("Tesouro Selic 2029", "2026-09", "70"),
            _btd("Tesouro IPCA+ 2035", "2026-09", "30"),
        ],
    )

    snapshot = build_estoque_snapshot(records)

    assert snapshot is not None
    assert snapshot.latest_data_date == "2026-09"
    assert "2026-09" in {point.period for point in snapshot.points}

    provider = TesouroSeriesProvider(estoque=list(records))
    points = provider.fetch(
        SeriesKey(DIMENSAO_FAMILIA, SELIC),
        "2026-09-01",
        "2026-09-30",
        BUCKET_MENSAL,
    )

    percentual = [
        point.value for point in points
        if point.metric == METRICA_ESTOQUE_PCT
    ]
    assert percentual == [Decimal("70")]


def test_provider_family_and_product_use_aggregated_records():
    records = [_btd("Tesouro Selic 2029", "2026-09", "70")]
    provider = TesouroSeriesProvider(estoque=records)

    family = provider.fetch(
        SeriesKey(DIMENSAO_FAMILIA, SELIC),
        "2026-09-01",
        "2026-09-30",
        BUCKET_MENSAL,
    )
    product = provider.fetch(
        SeriesKey(DIMENSAO_PRODUTO, "Tesouro Selic 2029"),
        "2026-09-01",
        "2026-09-30",
        BUCKET_MENSAL,
    )

    assert family and product
