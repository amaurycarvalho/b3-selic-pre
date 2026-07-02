from b3_selic_pre.application.analyze._config import EvolutionConfig
from b3_selic_pre.application.analyze._evolucao import EvolutionReport


def gerar_texto_regime(regime: str) -> str:
    textos = {
        "Bear Steepening":
            "O mercado revisou para cima toda a estrutura de juros, principalmente os vencimentos longos.",
        "Bear Flattening":
            "O mercado revisou para cima toda a estrutura de juros, principalmente os vencimentos curtos.",
        "Bull Steepening":
            "O mercado passou a esperar cortes de juros, sobretudo nos vencimentos curtos.",
        "Bull Flattening":
            "O mercado reduziu as expectativas de juros, principalmente nos vencimentos longos.",
        "Bear Parallel Shift":
            "O mercado alterou toda a estrutura de juros sem mudanças relevantes na inclinação.",
        "Bull Parallel Shift":
            "O mercado alterou toda a estrutura de juros sem mudanças relevantes na inclinação.",
        "Twist":
            "Houve movimento divergente entre curto e longo prazo.",
        "Estável":
            "A curva permaneceu praticamente estável desde a última atualização.",
    }
    for key in ("Bear Steepening", "Bear Flattening", "Bull Steepening",
                "Bull Flattening", "Bear Parallel Shift", "Bull Parallel Shift",
                "Twist", "Estável"):
        if regime == key or (regime.endswith("Parallel Shift") and key.endswith("Parallel Shift")):
            return textos[key]
    return textos["Estável"]


def gerar_texto_politica(monetary_policy_msg: str, delta_real: float) -> str:
    if delta_real > 5:
        prefixo = "▲"
    elif delta_real < -5:
        prefixo = "▼"
    else:
        prefixo = "→"

    textos_expandidos = {
        "Mercado passou a precificar política mais restritiva":
            "O mercado passou a precificar uma política monetária significativamente mais contracionista.",
        "Política ligeiramente mais restritiva":
            "O mercado elevou ligeiramente a expectativa para os juros reais.",
        "Política praticamente inalterada":
            "A percepção sobre a política monetária permaneceu praticamente inalterada.",
        "Política ligeiramente menos restritiva":
            "O mercado passou a esperar uma política monetária menos restritiva.",
        "Mercado passou a precificar política significativamente menos restritiva":
            "O mercado passou a precificar uma política monetária significativamente menos contracionista.",
    }

    texto = textos_expandidos.get(monetary_policy_msg, monetary_policy_msg)
    sinal = f"+{delta_real:.0f}" if delta_real >= 0 else f"{delta_real:.0f}"
    return f"{prefixo} {texto} ({sinal} bps)"


def gerar_texto_premio(term_premium_msg: str, delta_slope: float) -> str:
    if delta_slope > 10:
        prefixo = "▲"
    elif delta_slope < -10:
        prefixo = "▼"
    else:
        prefixo = "→"

    textos_expandidos = {
        "Prêmio de prazo aumentou significativamente":
            "O prêmio exigido para aplicações de longo prazo aumentou.",
        "Prêmio aumentou":
            "O prêmio exigido para aplicações de longo prazo aumentou.",
        "Praticamente estável":
            "O prêmio de prazo permaneceu praticamente inalterado.",
        "Prêmio diminuiu":
            "O prêmio exigido para aplicações longas diminuiu.",
        "Forte redução do prêmio":
            "O prêmio exigido para aplicações longas diminuiu.",
    }

    texto = textos_expandidos.get(term_premium_msg, term_premium_msg)
    return f"{prefixo} {texto}"


def gerar_texto_intensidade(intensidade: str) -> str:
    textos = {
        "Muito Fraca": "A magnitude das alterações foi muito fraca.",
        "Fraca": "A magnitude das alterações foi fraca.",
        "Moderada": "A magnitude das alterações foi moderada.",
        "Forte": "A magnitude das alterações foi forte.",
        "Muito Forte": "A magnitude das alterações foi muito forte.",
    }
    return textos.get(intensidade, "")


def gerar_texto_direcao(direction: str) -> str:
    return direction


def montar_evolucao_resumo(
    evolution_report: EvolutionReport, config: EvolutionConfig
) -> list[str]:
    regime_texto = gerar_texto_regime(evolution_report.regime)
    politica_texto = gerar_texto_politica(
        evolution_report.monetary_policy_msg, evolution_report.delta_real_bps
    )
    premio_texto = gerar_texto_premio(
        evolution_report.term_premium_msg, evolution_report.delta_slope_bps
    )
    intensidade_texto = gerar_texto_intensidade(evolution_report.intensity)
    direcao_texto = gerar_texto_direcao(evolution_report.direction)

    blocos: list[str] = []

    if evolution_report.regime == "Estável":
        blocos.append(f"Regime\n● {evolution_report.regime}\n{regime_texto}")
        blocos.append(f"Direção Geral\n{direcao_texto}")
        blocos.append(
            f"Mensagem do Mercado\n"
            f"A curva permaneceu praticamente estável desde a última atualização. "
            f"{politica_texto} {premio_texto}"
        )
    else:
        blocos.append(f"Regime\n● {evolution_report.regime}\n{regime_texto}")
        blocos.append(f"Política Monetária\n{politica_texto}")
        blocos.append(f"Prêmio de Prazo\n{premio_texto}")
        blocos.append(f"Intensidade\n● {evolution_report.intensity}\n{intensidade_texto}")
        blocos.append(f"Direção Geral\n{direcao_texto}")
        blocos.append(
            f"Mensagem do Mercado\n"
            f"{regime_texto} {intensidade_texto} "
            f"{politica_texto} {premio_texto}"
        )

    return blocos
