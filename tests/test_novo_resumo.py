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
from b3_selic_pre.application.analyze._resumo import (
    _calc_slope_from_records,
    _classificar_estabilidade,
    _classificar_steepening,
    _estabilidade_fallback,
    _steepening_fallback,
    calcular_estabilidade,
    calcular_steepening,
    classificar_premio,
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
        self.assertEqual(
            gerar_texto_nominal("Muito Baixos"),
            "O mercado precifica juros historicamente baixos.",
        )

    def test_baixos(self):
        self.assertEqual(
            gerar_texto_nominal("Baixos"),
            "O mercado precifica juros relativamente baixos.",
        )

    def test_moderados(self):
        self.assertEqual(
            gerar_texto_nominal("Moderados"),
            "O mercado precifica juros próximos da média histórica.",
        )

    def test_altos(self):
        self.assertEqual(
            gerar_texto_nominal("Altos"),
            "O mercado precifica juros elevados.",
        )

    def test_muito_altos(self):
        self.assertEqual(
            gerar_texto_nominal("Muito Altos"),
            "O mercado precifica juros entre os maiores níveis observados.",
        )

    def test_unknown_returns_empty(self):
        self.assertEqual(gerar_texto_nominal("Desconhecido"), "")


class TestGerarTextoRestricao(unittest.TestCase):
    def test_expansionista(self):
        self.assertEqual(
            gerar_texto_restricao("Expansionista"),
            "A política monetária estimula crédito e atividade.",
        )

    def test_neutra(self):
        self.assertEqual(
            gerar_texto_restricao("Neutra"),
            "A política monetária é aproximadamente neutra.",
        )

    def test_restritiva(self):
        self.assertEqual(
            gerar_texto_restricao("Restritiva"),
            "A política monetária busca conter pressões inflacionárias.",
        )

    def test_muito_restritiva(self):
        self.assertEqual(
            gerar_texto_restricao("Muito Restritiva"),
            "A política monetária permanece fortemente voltada ao controle da inflação.",
        )

    def test_unknown_returns_empty(self):
        self.assertEqual(gerar_texto_restricao("Desconhecida"), "")


class TestGerarTextoInclinacao(unittest.TestCase):
    def test_quase_plana(self):
        self.assertEqual(
            gerar_texto_inclinacao("Quase Plana"),
            "Os juros são praticamente iguais em todos os prazos, indicando forte consenso de que o nível atual deverá permanecer por um longo período.",
        )

    def test_muito_plana(self):
        self.assertEqual(
            gerar_texto_inclinacao("Muito Plana"),
            "A pequena diferença entre os vencimentos curtos e longos indica que os investidores esperam a manutenção desse nível de juros por um período prolongado, sem antecipar mudanças significativas na política monetária.",
        )

    def test_plana(self):
        self.assertEqual(
            gerar_texto_inclinacao("Plana"),
            "Os juros de longo prazo permanecem ligeiramente acima dos de curto prazo, sugerindo expectativa de estabilidade da política monetária com um pequeno prêmio para prazos maiores.",
        )

    def test_moderadamente_inclinada(self):
        self.assertEqual(
            gerar_texto_inclinacao("Moderadamente Inclinada"),
            "Os investidores exigem um prêmio moderado para aplicações de longo prazo, refletindo alguma incerteza sobre a evolução da inflação e dos juros nos próximos anos.",
        )

    def test_muito_inclinada(self):
        self.assertEqual(
            gerar_texto_inclinacao("Muito Inclinada"),
            "Os juros aumentam significativamente conforme o prazo, indicando que o mercado exige um prêmio elevado para aplicações longas devido às incertezas sobre inflação, política monetária e riscos econômicos futuros.",
        )

    def test_unknown_returns_empty(self):
        self.assertEqual(gerar_texto_inclinacao("Desconhecida"), "")


class TestGerarTextoSteepening(unittest.TestCase):
    def test_steepening_format(self):
        text = gerar_texto_steepening("Steepening", "Moderado", 18.0)
        self.assertEqual(text, "▲ Steepening Moderado (+18 bps)")

    def test_flattening_format(self):
        text = gerar_texto_steepening("Flattening", "Forte", -30.0)
        self.assertEqual(text, "▼ Flattening Forte (30 bps)")

    def test_estavel(self):
        text = gerar_texto_steepening("Estavel", "Nenhuma", 0.0)
        self.assertEqual(text, "Sem alteração relevante na última atualização.")


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

    def test_nominal_content_exact(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertEqual(
            blocos["Nível Nominal"],
            "Nível Nominal\n"
            "● Muito Altos (14.25%)\n"
            "O mercado precifica juros entre os maiores níveis observados.",
        )

    def test_politica_monetaria_content_exact(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertEqual(
            blocos["Política Monetária"],
            "Política Monetária\n"
            "● Muito Restritiva (juro real: 11.25%)\n"
            "A política monetária permanece fortemente voltada ao controle da inflação.",
        )

    def test_inclinacao_content_exact(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertEqual(
            blocos["Inclinação"],
            "Inclinação\n"
            "● Moderadamente Inclinada (75 bps)\n"
            "Os investidores exigem um prêmio moderado para aplicações de longo prazo, refletindo alguma incerteza sobre a evolução da inflação e dos juros nos próximos anos.",
        )

    def test_premio_de_prazo_content_exact(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertEqual(
            blocos["Prêmio de Prazo"],
            "Prêmio de Prazo\n"
            "● Normal (75 bps)",
        )

    def test_mensagem_do_mercado_content_exact(self):
        blocos = montar_resumo_executivo(self.indicadores, self.config)
        self.assertEqual(
            blocos["Mensagem do Mercado"],
            "Mensagem do Mercado\n"
            "O mercado precifica juros entre os maiores níveis observados. "
            "A política monetária permanece fortemente voltada ao controle da inflação. "
            "Os investidores exigem um prêmio moderado para aplicações de longo prazo, refletindo alguma incerteza sobre a evolução da inflação e dos juros nos próximos anos.",
        )

    def test_estabilidade_estimada_content(self):
        estabilidade = {"deviation_bps": 8.0, "nivel": "Alta", "estimado": True}
        blocos = montar_resumo_executivo(self.indicadores, self.config, estabilidade)
        self.assertEqual(
            blocos["Estabilidade das Expectativas"],
            "Estabilidade das Expectativas\n"
            "● Alta (estimado por ausência de histórico)",
        )

    def test_estabilidade_real_content(self):
        estabilidade = {"deviation_bps": 8.0, "nivel": "Alta", "estimado": False}
        blocos = montar_resumo_executivo(self.indicadores, self.config, estabilidade)
        self.assertEqual(
            blocos["Estabilidade das Expectativas"],
            "Estabilidade das Expectativas\n"
            "● Alta (desvio médio: 8.0 bps)",
        )

    def test_ultima_mudanca_content(self):
        steepening = {"direcao": "Steepening", "delta_bps": 12.0, "magnitude": "Moderado"}
        blocos = montar_resumo_executivo(self.indicadores, self.config, None, steepening)
        self.assertEqual(
            blocos["Última Mudança"],
            "Última Mudança\n"
            "▲ Steepening Moderado (+12 bps)",
        )

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


class TestClassificarEstabilidade(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig()

    def test_muito_alta(self):
        result = _classificar_estabilidade(1.0, self.config)
        self.assertEqual(result["nivel"], "Muito Alta")
        self.assertFalse(result["estimado"])

    def test_alta(self):
        result = _classificar_estabilidade(5.0, self.config)
        self.assertEqual(result["nivel"], "Alta")

    def test_media(self):
        result = _classificar_estabilidade(10.0, self.config)
        self.assertEqual(result["nivel"], "Média")

    def test_baixa(self):
        result = _classificar_estabilidade(20.0, self.config)
        self.assertEqual(result["nivel"], "Baixa")

    def test_muito_baixa(self):
        result = _classificar_estabilidade(35.0, self.config)
        self.assertEqual(result["nivel"], "Muito Baixa")

    def test_estimado_flag(self):
        result = _classificar_estabilidade(5.0, self.config, estimado=True)
        self.assertTrue(result["estimado"])

    def test_deviation_rounded_to_two_decimals(self):
        result = _classificar_estabilidade(4.999, self.config)
        self.assertEqual(result["deviation_bps"], 5.0)


class TestClassificarSteepening(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig()

    def test_leve(self):
        result = _classificar_steepening(9.0, self.config)
        self.assertEqual(result["magnitude"], "Leve")
        self.assertEqual(result["direcao"], "Steepening")

    def test_moderado(self):
        result = _classificar_steepening(10.0, self.config)
        self.assertEqual(result["magnitude"], "Moderado")

    def test_forte(self):
        result = _classificar_steepening(20.0, self.config)
        self.assertEqual(result["magnitude"], "Forte")

    def test_muito_forte(self):
        result = _classificar_steepening(40.0, self.config)
        self.assertEqual(result["magnitude"], "Muito Forte")

    def test_estavel(self):
        result = _classificar_steepening(0.0, self.config)
        self.assertEqual(result, {"direcao": "Estavel", "delta_bps": 0.0, "magnitude": "Nenhuma"})

    def test_flattening_direction(self):
        result = _classificar_steepening(-10.0, self.config)
        self.assertEqual(result["direcao"], "Flattening")
        self.assertEqual(result["magnitude"], "Moderado")

    def test_delta_rounded_to_two_decimals(self):
        result = _classificar_steepening(10.004, self.config)
        self.assertEqual(result["delta_bps"], 10.0)


class TestCalcSlopeFromRecords(unittest.TestCase):
    def test_empty_returns_none(self):
        self.assertIsNone(_calc_slope_from_records([]))

    def test_single_record_returns_none(self):
        records = [RateRecord(day252=1, day360=1, rate="14.65")]
        self.assertIsNone(_calc_slope_from_records(records))

    def test_two_records(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14.00"),
            RateRecord(day252=2, day360=2, rate="15.00"),
        ]
        self.assertEqual(_calc_slope_from_records(records), 100.0)

    def test_comma_decimal(self):
        records = [
            RateRecord(day252=1, day360=1, rate="14,00"),
            RateRecord(day252=2, day360=2, rate="15,00"),
        ]
        self.assertEqual(_calc_slope_from_records(records), 100.0)


class TestEstabilidadeFallback(unittest.TestCase):
    def test_default_fallback_returns_estimado(self):
        config = CurvaJurosConfig(stability_fallback="default")
        result = _estabilidade_fallback(config)
        self.assertIsNotNone(result)
        self.assertTrue(result["estimado"])
        self.assertAlmostEqual(result["deviation_bps"], 15.0)

    def test_auto_fallback(self):
        config = CurvaJurosConfig(stability_fallback="auto")
        result = _estabilidade_fallback(config)
        self.assertIsNotNone(result)
        self.assertTrue(result["estimado"])

    def test_unavailable_returns_none(self):
        config = CurvaJurosConfig(stability_fallback="unavailable")
        self.assertIsNone(_estabilidade_fallback(config))


class TestSteepeningFallback(unittest.TestCase):
    def test_auto_uses_delta_division(self):
        config = CurvaJurosConfig(steepening_fallback="auto")
        result = _steepening_fallback(50.0, config)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["delta_bps"], 10.0)

    def test_default_uses_estimated_delta(self):
        config = CurvaJurosConfig(steepening_fallback="default")
        result = _steepening_fallback(50.0, config)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["delta_bps"], 15.0)

    def test_unavailable_returns_none(self):
        config = CurvaJurosConfig(steepening_fallback="unavailable")
        self.assertIsNone(_steepening_fallback(50.0, config))


class TestCalcularEstabilidadeDetalhado(unittest.TestCase):
    def test_breaks_loop_on_empty_window_date(self):
        historical = {
            "2024-01-01": [],
            "2024-01-02": _make_records(14.0, 14.5, 15.0, 15.5),
            "2024-01-03": _make_records(14.1, 14.6, 15.1, 15.6),
            "2024-01-04": _make_records(14.2, 14.7, 15.2, 15.7),
        }
        config = CurvaJurosConfig(stability_window=4, stability_fallback="default")
        result = calcular_estabilidade(historical, _make_records(14.0, 14.5), config)
        self.assertIsNotNone(result)
        self.assertFalse(result["estimado"])

    def test_insufficient_slopes_uses_fallback(self):
        historical = {
            "2024-01-01": _make_records(14.0, 14.5),
            "2024-01-02": [RateRecord(day252=1, day360=1, rate="14.1")],
        }
        config = CurvaJurosConfig(stability_window=2, stability_fallback="default")
        result = calcular_estabilidade(historical, _make_records(14.0, 14.5), config)
        self.assertIsNotNone(result)
        self.assertTrue(result["estimado"])

    def test_uses_slope_delta_between_first_and_last(self):
        historical = {
            "2024-01-01": _make_records(14.0, 14.5, 15.0),
            "2024-01-02": _make_records(14.0, 14.5, 15.0),
            "2024-01-03": _make_records(14.0, 14.5, 15.0),
            "2024-01-04": _make_records(14.0, 14.5, 15.0),
        }
        config = CurvaJurosConfig(stability_window=4, stability_fallback="default")
        result = calcular_estabilidade(historical, _make_records(14.0, 14.5), config)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["deviation_bps"], 0.0)
        self.assertFalse(result["estimado"])

    def test_non_estimado_when_sufficient_history(self):
        historical = {
            "2024-01-01": _make_records(14.0, 14.5, 15.0),
            "2024-01-02": _make_records(14.1, 14.6, 15.1),
            "2024-01-03": _make_records(14.2, 14.7, 15.2),
            "2024-01-04": _make_records(14.3, 14.8, 15.3),
        }
        config = CurvaJurosConfig(stability_window=4, stability_fallback="default")
        result = calcular_estabilidade(historical, _make_records(14.0, 14.5), config)
        self.assertIsNotNone(result)
        self.assertFalse(result["estimado"])


class TestClassificarPremioBoundaries(unittest.TestCase):
    def setUp(self):
        self.config = CurvaJurosConfig()

    def test_boundary_20(self):
        self.assertEqual(classificar_premio(20, self.config), "Baixo")

    def test_boundary_50(self):
        self.assertEqual(classificar_premio(50, self.config), "Normal")

    def test_boundary_90(self):
        self.assertEqual(classificar_premio(90, self.config), "Elevado")

    def test_boundary_150(self):
        self.assertEqual(classificar_premio(150, self.config), "Muito Elevado")


if __name__ == "__main__":
    unittest.main()
