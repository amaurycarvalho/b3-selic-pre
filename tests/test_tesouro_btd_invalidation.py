from decimal import Decimal

from b3_selic_pre.application.tesouro import (
    DIMENSAO_FAMILIA,
    METRICA_ESTOQUE_VALOR,
    SELIC,
    SeriesPoint,
    SeriesSourceSnapshot,
    build_estoque_snapshot,
    merge_estoque,
)
from b3_selic_pre.domain.models import (
    EstoqueMensalTitulo,
    EstoqueTesouroDireto,
)
from b3_selic_pre.infrastructure.tesouro_analytics_cache import (
    TesouroAnalyticsCache,
)
from b3_selic_pre.infrastructure.tesouro_series_cache import (
    ABSENT_SENTINEL,
    SOURCE_DEPENDENCIES,
    TesouroSeriesCache,
)


def _cache(tmp_path):
    return TesouroSeriesCache(
        TesouroAnalyticsCache(tmp_path / "analytics"),
        raw_dir=tmp_path / "raw",
        lock_path=tmp_path / "locks" / "analytics.lock",
    )


def _write_raw(tmp_path, name, content="data"):
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / name).write_text(content, encoding="utf-8")


def _snapshot(name, period):
    return SeriesSourceSnapshot(
        name,
        (
            SeriesPoint(
                period,
                METRICA_ESTOQUE_VALOR,
                Decimal("100"),
                Decimal("100"),
                DIMENSAO_FAMILIA,
                SELIC,
            ),
        ),
        period,
        ("Tesouro Selic 2029",),
    )


def _write_snapshots(tmp_path):
    _write_raw(tmp_path, "estoque.csv")
    _write_raw(tmp_path, "vendastesourodireto.csv")
    _write_raw(tmp_path, "recompras.csv")
    cache = _cache(tmp_path)
    for name in ("estoque", "demanda", "fluxo"):
        hashes = cache.expected_hashes(name)
        assert hashes is not None
        cache.write(
            _snapshot(name, "2026-10"),
            source="Cache",
            extracted_at=None,
            expected_hashes=hashes,
        )
    return cache


def test_missing_btd_file_uses_stable_absent_sentinel(tmp_path):
    _write_raw(tmp_path, "estoque.csv")
    cache = _cache(tmp_path)

    hashes = cache.expected_hashes("estoque")

    assert hashes is not None
    assert hashes["estoque-btd"] == ABSENT_SENTINEL


def test_btd_file_appearing_or_disappearing_changes_only_stock(tmp_path):
    _write_raw(tmp_path, "estoque.csv")
    _write_raw(tmp_path, "vendastesourodireto.csv")
    _write_raw(tmp_path, "recompras.csv")
    cache = _cache(tmp_path)
    absent = cache.expected_hashes("estoque")
    demand = cache.expected_hashes("demanda")
    flow = cache.expected_hashes("fluxo")

    _write_raw(tmp_path, "estoque-btd.json", "overlay")
    present = cache.expected_hashes("estoque")

    assert absent != present
    assert cache.expected_hashes("demanda") == demand
    assert cache.expected_hashes("fluxo") == flow

    (tmp_path / "raw" / "estoque-btd.json").unlink()
    removed = cache.expected_hashes("estoque")

    assert removed == absent


def test_btd_change_invalidates_only_the_stock_partition(tmp_path):
    cache = _write_snapshots(tmp_path)
    demand_hashes = cache.expected_hashes("demanda")
    flow_hashes = cache.expected_hashes("fluxo")
    assert cache.read("estoque") is not None

    _write_raw(tmp_path, "estoque-btd.json", "overlay")
    stock_hashes = cache.expected_hashes("estoque")

    assert cache.read("estoque", stock_hashes) is None
    assert cache.read("demanda", demand_hashes) is not None
    assert cache.read("fluxo", flow_hashes) is not None


def test_dependencies_declare_optional_btd_only_for_stock():
    assert SOURCE_DEPENDENCIES["estoque"] == ("estoque", "estoque-btd")
    assert "estoque-btd" not in SOURCE_DEPENDENCIES["demanda"]
    assert "estoque-btd" not in SOURCE_DEPENDENCIES["fluxo"]


def _ckan(mes, valor):
    return EstoqueTesouroDireto(
        "Tesouro Selic 2029",
        "2029-01-02",
        mes,
        Decimal("1"),
        Decimal("1"),
        Decimal(valor),
    )


def _btd(mes, valor):
    return EstoqueMensalTitulo(
        "Tesouro Selic 2029", mes, Decimal(valor)
    )


def test_snapshot_anchors_latest_month_on_btd():
    merged = merge_estoque(
        [_ckan("2026-08", "100")],
        [_btd("2026-09", "120")],
    )

    snapshot = build_estoque_snapshot(merged)

    assert snapshot is not None
    assert snapshot.latest_data_date == "2026-09"
    assert "2026-09" in {point.period for point in snapshot.points}


def test_snapshot_without_overlay_is_unchanged():
    ckan = [_ckan("2026-08", "100")]
    merged = merge_estoque(ckan, [_btd("2026-08", "999")])

    assert build_estoque_snapshot(merged) == build_estoque_snapshot(ckan)


def test_retention_cutoff_uses_btd_latest_month():
    merged = merge_estoque(
        [_ckan("2023-08", "10"), _ckan("2026-08", "100")],
        [_btd("2026-09", "120")],
    )

    snapshot = build_estoque_snapshot(merged)

    assert snapshot is not None
    periods = {point.period for point in snapshot.points}
    assert "2023-08" not in periods
    assert "2026-09" in periods
