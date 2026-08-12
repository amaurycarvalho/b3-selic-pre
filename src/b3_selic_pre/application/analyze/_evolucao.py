from __future__ import annotations

from dataclasses import dataclass, field

from b3_selic_pre.application.analyze._config import CurvaJurosConfig, EvolutionConfig
from b3_selic_pre.domain.models import RateRecord


def extrair_deltas(
    current_records: list[RateRecord],
    previous_records: list[RateRecord],
) -> tuple[float, float, float, float]:
    """Calcula os deltas de curto/longo prazo, da inclinação e do juro real.

    As taxas são convertidas de string para float normalizando a vírgula, e os
    deltas são expressos em pontos-base (bps) entre as duas datas comparadas.
    """
    current_rates = [float(r.rate.replace(",", ".")) for r in current_records]
    previous_rates = [float(r.rate.replace(",", ".")) for r in previous_records]
    delta_short = (current_rates[0] - previous_rates[0]) * 100
    delta_long = (current_rates[-1] - previous_rates[-1]) * 100
    current_slope = (current_rates[-1] - current_rates[0]) * 100
    previous_slope = (previous_rates[-1] - previous_rates[0]) * 100
    delta_slope = current_slope - previous_slope
    delta_real = delta_short
    return delta_short, delta_long, delta_slope, delta_real


def classificar_movimento(
    delta_short: float, delta_long: float, config: EvolutionConfig
) -> str:
    """Classifica o movimento geral da curva (Estável, Bear, Bull ou Twist).

    Quando a variação em ambas as pontas ultrapassa o limiar configurado na
    mesma direção o movimento é Bear (alta) ou Bull (baixa); direções opostas
    geram Twist, e variações pequenas demais resultam em Estável.
    """
    threshold = config.movement_threshold_bps
    if max(abs(delta_short), abs(delta_long)) < threshold:
        return "Estável"
    if delta_short > threshold and delta_long > threshold:
        return "Bear"
    if delta_short < -threshold and delta_long < -threshold:
        return "Bull"
    if (delta_short > threshold and delta_long < -threshold) or (
        delta_short < -threshold and delta_long > threshold
    ):
        return "Twist"
    return "Estável"


def classificar_slope_movement(
    delta_slope: float, config: EvolutionConfig
) -> str:
    """Classifica a variação da inclinação em Steepening, Flattening ou Parallel Shift.

    Usa o limiar de inclinação configurado: delta positivo indica inclinação da
    curva, delta negativo indica achatamento, e variações pequenas são neutras.
    """
    threshold = config.steepening_threshold_bps
    if delta_slope > threshold:
        return "Steepening"
    if delta_slope < -threshold:
        return "Flattening"
    return "Parallel Shift"


def classificar_regime(movimento: str, slope_movement: str) -> str:
    """Combina movimento geral e variação da inclinação em um regime único.

    Estados Estável e Twist são mantidos como estão; caso contrário o regime é
    a concatenação do movimento geral com a variação da inclinação (ex.: Bear
    Steepening).
    """
    if movimento == "Estável":
        return "Estável"
    if movimento == "Twist":
        return "Twist"
    return f"{movimento} {slope_movement}"


def classificar_intensidade(
    delta_short: float, delta_long: float, config: EvolutionConfig
) -> str:
    """Classifica a intensidade do movimento pela maior variação entre as pontas.

    Compara a variação máxima absoluta com as faixas de intensidade configuradas
    (muito fraca, fraca, moderada, forte e muito forte).
    """
    max_abs = max(abs(delta_short), abs(delta_long))
    if max_abs <= config.very_weak_max:
        return "Muito Fraca"
    if max_abs <= config.weak_max:
        return "Fraca"
    if max_abs <= config.moderate_max:
        return "Moderada"
    if max_abs <= config.strong_max:
        return "Forte"
    return "Muito Forte"


def classificar_politica_monetaria(
    delta_real: float, config: EvolutionConfig
) -> str:
    """Traduz a variação do juro real em mensagem sobre a política monetária.

    Deltas positivos indicam política mais restritiva e deltas negativos
    indicam política menos restritiva, conforme os limiares configurados.
    """
    if delta_real > config.highly_restrictive_min:
        return "Mercado passou a precificar política mais restritiva"
    if delta_real > config.slightly_restrictive_min:
        return "Política ligeiramente mais restritiva"
    if abs(delta_real) <= config.neutral_max:
        return "Política praticamente inalterada"
    if delta_real < -config.slightly_loose_max:
        return "Mercado passou a precificar política significativamente menos restritiva"
    if delta_real < -config.slightly_restrictive_min:
        return "Política ligeiramente menos restritiva"
    return "Política praticamente inalterada"


def classificar_premio_prazo(
    delta_slope: float, config: EvolutionConfig
) -> str:
    """Descreve a variação do prêmio de prazo conforme o delta da inclinação.

    Deltas positivos aumentam o prêmio de prazo e deltas negativos o reduzem,
    sempre usando os limiares de aumento e redução definidos na configuração.
    """
    if delta_slope > config.significantly_increased_min:
        return "Prêmio de prazo aumentou significativamente"
    if delta_slope > config.increased_min:
        return "Prêmio aumentou"
    if abs(delta_slope) <= config.increased_min:
        return "Praticamente estável"
    if delta_slope < -config.decreased_min:
        return "Forte redução do prêmio"
    if delta_slope < -config.increased_min:
        return "Prêmio diminuiu"
    return "Praticamente estável"


def derivar_direcao_geral(regime: str, intensidade: str) -> str:
    """Deriva a mensagem de direção geral dos juros a partir do regime e intensidade.

    Regimes Bear e Bull são convertidos em mensagens de revisão altista ou
    baixista, com tratamento especial para intensidade muito fraca.
    """
    if regime == "Estável":
        return "→ Estrutura a Juros Praticamente Estável"
    if regime == "Twist":
        return "↕ Movimento Misto na Estrutura"
    if regime.startswith("Bear"):
        if intensidade in ("Muito Fraca",):
            return "→ Juros Marginalmente Mais Altos"
        return "↑ Revisão Altista dos Juros"
    if regime.startswith("Bull"):
        if intensidade in ("Muito Fraca",):
            return "→ Juros Marginalmente Mais Baixos"
        return "↓ Revisão Baixista dos Juros"
    return "→ Estrutura a Juros Praticamente Estável"


@dataclass
class EvolutionReport:
    """Relatório da evolução da curva entre duas datas com mensagens e deltas."""

    statements: list[str] = field(default_factory=list)
    delta_short_bps: float = 0.0
    delta_long_bps: float = 0.0
    delta_slope_bps: float = 0.0
    delta_real_bps: float = 0.0
    regime: str = ""
    intensity: str = ""
    monetary_policy_msg: str = ""
    term_premium_msg: str = ""
    direction: str = ""
    market_message: str = ""


def analyze_evolution(
    current: list[RateRecord],
    previous: list[RateRecord],
    config: CurvaJurosConfig | None = None,
) -> EvolutionReport | None:
    """Analisa a evolução da curva entre as duas datas e monta o relatório final.

    Sem dados anteriores retorna ``None``. Caso contrário classifica movimento,
    regime, intensidade, política monetária e prêmio de prazo, devolvendo um
    :class:`EvolutionReport` com todas as mensagens e deltas calculados.
    """
    if not previous:
        return None

    if config is None:
        config = CurvaJurosConfig.from_settings()

    evol_config = config.evolucao
    delta_short, delta_long, delta_slope, delta_real = extrair_deltas(current, previous)

    movimento = classificar_movimento(delta_short, delta_long, evol_config)
    slope_movement = classificar_slope_movement(delta_slope, evol_config)
    regime = classificar_regime(movimento, slope_movement)

    if movimento == "Estável":
        intensidade = "Muito Fraca"
    else:
        intensidade = classificar_intensidade(delta_short, delta_long, evol_config)
    politica_msg = classificar_politica_monetaria(delta_real, evol_config)
    premio_msg = classificar_premio_prazo(delta_slope, evol_config)
    direction = derivar_direcao_geral(regime, intensidade)

    return EvolutionReport(
        statements=[],
        delta_short_bps=round(delta_short, 2),
        delta_long_bps=round(delta_long, 2),
        delta_slope_bps=round(delta_slope, 2),
        delta_real_bps=round(delta_real, 2),
        regime=regime,
        intensity=intensidade,
        monetary_policy_msg=politica_msg,
        term_premium_msg=premio_msg,
        direction=direction,
        market_message="",
    )
