import unittest

from b3_selic_pre.application.analyze import (
    CurvaJurosConfig,
    EvolutionConfig,
    EvolutionReport,
    analyze_evolution,
)
from b3_selic_pre.application.analyze._evolucao import (
    classificar_intensidade,
    classificar_movimento,
    classificar_politica_monetaria,
    classificar_premio_prazo,
    classificar_regime,
    classificar_slope_movement,
    derivar_direcao_geral,
    extrair_deltas,
)
from b3_selic_pre.application.analyze._texto_evolucao import (
    gerar_texto_direcao,
    gerar_texto_intensidade,
    gerar_texto_politica,
    gerar_texto_premio,
    gerar_texto_regime,
    montar_evolucao_resumo,
)
from b3_selic_pre.domain.models import RateRecord


def _make_records(*rates):
    return [
        RateRecord(day252=i * 21, day360=i * 30, rate=str(r).replace(".", ","))
        for i, r in enumerate(rates)
    ]


class TestExtrairDeltas(unittest.TestCase):
    def test_delta_short_long_slope_real(self):
        current = _make_records(14.25, 14.50, 14.75, 15.00)
        previous = _make_records(14.00, 14.25, 14.50, 14.75)
        ds, dl, dsl, dr = extrair_deltas(current, previous)
        self.assertAlmostEqual(ds, 25.0)
        self.assertAlmostEqual(dl, 25.0)
        self.assertAlmostEqual(dsl, 0.0)
        self.assertAlmostEqual(dr, 25.0)

    def test_negative_deltas(self):
        current = _make_records(13.00, 13.25, 13.50, 13.75)
        previous = _make_records(14.00, 14.25, 14.50, 14.75)
        ds, dl, dsl, dr = extrair_deltas(current, previous)
        self.assertAlmostEqual(ds, -100.0)
        self.assertAlmostEqual(dl, -100.0)
        self.assertAlmostEqual(dsl, 0.0)
        self.assertAlmostEqual(dr, -100.0)

    def test_slope_change(self):
        current = _make_records(14.00, 14.50, 15.00, 15.50)
        previous = _make_records(14.00, 14.25, 14.50, 14.75)
        ds, dl, dsl, dr = extrair_deltas(current, previous)
        self.assertAlmostEqual(ds, 0.0)
        self.assertAlmostEqual(dl, 75.0)
        self.assertAlmostEqual(dsl, 75.0)
        self.assertAlmostEqual(dr, 0.0)


class TestClassificarMovimento(unittest.TestCase):
    def setUp(self):
        self.config = EvolutionConfig(movement_threshold_bps=5.0)

    def test_bear(self):
        self.assertEqual(
            classificar_movimento(25.0, 30.0, self.config), "Bear"
        )

    def test_bull(self):
        self.assertEqual(
            classificar_movimento(-25.0, -30.0, self.config), "Bull"
        )

    def test_twist_bull_short_bear_long(self):
        self.assertEqual(
            classificar_movimento(-25.0, 30.0, self.config), "Twist"
        )

    def test_twist_bear_short_bull_long(self):
        self.assertEqual(
            classificar_movimento(25.0, -30.0, self.config), "Twist"
        )

    def test_stable_below_threshold(self):
        self.assertEqual(
            classificar_movimento(3.0, 4.0, self.config), "Estável"
        )

    def test_stable_one_above_one_below(self):
        self.assertEqual(
            classificar_movimento(6.0, 3.0, self.config), "Estável"
        )

    def test_bear_exact_threshold(self):
        self.assertEqual(
            classificar_movimento(6.0, 7.0, self.config), "Bear"
        )

    def test_bull_exact_threshold(self):
        self.assertEqual(
            classificar_movimento(-6.0, -7.0, self.config), "Bull"
        )


class TestClassificarSlopeMovement(unittest.TestCase):
    def setUp(self):
        self.config = EvolutionConfig(steepening_threshold_bps=5.0)

    def test_steepening(self):
        self.assertEqual(
            classificar_slope_movement(10.0, self.config), "Steepening"
        )

    def test_flattening(self):
        self.assertEqual(
            classificar_slope_movement(-10.0, self.config), "Flattening"
        )

    def test_parallel_shift(self):
        self.assertEqual(
            classificar_slope_movement(3.0, self.config), "Parallel Shift"
        )

    def test_parallel_shift_negative(self):
        self.assertEqual(
            classificar_slope_movement(-3.0, self.config), "Parallel Shift"
        )

    def test_steepening_exact_threshold(self):
        self.assertEqual(
            classificar_slope_movement(5.0, self.config), "Parallel Shift"
        )

    def test_flattening_exact_threshold(self):
        self.assertEqual(
            classificar_slope_movement(-5.0, self.config), "Parallel Shift"
        )


class TestClassificarRegime(unittest.TestCase):
    def test_bear_steepening(self):
        self.assertEqual(
            classificar_regime("Bear", "Steepening"), "Bear Steepening"
        )

    def test_bear_flattening(self):
        self.assertEqual(
            classificar_regime("Bear", "Flattening"), "Bear Flattening"
        )

    def test_bull_steepening(self):
        self.assertEqual(
            classificar_regime("Bull", "Steepening"), "Bull Steepening"
        )

    def test_bull_flattening(self):
        self.assertEqual(
            classificar_regime("Bull", "Flattening"), "Bull Flattening"
        )

    def test_bear_parallel_shift(self):
        self.assertEqual(
            classificar_regime("Bear", "Parallel Shift"), "Bear Parallel Shift"
        )

    def test_bull_parallel_shift(self):
        self.assertEqual(
            classificar_regime("Bull", "Parallel Shift"), "Bull Parallel Shift"
        )

    def test_twist_any_slope(self):
        self.assertEqual(
            classificar_regime("Twist", "Steepening"), "Twist"
        )
        self.assertEqual(
            classificar_regime("Twist", "Flattening"), "Twist"
        )
        self.assertEqual(
            classificar_regime("Twist", "Parallel Shift"), "Twist"
        )

    def test_stable_any_slope(self):
        self.assertEqual(
            classificar_regime("Estável", "Steepening"), "Estável"
        )
        self.assertEqual(
            classificar_regime("Estável", "Flattening"), "Estável"
        )


class TestClassificarIntensidade(unittest.TestCase):
    def setUp(self):
        self.config = EvolutionConfig(
            very_weak_max=5.0, weak_max=15.0,
            moderate_max=30.0, strong_max=50.0,
        )

    def test_muito_fraca(self):
        self.assertEqual(
            classificar_intensidade(3.0, 4.0, self.config), "Muito Fraca"
        )

    def test_fraca(self):
        self.assertEqual(
            classificar_intensidade(10.0, 12.0, self.config), "Fraca"
        )

    def test_moderada(self):
        self.assertEqual(
            classificar_intensidade(20.0, 25.0, self.config), "Moderada"
        )

    def test_forte(self):
        self.assertEqual(
            classificar_intensidade(35.0, 40.0, self.config), "Forte"
        )

    def test_muito_forte(self):
        self.assertEqual(
            classificar_intensidade(55.0, 60.0, self.config), "Muito Forte"
        )

    def test_boundary_weak_max(self):
        self.assertEqual(
            classificar_intensidade(5.0, 5.0, self.config), "Muito Fraca"
        )


class TestClassificarPoliticaMonetaria(unittest.TestCase):
    def setUp(self):
        self.config = EvolutionConfig(
            highly_restrictive_min=20.0,
            slightly_restrictive_min=5.0,
            neutral_max=5.0,
            slightly_loose_max=20.0,
        )

    def test_highly_restrictive(self):
        self.assertEqual(
            classificar_politica_monetaria(25.0, self.config),
            "Mercado passou a precificar política mais restritiva",
        )

    def test_slightly_restrictive(self):
        self.assertEqual(
            classificar_politica_monetaria(10.0, self.config),
            "Política ligeiramente mais restritiva",
        )

    def test_neutral(self):
        self.assertEqual(
            classificar_politica_monetaria(3.0, self.config),
            "Política praticamente inalterada",
        )

    def test_slightly_loose(self):
        self.assertEqual(
            classificar_politica_monetaria(-10.0, self.config),
            "Política ligeiramente menos restritiva",
        )

    def test_highly_loose(self):
        self.assertEqual(
            classificar_politica_monetaria(-25.0, self.config),
            "Mercado passou a precificar política significativamente menos restritiva",
        )

    def test_boundary_neutral(self):
        self.assertEqual(
            classificar_politica_monetaria(5.0, self.config),
            "Política praticamente inalterada",
        )
        self.assertEqual(
            classificar_politica_monetaria(-5.0, self.config),
            "Política praticamente inalterada",
        )


class TestClassificarPremioPrazo(unittest.TestCase):
    def setUp(self):
        self.config = EvolutionConfig(
            significantly_increased_min=20.0,
            increased_min=10.0,
            decreased_min=20.0,
        )

    def test_significantly_increased(self):
        self.assertEqual(
            classificar_premio_prazo(25.0, self.config),
            "Prêmio de prazo aumentou significativamente",
        )

    def test_increased(self):
        self.assertEqual(
            classificar_premio_prazo(15.0, self.config),
            "Prêmio aumentou",
        )

    def test_stable(self):
        self.assertEqual(
            classificar_premio_prazo(5.0, self.config),
            "Praticamente estável",
        )

    def test_decreased(self):
        self.assertEqual(
            classificar_premio_prazo(-15.0, self.config),
            "Prêmio diminuiu",
        )

    def test_strong_reduction(self):
        self.assertEqual(
            classificar_premio_prazo(-25.0, self.config),
            "Forte redução do prêmio",
        )

    def test_boundary_increased_min(self):
        self.assertEqual(
            classificar_premio_prazo(10.0, self.config),
            "Praticamente estável",
        )


class TestDerivarDirecaoGeral(unittest.TestCase):
    def test_bear_fraca(self):
        self.assertEqual(
            derivar_direcao_geral("Bear Steepening", "Fraca"),
            "↑ Revisão Altista dos Juros",
        )

    def test_bear_moderada(self):
        self.assertEqual(
            derivar_direcao_geral("Bear Flattening", "Moderada"),
            "↑ Revisão Altista dos Juros",
        )

    def test_bear_muito_fraca(self):
        self.assertEqual(
            derivar_direcao_geral("Bear Parallel Shift", "Muito Fraca"),
            "→ Juros Marginalmente Mais Altos",
        )

    def test_bull_fraca(self):
        self.assertEqual(
            derivar_direcao_geral("Bull Steepening", "Fraca"),
            "↓ Revisão Baixista dos Juros",
        )

    def test_bull_muito_fraca(self):
        self.assertEqual(
            derivar_direcao_geral("Bull Flattening", "Muito Fraca"),
            "→ Juros Marginalmente Mais Baixos",
        )

    def test_twist(self):
        self.assertEqual(
            derivar_direcao_geral("Twist", "Moderada"),
            "↕ Movimento Misto na Estrutura",
        )

    def test_estavel(self):
        self.assertEqual(
            derivar_direcao_geral("Estável", "Muito Fraca"),
            "→ Estrutura a Juros Praticamente Estável",
        )


class TestTextoRegime(unittest.TestCase):
    def test_bear_steepening(self):
        self.assertIn(
            "revisou para cima toda a estrutura",
            gerar_texto_regime("Bear Steepening"),
        )

    def test_bear_flattening(self):
        self.assertIn(
            "revisou para cima toda a estrutura",
            gerar_texto_regime("Bear Flattening"),
        )

    def test_bull_steepening(self):
        self.assertIn(
            "passou a esperar cortes de juros",
            gerar_texto_regime("Bull Steepening"),
        )

    def test_bull_flattening(self):
        self.assertIn(
            "reduziu as expectativas de juros",
            gerar_texto_regime("Bull Flattening"),
        )

    def test_parallel_shift(self):
        self.assertIn(
            "sem mudanças relevantes na inclinação",
            gerar_texto_regime("Bear Parallel Shift"),
        )
        self.assertIn(
            "sem mudanças relevantes na inclinação",
            gerar_texto_regime("Bull Parallel Shift"),
        )

    def test_twist(self):
        self.assertEqual(
            gerar_texto_regime("Twist"),
            "Houve movimento divergente entre curto e longo prazo.",
        )

    def test_estavel(self):
        self.assertEqual(
            gerar_texto_regime("Estável"),
            "A curva permaneceu praticamente estável desde a última atualização.",
        )


class TestTextoPolitica(unittest.TestCase):
    def test_highly_restrictive_prefix(self):
        result = gerar_texto_politica(
            "Mercado passou a precificar política mais restritiva", 25.0
        )
        self.assertTrue(result.startswith("▲"))
        self.assertIn("significativamente mais contracionista", result)

    def test_slightly_restrictive_prefix(self):
        result = gerar_texto_politica(
            "Política ligeiramente mais restritiva", 10.0
        )
        self.assertTrue(result.startswith("▲"))
        self.assertIn("elevou ligeiramente", result)

    def test_neutral_prefix(self):
        result = gerar_texto_politica(
            "Política praticamente inalterada", 3.0
        )
        self.assertTrue(result.startswith("→"))
        self.assertIn("praticamente inalterada", result)

    def test_loose_prefix(self):
        result = gerar_texto_politica(
            "Política ligeiramente menos restritiva", -10.0
        )
        self.assertTrue(result.startswith("▼"))
        self.assertIn("menos restritiva", result)

    def test_highly_loose_prefix(self):
        result = gerar_texto_politica(
            "Mercado passou a precificar política significativamente menos restritiva", -25.0
        )
        self.assertTrue(result.startswith("▼"))
        self.assertIn("significativamente menos contracionista", result)

    def test_formata_bps_positivo(self):
        result = gerar_texto_politica(
            "Política ligeiramente mais restritiva", 10.0
        )
        self.assertIn("+10 bps", result)

    def test_formata_bps_negativo(self):
        result = gerar_texto_politica(
            "Política ligeiramente menos restritiva", -10.0
        )
        self.assertIn("-10 bps", result)


class TestTextoPremio(unittest.TestCase):
    def test_increased_prefix(self):
        result = gerar_texto_premio(
            "Prêmio de prazo aumentou significativamente", 25.0
        )
        self.assertTrue(result.startswith("▲"))
        self.assertIn("aumentou", result)

    def test_stable_prefix(self):
        result = gerar_texto_premio("Praticamente estável", 5.0)
        self.assertTrue(result.startswith("→"))
        self.assertIn("praticamente inalterado", result)

    def test_decreased_prefix(self):
        result = gerar_texto_premio("Forte redução do prêmio", -25.0)
        self.assertTrue(result.startswith("▼"))
        self.assertIn("diminuiu", result)


class TestTextoIntensidade(unittest.TestCase):
    def test_muito_fraca(self):
        self.assertEqual(
            gerar_texto_intensidade("Muito Fraca"),
            "A magnitude das alterações foi muito fraca.",
        )

    def test_fraca(self):
        self.assertEqual(
            gerar_texto_intensidade("Fraca"),
            "A magnitude das alterações foi fraca.",
        )

    def test_moderada(self):
        self.assertEqual(
            gerar_texto_intensidade("Moderada"),
            "A magnitude das alterações foi moderada.",
        )

    def test_forte(self):
        self.assertEqual(
            gerar_texto_intensidade("Forte"),
            "A magnitude das alterações foi forte.",
        )

    def test_muito_forte(self):
        self.assertEqual(
            gerar_texto_intensidade("Muito Forte"),
            "A magnitude das alterações foi muito forte.",
        )


class TestTextoDirecao(unittest.TestCase):
    def test_returns_direction_string(self):
        self.assertEqual(
            gerar_texto_direcao("↑ Revisão Altista dos Juros"),
            "↑ Revisão Altista dos Juros",
        )


class TestMontarEvolucaoResumo(unittest.TestCase):
    def setUp(self):
        self.config = EvolutionConfig()

    def test_full_version(self):
        report = EvolutionReport(
            regime="Bear Steepening",
            intensity="Forte",
            monetary_policy_msg="Mercado passou a precificar política mais restritiva",
            term_premium_msg="Prêmio de prazo aumentou significativamente",
            direction="↑ Revisão Altista dos Juros",
            delta_real_bps=25.0,
            delta_slope_bps=25.0,
        )
        blocos = montar_evolucao_resumo(report, self.config)
        self.assertEqual(len(blocos), 6)
        self.assertIn("Regime", blocos[0])
        self.assertIn("Política Monetária", blocos[1])
        self.assertIn("Prêmio de Prazo", blocos[2])
        self.assertIn("Intensidade", blocos[3])
        self.assertIn("Direção Geral", blocos[4])
        self.assertIn("Mensagem do Mercado", blocos[5])

    def test_compact_version_estavel(self):
        report = EvolutionReport(
            regime="Estável",
            intensity="Muito Fraca",
            monetary_policy_msg="Política praticamente inalterada",
            term_premium_msg="Praticamente estável",
            direction="→ Estrutura a Juros Praticamente Estável",
            delta_real_bps=2.0,
            delta_slope_bps=2.0,
        )
        blocos = montar_evolucao_resumo(report, self.config)
        self.assertEqual(len(blocos), 3)
        self.assertIn("Regime", blocos[0])
        self.assertIn("Direção Geral", blocos[1])
        self.assertIn("Mensagem do Mercado", blocos[2])


class TestAnalyzeEvolution(unittest.TestCase):
    def test_returns_none_with_empty_previous(self):
        current = _make_records(14.25, 14.50, 14.75, 15.00)
        result = analyze_evolution(current, [])
        self.assertIsNone(result)

    def test_returns_evolution_report(self):
        current = _make_records(14.25, 14.50, 14.75, 15.00)
        previous = _make_records(14.00, 14.25, 14.50, 14.75)
        result = analyze_evolution(current, previous)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, EvolutionReport)
        self.assertAlmostEqual(result.delta_short_bps, 25.0)
        self.assertAlmostEqual(result.delta_long_bps, 25.0)
        self.assertEqual(result.regime, "Bear Parallel Shift")
        self.assertEqual(result.intensity, "Moderada")

    def test_custom_config(self):
        current = _make_records(14.25, 14.50, 14.75, 15.00)
        previous = _make_records(14.00, 14.25, 14.50, 14.75)
        config = CurvaJurosConfig()
        config.evolucao.movement_threshold_bps = 30.0
        result = analyze_evolution(current, previous, config)
        self.assertIsNotNone(result)
        self.assertEqual(result.regime, "Estável")
        self.assertEqual(result.intensity, "Muito Fraca")

    def test_orquestra_pipeline_completo(self):
        current = _make_records(15.00, 15.25, 15.50, 15.75)
        previous = _make_records(14.00, 14.25, 14.50, 14.75)
        result = analyze_evolution(current, previous)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.delta_short_bps, 100.0)
        self.assertAlmostEqual(result.delta_long_bps, 100.0)
        self.assertAlmostEqual(result.delta_slope_bps, 0.0)
        self.assertAlmostEqual(result.delta_real_bps, 100.0)
        self.assertEqual(result.regime, "Bear Parallel Shift")
        self.assertEqual(result.intensity, "Muito Forte")
        self.assertIn("mais restritiva", result.monetary_policy_msg)


if __name__ == "__main__":
    unittest.main()
