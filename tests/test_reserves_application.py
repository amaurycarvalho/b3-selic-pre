"""Testes dos serviços de aplicação de reservas internacionais."""

import json
from datetime import date, timedelta

import pytest

from b3_selic_pre.application.reserves.config import (
    ReservesConfig,
    meses_janela,
)
from b3_selic_pre.application.reserves.export import (
    format_series_csv,
    json_artifact_from_payload,
    series_artifact,
    series_artifact_from_payload,
    series_csv_from_payload,
)
from b3_selic_pre.application.reserves.indicators import (
    classify_regime,
    compute_indicators,
    drawdown,
    range_position,
    trend_90d,
    variation,
)
from b3_selic_pre.application.reserves.payloads import (
    AVISO_REGIME,
    empty_payload,
    filter_payload_window,
    indicators_payload,
    missing_dates,
    reserves_payload,
)
from b3_selic_pre.application.reserves.series import (
    incremental_start,
    merge_points,
    parse_reserves_sgs,
    points_hash,
    retained_points,
    shift_months,
    snapshot_hash,
    window_bounds,
)
from b3_selic_pre.domain.market import MarketQuote
from b3_selic_pre.domain.reserves import (
    ATIVO_RESERVAS,
    FONTE_RESERVAS,
    UNIDADE_RESERVAS,
    ReservesIndicators,
    ReservesRegime,
    ReservesThresholds,
)


def _quote(day: str, value: float) -> MarketQuote:
    return MarketQuote(
        data=day,
        ativo=ATIVO_RESERVAS,
        valor=value,
        unidade=UNIDADE_RESERVAS,
        origem=FONTE_RESERVAS,
        metodo="oficial",
        extraido_em="2026-10-30T12:00:00+00:00",
    )


def _daily(days: int, start: str = "2025-09-01") -> list[MarketQuote]:
    first = date.fromisoformat(start)
    return [
        _quote(
            (first + timedelta(days=index)).isoformat(),
            300000 + index * 100,
        )
        for index in range(days)
    ]


def _declining(days: int) -> list[MarketQuote]:
    first = date(2025, 9, 1)
    return [
        _quote(
            (first + timedelta(days=index)).isoformat(),
            400000 - index * 250,
        )
        for index in range(days)
    ]


def test_config_defaults_and_mapping():
    default = ReservesConfig()
    assert default.janela == "12m"
    assert default.sobreposicao_dias == 5
    assert default.retencao_anos == 3
    assert default.thresholds.var_aumento == 2.0
    assert default.meses() == 12

    custom = ReservesConfig.from_mapping(
        {
            "janela": "3a",
            "sobreposicao_dias": 2,
            "cache": {"recente_minutos": 15, "mes_horas": 1},
            "retencao_anos": 4,
            "limiares": {"var_aumento": 1.0, "drawdown": -5.0},
            "schema_version": 2,
        }
    )
    assert custom.janela == "3a"
    assert custom.meses() == 36
    assert custom.sobreposicao_dias == 2
    assert custom.recente_minutos == 15
    assert custom.mes_horas == 1
    assert custom.retencao_anos == 4
    assert custom.thresholds.var_aumento == 1.0
    assert custom.thresholds.drawdown == -5.0
    assert custom.parametros()["schema_version"] == 2

    invalid = ReservesConfig.from_mapping({"janela": "5a"})
    assert invalid.janela == "12m"
    assert meses_janela("3a") == 36
    assert meses_janela("invalida") == 12


def test_parse_reserves_sgs_normalizes_dates_and_values():
    payload = json.dumps(
        [
            {"data": "29/10/2026", "valor": "364.540,5"},
            {"data": "28/10/2026", "valor": "364000,0"},
            {"data": "invalida", "valor": "1"},
            {"data": "27/10/2026", "valor": "x"},
        ]
    )

    quotes = parse_reserves_sgs(payload, extraido_em="2026-10-30T00:00:00")

    assert [quote.data for quote in quotes] == [
        "2026-10-28",
        "2026-10-29",
    ]
    assert quotes[-1].valor == pytest.approx(364540.5)
    assert quotes[-1].unidade == UNIDADE_RESERVAS
    assert quotes[-1].origem == FONTE_RESERVAS
    assert quotes[-1].extraido_em == "2026-10-30T00:00:00"
    assert parse_reserves_sgs(b"not-json") == []


def test_merge_revisions_and_gaps():
    existing = [_quote("2026-10-01", 1.0), _quote("2026-10-02", 2.0)]
    incoming = [_quote("2026-10-02", 2.5), _quote("2026-10-04", 4.0)]

    merged = merge_points(existing, incoming)

    assert [point.data for point in merged] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-04",
    ]
    assert merged[1].valor == 2.5


def test_retained_window_and_stable_hash():
    recent = _daily(400)
    old = _quote("2010-01-01", 1.0)
    config = ReservesConfig()

    retained = retained_points(recent + [old], recent[-1].data, 3)
    assert all(point.data >= "2023-10-30" for point in retained)

    first = snapshot_hash(recent + [old], config)
    second = snapshot_hash(list(reversed(recent)), config)
    assert first == second

    revised = [*recent[:-1], _quote(recent[-1].data, 999999.0)]
    assert snapshot_hash(revised, config) != first
    assert points_hash(recent) == points_hash(list(reversed(recent)))


def test_incremental_start_uses_business_days():
    assert incremental_start("2026-10-30", 5) == "2026-10-23"
    assert incremental_start("2026-10-30", 0) == "2026-10-30"
    assert incremental_start("invalida", 5) == "invalida"


def test_shift_months_and_window_bounds_clamp():
    assert shift_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert shift_months(date(2026, 3, 31), -1) == date(2026, 2, 28)
    points = _daily(10, start="2026-10-20")
    inicio, fim = window_bounds(points, 12)
    assert fim == points[-1].data
    assert inicio == shift_months(date.fromisoformat(fim), -12).isoformat()


def test_indicators_growth_decline_and_stability():
    growth = compute_indicators(_daily(400))
    assert growth.nivel_atual is not None
    assert growth.var_1m is not None
    assert growth.var_3m is not None
    assert growth.var_12m is not None
    assert growth.tendencia_90d is not None
    assert growth.drawdown_12m is not None
    assert growth.posicao_faixa_12m is not None
    assert growth.regime == ReservesRegime.AUMENTO

    decline = compute_indicators(_declining(400))
    assert decline.var_3m < 0
    assert decline.drawdown_12m < 0
    assert decline.regime == ReservesRegime.DETERIORACAO

    stable = compute_indicators(
        [_quote((date(2025, 1, 1) + timedelta(days=i)).isoformat(), 350000.0)
         for i in range(600)]
    )
    assert stable.var_3m == pytest.approx(0.0)
    assert stable.regime == ReservesRegime.ESTAVEL


def test_indicators_omit_insufficient_history_and_are_deterministic():
    single = [_quote("2026-10-30", 350000.0)]
    first = compute_indicators(single)
    second = compute_indicators(single)

    assert first == second
    assert first.var_1m is None
    assert first.var_3m is None
    assert first.var_12m is None
    assert first.tendencia_90d is None
    assert first.drawdown_12m == pytest.approx(0.0)
    assert first.regime is None
    assert compute_indicators([]).vazio


def test_regime_threshold_boundaries():
    thresholds = ReservesThresholds()

    assert (
        classify_regime(2.01, -1.0, True, thresholds)
        == ReservesRegime.AUMENTO
    )
    assert (
        classify_regime(2.0, -1.0, True, thresholds)
        == ReservesRegime.ESTAVEL
    )
    assert (
        classify_regime(-2.01, -3.01, False, thresholds)
        == ReservesRegime.DETERIORACAO
    )
    assert (
        classify_regime(-2.01, -3.0, False, thresholds)
        == ReservesRegime.DETERIORACAO
    )
    assert (
        classify_regime(-2.01, -2.99, False, thresholds)
        == ReservesRegime.ESTAVEL
    )
    assert classify_regime(None, -5.0, False, thresholds) is None


def test_metric_helpers():
    points = [
        _quote("2025-10-30", 100.0),
        _quote("2026-07-30", 200.0),
        _quote("2026-10-30", 300.0),
    ]
    reference = date(2026, 10, 30)

    assert variation(points, reference, 3) == pytest.approx(50.0)
    assert drawdown(points, reference) == pytest.approx(0.0)
    assert range_position(points, reference) == pytest.approx(1.0)
    assert trend_90d(points, reference) is None
    assert (
        trend_90d(
            [_quote("2026-08-15", 100.0), _quote("2026-10-30", 120.0)],
            reference,
        )
        is not None
    )


def test_payloads_and_exports_contract():
    points = _daily(400)
    indicators = compute_indicators(points)
    payload = reserves_payload(
        points,
        indicators,
        {"inicio": points[0].data, "fim": points[-1].data},
        "Cache",
        "2026-10-30T00:00:00",
    )

    assert {"janela", "serie", "series", "indicadores", "origem", "gerado_em"} <= set(payload)
    assert payload["serie"]["itens"][0]["unidade"] == UNIDADE_RESERVAS
    assert payload["regime"] == "aumento"
    assert payload["aviso"] == AVISO_REGIME
    assert indicators_payload(indicators)["regime"] == "aumento"
    assert indicators_payload(ReservesIndicators())["unidade"]

    csv = format_series_csv(points)
    assert csv.splitlines()[0] == "DATA;VALOR;UNIDADE;ORIGEM;METODO"
    assert points[-1].data in csv
    assert "Ponto" not in csv
    assert series_artifact(points).name == "reservas-serie.csv"
    assert series_artifact_from_payload(payload).name == "reservas-serie.csv"
    assert series_csv_from_payload(payload).startswith("DATA;VALOR")

    artifact = json_artifact_from_payload(payload)
    assert artifact.name == "reservas.json"
    assert json.loads(artifact.content)["indicadores"]["regime"] == "aumento"


def test_filter_payload_and_missing_dates():
    payload = reserves_payload(
        [_quote("2026-10-01", 1.0), _quote("2026-10-02", 2.0)],
        ReservesIndicators(),
        {"inicio": "2026-10-01", "fim": "2026-10-02"},
        "Cache",
        "2026-10-03T00:00:00",
    )

    filtered = filter_payload_window(payload, "2026-10-02", None)
    assert filtered["serie"]["itens"][0]["data"] == "2026-10-02"
    assert filter_payload_window(payload, "2030-01-01", None) is None
    assert missing_dates(payload, "2026-10-01", "2026-10-05") == [
        "2026-10-05"
    ]
    assert empty_payload({"inicio": "", "fim": ""})["serie"]["itens"] == []
