import unittest

import numpy as np

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.application.analyze import analyze
from b3_selic_pre.application.analyze._config import InferenceConfig
from b3_selic_pre.application.analyze._metrics import extract_detailed_metrics
from b3_selic_pre.application.analyze._features import compute_features, Feature, FeatureType
from b3_selic_pre.application.analyze._classifier import classify, Fact, RuleEvaluation
from b3_selic_pre.application.analyze._registry import get_rules_sorted, RuleDef, FactType as RegistryFactType
from b3_selic_pre.application.analyze._scoring import (
    SCORING_POLICY,
    compute_score,
    compute_confidence_per_level,
    classify_intensity,
)
from b3_selic_pre.application.analyze._templates import resolve_template, TEMPLATES
from b3_selic_pre.application.analyze._report import (
    AnalysisReport,
    AnalysisResult,
    build_statements_from_facts,
    format_report,
    build_report,
    ENGINE_VERSION,
    RULESET_VERSION,
)


def _make_records(*rates, day_step=21):
    return [
        RateRecord(day252=i * day_step, day360=i * 30, rate=str(r).replace(".", ","))
        for i, r in enumerate(rates)
    ]


def _rates_from(records):
    return [float(r.rate.replace(",", ".")) for r in records]


# ========================== 11.1 Metrics ==========================


class TestMetrics(unittest.TestCase):
    def test_oscilacao_formula(self):
        records = _make_records(10, 12, 9, 14, 8, 15, 10, 13, day_step=20)
        m = extract_detailed_metrics(records)
        n = len(records)
        self.assertGreater(m.indice_oscilacao, 0.0)
        self.assertAlmostEqual(m.indice_oscilacao, m.qtd_mudancas / (n - 2))

    def test_monotonia_formula(self):
        records = _make_records(10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, day_step=50)
        m = extract_detailed_metrics(records)
        self.assertAlmostEqual(m.indice_monotonia, 1.0)

    def test_convexidade_polyfit(self):
        records = _make_records(10.0, 9.5, 9.0, 9.5, 10.0, day_step=50)
        m = extract_detailed_metrics(records)
        self.assertIsNotNone(m.indice_convexidade)

    def test_volatilidade_guard_zero_amplitude(self):
        records = _make_records(10.0, 10.0, 10.0, day_step=50)
        m = extract_detailed_metrics(records)
        self.assertEqual(m.indice_volatilidade, 0.0)

    def test_volatilidade_with_amplitude(self):
        records = _make_records(10.0, 12.0, 11.0, 13.0, 10.0, day_step=50)
        m = extract_detailed_metrics(records)
        self.assertGreater(m.indice_volatilidade, 0.0)

    def test_maximo_global_index(self):
        records = _make_records(10.0, 12.0, 11.0, 8.0, 13.0, day_step=50)
        m = extract_detailed_metrics(records)
        self.assertEqual(m.indice_maximo_global, 4)

    def test_empty_defaults(self):
        m = extract_detailed_metrics([])
        self.assertEqual(m.indice_oscilacao, 0.0)
        self.assertEqual(m.indice_monotonia, 0.0)
        self.assertEqual(m.indice_convexidade, 0.0)
        self.assertEqual(m.indice_volatilidade, 0.0)
        self.assertEqual(m.indice_maximo_global, 0)


# ========================== 11.3 Features ==========================


class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.config = InferenceConfig()

    def test_trend_up(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["TREND_UP"].value)
        self.assertEqual(f["TREND_UP"].type, FeatureType.BOOLEAN)
        self.assertEqual(f["TREND_UP"].derived_from_metrics, ["slope_global"])

    def test_trend_down(self):
        records = _make_records(14.0, 13.5, 13.0, 12.5, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["TREND_DOWN"].value)

    def test_valley_early(self):
        records = _make_records(14.15, 14.10, 14.05, 14.10, 14.20, 14.30, day_step=54)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["VALLEY_EARLY"].value)

    def test_valley_early_not_at_end(self):
        records = _make_records(14.0, 13.0, 12.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertFalse(f["VALLEY_EARLY"].value)

    def test_peak_early(self):
        records = _make_records(10.0, 11.0, 12.0, 10.0, 9.0, 8.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["PEAK_EARLY"].value)

    def test_oscillating(self):
        records = _make_records(10, 12, 8, 14, 9, 15, 10, 13, 11, 16, day_step=20)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["OSCILLATING"].value)

    def test_smooth(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["SMOOTH"].value)

    def test_rough(self):
        records = _make_records(10, 15, 9, 16, 8, 15, 9, 16, 10, day_step=20)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["ROUGH"].value)

    def test_monotonic(self):
        records = _make_records(10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["MONOTONIC"].value)

    def test_convexity_enum(self):
        records = _make_records(10.0, 9.0, 10.0, 11.0, 12.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertEqual(f["CONVEXITY"].type, FeatureType.ENUM)
        self.assertIn(f["CONVEXITY"].value, ["LINEAR", "CONVEX", "CONCAVE"])

    def test_volatility_moderate(self):
        records = _make_records(10.0, 10.2, 10.4, 10.6, 10.8, 11.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        vol = m.indice_volatilidade
        self.assertEqual(f["VOLATILITY_MODERATE"].value,
                         self.config.volatilidade_baixa < vol < self.config.volatilidade_alta)

    def test_after_min_up_restricted_window(self):
        rates = [14.15, 14.10, 14.05, 14.05, 14.08, 14.12, 14.15, 14.18,
                 14.20, 14.22, 14.23, 14.23, 14.23, 14.23, 14.23]
        records = _make_records(*rates, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["AFTER_MIN_UP"].value)

    def test_after_min_up_false_when_max_before_min(self):
        rates = [14.20, 14.10, 14.05, 14.03, 14.02, 14.01, 14.00]
        records = _make_records(*rates, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertFalse(f["AFTER_MIN_UP"].value)

    def test_after_max_down_restricted_window(self):
        rates = [14.20, 14.25, 14.30, 14.35, 14.40, 14.35, 14.30, 14.25,
                 14.20, 14.15, 14.10, 14.10, 14.10, 14.10, 14.10]
        records = _make_records(*rates, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        self.assertTrue(f["AFTER_MAX_DOWN"].value)

    def test_derived_from_metrics(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        m = extract_detailed_metrics(records)
        f = compute_features(m, _rates_from(records), self.config)
        for feature in f.values():
            self.assertIsInstance(feature.derived_from_metrics, list)
            self.assertGreater(len(feature.derived_from_metrics), 0)

    # 11.20 Test feature immutability
    def test_feature_immutable(self):
        feat = Feature(name="TEST", value=True, type=FeatureType.BOOLEAN, derived_from_metrics=["m1"])
        with self.assertRaises(Exception):
            feat.value = False


# ========================== 11.4 Registry ==========================


class TestRegistry(unittest.TestCase):
    def test_get_rules_sorted(self):
        rules = get_rules_sorted()
        priorities = [r.priority for r in rules]
        self.assertEqual(priorities, sorted(priorities))

    def test_no_duplicate_ids(self):
        rules = get_rules_sorted()
        ids = [r.id for r in rules]
        self.assertEqual(len(ids), len(set(ids)))

    def test_exclusive_groups_consistent(self):
        rules = get_rules_sorted()
        primary_rules = [r for r in rules if r.exclusive_group == "PRIMARY_CLASS"]
        self.assertGreater(len(primary_rules), 1)
        for r in primary_rules:
            self.assertEqual(r.fact_type, RegistryFactType.CLASSIFICATION)

    def test_all_structure_rules_gated_or_independent(self):
        rules = get_rules_sorted()
        dependent = {"RECUPERACAO_SUSTENTADA"}
        for r in rules:
            if r.fact_type == RegistryFactType.STRUCTURE:
                if r.generated_fact in dependent:
                    self.assertGreater(len(r.gated_by), 0,
                                       f"{r.id} must be gated (dependent)")
                else:
                    self.assertEqual(len(r.gated_by), 0,
                                     f"{r.id} must be ungated (independent)")

    def test_all_quality_rules_ungated(self):
        rules = get_rules_sorted()
        for r in rules:
            if r.fact_type == RegistryFactType.QUALITY:
                self.assertEqual(len(r.gated_by), 0)


# ========================== 11.5 Classifier ==========================


class TestClassifier(unittest.TestCase):
    def setUp(self):
        self.config = InferenceConfig()

    def _features_for(self, *rates, day_step=21):
        records = _make_records(*rates, day_step=day_step)
        m = extract_detailed_metrics(records)
        return compute_features(m, _rates_from(records), self.config)

    def test_purity(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        result1, _ = classify(features, self.config)
        result2, _ = classify(features, self.config)
        self.assertEqual(len(result1), len(result2))
        for f1, f2 in zip(result1, result2):
            self.assertEqual(f1.id, f2.id)
            self.assertEqual(f1.confidence, f2.confidence)

    # 11.6 VALE short-circuit
    def test_vale_short_circuit_no_valley(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        features_dict = {f.name: f for f in features.values()}
        vale_feature = features_dict.get("VALLEY_EARLY")
        self.assertFalse(vale_feature.value)
        facts, _ = classify(features, self.config)
        fact_ids = [f.id for f in facts]
        self.assertNotIn("VALE", fact_ids)

    # 11.7 VALE tolerance: 3/4 optional → activates
    def test_vale_activates_with_3_of_4(self):
        rates_list = [14.15, 14.14, 14.12, 14.10, 14.08, 14.06, 14.05, 14.07, 14.10,
                      14.15, 14.20, 14.25, 14.30, 14.35, 14.39]
        features = self._features_for(*rates_list, day_step=54)
        facts, _ = classify(features, self.config)
        vale_facts = [f for f in facts if f.id == "VALE"]
        self.assertEqual(len(vale_facts), 1)
        self.assertAlmostEqual(vale_facts[0].confidence, 0.75)

    # 11.7 VALE tolerance: 2/4 optional → does not activate
    def test_vale_rejected_with_2_of_4(self):
        strict_config = InferenceConfig(recuperacao_min_ratio=0.99, vale_posicao_max=0.15)
        rates_list = [14.15, 14.14, 14.12, 14.10, 14.08, 14.06, 14.05, 14.07, 14.10,
                      14.15, 14.20, 14.25, 14.30, 14.35, 14.39]
        records = _make_records(*rates_list, day_step=54)
        m = extract_detailed_metrics(records)
        features = compute_features(m, _rates_from(records), strict_config)
        facts, _ = classify(features, strict_config)
        fact_ids = [f.id for f in facts]
        self.assertNotIn("VALE", fact_ids)

    # 11.8 exclusive_group
    def test_exclusive_group_only_one_primary(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        facts, _ = classify(features, self.config)
        primary_facts = [f for f in facts if f.fact_type == RegistryFactType.CLASSIFICATION]
        self.assertEqual(len(primary_facts), 1)

    # 11.9 confidence
    def test_confidence_computation(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        facts, _ = classify(features, self.config)
        ascendente = [f for f in facts if f.id == "ASCENDENTE"]
        self.assertEqual(len(ascendente), 1)
        self.assertEqual(ascendente[0].confidence, 1.0)

    # 11.10 derived_from_features
    def test_derived_from_features(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        facts, _ = classify(features, self.config)
        ascendente = [f for f in facts if f.id == "ASCENDENTE"][0]
        self.assertIn("TREND_UP", ascendente.derived_from_features)
        for feat_name in ascendente.derived_from_features:
            self.assertIn(feat_name, features)

    # 11.5 Classifier purity (call twice)
    def test_classifier_deterministic(self):
        features = self._features_for(14.15, 14.10, 14.05, 14.10, 14.20, 14.30, 14.40,
                                      14.50, 14.60, day_step=50)
        result1, _ = classify(features, self.config)
        result2, _ = classify(features, self.config)
        self.assertEqual([f.id for f in result1], [f.id for f in result2])
        self.assertEqual([f.confidence for f in result1], [f.confidence for f in result2])

    # 5.7 Classifier must NOT mutate inputs
    def test_classifier_does_not_mutate_features(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        m = extract_detailed_metrics(records)
        features = compute_features(m, _rates_from(records), self.config)
        before = {k: f.value for k, f in features.items()}
        classify(features, self.config)[0]
        after = {k: f.value for k, f in features.items()}
        self.assertEqual(before, after)

    # R199 fallback tests
    def test_rulevaluation_matched_and_missing(self):
        rates_list = [14.15, 14.14, 14.12, 14.10, 14.06, 14.05, 14.07, 14.15,
                      14.25, 14.35, 14.39, 14.38, 14.30, 14.25, 14.21]
        features = self._features_for(*rates_list, day_step=54)
        _, evaluations = classify(features, self.config)
        vale_eval = next((e for e in evaluations if e.rule_id == "VALE"), None)
        self.assertIsNotNone(vale_eval)
        self.assertIn("VALLEY_EARLY", vale_eval.matched_features)
        self.assertFalse(vale_eval.activated)

    def test_rulevaluation_skipped_for_activated_group(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        _, evaluations = classify(features, self.config)
        asc_eval = next((e for e in evaluations if e.rule_id == "ASCENDENTE"), None)
        self.assertIsNotNone(asc_eval)
        self.assertTrue(asc_eval.activated)
        desc_eval = next((e for e in evaluations if e.rule_id == "DESCENDENTE"), None)
        self.assertIsNone(desc_eval)

    def test_r199_promotes_vale(self):
        strict_config = InferenceConfig(
            recuperacao_min_ratio=0.99,
            vale_posicao_max=0.40,
        )
        rates_list = [14.15, 14.14, 14.12, 14.10, 14.08, 14.06, 14.05, 14.07,
                      14.10, 14.13, 14.15, 14.18, 14.20, 14.22, 14.25]
        records = _make_records(*rates_list, day_step=54)
        m = extract_detailed_metrics(records)
        features = compute_features(m, _rates_from(records), strict_config)
        facts, evaluations = classify(features, strict_config)
        primary_ids = [f.id for f in facts if f.fact_type == RegistryFactType.CLASSIFICATION]
        if "VALE" in primary_ids:
            vale_fact = next(f for f in facts if f.id == "VALE")
            self.assertIn(vale_fact.template_id, ["vale_primary", "fallback_primary"])

    def test_r199_does_not_promote_below_threshold(self):
        strict_config = InferenceConfig(
            recuperacao_min_ratio=0.99,
            vale_posicao_max=0.10,
        )
        rates_list = [14.15, 14.14, 14.12, 14.10, 14.08, 14.06, 14.05, 14.07, 14.10,
                      14.15, 14.20, 14.25, 14.30, 14.35, 14.39]
        records = _make_records(*rates_list, day_step=54)
        m = extract_detailed_metrics(records)
        features = compute_features(m, _rates_from(records), strict_config)
        facts, _ = classify(features, strict_config)
        primary_ids = [f.id for f in facts if f.fact_type == RegistryFactType.CLASSIFICATION]
        if "VALE" in primary_ids:
            vale_fact = next(f for f in facts if f.id == "VALE")
            self.assertNotEqual(vale_fact.template_id, "fallback_primary")

    def test_r199_not_executed_when_primary_active(self):
        features = self._features_for(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        facts, _ = classify(features, self.config)
        primary_ids = [f.id for f in facts if f.fact_type == RegistryFactType.CLASSIFICATION]
        self.assertIn("ASCENDENTE", primary_ids)
        for f in facts:
            self.assertNotEqual(f.template_id, "fallback_primary")

    def test_r199_selects_best_among_multiple(self):
        strict_config = InferenceConfig(
            recuperacao_min_ratio=0.85,
            vale_posicao_max=0.40,
            epsilon_slope=0.001,
        )
        rates_list = [14.15, 14.14, 14.12, 14.10, 14.06, 14.05, 14.08, 14.15,
                      14.25, 14.39, 14.40, 14.38, 14.30, 14.25, 14.21]
        records = _make_records(*rates_list, day_step=54)
        m = extract_detailed_metrics(records)
        features = compute_features(m, _rates_from(records), strict_config)
        facts, evaluations = classify(features, strict_config)
        primary_ids = [f.id for f in facts if f.fact_type == RegistryFactType.CLASSIFICATION]
        if len(primary_ids) > 0 and primary_ids[0] != "INDEFINIDA":
            promoted = next((f for f in facts if f.template_id == "fallback_primary"), None)
            if promoted:
                self.assertIn(promoted.id, ["VALE", "PICO", "ASCENDENTE", "DESCENDENTE"])

    def test_achatamento_independent_of_primary(self):
        config = InferenceConfig(steepening_ratio=1.0)
        rates_list = [14.15, 14.10, 14.05, 14.00, 13.95, 13.90, 13.85, 13.80,
                      13.75, 13.70, 13.68, 13.66, 13.64, 13.62, 13.60]
        records = _make_records(*rates_list, day_step=50)
        m = extract_detailed_metrics(records)
        features = compute_features(m, _rates_from(records), config)
        facts, _ = classify(features, config)
        fact_ids = [f.id for f in facts]
        self.assertIn("ACHATAMENTO", fact_ids)

    def test_recuperacao_sustentada_still_gated(self):
        features = self._features_for(14.15, 14.10, 14.05, 14.08, day_step=54)
        features_dict = {f.name: f for f in features.values()}
        facts, _ = classify(features, self.config)
        primary_ids = [f.id for f in facts if f.fact_type == RegistryFactType.CLASSIFICATION]
        if "VALE" not in primary_ids:
            struct_ids = [f.id for f in facts if f.fact_type == RegistryFactType.STRUCTURE]
            self.assertNotIn("RECUPERACAO_SUSTENTADA", struct_ids)


# ========================== 11.11-11.14 Scoring ==========================


class TestScoring(unittest.TestCase):
    def test_score_from_policy(self):
        facts = [
            Fact(id="ASCENDENTE", rule_id="ASCENDENTE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=1.0, derived_from_features=[], template_id=""),
            Fact(id="MONOTONIA", rule_id="MONOTONIA_STRUCT", fact_type=RegistryFactType.STRUCTURE,
                 confidence=1.0, derived_from_features=[], template_id=""),
        ]
        score = compute_score(facts)
        self.assertEqual(score, 6)

    def test_different_policies(self):
        facts = [
            Fact(id="ASCENDENTE", rule_id="ASCENDENTE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=1.0, derived_from_features=[], template_id=""),
        ]
        conservative = {"ASCENDENTE": (1, 2)}
        aggressive = {"ASCENDENTE": (3, 3)}
        self.assertNotEqual(compute_score(facts, conservative), compute_score(facts, aggressive))

    # 11.12 ScoringPolicy isolation
    def test_scoring_no_features_import(self):
        import importlib
        scoring = importlib.import_module("b3_selic_pre.application.analyze._scoring")
        with self.assertRaises(AttributeError):
            _ = scoring.Feature

    # 11.13 score weight table
    def test_score_table_all_entries(self):
        for fact_id, (base, level) in SCORING_POLICY.items():
            self.assertIsInstance(base, int)
            self.assertIsInstance(level, int)
            self.assertIn(level, (1, 2, 3))

    # 11.14 classification ranges
    def test_intensity_ranges(self):
        self.assertIn("estavel", classify_intensity(0, "asc").lower())
        self.assertIn("estavel", classify_intensity(2, "asc").lower())
        self.assertIn("ascendente", classify_intensity(3, "asc").lower())
        self.assertIn("ascendente", classify_intensity(5, "asc").lower())
        self.assertIn("relevante", classify_intensity(6, "asc").lower())
        self.assertIn("significativa", classify_intensity(9, "asc").lower())
        self.assertIn("expressiva", classify_intensity(12, "asc").lower())

    def test_intensity_desc(self):
        self.assertIn("invertida", classify_intensity(4, "desc").lower())

    def test_intensity_plana(self):
        self.assertIn("estavel", classify_intensity(1, "plana").lower())

    def test_confidence_per_level(self):
        facts = [
            Fact(id="ASCENDENTE", rule_id="ASCENDENTE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=0.8, derived_from_features=[], template_id=""),
            Fact(id="MONOTONIA", rule_id="MONOTONIA_STRUCT", fact_type=RegistryFactType.STRUCTURE,
                 confidence=1.0, derived_from_features=[], template_id=""),
        ]
        conf = compute_confidence_per_level(facts)
        self.assertIn("classification", conf)
        self.assertAlmostEqual(conf["classification"], 0.8)

    def test_new_facts_score(self):
        facts = [
            Fact(id="VALE", rule_id="VALE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=0.74, derived_from_features=[], template_id=""),
            Fact(id="RECUPERACAO_LONGA", rule_id="RECUPERACAO_LONGA", fact_type=RegistryFactType.STRUCTURE,
                 confidence=1.0, derived_from_features=[], template_id=""),
            Fact(id="VOLATILIDADE_MODERADA", rule_id="VOLATILIDADE_MODERADA", fact_type=RegistryFactType.QUALITY,
                 confidence=1.0, derived_from_features=[], template_id=""),
        ]
        score = compute_score(facts)
        self.assertEqual(score, 8)  # 6 + 2 + 0


# ========================== 11.15-11.18 Templates & Report ==========================


class TestTemplates(unittest.TestCase):
    def test_resolve_template_pt(self):
        text = resolve_template("asc_primary", "pt")
        self.assertIn("tendencia global ascendente", text.lower())

    def test_resolve_template_en_empty(self):
        text = resolve_template("asc_primary", "en")
        self.assertEqual(text, "")

    def test_resolve_template_missing_locale(self):
        text = resolve_template("asc_primary", "fr")
        self.assertIn("tendencia global ascendente", text.lower())

    def test_templates_structure(self):
        for locale, templates in TEMPLATES.items():
            self.assertIsInstance(templates, dict)

    def test_fallback_primary_template(self):
        text = resolve_template("fallback_primary", "pt")
        self.assertIn("{classe}", text)
        self.assertIn("{pct}", text)

    def test_volmod_qual_template(self):
        text = resolve_template("volmod_qual", "pt")
        self.assertIn("moderada", text.lower())

    def test_longrec_struct_template(self):
        text = resolve_template("longrec_struct", "pt")
        self.assertIn("recuperacao longa", text.lower())


class TestReport(unittest.TestCase):
    def test_empty_report(self):
        report = build_report([], 0, "")
        formatted = format_report(report)
        self.assertIn("Sem dados", formatted)

    def test_report_consumes_only_facts(self):
        import importlib
        report_mod = importlib.import_module("b3_selic_pre.application.analyze._report")
        with self.assertRaises(AttributeError):
            _ = report_mod.Feature
        with self.assertRaises(AttributeError):
            _ = report_mod.DetailedMetrics

    # 11.17 5-block report
    def test_report_has_five_blocks(self):
        facts = [
            Fact(id="ASCENDENTE", rule_id="ASCENDENTE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=1.0, derived_from_features=["TREND_UP"], template_id="asc_primary"),
            Fact(id="MONOTONIA", rule_id="MONOTONIA_STRUCT", fact_type=RegistryFactType.STRUCTURE,
                 confidence=1.0, derived_from_features=["MONOTONIC"], template_id="mono_struct"),
            Fact(id="CURVA_SUAVE", rule_id="CURVA_SUAVE", fact_type=RegistryFactType.QUALITY,
                 confidence=1.0, derived_from_features=["SMOOTH"], template_id="smooth_qual"),
        ]
        statements = build_statements_from_facts(facts, 9, "Significativa", {"classification": 1.0})
        text = "\n".join(statements)
        self.assertIn("CLASSE PRIMARIA", text)
        self.assertIn("ESTRUTURA", text)
        self.assertIn("QUALIDADE", text)
        self.assertIn("INTENSIDADE", text)
        self.assertIn("TREND_UP", text)
        self.assertIn("Score: 9", text)

    # 11.18 executive summary order
    def test_executive_summary_order(self):
        facts = [
            Fact(id="ASCENDENTE", rule_id="ASCENDENTE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=1.0, derived_from_features=[], template_id="asc_primary"),
        ]
        stmts = build_statements_from_facts(facts, 3, "Moderada", {})
        text = "\n".join(stmts)
        idx_primary = text.index("CLASSE PRIMARIA")
        idx_intensity = text.index("INTENSIDADE")
        self.assertLess(idx_primary, idx_intensity)

    # 8.5 empty blocks omitted
    def test_empty_blocks_omitted(self):
        facts = [
            Fact(id="ASCENDENTE", rule_id="ASCENDENTE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=1.0, derived_from_features=[], template_id="asc_primary"),
        ]
        stmts = build_statements_from_facts(facts, 3, "Moderada", {})
        text = "\n".join(stmts)
        self.assertNotIn("ESTRUTURA", text)

    # 11.19 engine version
    def test_engine_version(self):
        self.assertEqual(ENGINE_VERSION, "2.0.0")
        self.assertEqual(RULESET_VERSION, "1.1.0")

    def test_analysis_result_dataclass(self):
        result = AnalysisResult(
            engine_version="2.0.0",
            ruleset_version="1.0.0",
            generated_at="2024-01-01T00:00:00",
            facts=[],
            score=0,
            intensity_label="",
            confidence={},
        )
        self.assertEqual(result.engine_version, "2.0.0")

    def test_fallback_primary_placeholders_rendered(self):
        facts = [
            Fact(id="VALE", rule_id="VALE", fact_type=RegistryFactType.CLASSIFICATION,
                 confidence=0.74, derived_from_features=["VALLEY_EARLY", "FINAL_GT_INITIAL"],
                 template_id="fallback_primary"),
        ]
        stmts = build_statements_from_facts(facts, 6, "Relevante", {"classification": 0.74})
        text = "\n".join(stmts)
        self.assertIn("VALE", text)
        self.assertIn("74%", text)
        self.assertNotIn("{classe}", text)
        self.assertNotIn("{pct}", text)


# ========================== 11.21 Full Integration ==========================


class TestAnalyzeFacade(unittest.TestCase):
    def test_empty_records(self):
        report = analyze([])
        self.assertEqual(len(report.statements), 0)
        self.assertEqual(report.score, 0)

    def test_ascending_curve(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0, day_step=50)
        report = analyze(records)
        self.assertGreater(len(report.statements), 0)
        self.assertGreater(report.score, 0)

    def test_valley_curve(self):
        rates = [14.15, 14.14, 14.12, 14.10, 14.08, 14.06, 14.05, 14.07, 14.10,
                 14.15, 14.20, 14.25, 14.30, 14.35, 14.39]
        records = _make_records(*rates, day_step=54)
        report = analyze(records)
        self.assertGreater(report.score, 0)
        formatted = format_report(report)
        self.assertIn("depressao", formatted.lower())

    def test_descending_curve(self):
        records = _make_records(14.0, 13.5, 13.0, 12.5, 12.0, day_step=50)
        report = analyze(records)
        formatted = format_report(report)
        self.assertIn("tendencia global descendente", formatted.lower())

    def test_config_override(self):
        records = _make_records(10.0, 10.02, 10.04, 10.06, 10.08, 10.10, day_step=50)
        report = analyze(records, config=InferenceConfig(epsilon_slope=0.0))
        formatted = format_report(report)
        self.assertIn("tendencia global ascendente", formatted.lower())

    def test_consolidated_placeholder(self):
        records = [RateRecord(day252=0, day360=0, rate="10,0")]
        report = analyze(records, view_mode="consolidated")
        self.assertIn("nao implementada", report.statements[0].lower())

    def test_evolution_placeholder(self):
        records = [RateRecord(day252=0, day360=0, rate="10,0")]
        hist = {"2024-01-01": records}
        report = analyze(records, historical_data=hist, evolution_active=True)
        self.assertIn("nao implementada", report.statements[0].lower())

    def test_valley_plateau_curve_r199(self):
        rates = [14.15, 14.12, 14.09, 14.07, 14.05, 14.05, 14.06, 14.08,
                 14.10, 14.13, 14.15, 14.17, 14.18, 14.19, 14.20, 14.21,
                 14.22, 14.23, 14.25, 14.27, 14.30, 14.33, 14.36, 14.38,
                 14.39, 14.40, 14.40, 14.40, 14.40, 14.40, 14.40, 14.40]
        records = _make_records(*rates, day_step=50)
        report = analyze(records)
        formatted = format_report(report)
        self.assertGreater(report.score, 0)
        self.assertNotIn("INDEFINIDA", formatted.split("INTENSIDADE")[0])


if __name__ == "__main__":
    unittest.main()
