from dataclasses import dataclass, field

from b3_selic_pre.application.analyze._config import InferenceConfig
from b3_selic_pre.application.analyze._features import Feature
from b3_selic_pre.application.analyze._registry import RuleDef, FactType, get_rules_sorted


@dataclass
class Fact:
    id: str
    rule_id: str
    fact_type: FactType
    confidence: float
    derived_from_features: list[str]
    text: str = ""
    template_id: str = ""


@dataclass
class RuleEvaluation:
    rule_id: str
    matched_features: list[str]
    missing_features: list[str]
    activation_score: float
    activated: bool


FEATURE_WEIGHTS: dict[str, float] = {
    "VALLEY_EARLY": 3.0,
    "PEAK_EARLY": 3.0,
    "SIGMOIDAL_SHAPE": 3.0,
    "TREND_UP": 3.0,
    "TREND_DOWN": 3.0,
    "OSCILLATING": 3.0,
    "FINAL_GT_INITIAL": 2.0,
    "FINAL_LT_INITIAL": 2.0,
    "AFTER_MIN_UP": 2.0,
    "AFTER_MAX_DOWN": 2.0,
    "AMPLITUDE_LOW": 2.0,
    "DELTA_FINAL_LOW": 2.0,
    "SLOPE_FLAT": 2.0,
    "RECOVERY_STRONG": 1.5,
    "MONOTONIC": 1.5,
    "SHORT_END_UP": 1.0,
    "SHORT_END_DOWN": 1.0,
    "LONG_END_UP": 1.0,
    "LONG_END_DOWN": 1.0,
    "MID_END_UP": 1.0,
}


def _rule_features(rule: RuleDef) -> list[str]:
    return list(rule.required_features) + list(rule.optional_features)


def _check_feature(features: dict[str, Feature], name: str) -> bool:
    f = features.get(name)
    return f is not None and bool(f.value)


def _compute_activation_score(
    features: dict[str, Feature],
    rule: RuleDef,
) -> float:
    all_feats = _rule_features(rule)
    if not all_feats:
        return 0.0
    total_weight = sum(FEATURE_WEIGHTS.get(f, 1.0) for f in all_feats)
    matched_weight = sum(
        FEATURE_WEIGHTS.get(f, 1.0) for f in all_feats
        if _check_feature(features, f)
    )
    return matched_weight / total_weight if total_weight > 0 else 0.0


def classify(
    features: dict[str, Feature],
    config: InferenceConfig,
) -> tuple[list[Fact], list[RuleEvaluation]]:
    rules = get_rules_sorted()
    facts: list[Fact] = []
    evaluations: list[RuleEvaluation] = []
    activated_groups: set[str] = set()
    activated_facts: set[str] = set()

    for rule in rules:
        # Exclusive group check
        if rule.exclusive_group and rule.exclusive_group in activated_groups:
            continue

        # Gating check
        if rule.gated_by:
            gated = any(g in activated_facts for g in rule.gated_by)
            if not gated:
                continue

        # Build matched/missing for this rule
        all_feats = _rule_features(rule)
        matched = [f for f in all_feats if _check_feature(features, f)]
        missing = [f for f in all_feats if not _check_feature(features, f)]
        score = _compute_activation_score(features, rule)

        # Required features check
        required_satisfied = all(
            _check_feature(features, f) for f in rule.required_features
        )
        if rule.required_features and not required_satisfied:
            evaluations.append(RuleEvaluation(
                rule_id=rule.id,
                matched_features=matched,
                missing_features=missing,
                activation_score=score,
                activated=False,
            ))
            continue

        # INDEFINIDA always passes (no required features)
        if rule.id == "INDEFINIDA":
            fact = Fact(
                id=rule.generated_fact,
                rule_id=rule.id,
                fact_type=rule.fact_type,
                confidence=1.0,
                derived_from_features=[],
                template_id=rule.template_id,
            )
            facts.append(fact)
            activated_facts.add(rule.generated_fact)
            if rule.exclusive_group:
                activated_groups.add(rule.exclusive_group)
            evaluations.append(RuleEvaluation(
                rule_id=rule.id,
                matched_features=matched,
                missing_features=missing,
                activation_score=score,
                activated=True,
            ))
            continue

        # Optional features check
        satisfied_optional = [
            f for f in rule.optional_features
            if _check_feature(features, f)
        ]
        if len(satisfied_optional) < rule.min_optional:
            evaluations.append(RuleEvaluation(
                rule_id=rule.id,
                matched_features=matched,
                missing_features=missing,
                activation_score=score,
                activated=False,
            ))
            continue

        # Compute confidence
        total_optional = len(rule.optional_features)
        if total_optional > 0:
            confidence = len(satisfied_optional) / total_optional
        else:
            confidence = 1.0

        # Build derived_from_features
        derived = list(rule.required_features) + satisfied_optional

        fact = Fact(
            id=rule.generated_fact,
            rule_id=rule.id,
            fact_type=rule.fact_type,
            confidence=confidence,
            derived_from_features=derived,
            template_id=rule.template_id,
        )
        facts.append(fact)
        activated_facts.add(rule.generated_fact)
        if rule.exclusive_group:
            activated_groups.add(rule.exclusive_group)
        evaluations.append(RuleEvaluation(
            rule_id=rule.id,
            matched_features=matched,
            missing_features=missing,
            activation_score=score,
            activated=True,
        ))

    # --- R199 fallback: Primary Class by Dominance ---
    if not any(f.fact_type == FactType.CLASSIFICATION for f in facts):
        # Collect primary class evaluations
        primary_rules = [r for r in rules
                         if r.exclusive_group == "PRIMARY_CLASS"
                         and r.id != "INDEFINIDA"]
        primary_rule_ids = {r.id for r in primary_rules}
        primary_evals = [e for e in evaluations if e.rule_id in primary_rule_ids]

        if primary_evals:
            best = max(primary_evals, key=lambda e: e.activation_score)
            if best.activation_score >= 0.70:
                # Find the rule to get generated_fact and template_id
                best_rule = next((r for r in rules if r.id == best.rule_id), None)
                if best_rule:
                    promoted_fact = Fact(
                        id=best_rule.generated_fact,
                        rule_id=best_rule.id,
                        fact_type=FactType.CLASSIFICATION,
                        confidence=best.activation_score,
                        derived_from_features=best.matched_features,
                        template_id="fallback_primary",
                    )
                    facts.append(promoted_fact)

    return facts, evaluations


# Backward compatibility re-exports
LevelResult = None
InferenceResult = None
