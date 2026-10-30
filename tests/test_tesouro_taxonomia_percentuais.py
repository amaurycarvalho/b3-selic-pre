import logging
from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import (
    IGP_M,
    IPCA,
    IPCA_JUROS,
    OUTROS,
    PREFIXADO,
    SELIC,
    SELIC_RESERVA,
    TesouroDataError,
    classificar_familia,
    composicao_estoque_por_familia,
    composicao_estoque_por_titulo,
    fluxo_liquido_por_familia,
    fluxo_liquido_por_titulo,
    inicio_janela,
    percentual_demanda_por_familia,
    percentual_demanda_por_titulo,
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


def _resgate(tipo, titulo, data, valor, vencimento="2029-01-02"):
    return ResgateTesouroDireto(
        tipo,
        titulo,
        vencimento,
        data,
        None,
        Decimal("1"),
        Decimal(valor),
    )


class TestTaxonomia:
    @pytest.mark.parametrize(
        "titulo,familia,subfamilia",
        [
            ("Tesouro Selic 2029", SELIC, SELIC),
            ("Tesouro Reserva", SELIC, SELIC_RESERVA),
            ("Tesouro IPCA+ 2035", IPCA, IPCA),
            (
                "Tesouro IPCA+ com Juros Semestrais 2040",
                IPCA,
                IPCA_JUROS,
            ),
            ("Tesouro RendA+ 2065", IPCA, "RENDA"),
            ("Tesouro Educa+ 2040", IPCA, "EDUCA"),
            ("Tesouro Prefixado 2032", PREFIXADO, PREFIXADO),
            (
                "Tesouro Prefixado com Juros Semestrais 2035",
                PREFIXADO,
                "PREFIXADO_JUROS",
            ),
            (
                "Tesouro IGPM+ com Juros Semestrais 2032",
                IGP_M,
                "IGP_M",
            ),
        ],
    )
    def test_classifica_titulos_conhecidos(self, titulo, familia, subfamilia):
        result = classificar_familia(titulo)

        assert result.familia == familia
        assert result.subfamilia == subfamilia

    def test_reserva_soma_em_selic(self):
        assert classificar_familia("Tesouro Reserva").familia == SELIC

    def test_titulo_desconhecido_gera_outros_com_aviso(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = classificar_familia("Tesouro Quântico 2099")

        assert result.familia == OUTROS
        assert result.subfamilia == OUTROS
        assert "Tesouro Quântico 2099" in caplog.text

    def test_ignora_caixa_e_acentos(self):
        assert classificar_familia("tesouro ipca+ 2035").familia == IPCA


class TestComposicaoEstoque:
    def test_percentual_por_familia_usa_ultimo_mes(self):
        records = [
            _estoque("Tesouro Selic 2029", "2026-08", "1000"),
            _estoque("Tesouro Selic 2029", "2026-09", "60000"),
            _estoque("Tesouro IPCA+ 2035", "2026-09", "20000"),
            _estoque("Tesouro Reserva", "2026-09", "20000"),
        ]

        result = composicao_estoque_por_familia(records)
        by_key = {item.chave: item for item in result}

        assert by_key[SELIC].valor == Decimal("80000")
        assert by_key[SELIC].percentual == Decimal("80")
        assert by_key[IPCA].percentual == Decimal("20")
        assert sum(item.percentual for item in result) == Decimal("100")
        assert all(item.total == Decimal("100000") for item in result)

    def test_percentual_por_titulo(self):
        records = [
            _estoque("Tesouro Selic 2029", "2026-09", "60000"),
            _estoque("Tesouro IPCA+ 2035", "2026-09", "40000"),
        ]

        result = composicao_estoque_por_titulo(records)
        by_key = {item.chave: item.percentual for item in result}

        assert by_key["Tesouro Selic 2029"] == Decimal("60")
        assert by_key["Tesouro IPCA+ 2035"] == Decimal("40")

    def test_total_zero_levanta_erro(self):
        records = [_estoque("Tesouro Selic 2029", "2026-09", "0")]

        with pytest.raises(TesouroDataError, match="zero"):
            composicao_estoque_por_familia(records)

    def test_estoque_vazio_retorna_vazio(self):
        assert composicao_estoque_por_familia([]) == []


class TestDemanda:
    def _vendas(self):
        return [
            _venda("Tesouro Selic 2029", "2026-10-02", "40"),
            _venda("Tesouro IPCA+ 2035", "2026-09-20", "60"),
            _venda("Tesouro Selic 2029", "2026-08-01", "1000"),
        ]

    def test_janela_14_dias_ancorada_na_maior_data(self):
        result = percentual_demanda_por_familia(
            self._vendas(), "14d"
        )
        by_key = {item.chave: item for item in result}

        assert by_key[SELIC].valor == Decimal("40")
        assert by_key[IPCA].valor == Decimal("60")
        assert by_key[SELIC].percentual == Decimal("40")
        assert by_key[IPCA].percentual == Decimal("60")
        assert sum(item.percentual for item in result) == Decimal("100")

    def test_janela_maior_inclui_historico(self):
        result = percentual_demanda_por_familia(
            self._vendas(), "3m"
        )
        by_key = {item.chave: item for item in result}

        assert by_key[SELIC].valor == Decimal("1040")
        assert by_key[IPCA].valor == Decimal("60")
        assert by_key[SELIC].total == Decimal("1100")

    def test_percentual_por_titulo(self):
        result = percentual_demanda_por_titulo(
            self._vendas(), "3m"
        )
        by_key = {item.chave: item.percentual for item in result}

        assert by_key["Tesouro Selic 2029"] == (
            Decimal("1040") / Decimal("1100") * Decimal("100")
        )
        assert by_key["Tesouro IPCA+ 2035"] == (
            Decimal("60") / Decimal("1100") * Decimal("100")
        )

    def test_janela_vazia_retorna_vazio_sem_erro(self):
        assert percentual_demanda_por_familia([], "14d") == []

    def test_janelas_12_meses_e_3_anos(self):
        vendas = [
            _venda("Tesouro Selic 2029", "2024-01-01", "10"),
            _venda("Tesouro IPCA+ 2035", "2026-10-02", "90"),
        ]

        doze_meses = percentual_demanda_por_familia(vendas, "12m")
        tres_anos = percentual_demanda_por_familia(vendas, "3a")
        by_key = {item.chave: item for item in tres_anos}

        assert [item.chave for item in doze_meses] == [IPCA]
        assert by_key[SELIC].percentual == Decimal("10")
        assert by_key[IPCA].percentual == Decimal("90")

    def test_inicio_das_janelas(self):
        assert inicio_janela("2026-10-02", "14d") == "2026-09-18"
        assert inicio_janela("2026-10-02", "3m") == "2026-07-02"
        assert inicio_janela("2026-10-02", "12m") == "2025-10-02"
        assert inicio_janela("2026-10-02", "3a") == "2023-10-02"

    def test_janela_invalida(self):
        with pytest.raises(ValueError):
            percentual_demanda_por_familia(self._vendas(), "2m")


class TestFluxoLiquido:
    def _dados(self):
        vendas = [
            _venda("Tesouro Selic 2029", "2026-10-02", "100"),
            _venda("Tesouro IPCA+ 2035", "2026-10-01", "50"),
        ]
        resgates = [
            _resgate("recompra", "Tesouro Selic 2029", "2026-09-20", "40"),
            _resgate("recompra", "Tesouro IPCA+ 2035", "2026-10-01", "80"),
            _resgate("cupom", "Tesouro Selic 2029", "2026-10-02", "999"),
            _resgate("vencimento", "Tesouro IPCA+ 2035", "2026-10-02", "999"),
        ]
        return vendas, resgates

    def test_fluxo_positivo_e_negativo_por_familia(self):
        vendas, resgates = self._dados()

        result = fluxo_liquido_por_familia(vendas, resgates, "3m")
        by_key = {item.chave: item for item in result}

        assert by_key[SELIC].valor_vendas == Decimal("100")
        assert by_key[SELIC].valor_recompras == Decimal("40")
        assert by_key[SELIC].fluxo_liquido == Decimal("60")
        assert by_key[IPCA].fluxo_liquido == Decimal("-30")

    def test_fluxo_por_titulo_e_exclusao_de_eventos_contratuais(self):
        vendas, resgates = self._dados()

        result = fluxo_liquido_por_titulo(vendas, resgates, "3m")
        by_key = {item.chave: item for item in result}

        assert by_key["Tesouro Selic 2029"].fluxo_liquido == Decimal("60")
        assert by_key["Tesouro IPCA+ 2035"].fluxo_liquido == Decimal("-30")

    def test_sem_dados_retorna_vazio(self):
        assert fluxo_liquido_por_familia([], [], "3m") == []
