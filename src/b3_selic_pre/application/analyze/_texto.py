from b3_selic_pre.application.analyze._config import CurvaJurosConfig
from b3_selic_pre.application.analyze._resumo import (
    Indicadores,
    classificar_inclinacao,
    classificar_nominal,
    classificar_premio,
    classificar_restricao,
)


def gerar_texto_nominal(classificacao: str) -> str:
    textos = {
        "Muito Baixos": "O mercado precifica juros historicamente baixos.",
        "Baixos": "O mercado precifica juros relativamente baixos.",
        "Moderados": "O mercado precifica juros próximos da média histórica.",
        "Altos": "O mercado precifica juros elevados.",
        "Muito Altos": "O mercado precifica juros entre os maiores níveis observados.",
    }
    return textos.get(classificacao, "")


def gerar_texto_restricao(classificacao: str) -> str:
    textos = {
        "Expansionista": "A política monetária estimula crédito e atividade.",
        "Neutra": "A política monetária é aproximadamente neutra.",
        "Restritiva": "A política monetária busca conter pressões inflacionárias.",
        "Muito Restritiva": "A política monetária permanece fortemente voltada ao controle da inflação.",
    }
    return textos.get(classificacao, "")


def gerar_texto_inclinacao(classificacao: str) -> str:
    textos = {
        "Quase Plana":
            "Os juros são praticamente iguais em todos os prazos, indicando forte consenso de que o nível atual deverá permanecer por um longo período.",

        "Muito Plana":
            "A pequena diferença entre os vencimentos curtos e longos indica que os investidores esperam a manutenção desse nível de juros por um período prolongado, sem antecipar mudanças significativas na política monetária.",

        "Plana":
            "Os juros de longo prazo permanecem ligeiramente acima dos de curto prazo, sugerindo expectativa de estabilidade da política monetária com um pequeno prêmio para prazos maiores.",

        "Moderadamente Inclinada":
            "Os investidores exigem um prêmio moderado para aplicações de longo prazo, refletindo alguma incerteza sobre a evolução da inflação e dos juros nos próximos anos.",

        "Muito Inclinada":
            "Os juros aumentam significativamente conforme o prazo, indicando que o mercado exige um prêmio elevado para aplicações longas devido às incertezas sobre inflação, política monetária e riscos econômicos futuros.",
    }    
    return textos.get(classificacao, "")


def gerar_texto_steepening(
    direcao: str, magnitude: str, delta_bps: float
) -> str:
    if direcao == "Estavel":
        return "Sem alteração relevante na última atualização."
    if direcao == "Steepening":
        return f"▲ Steepening {magnitude} (+{delta_bps:.0f} bps)"
    return f"▼ Flattening {magnitude} ({abs(delta_bps):.0f} bps)"


def montar_resumo_executivo(
    indicadores: Indicadores, config: CurvaJurosConfig,
    estabilidade: dict | None = None,
    steepening: dict | None = None,
) -> dict[str, str]:
    blocos: dict[str, str] = {}

    nominal = classificar_nominal(indicadores.taxa_curta, config)
    blocos["Nível Nominal"] = (
        f"Nível Nominal\n"
        f"● {nominal} ({indicadores.taxa_curta:.2f}%)\n"
        f"{gerar_texto_nominal(nominal)}"
    )

    restricao = classificar_restricao(indicadores.juro_real, config)
    blocos["Política Monetária"] = (
        f"Política Monetária\n"
        f"● {restricao} (juro real: {indicadores.juro_real:.2f}%)\n"
        f"{gerar_texto_restricao(restricao)}"
    )

    inclinacao = classificar_inclinacao(indicadores.inclinacao_bps)
    blocos["Inclinação"] = (
        f"Inclinação\n"
        f"● {inclinacao} ({indicadores.inclinacao_bps:.0f} bps)\n"
        f"{gerar_texto_inclinacao(inclinacao)}"
    )

    premio = classificar_premio(indicadores.inclinacao_bps, config)
    blocos["Prêmio de Prazo"] = (
        f"Prêmio de Prazo\n"
        f"● {premio} ({indicadores.inclinacao_bps:.0f} bps)"
    )

    if estabilidade is not None:
        if estabilidade.get("estimado"):
            sufixo = "estimado por ausência de histórico"
        else:
            sufixo = f"desvio médio: {estabilidade['deviation_bps']:.1f} bps"
        blocos["Estabilidade das Expectativas"] = (
            f"Estabilidade das Expectativas\n"
            f"● {estabilidade['nivel']} ({sufixo})"
        )

    if steepening is not None:
        texto_steep = gerar_texto_steepening(
            steepening["direcao"], steepening["magnitude"], steepening["delta_bps"]
        )
        blocos["Última Mudança"] = (
            f"Última Mudança\n"
            f"{texto_steep}"
        )

    blocos["Mensagem do Mercado"] = (
        f"Mensagem do Mercado\n"
        f"{gerar_texto_nominal(nominal)} "
        f"{gerar_texto_restricao(restricao)} "
        f"{gerar_texto_inclinacao(inclinacao)}"
    )

    return blocos
