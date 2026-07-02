from b3_selic_pre.application.analyze._config import CurvaJurosConfig
from b3_selic_pre.application.analyze._resumo import (
    AnalysisReport,
    Indicadores,
    calcular_estabilidade,
    calcular_steepening,
    classificar_inclinacao,
    classificar_nominal,
    classificar_premio,
    classificar_restricao,
    extrair_indicadores,
)
from b3_selic_pre.application.analyze._texto import montar_resumo_executivo
from b3_selic_pre.domain.models import RateRecord


def analyze(
    records: list[RateRecord],
    historical_data: dict[str, list[RateRecord]] | None = None,
    view_mode: str = "raw",
    evolution_active: bool = False,
    threshold_overrides: dict | None = None,
    config: CurvaJurosConfig | None = None,
    locale: str = "pt",
) -> AnalysisReport:
    if not records:
        return AnalysisReport()

    if config is None:
        config = CurvaJurosConfig.from_settings()

    if threshold_overrides:
        for key, value in threshold_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

    indicadores = extrair_indicadores(records, config)
    estabilidade = calcular_estabilidade(historical_data, records, config)
    steepening = calcular_steepening(records, historical_data, config)

    blocos = montar_resumo_executivo(indicadores, config, estabilidade, steepening)

    statements = list(blocos.values())

    return AnalysisReport(statements=statements, score=0, score_label="")


__all__ = [
    "AnalysisReport",
    "CurvaJurosConfig",
    "Indicadores",
    "analyze",
    "extrair_indicadores",
    "classificar_nominal",
    "classificar_restricao",
    "classificar_premio",
    "classificar_inclinacao",
    "calcular_estabilidade",
    "calcular_steepening",
    "montar_resumo_executivo",
]
