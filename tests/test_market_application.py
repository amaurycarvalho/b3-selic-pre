"""Testes dos serviços de aplicação de câmbio e ouro."""

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from b3_selic_pre.application.market.cache_key import composite_key, key_from_config
from b3_selic_pre.application.market.config import MarketConfig
from b3_selic_pre.application.market.export import (
    format_forecast_csv,
    format_history_csv,
    format_market_json,
    forecast_artifact,
    history_artifact,
    json_artifact,
)
from b3_selic_pre.application.market.forecast import (
    FOCUS_AUSENTE,
    HISTORICO_INSUFICIENTE,
    FocusExpectation,
    add_months,
    dol_short_premium,
    ewma_sigma,
    focus_target,
    forecast_usd,
    log_returns,
    statistical_forecast,
)
from b3_selic_pre.application.market.indicators import (
    compute_indicators,
    focus_gap,
    realized_volatility,
    regime_signal,
    term_premium,
)
from b3_selic_pre.application.market.payloads import (
    AVISO_CENARIO,
    build_forecasts,
    forecast_payload,
    indicators_payload,
    market_payload,
    quote_payload,
    series_payload,
)
from b3_selic_pre.application.market.series import (
    bucket_points,
    derive_gold,
    filter_window,
    gold_brl_per_gram,
    layered_buckets,
    resolution_for,
    series_from_quotes,
    stale_gold,
    troy_ounce_to_grams,
)
from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    UNIDADE_OURO,
    UNIDADE_USD,
    MarketQuote,
    PolicyIndicators,
    Resolution,
)


def _quote(data, valor, ativo=ATIVO_USD, **overrides):
    values = {
        "data": data,
        "ativo": ativo,
        "valor": valor,
        "unidade": UNIDADE_USD if ativo == ATIVO_USD else UNIDADE_OURO,
        "origem": "fonte",
        "metodo": "oficial",
        "extraido_em": "2026-10-30T12:00:00+00:00",
    }
    values.update(overrides)
    return MarketQuote(**values)


def _daily_series(days=80, start=2019.0, step=0.01):
    base = date(2026, 10, 30)
    return [
        _quote(
            (base - timedelta(days=index)).isoformat(),
            start + (days - index) * step,
        )
        for index in range(days)
    ]


def test_config_from_mapping_and_parameters():
    config = MarketConfig.from_mapping(
        {
            "resolucao": {"diario_dias": 10, "semanal_dias": 80},
            "projecao": {"meses": 6, "regime_ratio": 2.0},
            "cache": {"recente_minutos": 5},
            "schema_version": 7,
        }
    )

    assert config.resolucao.diario_dias == 10
    assert config.projecao.meses == 6
    assert config.projecao.regime_ratio == 2.0
    assert config.cache.recente_minutos == 5
    assert config.schema_version == 7
    assert config.parametros_resolucao()["semanal_dias"] == 80
    assert config.parametros_projecao()["meses"] == 6


def test_composite_key_is_stable_and_order_independent():
    first = composite_key(
        {"b": "2", "a": "1"}, {"d": 1}, {"p": 2}, 1
    )
    second = composite_key(
        {"a": "1", "b": "2"}, {"d": 1}, {"p": 2}, 1
    )

    assert first == second
    assert first != composite_key(
        {"a": "1", "b": "3"}, {"d": 1}, {"p": 2}, 1
    )


def test_composite_key_changes_with_parameters_and_schema():
    sources = {"a": "1"}
    base = composite_key(sources, {"d": 1}, {"p": 2}, 1)

    assert base != composite_key(sources, {"d": 2}, {"p": 2}, 1)
    assert base != composite_key(sources, {"d": 1}, {"p": 3}, 1)
    assert base != composite_key(sources, {"d": 1}, {"p": 2}, 2)


def test_key_from_config_uses_config_parameters():
    config = MarketConfig()
    key = key_from_config({"a": "1"}, config)

    assert key == composite_key(
        {"a": "1"},
        config.parametros_resolucao(),
        config.parametros_projecao(),
        config.schema_version,
    )


def test_resolution_boundaries():
    config = MarketConfig()
    reference = date(2026, 10, 30)

    assert resolution_for("2026-10-30", reference, config) == Resolution.DIA
    assert resolution_for("2026-10-16", reference, config) == Resolution.DIA
    assert resolution_for("2026-10-15", reference, config) == Resolution.SEMANA
    assert resolution_for("2026-08-01", reference, config) == Resolution.SEMANA
    assert resolution_for("2026-07-31", reference, config) == Resolution.MES


def test_bucket_points_daily_preserves_each_point():
    points = [
        _quote("2026-10-01", 5.0),
        _quote("2026-10-02", 5.2),
    ]

    buckets = bucket_points(points, Resolution.DIA)

    assert [bucket.fim for bucket in buckets] == ["2026-10-01", "2026-10-02"]


def test_bucket_points_weekly_ohlc_preserves_extremes():
    points = [
        _quote("2026-10-05", 5.1),
        _quote("2026-10-06", 5.5),
        _quote("2026-10-07", 4.9),
        _quote("2026-10-08", 5.2),
    ]

    buckets = bucket_points(points, Resolution.SEMANA)

    assert len(buckets) == 1
    bucket = buckets[0]
    assert bucket.inicio == "2026-10-05"
    assert bucket.fim == "2026-10-08"
    assert bucket.abertura == 5.1
    assert bucket.minimo == 4.9
    assert bucket.maximo == 5.5
    assert bucket.fechamento == 5.2
    assert bucket.ultimo == 5.2


def test_bucket_points_monthly_groups_by_month_and_year():
    points = [
        _quote("2026-06-01", 1.0),
        _quote("2026-06-20", 2.0),
        _quote("2026-07-01", 3.0),
        _quote("2028-06-01", 4.0),
    ]

    buckets = bucket_points(points, Resolution.MES)

    assert [bucket.fim for bucket in buckets] == [
        "2026-06-20",
        "2026-07-01",
        "2028-06-01",
    ]


def test_layered_buckets_mixes_resolutions_and_skips_gaps():
    reference = "2026-10-30"
    points = [
        _quote("2026-10-30", 1.0),
        _quote("2026-10-29", 2.0),
        _quote("2026-10-15", 3.0),
        _quote("2026-10-10", 4.0),
        _quote("2026-06-15", 5.0),
        _quote("2026-06-20", 6.0),
        _quote("2026-01-15", 7.0),
    ]

    buckets = layered_buckets(points, reference, MarketConfig())

    endings = [bucket.fim for bucket in buckets]
    assert endings == sorted(endings)
    assert "2026-06-20" in endings
    assert "2026-10-29" in endings
    assert len(buckets) == 6


def test_filter_window_is_inclusive():
    points = [_quote("2026-01-01", 1.0), _quote("2026-01-10", 2.0)]

    assert [p.valor for p in filter_window(points, "2026-01-02", "2026-01-10")] == [2.0]


def test_ounce_conversion_and_gold_derivation():
    assert troy_ounce_to_grams(31.1034768) == pytest.approx(1.0)
    assert gold_brl_per_gram(2000.0, 5.0) == pytest.approx(321.514, rel=1e-4)

    gold = derive_gold(_quote("2026-01-01", 2000.0), _quote("2026-01-01", 5.0))

    assert gold.ativo == ATIVO_OURO
    assert gold.unidade == UNIDADE_OURO
    assert gold.metodo == "derivado"
    assert "fonte" in gold.origem


def test_stale_gold_reuses_last_value_with_age():
    last = _quote(
        "2026-01-01",
        300.0,
        ativo=ATIVO_OURO,
        extraido_em="2026-10-30T10:00:00+00:00",
        metodo="derivado",
    )
    reference = datetime(2026, 10, 30, 15, tzinfo=timezone.utc)

    stale = stale_gold(last, reference)

    assert stale.valor == 300.0
    assert stale.metodo == "cache_defasado"
    assert stale.defasagem_horas == pytest.approx(5.0)


def test_series_from_quotes_preserves_dates_and_provenance():
    series = series_from_quotes(
        ATIVO_USD,
        UNIDADE_USD,
        [_quote("2026-01-02", 2.0), _quote("2026-01-01", 1.0)],
    )

    assert [point.data for point in series.pontos] == [
        "2026-01-01",
        "2026-01-02",
    ]
    assert series.extraido_em
    assert series.origem == "fonte"


def test_focus_target_interpolates_log_linearly():
    expectations = [
        FocusExpectation(2027, 5.0),
        FocusExpectation(2028, 6.05),
    ]

    target = focus_target(expectations, date(2027, 10, 30), 12)

    assert target == pytest.approx(6.0, rel=2e-2)


def test_forecast_usd_builds_bands_and_target():
    outcome = forecast_usd(
        _quote("2026-10-30", 5.0),
        [FocusExpectation(2027, 5.5, 5.0, 6.0)],
        date(2026, 10, 30),
        MarketConfig(),
    )

    assert outcome.disponivel
    assert len(outcome.pontos) == 12
    assert outcome.pontos[-1].centro == pytest.approx(5.5)
    assert outcome.pontos[0].cenario == "Cenário de mercado"
    widths = [
        point.banda(80).superior - point.banda(80).inferior
        for point in outcome.pontos
    ]
    assert widths == sorted(widths)


def test_forecast_usd_without_focus_reports_absence():
    outcome = forecast_usd(
        _quote("2026-10-30", 5.0), [], date(2026, 10, 30), MarketConfig()
    )

    assert not outcome.disponivel
    assert outcome.motivo == FOCUS_AUSENTE


def test_dol_short_premium_annualizes():
    premium = dol_short_premium(
        _quote("2026-10-30", 5.1),
        _quote("2026-10-30", 5.0),
        30,
    )

    assert premium == pytest.approx((5.1 / 5.0 - 1) * 252 / 30 * 100)
    assert dol_short_premium(_quote("2026-10-30", 5.1), _quote("2026-10-30", 5.0), 0) is None


def test_statistical_forecast_is_deterministic_with_growing_bands():
    history = _daily_series(days=80)
    config = MarketConfig()

    first = statistical_forecast(
        ATIVO_OURO, history, date(2026, 10, 30), config
    )
    second = statistical_forecast(
        ATIVO_OURO, history, date(2026, 10, 30), config
    )

    assert first == second
    widths = [
        point.banda(95).superior - point.banda(95).inferior
        for point in first.pontos
    ]
    assert widths == sorted(widths)
    assert first.pontos[0].cenario == "Projeção estatística"


def test_statistical_forecast_requires_enough_history():
    outcome = statistical_forecast(
        ATIVO_OURO,
        _daily_series(days=5),
        date(2026, 10, 30),
        MarketConfig(),
    )

    assert not outcome.disponivel
    assert outcome.motivo == HISTORICO_INSUFICIENTE


def test_log_returns_and_ewma_are_finite():
    returns = log_returns([100, 101, 100])

    assert len(returns) == 2
    assert ewma_sigma(returns, 0.94) > 0
    assert ewma_sigma([], 0.94) == 0.0
    assert log_returns([0, 1]) == []


def test_add_months_clamps_day():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 1, 31), 12) == date(2027, 1, 31)


def test_indicators_term_premium_gap_and_dol():
    assert term_premium(5.5, 5.0) == pytest.approx(10.0)
    assert term_premium(5.5, 0) is None
    assert focus_gap(5.5, 5.0) == pytest.approx(0.5)

    spot = _quote("2026-10-30", 5.0)
    indicators = compute_indicators(
        _daily_series(days=100),
        spot,
        MarketConfig(),
        focus=5.5,
        dol_front=_quote("2026-10-30", 5.1),
        dias_ate_vencimento=30,
    )

    assert indicators.premio_termo == pytest.approx(10.0)
    assert indicators.gap_focus == pytest.approx(0.5)
    assert indicators.premio_dol is not None
    assert indicators.vol30 is not None
    assert indicators.limiar_regime == 1.5


def test_indicators_omit_missing_inputs():
    indicators = compute_indicators(
        [], _quote("2026-10-30", 5.0), MarketConfig()
    )

    assert indicators.premio_termo is None
    assert indicators.premio_dol is None
    assert indicators.gap_focus is None
    assert indicators.vol30 is None
    assert indicators.regime is None


def test_regime_signal_threshold_and_drift_direction():
    assert regime_signal(20.0, 10.0, 0.1, -0.1, 1.5) is True
    assert regime_signal(10.0, 10.0, 0.1, -0.1, 1.5) is False
    assert regime_signal(20.0, 10.0, 0.1, 0.1, 1.5) is False
    assert regime_signal(None, 10.0, 0.1, -0.1, 1.5) is None
    assert regime_signal(20.0, 0.0, 0.1, -0.1, 1.5) is None


def test_realized_volatility_needs_returns():
    assert realized_volatility([1.0]) is None
    assert realized_volatility([100.0, 101.0, 102.0]) > 0


def test_payload_serialization_and_aviso():
    quote = _quote("2026-01-01", 5.0)
    series = series_from_quotes(ATIVO_USD, UNIDADE_USD, [quote])

    assert quote_payload(quote)["defasado"] is False
    assert series_payload(series)["itens"][0]["data"] == "2026-01-01"
    assert indicators_payload(PolicyIndicators(vol30=1.0))["aviso"] == AVISO_CENARIO
    assert "premio_termo" not in indicators_payload(PolicyIndicators(vol30=1.0))


def test_build_forecasts_falls_back_to_statistics_without_focus():
    history = _daily_series(days=80)
    outcomes = build_forecasts(
        history[-1],
        history,
        history,
        [],
        date(2026, 10, 30),
        MarketConfig(),
    )

    assert outcomes[ATIVO_USD].pontos[0].cenario == "Projeção estatística"
    assert outcomes[ATIVO_OURO].disponivel


def test_market_payload_has_all_contract_keys():
    series = series_from_quotes(ATIVO_USD, UNIDADE_USD, [_quote("2026-01-01", 5.0)])
    outcomes = build_forecasts(
        None, [], [], [], date(2026, 10, 30), MarketConfig()
    )

    payload = market_payload(
        {"inicio": "2026-01-01", "fim": "2026-12-31"},
        {ATIVO_USD: series},
        outcomes,
        PolicyIndicators(referencia="2026-01-01"),
        "cache",
        "2026-01-02T00:00:00",
    )

    assert set(payload) >= {
        "janela",
        "series",
        "previsao",
        "indicadores",
        "origem",
        "gerado_em",
    }
    assert payload["previsao"][ATIVO_OURO]["aviso"] == AVISO_CENARIO


def test_forecast_payload_includes_reason_when_unavailable():
    outcome = statistical_forecast(
        ATIVO_OURO, [], date(2026, 10, 30), MarketConfig()
    )

    payload = forecast_payload(ATIVO_OURO, outcome)

    assert payload["disponivel"] is False
    assert payload["motivo"] == HISTORICO_INSUFICIENTE


def test_history_csv_format_and_artifact():
    series = series_from_quotes(
        ATIVO_USD,
        UNIDADE_USD,
        [_quote("2026-01-01", 5.123456)],
    )

    content = format_history_csv([series])

    assert content.splitlines()[0] == "DATA;ATIVO;VALOR;UNIDADE;ORIGEM;METODO"
    assert "2026-01-01;usd;5.123456;BRL/USD;fonte;oficial" in content
    assert history_artifact([series]).name == "mercado-historico.csv"


def test_forecast_csv_format_and_artifact():
    outcome = forecast_usd(
        _quote("2026-10-30", 5.0),
        [FocusExpectation(2027, 5.5, 5.0, 6.0)],
        date(2026, 10, 30),
        MarketConfig(),
    )

    content = format_forecast_csv(outcome.pontos)

    assert content.splitlines()[0] == (
        "DATA;ATIVO;CENARIO;INFERIOR_80;SUPERIOR_80;"
        "INFERIOR_95;SUPERIOR_95;METODO"
    )
    assert content.count("Cenário de mercado") == 12
    assert forecast_artifact(outcome.pontos).name == "mercado-previsao.csv"


def test_json_format_and_artifact():
    series = series_from_quotes(ATIVO_USD, UNIDADE_USD, [_quote("2026-01-01", 5.0)])
    outcomes = build_forecasts(None, [], [], [], date(2026, 10, 30), MarketConfig())
    artifact = json_artifact(
        {"inicio": "2026-01-01", "fim": "2026-01-02"},
        {ATIVO_USD: series},
        outcomes,
        PolicyIndicators(referencia="2026-01-01"),
        "cache",
        "2026-01-02T00:00:00",
    )

    assert artifact.name == "mercado.json"
    assert json.loads(artifact.content)["origem"] == "cache"
    assert format_market_json({"a": 1}).endswith("\n")
