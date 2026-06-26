from dataclasses import dataclass
from enum import Enum

import numpy as np

from b3_selic_pre.application.analyze._config import InferenceConfig
from b3_selic_pre.application.analyze._metrics import DetailedMetrics


class FeatureType(Enum):
    BOOLEAN = "boolean"
    ENUM = "enum"
    ORDINAL = "ordinal"


@dataclass(frozen=True)
class Feature:
    name: str
    value: bool | str | int
    type: FeatureType
    derived_from_metrics: list[str]


def _bool_feat(name: str, value: bool, derived: list[str]) -> Feature:
    return Feature(name=name, value=value, type=FeatureType.BOOLEAN, derived_from_metrics=derived)


def compute_features(
    metrics: DetailedMetrics,
    rates: list[float],
    config: InferenceConfig,
) -> dict[str, Feature]:
    features: dict[str, Feature] = {}
    n = len(rates)

    slope_global = metrics.slope_global
    convexity = metrics.indice_convexidade
    amplitude = metrics.amplitude
    suavidade = metrics.indice_suavidade
    volatilidade = metrics.indice_volatilidade
    oscilacao = metrics.indice_oscilacao
    monotonia = metrics.indice_monotonia

    epsilon = config.epsilon_slope

    # --- Basic trend ---

    features["TREND_UP"] = _bool_feat("TREND_UP", slope_global > epsilon, ["slope_global"])
    features["TREND_DOWN"] = _bool_feat("TREND_DOWN", slope_global < -epsilon, ["slope_global"])
    features["SLOPE_FLAT"] = _bool_feat("SLOPE_FLAT", abs(slope_global) < epsilon, ["slope_global"])

    features["FINAL_GT_INITIAL"] = _bool_feat(
        "FINAL_GT_INITIAL", metrics.taxa_final > metrics.taxa_inicial, ["delta_final"]
    )
    features["FINAL_LT_INITIAL"] = _bool_feat(
        "FINAL_LT_INITIAL", metrics.taxa_final < metrics.taxa_inicial, ["delta_final"]
    )

    # --- Segment-based ---

    if n >= 3:
        third = max(1, n // 3)
        short_end = rates[:third]
        short_mean = sum(short_end) / len(short_end)
        short_start = rates[0]
        features["SHORT_END_UP"] = _bool_feat(
            "SHORT_END_UP", short_mean > short_start + epsilon, ["slope_global"]
        )
        features["SHORT_END_DOWN"] = _bool_feat(
            "SHORT_END_DOWN", short_mean < short_start - epsilon, ["slope_global"]
        )

        two_thirds = max(1, 2 * n // 3)
        mid_section = rates[third:two_thirds]
        mid_mean = None
        if mid_section:
            mid_mean = sum(mid_section) / len(mid_section)
            features["MID_END_UP"] = _bool_feat(
                "MID_END_UP", mid_mean > short_mean + epsilon, ["slope_global"]
            )

        long_end = rates[two_thirds:]
        if long_end:
            long_mean = sum(long_end) / len(long_end)
            features["LONG_END_UP"] = _bool_feat(
                "LONG_END_UP",
                long_mean > (mid_mean + epsilon if mid_mean is not None else short_mean + epsilon),
                ["slope_global"],
            )
            features["LONG_END_DOWN"] = _bool_feat(
                "LONG_END_DOWN", long_mean < rates[two_thirds] - epsilon, ["slope_global"]
            )
    else:
        for k in ("SHORT_END_UP", "SHORT_END_DOWN", "MID_END_UP", "LONG_END_UP", "LONG_END_DOWN"):
            if k not in features:
                features[k] = _bool_feat(k, False, ["slope_global"])

    # --- Valley / Peak ---

    if n > 0:
        features["VALLEY_EARLY"] = _bool_feat(
            "VALLEY_EARLY",
            (
                metrics.indice_minimo_global > 0
                and metrics.indice_minimo_global / n <= config.vale_posicao_max
                and metrics.indice_minimo_global < n - 2
            ),
            ["indice_minimo_global"],
        )
        features["PEAK_EARLY"] = _bool_feat(
            "PEAK_EARLY",
            (
                metrics.indice_maximo_global > 0
                and metrics.indice_maximo_global < n - 2
                and metrics.indice_maximo_global / n <= config.pico_posicao_max
            ),
            ["indice_maximo_global"],
        )

        min_idx = metrics.indice_minimo_global
        max_idx = metrics.indice_maximo_global

        if max_idx > min_idx:
            min_val = rates[min_idx]
            last_min = max(i for i, r in enumerate(rates) if r == min_val)
            recovery_start = min(last_min, max_idx - 1)
            recovery_zone = rates[recovery_start:max_idx + 1]
            after_min_deltas = [recovery_zone[i + 1] - recovery_zone[i] for i in range(len(recovery_zone) - 1)] if len(recovery_zone) >= 2 else []
        else:
            after_min_deltas = []
        pos_after_min = sum(1 for d in after_min_deltas if d >= 0)
        if len(after_min_deltas) > 0:
            after_min_ratio = pos_after_min / len(after_min_deltas)
        else:
            after_min_ratio = 0.0
        features["AFTER_MIN_UP"] = _bool_feat(
            "AFTER_MIN_UP",
            after_min_ratio >= config.recuperacao_min_ratio,
            ["indice_minimo_global"],
        )

        if min_idx > max_idx:
            max_val = rates[max_idx]
            last_max = max(i for i, r in enumerate(rates) if r == max_val)
            descent_start = min(last_max, min_idx - 1)
            descent_zone = rates[descent_start:min_idx + 1]
            after_max_deltas = [descent_zone[i + 1] - descent_zone[i] for i in range(len(descent_zone) - 1)] if len(descent_zone) >= 2 else []
        else:
            after_max_deltas = []
        neg_after_max = sum(1 for d in after_max_deltas if d <= 0)
        if len(after_max_deltas) > 0:
            after_max_ratio = neg_after_max / len(after_max_deltas)
        else:
            after_max_ratio = 0.0
        features["AFTER_MAX_DOWN"] = _bool_feat(
            "AFTER_MAX_DOWN",
            after_max_ratio >= config.recuperacao_min_ratio,
            ["indice_maximo_global"],
        )
    else:
        for k in ("VALLEY_EARLY", "PEAK_EARLY", "AFTER_MIN_UP", "AFTER_MAX_DOWN"):
            if k not in features:
                features[k] = _bool_feat(k, False, ["indice_minimo_global"])

    # --- Oscillation ---

    features["OSCILLATING"] = _bool_feat(
        "OSCILLATING",
        n >= 8 and oscilacao >= config.oscilacao_threshold,
        ["indice_oscilacao"],
    )

    # --- Smoothness ---

    if amplitude > config.epsilon_amplitude:
        features["SMOOTH"] = _bool_feat(
            "SMOOTH",
            (suavidade / amplitude) <= config.suavidade_relativo,
            ["indice_suavidade", "amplitude"],
        )
    else:
        features["SMOOTH"] = _bool_feat("SMOOTH", True, ["indice_suavidade", "amplitude"])

    features["ROUGH"] = _bool_feat(
        "ROUGH",
        suavidade >= config.suavidade_serrilhado,
        ["indice_suavidade"],
    )

    # --- Monotonicity ---

    features["MONOTONIC"] = _bool_feat(
        "MONOTONIC",
        n >= 3 and monotonia >= config.monotonico_ratio,
        ["indice_monotonia"],
    )

    # --- Recovery ---

    features["RECOVERY_STRONG"] = _bool_feat(
        "RECOVERY_STRONG",
        (metrics.longo.delta > 0 and metrics.medio.delta > 0),
        ["delta_final"],
    )

    # --- Sigmoid ---

    sigmoidal = False
    if n >= 4 and metrics.qtd_inflexoes >= 2:
        min_segment = n * config.sigmoide_segment_min
        inflex_positions = []
        slopes = [rates[i + 1] - rates[i] for i in range(n - 1)]
        curvaturas = [slopes[i + 1] - slopes[i] for i in range(len(slopes) - 1)]
        for i in range(1, len(curvaturas)):
            if curvaturas[i] * curvaturas[i - 1] < 0:
                inflex_positions.append(i + 1)
        if len(inflex_positions) >= 2:
            segments = []
            prev = 0
            for pos in inflex_positions:
                segments.append(pos - prev)
                prev = pos
            segments.append(n - prev)
            sigmoidal = all(s >= min_segment for s in segments if s > 0)
    features["SIGMOIDAL_SHAPE"] = _bool_feat(
        "SIGMOIDAL_SHAPE", sigmoidal, ["qtd_inflexoes"]
    )

    # --- Flat ---

    features["AMPLITUDE_LOW"] = _bool_feat(
        "AMPLITUDE_LOW",
        amplitude < config.amplitude_consenso,
        ["amplitude"],
    )
    features["DELTA_FINAL_LOW"] = _bool_feat(
        "DELTA_FINAL_LOW",
        abs(metrics.delta_final) < config.epsilon_horizontal,
        ["delta_final"],
    )

    # --- Structural ---

    achata = False
    empina = False
    curto_d = metrics.curto.delta
    longo_d = metrics.longo.delta
    if curto_d != 0 and longo_d != 0 and ((curto_d > 0 and longo_d > 0) or (curto_d < 0 and longo_d < 0)):
        ratio_cl = abs(curto_d) / abs(longo_d)
        ratio_lc = abs(longo_d) / abs(curto_d)
        if ratio_cl >= config.steepening_ratio:
            achata = True
        elif ratio_lc >= config.steepening_ratio:
            empina = True
    features["ACHATAMENTO_FLAG"] = _bool_feat("ACHATAMENTO_FLAG", achata, ["delta_final"])
    features["EMPINAMENTO_FLAG"] = _bool_feat("EMPINAMENTO_FLAG", empina, ["delta_final"])

    torcao = False
    if metrics.curto.delta > 0 and metrics.longo.delta < -abs(metrics.curto.delta) * 0.5:
        torcao = True
    features["TORCAO_FLAG"] = _bool_feat("TORCAO_FLAG", torcao, ["delta_final"])

    staircase = False
    if n >= 4 and metrics.qtd_inflexoes >= 2:
        staircase = metrics.indice_oscilacao >= config.oscilacao_threshold * 0.5
    features["STAIRCASE"] = _bool_feat("STAIRCASE", staircase, ["indice_oscilacao", "qtd_inflexoes"])

    # --- Volatility ---

    features["VOLATILITY_LOW"] = _bool_feat(
        "VOLATILITY_LOW",
        volatilidade <= config.volatilidade_baixa,
        ["indice_volatilidade"],
    )
    features["VOLATILITY_HIGH"] = _bool_feat(
        "VOLATILITY_HIGH",
        volatilidade >= config.volatilidade_alta,
        ["indice_volatilidade"],
    )
    features["VOLATILITY_MODERATE"] = _bool_feat(
        "VOLATILITY_MODERATE",
        config.volatilidade_baixa < volatilidade < config.volatilidade_alta,
        ["indice_volatilidade"],
    )

    # --- Amplitude consensus / dispersion ---

    features["AMPLITUDE_CONSENSO"] = _bool_feat(
        "AMPLITUDE_CONSENSO",
        amplitude < config.amplitude_consenso,
        ["amplitude"],
    )
    features["AMPLITUDE_DISPERSAO"] = _bool_feat(
        "AMPLITUDE_DISPERSAO",
        amplitude > config.amplitude_dispersao,
        ["amplitude"],
    )

    # --- Long Recovery ---

    long_recovery = False
    if n >= 20:
        min_seg_len = max(10, int(n * config.recuperacao_longa_min_pct))
        best_seg = None
        best_len = 0
        for i in range(n):
            for j in range(i + min_seg_len, n + 1):
                seg = rates[i:j]
                seg_len = j - i
                if seg_len < min_seg_len:
                    continue
                deltas = [seg[k + 1] - seg[k] for k in range(seg_len - 1)]
                pos_count = sum(1 for d in deltas if d > config.epsilon_slope)
                if seg_len - 1 > 0 and (pos_count / (seg_len - 1)) < config.recuperacao_longa_min_ratio:
                    continue
                seg_amplitude = max(seg) - min(seg)
                if seg_amplitude < amplitude * config.recuperacao_longa_min_amplitude:
                    continue
                if seg_len >= 2:
                    x = np.arange(seg_len, dtype=float)
                    slope = float(np.polyfit(x, seg, 1)[0])
                    if slope <= config.epsilon_slope:
                        continue
                if seg_len > best_len:
                    best_len = seg_len
                    best_seg = (i, j)
        if best_seg is not None:
            long_recovery = True

    features["LONG_RECOVERY"] = _bool_feat(
        "LONG_RECOVERY",
        long_recovery,
        ["indice_oscilacao", "amplitude"],
    )

    # --- Enum features ---

    if abs(convexity) < config.epsilon_convexity:
        conv_value = "LINEAR"
    elif convexity > 0:
        conv_value = "CONVEX"
    else:
        conv_value = "CONCAVE"
    features["CONVEXITY"] = Feature(
        name="CONVEXITY",
        value=conv_value,
        type=FeatureType.ENUM,
        derived_from_metrics=["indice_convexidade"],
    )

    return features
