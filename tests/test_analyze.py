import unittest

from b3_selic_pre.domain.models import RateRecord
from b3_selic_pre.application.analyze import analyze, AnalysisThresholds
from b3_selic_pre.application.analyze._metrics import extract_detailed_metrics
from b3_selic_pre.application.analyze._metrics_evolution import (
    extract_envelope_metrics,
    extract_evolution_metrics,
)
from b3_selic_pre.application.analyze._rules import (
    regra_forma_curva,
    regra_inclinacao,
    regra_convexidade,
    regra_volatilidade,
    regra_oscilacoes,
    regra_spread_envelope,
    regra_tendencia_envelope,
    regra_tendencia_evolucao,
    regra_difusao,
    regra_rotacao,
    regra_intensidade,
    regra_score_agregado,
)
from b3_selic_pre.application.analyze._report import build_report, format_report


def _make_records(*rates):
    return [
        RateRecord(day252=i * 21, day360=i * 30, rate=str(r).replace(".", ","))
        for i, r in enumerate(rates)
    ]


class TestDetailedMetrics(unittest.TestCase):
    def test_empty_records_returns_defaults(self):
        m = extract_detailed_metrics([], AnalysisThresholds())
        self.assertEqual(m.taxa_inicial, 0.0)
        self.assertEqual(m.taxa_final, 0.0)
        self.assertEqual(m.taxa_maxima, 0.0)
        self.assertEqual(m.taxa_minima, 0.0)
        self.assertIsNone(m.slope)
        self.assertIsNone(m.convexidade)
        self.assertIsNone(m.volatilidade)
        self.assertEqual(m.oscilacoes, 0)

    def test_basic_metrics_computed(self):
        records = _make_records(10.0, 10.5, 11.0, 10.8, 10.3)
        m = extract_detailed_metrics(records, AnalysisThresholds())
        self.assertEqual(m.taxa_inicial, 10.0)
        self.assertEqual(m.taxa_final, 10.3)
        self.assertEqual(m.taxa_maxima, 11.0)
        self.assertEqual(m.taxa_minima, 10.0)
        self.assertIsNotNone(m.slope)
        self.assertIsNotNone(m.convexidade)
        self.assertIsNotNone(m.volatilidade)

    def test_ascending_rates_slope_positive(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0)
        m = extract_detailed_metrics(records, AnalysisThresholds())
        self.assertGreater(m.slope, 0)

    def test_descending_rates_slope_negative(self):
        records = _make_records(12.0, 11.5, 11.0, 10.5, 10.0)
        m = extract_detailed_metrics(records, AnalysisThresholds())
        self.assertLess(m.slope, 0)

    def test_volatility_computed(self):
        records = _make_records(10.0, 10.0, 10.0, 10.0, 10.0)
        m = extract_detailed_metrics(records, AnalysisThresholds())
        self.assertAlmostEqual(m.volatilidade, 0.0, places=6)

    def test_oscillation_count(self):
        records = _make_records(10.0, 11.0, 10.0, 11.0, 10.0)
        m = extract_detailed_metrics(records, AnalysisThresholds())
        self.assertEqual(m.oscilacoes, 3)


class TestEnvelopeMetrics(unittest.TestCase):
    def test_empty_returns_zero(self):
        e = extract_envelope_metrics([], AnalysisThresholds())
        self.assertEqual(e.spread_medio, 0.0)

    def test_spread_computed(self):
        records = []
        for year in range(3):
            records.append(RateRecord(day252=year * 252, day360=year * 365, rate="10,0"))
            records.append(RateRecord(day252=year * 252 + 1, day360=year * 365, rate="12,0"))
        e = extract_envelope_metrics(records, AnalysisThresholds())
        self.assertGreater(e.spread_medio, 0)

    def test_increasing_spread_trend(self):
        records = []
        for year in range(5):
            base = 10.0 + year * 0.5
            records.append(RateRecord(day252=year, day360=year * 365, rate=f"{base:.1f}".replace(".", ",")))
            records.append(RateRecord(day252=year + 1000, day360=year * 365, rate=f"{base + year * 0.2:.1f}".replace(".", ",")))
        e = extract_envelope_metrics(records, AnalysisThresholds())
        self.assertIn(e.spread_tendencia, ("crescente", "estável"))


class TestEvolutionMetrics(unittest.TestCase):
    def test_empty_historical_data(self):
        ev = extract_evolution_metrics({})
        self.assertEqual(ev.deltas, [])
        self.assertEqual(ev.tendencia, "instabilidade")

    def test_continuous_upward_trend(self):
        historical = {
            "2026-01-01": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
            "2026-01-28": _make_records(11.0, 11.0, 11.0, 11.0, 11.0),
        }
        ev = extract_evolution_metrics(historical)
        self.assertEqual(ev.tendencia, "alta_continua")

    def test_continuous_downward_trend(self):
        historical = {
            "2026-01-01": _make_records(12.0, 12.0, 12.0, 12.0, 12.0),
            "2026-01-28": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
        }
        ev = extract_evolution_metrics(historical)
        self.assertEqual(ev.tendencia, "queda_continua")


class TestRules(unittest.TestCase):
    def setUp(self):
        self.t = AnalysisThresholds()

    def test_regra_forma_curva_ascendente(self):
        records = _make_records(10.0, 10.5, 11.0, 11.5, 12.0)
        m = extract_detailed_metrics(records, self.t)
        r = regra_forma_curva(m, self.t)
        self.assertIn("inclinação positiva", r.text)

    def test_regra_forma_curva_descendente(self):
        records = _make_records(12.0, 11.5, 11.0, 10.5, 10.0)
        m = extract_detailed_metrics(records, self.t)
        r = regra_forma_curva(m, self.t)
        self.assertIn("curva encontra-se invertida", r.text)

    def test_regra_forma_curva_plana(self):
        records = _make_records(10.0, 10.05, 9.98, 10.02, 10.0)
        m = extract_detailed_metrics(records, self.t)
        r = regra_forma_curva(m, self.t)
        self.assertIn("praticamente plana", r.text)

    def test_regra_inclinacao_muito_forte(self):
        steep_records = _make_records(10.0, 15.0, 20.0, 25.0, 30.0)
        m = extract_detailed_metrics(steep_records, self.t)
        r = regra_inclinacao(m, self.t)
        self.assertTrue(len(r.text) > 0)

    def test_regra_convexidade(self):
        records = _make_records(10.0, 10.0, 11.0, 12.0, 14.0)
        m = extract_detailed_metrics(records, self.t)
        r = regra_convexidade(m, self.t)
        self.assertIn("acelera", r.text)

    def test_regra_volatilidade_baixa(self):
        records = _make_records(10.0, 10.0, 10.0, 10.0, 10.0)
        m = extract_detailed_metrics(records, self.t)
        r = regra_volatilidade(m, self.t)
        self.assertIn("homogêneo", r.text)

    def test_regra_volatilidade_alta(self):
        records = _make_records(10.0, 15.0, 9.0, 16.0, 8.0)
        m = extract_detailed_metrics(records, self.t)
        r = regra_volatilidade(m, self.t)
        self.assertIn("irregularidade", r.text)

    def test_regra_oscilacoes_alto(self):
        records = _make_records(10, 11, 10, 11, 10, 11, 10, 11, 10, 11,
                                10, 11, 10, 11, 10, 11, 10, 11, 10, 11,
                                10, 11, 10, 11, 10, 11, 10, 11, 10, 11)
        m = extract_detailed_metrics(records, self.t)
        r = regra_oscilacoes(m, self.t)
        self.assertIn("oscilações", r.text)

    def test_regra_spread_envelope_estreito(self):
        records = [RateRecord(day252=0, day360=0, rate="10,0"),
                   RateRecord(day252=1, day360=365, rate="10,01")]
        e = extract_envelope_metrics(records, self.t)
        r = regra_spread_envelope(e, self.t)
        self.assertIn("consenso", r.text)

    def test_regra_spread_envelope_alto(self):
        records = [RateRecord(day252=0, day360=0, rate="10,0"),
                   RateRecord(day252=1, day360=0, rate="15,0"),
                   RateRecord(day252=2, day360=365, rate="10,0"),
                   RateRecord(day252=3, day360=365, rate="16,0")]
        e = extract_envelope_metrics(records, self.t)
        r = regra_spread_envelope(e, self.t)
        self.assertIn("elevada dispersão", r.text)

    def test_regra_tendencia_evolucao_alta(self):
        historical = {
            "2026-01-01": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
            "2026-01-28": _make_records(11.0, 11.0, 11.0, 11.0, 11.0),
        }
        ev = extract_evolution_metrics(historical)
        r = regra_tendencia_evolucao(ev, self.t)
        self.assertIn("reprecificada", r.text)

    def test_regra_difusao_disseminado(self):
        historical = {
            "2026-01-01": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
            "2026-01-28": _make_records(11.0, 11.0, 11.0, 11.0, 11.0),
        }
        ev = extract_evolution_metrics(historical)
        r = regra_difusao(ev, self.t)
        self.assertIn("disseminado", r.text)

    def test_regra_rotacao_bear_steepening(self):
        historical = {
            "2026-01-01": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
            "2026-01-28": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
        }
        ev = extract_evolution_metrics(historical)
        r = regra_rotacao(ev, self.t)
        self.assertIsNotNone(r)

    def test_regra_intensidade_pequena(self):
        historical = {
            "2026-01-01": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
            "2026-01-28": _make_records(10.05, 10.05, 10.05, 10.05, 10.05),
        }
        ev = extract_evolution_metrics(historical)
        r = regra_intensidade(ev, self.t)
        self.assertIn("discreto", r.text)

    def test_regra_score_agregado_estavel(self):
        r = regra_score_agregado(0, self.t)
        self.assertIn("estável", r.text)

    def test_regra_score_agregado_expressivo(self):
        r = regra_score_agregado(15, self.t)
        self.assertIn("expressiva", r.text)


class TestReport(unittest.TestCase):
    def test_build_report_empty(self):
        report = build_report([], 0, "")
        self.assertEqual(report.score, 0)

    def test_format_report_empty(self):
        result = format_report(build_report([], 0, ""))
        self.assertEqual(result, "Sem dados para análise.")

    def test_format_report_with_statements(self):
        report = build_report(
            ["Formato da Curva", "A curva está ascendente.", "Conclusão", "Mercado estável."],
            score=2,
            score_label="Mercado estável",
        )
        result = format_report(report)
        self.assertIn("Formato da Curva", result)
        self.assertIn("ascendente", result)
        self.assertIn("Conclusão", result)
        self.assertIn("Score: 2", result)


class TestAnalyzeFacade(unittest.TestCase):
    def test_empty_records(self):
        report = analyze([])
        self.assertEqual(len(report.statements), 0)
        self.assertEqual(report.score, 0)

    def test_detailed_mode_returns_analysis(self):
        records = _make_records(10.0, 10.5, 11.0, 10.8, 10.3)
        report = analyze(records, view_mode="raw")
        self.assertGreater(len(report.statements), 0)

    def test_consolidated_mode_returns_analysis(self):
        records = [RateRecord(day252=0, day360=0, rate="10,0"),
                   RateRecord(day252=1, day360=365, rate="12,0")]
        report = analyze(records, view_mode="consolidated")
        self.assertGreater(len(report.statements), 0)

    def test_evolution_mode_returns_analysis(self):
        records = _make_records(10.0, 10.0, 10.0, 10.0, 10.0)
        historical = {
            "2026-01-01": _make_records(10.0, 10.0, 10.0, 10.0, 10.0),
            "2026-01-28": _make_records(11.0, 11.0, 11.0, 11.0, 11.0),
        }
        report = analyze(records, historical_data=historical, evolution_active=True)
        self.assertGreater(len(report.statements), 0)

    def test_custom_thresholds(self):
        custom = AnalysisThresholds(curva_ascendente_min=5.0)
        records = _make_records(10.0, 10.5, 11.0, 10.8, 10.3)
        report = analyze(records, thresholds=custom)
        with_defaults = analyze(records)
        self.assertNotEqual(
            len(report.statements),
            len(with_defaults.statements),
        )


if __name__ == "__main__":
    unittest.main()
