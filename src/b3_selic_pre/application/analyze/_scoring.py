from b3_selic_pre.application.analyze._classifier import Fact
from b3_selic_pre.application.analyze._registry import FactType

SCORING_POLICY: dict[str, tuple[int, int]] = {
    "ASCENDENTE": (2, 3),
    "DESCENDENTE": (2, 3),
    "VALE": (2, 3),
    "PICO": (2, 3),
    "SIGMOIDE": (2, 3),
    "OSCILANTE": (1, 3),
    "PLANA": (0, 3),
    "INDEFINIDA": (0, 3),
    "RECUPERACAO_SUSTENTADA": (1, 2),
    "ACHATAMENTO": (1, 2),
    "EMPINAMENTO": (1, 2),
    "TORCAO": (2, 3),
    "DEGRAUS": (0, 1),
    "ENVELOPE_CRESCENTE": (1, 1),
    "ENVELOPE_DECRESCENTE": (1, 1),
    "CURVA_SUAVE": (1, 1),
    "BAIXA_VOLATILIDADE": (1, 1),
    "CURVA_SERRILHADA": (-1, 1),
    "ALTA_VOLATILIDADE": (-2, 1),
    "OSCILACAO": (-2, 1),
    "MONOTONIA": (0, 1),
    "VOLATILIDADE_MODERADA": (0, 1),
    "RECUPERACAO_LONGA": (1, 2),
}


def compute_score(facts: list[Fact], policy: dict[str, tuple[int, int]] | None = None) -> int:
    if policy is None:
        policy = SCORING_POLICY
    total = 0
    for fact in facts:
        entry = policy.get(fact.id)
        if entry:
            score_base, weight_level = entry
            total += score_base * weight_level
    return total


def compute_confidence_per_level(facts: list[Fact]) -> dict[str, float]:
    levels: dict[str, list[float]] = {}
    for fact in facts:
        level_key = fact.fact_type.value
        if level_key not in levels:
            levels[level_key] = []
        levels[level_key].append(fact.confidence)

    result: dict[str, float] = {}
    for level_key, confs in levels.items():
        if confs:
            result[level_key] = sum(confs) / len(confs)
        else:
            result[level_key] = 0.0
    return result


def classify_intensity(score: int, direction: str) -> str:
    if direction == "asc":
        if score >= 12:
            return "Mudanca estrutural ascendente expressiva"
        elif score >= 9:
            return "Mudanca estrutural ascendente significativa"
        elif score >= 6:
            return "Reprecificacao ascendente relevante"
        elif score >= 3:
            return "Curva estruturalmente ascendente"
        else:
            return "Mercado estavel"
    elif direction == "desc":
        if score >= 12:
            return "Mudanca estrutural descendente expressiva"
        elif score >= 9:
            return "Mudanca estrutural descendente significativa"
        elif score >= 6:
            return "Reprecificacao descendente relevante"
        elif score >= 3:
            return "Curva estruturalmente invertida"
        else:
            return "Mercado estavel"
    else:
        if score >= 12:
            return "Mudanca estrutural expressiva"
        elif score >= 9:
            return "Mudanca estrutural significativa"
        elif score >= 6:
            return "Reprecificacao relevante"
        elif score >= 3:
            return "Mudanca moderada"
        else:
            return "Mercado estavel"
