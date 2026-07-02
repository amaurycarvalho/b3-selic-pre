import unittest

from b3_selic_pre.application.analyze import (
    AnalysisReport,
    CurvaJurosConfig,
    analyze,
    calcular_estabilidade,
    calcular_steepening,
    classificar_inclinacao,
    classificar_nominal,
    classificar_premio,
    classificar_restricao,
    extrair_indicadores,
    montar_resumo_executivo,
)
from b3_selic_pre.application.analyze._texto import (
    gerar_texto_inclinacao,
    gerar_texto_nominal,
    gerar_texto_restricao,
    gerar_texto_steepening,
)
from b3_selic_pre.domain.models import RateRecord


def _make_records(*rates):
    return [
        RateRecord(day252=i * 21, day360=i * 30, rate=str(r).replace(".", ","))
        for i, r in enumerate(rates)
    ]


class TestExtrairIndicadores(unittest.TestCase):
    def test_basic_calculation(self):
        records = _make_records(14.25, 14.50, 14.75, 15.00)
        config = CurvaJurosConfig(expected_inflation=3.0)
        ind = extrair_indicadores(records, config)
        self.assertAlmostEqual(ind.taxa_curta, 14.25)
        self.assertAlmostEqual(ind.taxa_longa, 15.00)
        self.assertAlmostEqual(ind.inclinacao_bps, 75.0)
        self.assertAlmostEqual(ind.juro_real, 11.25)

    def test_negative_slope(self):
        records = _make_records(15.00, 14.50, 14.00, 13.50)
        config = CurvaJurosConfig(expected_inflation=4.0)
        ind = extrair_indicadores(records, config)
        self.assertAlmostEqual(ind.taxa_curta, 15.00)
        self.assertAlmostEqual(ind.taxa_longa, 13.50)
        self.assertAlmostEqual(ind.inclinacao_bps, -150.0)
        self.assertAlmostEqual(ind.juro_real, 11.0)

    def test_flat_curve(self):
        records = _make_records(10.0, 10.0, 10.0)
        config = CurvaJurosConfig(expected_inflation=5.0)
        ind = extrair_indicadores(records, config)
        self.assertAlmostEqual(ind.inclinacao_bps, 0.0)
        self.assertAlmostEqual(ind.juro_real, 5.0)


class TestClassificarNominal(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig()

    def test_muito_baixos(self):
        self.assertEqual(classificar_nominal(5.0, self.config), "Muito Baixos")

    def test_baixos(self):
        self.assertEqual(classificar_nominal(7.0, self.config), "Baixos")

    def test_moderados(self):
        self.assertEqual(classificar_nominal(10.0, self.config), "Moderados")

    def test_altos(self):
        self.assertEqual(classificar_nominal(12.0, self.config), "Altos")

    def test_muito_altos(self):
        self.assertEqual(classificar_nominal(14.0, self.config), "Muito Altos")

    def test_boundary_6(self):
        self.assertEqual(classificar_nominal(6.0, self.config), "Baixos")

    def test_boundary_9(self):
        self.assertEqual(classificar_nominal(9.0, self.config), "Moderados")

    def test_boundary_11(self):
        self.assertEqual(classificar_nominal(11.0, self.config), "Altos")

    def test_boundary_13(self):
        self.assertEqual(classificar_nominal(13.0, self.config), "Muito Altos")


class TestClassificarRestricao(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig()

    def test_expansionista(self):
        self.assertEqual(classificar_restricao(1.0, self.config), "Expansionista")

    def test_neutra(self):
        self.assertEqual(classificar_restricao(3.0, self.config), "Neutra")

    def test_restritiva(self):
        self.assertEqual(classificar_restricao(5.0, self.config), "Restritiva")

    def test_muito_restritiva(self):
        self.assertEqual(classificar_restricao(7.0, self.config), "Muito Restritiva")

    def test_boundary_2(self):
        self.assertEqual(classificar_restricao(2.0, self.config), "Neutra")

    def test_boundary_4(self):
        self.assertEqual(classificar_restricao(4.0, self.config), "Restritiva")

    def test_boundary_6(self):
        self.assertEqual(classificar_restricao(6.0, self.config), "Muito Restritiva")


class TestClassificarPremio(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig()

    def test_muito_baixo(self):
        self.assertEqual(classificar_premio(10, self.config), "Muito Baixo")

    def test_baixo(self):
        self.assertEqual(classificar_premio(30, self.config), "Baixo")

    def test_normal(self):
        self.assertEqual(classificar_premio(60, self.config), "Normal")

    def test_elevado(self):
        self.assertEqual(classificar_premio(100, self.config), "Elevado")

    def test_muito_elevado(self):
        self.assertEqual(classificar_premio(200, self.config), "Muito Elevado")


class TestClassificarInclinacao(unittest.TestCase):
    def test_quase_plana(self):
        self.assertEqual(classificar_inclinacao(5), "Quase Plana")

    def test_muito_plana(self):
        self.assertEqual(classificar_inclinacao(20), "Muito Plana")

    def test_plana(self):
        self.assertEqual(classificar_inclinacao(50), "Plana")

    def test_moderadamente_inclinada(self):
        self.assertEqual(classificar_inclinacao(80), "Moderadamente Inclinada")

    def test_muito_inclinada(self):
        self.assertEqual(classificar_inclinacao(150), "Muito Inclinada")

    def test_boundary_10(self):
        self.assertEqual(classificar_inclinacao(10), "Muito Plana")

    def test_boundary_30(self):
        self.assertEqual(classificar_inclinacao(30), "Plana")

    def test_boundary_60(self):
        self.assertEqual(classificar_inclinacao(60), "Moderadamente Inclinada")

    def test_boundary_100(self):
        self.assertEqual(classificar_inclinacao(100), "Muito Inclinada")


class TestCalcularEstabilidade(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig(stability_fallback="default")
        self.records = _make_records(14.0, 14.5, 15.0, 15.5)

    def test_default_fallback(self):
        result = calcular_estabilidade(None, self.records, self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["nivel"], "Média")
        self.assertAlmostEqual(result["deviation_bps"], 15.0)
        self.assertTrue(result["estimado"])

    def test_auto_fallback(self):
        config = CurvaJurosConfig(stability_fallback="auto")
        result = calcular_estabilidade(None, self.records, config)
        self.assertIsNotNone(result)
        self.assertTrue(result["estimado"])

    def test_unavailable_fallback(self):
        config = CurvaJurosConfig(stability_fallback="unavailable")
        result = calcular_estabilidade(None, self.records, config)
        self.assertIsNone(result)

    def test_with_historical_data(self):
        historical = {
            "2024-01-01": _make_records(14.0, 14.5, 15.0, 15.5),
            "2024-01-02": _make_records(14.1, 14.6, 15.1, 15.6),
            "2024-01-03": _make_records(14.2, 14.7, 15.2, 15.7),
            "2024-01-04": _make_records(14.3, 14.8, 15.3, 15.8),
        }
        result = calcular_estabilidade(historical, self.records, self.config)
        self.assertIsNotNone(result)
        self.assertIn("nivel", result)
        self.assertIn("deviation_bps", result)
        self.assertFalse(result["estimado"])

    def test_insufficient_history(self):
        historical = {"2024-01-01": _make_records(14.0, 14.5, 15.0)}
        config = CurvaJurosConfig(stability_window=4, stability_fallback="default")
        result = calcular_estabilidade(historical, self.records, config)
        self.assertIsNotNone(result)
        self.assertEqual(result["nivel"], "Média")
        self.assertTrue(result["estimado"])


class TestCalcularSteepening(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig(steepening_fallback="default")
        self.records = _make_records(14.0, 14.5, 15.0, 15.5)

    def test_default_fallback(self):
        result = calcular_steepening(self.records, None, self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["direcao"], "Steepening")
        self.assertAlmostEqual(result["delta_bps"], 15.0)

    def test_unavailable_fallback(self):
        config = CurvaJurosConfig(steepening_fallback="unavailable")
        result = calcular_steepening(self.records, None, config)
        self.assertIsNone(result)

    def test_auto_fallback(self):
        config = CurvaJurosConfig(steepening_fallback="auto")
        result = calcular_steepening(self.records, None, config)
        self.assertIsNotNone(result)
        self.assertIn("direcao", result)
        self.assertIn("delta_bps", result)
        self.assertIn("magnitude", result)

    def test_with_historical_data_steepening(self):
        historical = {
            "2024-01-01": _make_records(14.0, 14.2, 14.4, 14.6),
            "2024-01-02": _make_records(14.0, 14.5, 15.0, 15.5),
        }
        result = calcular_steepening(self.records, historical, self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["direcao"], "Steepening")

    def test_with_historical_data_flattening(self):
        records = _make_records(14.0, 14.2, 14.4, 14.6)
        historical = {
            "2024-01-01": _make_records(14.0, 14.5, 15.0, 15.5),
            "2024-01-02": _make_records(14.0, 14.5, 15.0, 15.5),
        }
        result = calcular_steepening(records, historical, self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["direcao"], "Flattening")

    def test_stable(self):
        records = _make_records(14.0, 14.0, 14.0, 14.0)
        historical = {
            "2024-01-01": _make_records(14.0, 14.0, 14.0, 14.0),
            "2024-01-02": _make_records(14.0, 14.0, 14.0, 14.0),
        }
        result = calcular_steepening(records, historical, self.config)
        self.assertIsNotNone(result)
        self.assertEqual(result["direcao"], "Estavel")


class TestGerarTextoNominal(unittest.TestCase):
    def test_muito_baixos(self):
        self.assertIn("historicamente baixos", gerar_texto_nominal("Muito Baixos"))

    def test_baixos(self):
        self.assertIn("relativamente baixos", gerar_texto_nominal("Baixos"))

    def test_moderados(self):
        self.assertIn("média histórica", gerar_texto_nominal("Moderados"))

    def test_altos(self):
        self.assertIn("juros elevados", gerar_texto_nominal("Altos"))

    def test_muito_altos(self):
        self.assertIn("maiores níveis", gerar_texto_nominal("Muito Altos"))

    def test_unknown_returns_empty(self):
        self.assertEqual(gerar_texto_nominal("Desconhecido"), "")


class TestGerarTextoRestricao(unittest.TestCase):
    def test_expansionista(self):
        self.assertIn("estimula crédito", gerar_texto_restricao("Expansionista"))

    def test_neutra(self):
        self.assertIn("aproximadamente neutra", gerar_texto_restricao("Neutra"))

    def test_restritiva(self):
        self.assertIn("conter pressões", gerar_texto_restricao("Restritiva"))

    def test_muito_restritiva(self):
        self.assertIn("controle da inflação", gerar_texto_restricao("Muito Restritiva"))


class TestGerarTextoInclinacao(unittest.TestCase):
    def test_quase_plana(self):
        self.assertIn("praticamente iguais", gerar_texto_inclinacao("Quase Plana"))

    def test_muito_plana(self):
        self.assertIn("pequena diferença", gerar_texto_inclinacao("Muito Plana"))

    def test_plana(self):
        self.assertIn("ligeiramente acima", gerar_texto_inclinacao("Plana"))

    def test_moderadamente_inclinada(self):
        self.assertIn("prêmio moderado", gerar_texto_inclinacao("Moderadamente Inclinada"))

    def test_muito_inclinada(self):
        self.assertIn("prêmio elevado", gerar_texto_inclinacao("Muito Inclinada"))


class TestGerarTextoSteepening(unittest.TestCase):
    def test_steepening_format(self):
        text = gerar_texto_steepening("Steepening", "Moderado", 18.0)
        self.assertIn("▲", text)
        self.assertIn("Steepening", text)
        self.assertIn("Moderado", text)
        self.assertIn("18 bps", text)

    def test_flattening_format(self):
        text = gerar_texto_steepening("Flattening", "Forte", -30.0)
        self.assertIn("▼", text)
        self.assertIn("Flattening", text)
        self.assertIn("Forte", text)
        self.assertIn("30 bps", text)

    def test_estavel(self):
        text = gerar_texto_steepening("Estavel", "Nenhuma", 0.0)
        self.assertIn("Sem alteração relevante", text)


class TestMontarResumoExecutivo(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig(expected_inflation=3.0)
        self.records = _make_records(14.25, 14.50, 14.75, 15.00)
        self.indicadores = extrair_indicadores(self.records, self.config)

    def test_all_blocks_present(self):
        estabilidade = {"deviation_bps": 8.0, "nivel": "Alta"}
        steepening = {"direcao": "Steepening", "delta_bps": 12.0, "magnitude": "Moderado"}
        blocos = montar_resumo_executivo(
            self.indicadores, self.config, estabilidade, steepening
        )
        self.assertIn("Nível Nominal", blocos)
        self.assertIn("Política Monetária", blocos)
        self.assertIn("Inclinação", blocos)
        self.assertIn("Prêmio de Prazo", blocos)
        self.assertIn("Estabilidade das Expectativas", blocos)
        self.assertIn("Última Mudança", blocos)
        self.assertIn("Mensagem do Mercado", blocos)

    def test_stability_omitted_when_none(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertNotIn("Estabilidade das Expectativas", blocos)

    def test_steepening_omitted_when_none(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertNotIn("Última Mudança", blocos)

    def test_nominal_content(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertIn("Muito Altos", blocos["Nível Nominal"])

    def test_mensagem_content(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertIn("mercado", blocos["Mensagem do Mercado"].lower())


class TestAnalyzeIntegration(unittest.TestCase):
    def test_empty_records(self):
        report = analyze([])
        self.assertEqual(len(report.statements), 0)
        self.assertEqual(report.score, 0)
        self.assertEqual(report.score_label, "")

    def test_valid_records(self):
        records = _make_records(14.25, 14.50, 14.75, 15.00)
        report = analyze(records)
        self.assertGreater(len(report.statements), 0)
        self.assertIsInstance(report, AnalysisReport)

    def test_custom_config(self):
        records = _make_records(5.0, 5.5, 6.0, 6.5)
        config = CurvaJurosConfig(expected_inflation=2.0)
        report = analyze(records, config=config)
        self.assertGreater(len(report.statements), 0)

    def test_report_structure(self):
        records = _make_records(14.25, 14.50, 14.75, 15.00)
        report = analyze(records)
        self.assertIsInstance(report.statements, list)
        self.assertEqual(report.score, 0)
        self.assertEqual(report.score_label, "")

    def test_with_historical_data(self):
        records = _make_records(14.0, 14.5, 15.0, 15.5)
        historical = {
            "2024-01-01": _make_records(13.0, 13.5, 14.0, 14.5),
            "2024-01-02": _make_records(13.5, 14.0, 14.5, 15.0),
            "2024-01-03": _make_records(13.6, 14.1, 14.6, 15.1),
            "2024-01-04": _make_records(13.8, 14.3, 14.8, 15.3),
        }
        report = analyze(records, historical_data=historical)
        self.assertGreater(len(report.statements), 0)


if __name__ == "__main__":
    unittest.main()
