"""Testes dos modelos puros de reservas internacionais."""

from b3_selic_pre.domain.reserves import (
    ATIVO_RESERVAS,
    FONTE_RESERVAS,
    UNIDADE_RESERVAS,
    UNIDADE_RESERVAS_BILHOES,
    ReservesIndicators,
    ReservesRegime,
    ReservesThresholds,
)


def test_constants_and_regime_values():
    assert ATIVO_RESERVAS == "reservas"
    assert FONTE_RESERVAS == "BCB SGS 13621"
    assert UNIDADE_RESERVAS == "USD_milhoes"
    assert UNIDADE_RESERVAS_BILHOES == "USD_bilhoes"
    assert ReservesRegime.AUMENTO.value == "aumento"
    assert ReservesRegime.ESTAVEL.value == "estavel"
    assert ReservesRegime.DETERIORACAO.value == "deterioracao"


def test_thresholds_defaults_mapping_and_aliases():
    default = ReservesThresholds()
    assert default.var_aumento == 2.0
    assert default.var_deterioracao == -2.0
    assert default.drawdown == -3.0
    assert default.limiar_aumento == 2.0
    assert default.limiar_deterioracao == -2.0
    assert default.limiar_drawdown == -3.0

    custom = ReservesThresholds.from_mapping(
        {"var_aumento": 1.5, "var_deterioracao": -1.0, "drawdown": -4.0}
    )
    assert custom.var_aumento == 1.5
    assert custom.var_deterioracao == -1.0
    assert custom.drawdown == -4.0
    assert custom.as_dict()["var_aumento"] == 1.5


def test_indicators_equality_units_and_missing_values():
    first = ReservesIndicators(nivel_atual=360.0, var_3m=1.5)
    second = ReservesIndicators(nivel_atual=360.0, var_3m=1.5)

    assert first == second
    assert first.unidade == UNIDADE_RESERVAS_BILHOES
    assert not first.vazio
    assert ReservesIndicators().vazio
    assert ReservesIndicators().regime is None
