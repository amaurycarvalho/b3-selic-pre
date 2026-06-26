from dataclasses import dataclass, field
from enum import Enum


class FactType(Enum):
    CLASSIFICATION = "classification"
    STRUCTURE = "structure"
    QUALITY = "quality"
    INTENSITY = "intensity"
    AUXILIARY = "auxiliary"


@dataclass
class RuleDef:
    id: str
    priority: int
    exclusive_group: str
    required_features: list[str]
    optional_features: list[str]
    min_optional: int
    gated_by: list[str] = field(default_factory=list)
    generated_fact: str = ""
    fact_type: FactType = FactType.AUXILIARY
    template_id: str = ""


_RULES: list[RuleDef] = [
    # === Level 1: PRIMARY CLASS ===
    # Priority order: OSCILANTE > VALE > PICO > SIGMOIDE > ASCENDENTE > DESCENDENTE > PLANA > INDEFINIDA

    RuleDef(
        id="OSCILANTE",
        priority=0,
        exclusive_group="PRIMARY_CLASS",
        required_features=["OSCILLATING"],
        optional_features=[],
        min_optional=0,
        generated_fact="OSCILANTE",
        fact_type=FactType.CLASSIFICATION,
        template_id="osc_primary",
    ),
    RuleDef(
        id="VALE",
        priority=10,
        exclusive_group="PRIMARY_CLASS",
        required_features=["VALLEY_EARLY"],
        optional_features=["FINAL_GT_INITIAL", "AFTER_MIN_UP", "RECOVERY_STRONG", "SHORT_END_UP"],
        min_optional=3,
        generated_fact="VALE",
        fact_type=FactType.CLASSIFICATION,
        template_id="vale_primary",
    ),
    RuleDef(
        id="PICO",
        priority=20,
        exclusive_group="PRIMARY_CLASS",
        required_features=["PEAK_EARLY"],
        optional_features=["FINAL_LT_INITIAL", "AFTER_MAX_DOWN", "LONG_END_DOWN", "SHORT_END_DOWN"],
        min_optional=3,
        generated_fact="PICO",
        fact_type=FactType.CLASSIFICATION,
        template_id="pico_primary",
    ),
    RuleDef(
        id="SIGMOIDE",
        priority=30,
        exclusive_group="PRIMARY_CLASS",
        required_features=["SIGMOIDAL_SHAPE"],
        optional_features=[],
        min_optional=0,
        generated_fact="SIGMOIDE",
        fact_type=FactType.CLASSIFICATION,
        template_id="sig_primary",
    ),
    RuleDef(
        id="ASCENDENTE",
        priority=40,
        exclusive_group="PRIMARY_CLASS",
        required_features=["TREND_UP"],
        optional_features=["LONG_END_UP", "MID_END_UP", "MONOTONIC"],
        min_optional=0,
        generated_fact="ASCENDENTE",
        fact_type=FactType.CLASSIFICATION,
        template_id="asc_primary",
    ),
    RuleDef(
        id="DESCENDENTE",
        priority=50,
        exclusive_group="PRIMARY_CLASS",
        required_features=["TREND_DOWN"],
        optional_features=["LONG_END_DOWN", "SHORT_END_DOWN"],
        min_optional=0,
        generated_fact="DESCENDENTE",
        fact_type=FactType.CLASSIFICATION,
        template_id="desc_primary",
    ),
    RuleDef(
        id="PLANA",
        priority=60,
        exclusive_group="PRIMARY_CLASS",
        required_features=["AMPLITUDE_LOW", "DELTA_FINAL_LOW", "SLOPE_FLAT"],
        optional_features=["SMOOTH"],
        min_optional=0,
        generated_fact="PLANA",
        fact_type=FactType.CLASSIFICATION,
        template_id="flat_primary",
    ),
    RuleDef(
        id="INDEFINIDA",
        priority=70,
        exclusive_group="PRIMARY_CLASS",
        required_features=[],
        optional_features=[],
        min_optional=0,
        generated_fact="INDEFINIDA",
        fact_type=FactType.CLASSIFICATION,
        template_id="und_primary",
    ),

    # === Level 2: STRUCTURE ===

    RuleDef(
        id="RECUPERACAO_SUSTENTADA",
        priority=200,
        exclusive_group="",
        required_features=[],
        optional_features=[],
        min_optional=0,
        gated_by=["VALE"],
        generated_fact="RECUPERACAO_SUSTENTADA",
        fact_type=FactType.STRUCTURE,
        template_id="rec_struct",
    ),
    RuleDef(
        id="ACHATAMENTO",
        priority=201,
        exclusive_group="",
        required_features=["ACHATAMENTO_FLAG"],
        optional_features=[],
        min_optional=0,
        generated_fact="ACHATAMENTO",
        fact_type=FactType.STRUCTURE,
        template_id="flat_struct",
    ),
    RuleDef(
        id="EMPINAMENTO",
        priority=202,
        exclusive_group="",
        required_features=["EMPINAMENTO_FLAG"],
        optional_features=[],
        min_optional=0,
        generated_fact="EMPINAMENTO",
        fact_type=FactType.STRUCTURE,
        template_id="steep_struct",
    ),
    RuleDef(
        id="TORCAO",
        priority=203,
        exclusive_group="",
        required_features=["TORCAO_FLAG"],
        optional_features=[],
        min_optional=0,
        generated_fact="TORCAO",
        fact_type=FactType.STRUCTURE,
        template_id="twist_struct",
    ),
    RuleDef(
        id="DEGRAUS",
        priority=204,
        exclusive_group="",
        required_features=["STAIRCASE"],
        optional_features=[],
        min_optional=0,
        generated_fact="DEGRAUS",
        fact_type=FactType.STRUCTURE,
        template_id="step_struct",
    ),
    RuleDef(
        id="MONOTONIA_STRUCT",
        priority=205,
        exclusive_group="",
        required_features=["MONOTONIC"],
        optional_features=[],
        min_optional=0,
        generated_fact="MONOTONIA",
        fact_type=FactType.STRUCTURE,
        template_id="mono_struct",
    ),
    RuleDef(
        id="RECUPERACAO_LONGA",
        priority=206,
        exclusive_group="",
        required_features=["LONG_RECOVERY"],
        optional_features=[],
        min_optional=0,
        generated_fact="RECUPERACAO_LONGA",
        fact_type=FactType.STRUCTURE,
        template_id="longrec_struct",
    ),

    # === Level 3: QUALITY ===

    RuleDef(
        id="CURVA_SUAVE",
        priority=400,
        exclusive_group="",
        required_features=["SMOOTH"],
        optional_features=[],
        min_optional=0,
        generated_fact="CURVA_SUAVE",
        fact_type=FactType.QUALITY,
        template_id="smooth_qual",
    ),
    RuleDef(
        id="CURVA_SERRILHADA",
        priority=401,
        exclusive_group="",
        required_features=["ROUGH"],
        optional_features=[],
        min_optional=0,
        generated_fact="CURVA_SERRILHADA",
        fact_type=FactType.QUALITY,
        template_id="rough_qual",
    ),
    RuleDef(
        id="BAIXA_VOLATILIDADE",
        priority=402,
        exclusive_group="",
        required_features=["VOLATILITY_LOW"],
        optional_features=[],
        min_optional=0,
        generated_fact="BAIXA_VOLATILIDADE",
        fact_type=FactType.QUALITY,
        template_id="lowvol_qual",
    ),
    RuleDef(
        id="ALTA_VOLATILIDADE",
        priority=403,
        exclusive_group="",
        required_features=["VOLATILITY_HIGH"],
        optional_features=[],
        min_optional=0,
        generated_fact="ALTA_VOLATILIDADE",
        fact_type=FactType.QUALITY,
        template_id="highvol_qual",
    ),
    RuleDef(
        id="OSCILACAO",
        priority=404,
        exclusive_group="",
        required_features=["OSCILLATING"],
        optional_features=[],
        min_optional=0,
        generated_fact="OSCILACAO",
        fact_type=FactType.QUALITY,
        template_id="osc_qual",
    ),
    RuleDef(
        id="ENVELOPE_CRESCENTE",
        priority=405,
        exclusive_group="",
        required_features=["AMPLITUDE_CONSENSO"],
        optional_features=[],
        min_optional=0,
        generated_fact="ENVELOPE_CRESCENTE",
        fact_type=FactType.QUALITY,
        template_id="envup_qual",
    ),
    RuleDef(
        id="ENVELOPE_DECRESCENTE",
        priority=406,
        exclusive_group="",
        required_features=["AMPLITUDE_DISPERSAO"],
        optional_features=[],
        min_optional=0,
        generated_fact="ENVELOPE_DECRESCENTE",
        fact_type=FactType.QUALITY,
        template_id="envdown_qual",
    ),
    RuleDef(
        id="VOLATILIDADE_MODERADA",
        priority=407,
        exclusive_group="",
        required_features=["VOLATILITY_MODERATE"],
        optional_features=[],
        min_optional=0,
        generated_fact="VOLATILIDADE_MODERADA",
        fact_type=FactType.QUALITY,
        template_id="volmod_qual",
    ),
]


def get_rules_sorted() -> list[RuleDef]:
    return sorted(_RULES, key=lambda r: r.priority)
