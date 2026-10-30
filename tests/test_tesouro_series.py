from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import (
    BUCKET_DIARIO,
    BUCKET_MENSAL,
    BUCKET_SEMANAL,
    DIMENSAO_FAMILIA,
    DIMENSAO_PRODUTO,
    DIMENSAO_PRODUTO_VENCIMENTO,
    METRICA_DEMANDA_PCT,
    METRICA_ESTOQUE_PCT,
    METRICA_FLUXO_LIQUIDO,
    SELIC,
    SeriesKey,
    SeriesPoint,
    SeriesProvider,
    TesouroSeriesProvider,
    bucket_para_janela,
    bucket_para_metrica,
    chave_series,
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


class FakeProvider:
    def fetch(self, key, start, end, bucket):
        return []


class TestContrato:
    def test_series_key_is_immutable(self):
        key = SeriesKey(DIMENSAO_FAMILIA, SELIC)
        with pytest.raises(AttributeError):
            key.key = "IPCA"

    def test_series_point_is_immutable_and_has_contract_fields(self):
        point = SeriesPoint(
            period="2026-10-02",
            metric=METRICA_DEMANDA_PCT,
            value=Decimal("60"),
            total=Decimal("100"),
            dimension=DIMENSAO_FAMILIA,
            key=SELIC,
        )
        assert point.period == "2026-10-02"
        with pytest.raises(AttributeError):
            point.value = Decimal("1")

    def test_fake_provider_satisfies_protocol(self):
        assert isinstance(FakeProvider(), SeriesProvider)

    def test_chave_series_por_dimensao(self):
        sale = _venda("Tesouro Selic 2029", "2026-10-02", "10")

        assert chave_series(sale, DIMENSAO_FAMILIA) == SELIC
        assert chave_series(sale, DIMENSAO_PRODUTO) == "Tesouro Selic 2029"
        assert chave_series(sale, DIMENSAO_PRODUTO_VENCIMENTO) == (
            "Tesouro Selic 2029|2029-01-02"
        )


class TestBuckets:
    def test_bucket_por_janela(self):
        assert bucket_para_janela("14d") == BUCKET_DIARIO
        assert bucket_para_janela("3m") == BUCKET_SEMANAL
        assert bucket_para_janela("12m") == BUCKET_MENSAL
        assert bucket_para_janela("3a") == BUCKET_MENSAL

    def test_estoque_e_sempre_mensal(self):
        assert bucket_para_metrica(METRICA_ESTOQUE_PCT, "14d") == BUCKET_MENSAL
        assert bucket_para_metrica(METRICA_DEMANDA_PCT, "14d") == (
            BUCKET_DIARIO
        )

    def test_janela_invalida(self):
        with pytest.raises(ValueError):
            bucket_para_janela("2m")


class TestProvider:
    def _provider(self):
        return TesouroSeriesProvider(
            vendas=[
                _venda("Tesouro Selic 2029", "2026-10-02", "60"),
                _venda("Tesouro IPCA+ 2035", "2026-10-02", "40"),
                _venda("Tesouro Selic 2029", "2026-08-03", "10"),
            ],
            resgates=[
                _recompra("Tesouro Selic 2029", "2026-10-02", "5"),
                _recompra("Tesouro IPCA+ 2035", "2026-10-02", "20"),
            ],
            estoque=[
                _estoque("Tesouro Selic 2029", "2026-09", "60"),
                _estoque("Tesouro IPCA+ 2035", "2026-09", "40"),
                _estoque("Tesouro Selic 2029", "2026-10", "70"),
                _estoque("Tesouro IPCA+ 2035", "2026-10", "30"),
            ],
        )

    def test_bucket_diario_para_14_dias(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2026-09-18",
            "2026-10-02",
            BUCKET_DIARIO,
        )
        demand = [
            item for item in points if item.metric == METRICA_DEMANDA_PCT
        ]

        assert [item.period for item in demand] == ["2026-10-02"]
        assert demand[0].value == Decimal("60")
        assert demand[0].total == Decimal("100")

    def test_bucket_semanal_para_3_meses(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2026-07-02",
            "2026-10-02",
            BUCKET_SEMANAL,
        )
        demand = [
            item for item in points if item.metric == METRICA_DEMANDA_PCT
        ]

        assert [item.period for item in demand] == [
            "2026-08-03",
            "2026-09-28",
        ]

    def test_bucket_mensal_para_12_meses(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2025-10-02",
            "2026-10-02",
            BUCKET_MENSAL,
        )
        demand = [
            item for item in points if item.metric == METRICA_DEMANDA_PCT
        ]

        assert [item.period for item in demand] == ["2026-08", "2026-10"]

    def test_estoque_sempre_mensal_mesmo_com_bucket_diario(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2026-09-01",
            "2026-10-31",
            BUCKET_DIARIO,
        )
        stock = [
            item for item in points if item.metric == METRICA_ESTOQUE_PCT
        ]

        assert [item.period for item in stock] == ["2026-09", "2026-10"]
        assert stock[0].value == Decimal("60")
        assert stock[1].value == Decimal("70")

    def test_fluxo_liquido_por_bucket(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2026-09-18",
            "2026-10-02",
            BUCKET_DIARIO,
        )
        fluxo = [
            item for item in points if item.metric == METRICA_FLUXO_LIQUIDO
        ]

        assert len(fluxo) == 1
        assert fluxo[0].period == "2026-10-02"
        assert fluxo[0].value == Decimal("55")

    def test_percentuais_somam_100_por_periodo(self):
        provider = self._provider()
        points = provider.fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2026-09-18",
            "2026-10-02",
            BUCKET_DIARIO,
        )
        selic = next(
            item for item in points if item.metric == METRICA_DEMANDA_PCT
        )
        ipca_points = provider.fetch(
            SeriesKey(DIMENSAO_FAMILIA, "IPCA"),
            "2026-09-18",
            "2026-10-02",
            BUCKET_DIARIO,
        )
        ipca = next(
            item
            for item in ipca_points
            if item.metric == METRICA_DEMANDA_PCT
        )

        assert selic.value + ipca.value == Decimal("100")

    def test_ciclo_de_vida_representa_lacuna(self):
        provider = self._provider()
        points = provider.fetch(
            SeriesKey(DIMENSAO_PRODUTO, "Tesouro IPCA+ 2035"),
            "2026-08-01",
            "2026-10-31",
            BUCKET_MENSAL,
        )
        stock = [
            item for item in points if item.metric == METRICA_ESTOQUE_PCT
        ]

        assert [item.period for item in stock] == ["2026-09", "2026-10"]

    def test_dimensao_produto_vencimento(self):
        points = self._provider().fetch(
            SeriesKey(
                DIMENSAO_PRODUTO_VENCIMENTO,
                "Tesouro Selic 2029|2029-01-02",
            ),
            "2026-09-01",
            "2026-10-31",
            BUCKET_MENSAL,
        )
        stock = [
            item for item in points if item.metric == METRICA_ESTOQUE_PCT
        ]

        assert [item.period for item in stock] == ["2026-09", "2026-10"]
        assert all(
            item.key == "Tesouro Selic 2029|2029-01-02"
            for item in stock
        )
        assert all(
            item.dimension == DIMENSAO_PRODUTO_VENCIMENTO
            for item in stock
        )

    def test_sem_periodos_futuros(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2026-07-01",
            "2026-12-31",
            BUCKET_MENSAL,
        )

        assert max(item.period for item in points) == "2026-10"

    def test_janela_sem_dados_retorna_vazio(self):
        points = self._provider().fetch(
            SeriesKey(DIMENSAO_FAMILIA, SELIC),
            "2020-01-01",
            "2020-12-31",
            BUCKET_MENSAL,
        )

        assert points == []
