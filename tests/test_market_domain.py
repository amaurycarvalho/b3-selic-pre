"""Testes dos modelos puros de mercado."""

from b3_selic_pre.domain.market import (
    ATIVO_OURO,
    ATIVO_USD,
    METODO_CACHE_DEFASADO,
    METODO_DERIVADO,
    UNIDADE_OURO,
    UNIDADE_USD,
    Bucket,
    ForecastBand,
    ForecastPoint,
    MarketQuote,
    MarketSeries,
    PolicyIndicators,
    Resolution,
    SourceRef,
)


def _quote(**overrides):
    values = {
        "data": "2026-10-30",
        "ativo": ATIVO_USD,
        "valor": 5.42,
        "unidade": UNIDADE_USD,
        "origem": "BCB SGS 1",
        "metodo": "oficial",
        "extraido_em": "2026-10-30T12:00:00+00:00",
    }
    values.update(overrides)
    return MarketQuote(**values)


def test_quote_equality_and_units():
    assert _quote() == _quote()
    assert _quote().unidade == UNIDADE_USD
    assert _quote(ativo=ATIVO_OURO, unidade=UNIDADE_OURO).unidade == "BRL/g"


def test_quote_staleness_flag():
    assert not _quote().defasado
    stale = _quote(metodo=METODO_CACHE_DEFASADO, defasagem_horas=30)
    assert stale.defasado
    assert stale.defasagem_horas == 30


def test_series_preserves_dates_and_provenance():
    first = _quote(data="2026-10-01")
    second = _quote(data="2026-10-02")
    series = MarketSeries(
        ativo=ATIVO_USD,
        unidade=UNIDADE_USD,
        resolucao=Resolution.DIA,
        pontos=(first, second),
        origem="BCB",
        metodo="oficial",
        extraido_em="2026-10-02T00:00:00",
    )

    assert [point.data for point in series.pontos] == [
        "2026-10-01",
        "2026-10-02",
    ]
    assert not series.vazia
    assert not series.defasada


def test_empty_and_stale_series_properties():
    assert MarketSeries(ATIVO_USD, UNIDADE_USD, Resolution.DIA).vazia
    stale = MarketSeries(
        ATIVO_OURO,
        UNIDADE_OURO,
        Resolution.SEMANA,
        pontos=(_quote(metodo=METODO_CACHE_DEFASADO),),
    )
    assert stale.defasada


def test_bucket_exposes_ohlc_and_representative_date():
    bucket = Bucket(
        inicio="2026-10-01",
        fim="2026-10-07",
        abertura=5.1,
        minimo=5.0,
        maximo=5.5,
        fechamento=5.4,
        ultimo=5.4,
    )

    assert bucket.data == "2026-10-07"
    assert bucket.minimo == 5.0
    assert bucket.maximo == 5.5


def test_forecast_point_lookup_band():
    point = ForecastPoint(
        data="2027-10-31",
        ativo=ATIVO_OURO,
        cenario="Projeção estatística",
        metodo=METODO_DERIVADO,
        centro=500.0,
        bandas=(
            ForecastBand(80, 450.0, 550.0),
            ForecastBand(95, 400.0, 600.0),
        ),
    )

    assert point.banda(80) == ForecastBand(80, 450.0, 550.0)
    assert point.banda(90) is None


def test_policy_indicators_empty_and_partial():
    assert PolicyIndicators().vazio
    assert not PolicyIndicators(vol30=0.2).vazio


def test_source_ref_defaults():
    ref = SourceRef("BCB")

    assert ref.metodo == "oficial"
    assert ref.extraido_em == ""
