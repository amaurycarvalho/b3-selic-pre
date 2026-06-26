from b3_selic_pre.application.analyze._thresholds import AnalysisThresholds
from b3_selic_pre.application.analyze._metrics import DetailedMetrics
from b3_selic_pre.application.analyze._metrics_evolution import (
    EnvelopeMetrics,
    EvolutionMetrics,
)


class RuleResult:
    def __init__(self, text: str = "", weight: int = 0, section: str = ""):
        self.text = text
        self.weight = weight
        self.section = section


def regra_forma_curva(
    metrics: DetailedMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    delta = metrics.taxa_final - metrics.taxa_inicial
    if delta > thresholds.curva_ascendente_min:
        return RuleResult(
            "A estrutura a termo apresenta inclinação positiva, "
            "indicando taxas maiores para vencimentos mais longos.",
            weight=2,
            section="Formato da Curva",
        )
    if delta < -thresholds.curva_descendente_min:
        return RuleResult(
            "A curva encontra-se invertida, refletindo expectativa "
            "de redução futura das taxas de juros.",
            weight=2,
            section="Formato da Curva",
        )
    if abs(delta) < thresholds.curva_plana_max:
        return RuleResult(
            "A curva permanece praticamente plana ao longo dos vencimentos.",
            weight=1,
            section="Formato da Curva",
        )
    return RuleResult()


def regra_inclinacao(
    metrics: DetailedMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if metrics.slope is None:
        return RuleResult()
    s = abs(metrics.slope)
    if s > thresholds.inclinacao_muito_forte:
        return RuleResult(
            "A inclinação da curva é muito acentuada, indicando "
            "prêmio relevante para prazos longos.",
            weight=2,
            section="Formato da Curva",
        )
    if s > thresholds.inclinacao_forte:
        return RuleResult(
            "A inclinação da curva é acentuada, indicando "
            "prêmio relevante para prazos longos.",
            weight=2,
            section="Formato da Curva",
        )
    if s > thresholds.inclinacao_moderada:
        return RuleResult(
            "A inclinação da curva é moderada, com prêmio "
            "gradual para os vencimentos mais longos.",
            weight=1,
            section="Formato da Curva",
        )
    if s > thresholds.inclinacao_fraca:
        return RuleResult(
            "A inclinação da curva é fraca, sugerindo "
            "expectativas homogêneas ao longo dos prazos.",
            weight=1,
            section="Formato da Curva",
        )
    return RuleResult(
        "A inclinação da curva é neutra, com prêmio "
        "desprezível entre os vencimentos.",
        weight=0,
        section="Formato da Curva",
    )


def regra_convexidade(
    metrics: DetailedMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if metrics.convexidade is None:
        return RuleResult()
    c = metrics.convexidade
    if c > thresholds.convexidade_relevante:
        return RuleResult(
            "O crescimento das taxas acelera nos vencimentos longos.",
            weight=1,
            section="Formato da Curva",
        )
    if c < -thresholds.convexidade_relevante:
        return RuleResult(
            "O avanço das taxas perde intensidade conforme aumenta o prazo.",
            weight=1,
            section="Formato da Curva",
        )
    return RuleResult(
        "A curva apresenta comportamento aproximadamente linear.",
        weight=0,
        section="Formato da Curva",
    )


def regra_volatilidade(
    metrics: DetailedMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if metrics.volatilidade is None:
        return RuleResult()
    v = metrics.volatilidade
    if v > thresholds.volatilidade_muito_alta:
        return RuleResult(
            "Observa-se elevada irregularidade entre vértices consecutivos, "
            "com oscilações acentuadas ao longo da curva.",
            weight=2,
            section="Dispersão e Consenso",
        )
    if v > thresholds.volatilidade_alta:
        return RuleResult(
            "Observa-se elevada irregularidade entre vértices consecutivos.",
            weight=2,
            section="Dispersão e Consenso",
        )
    if v > thresholds.volatilidade_normal_max:
        return RuleResult(
            "A variação entre vértices consecutivos está dentro do esperado.",
            weight=1,
            section="Dispersão e Consenso",
        )
    if v > thresholds.volatilidade_baixa:
        return RuleResult(
            "Os vértices apresentam comportamento relativamente homogêneo.",
            weight=1,
            section="Dispersão e Consenso",
        )
    return RuleResult(
        "Os vértices apresentam comportamento homogêneo.",
        weight=0,
        section="Dispersão e Consenso",
    )


def regra_oscilacoes(
    metrics: DetailedMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if metrics.oscilacoes > thresholds.oscilacoes_alto:
        return RuleResult(
            "Existem diversas oscilações locais, sugerindo "
            "baixa uniformidade da curva.",
            weight=1,
            section="Dispersão e Consenso",
        )
    if metrics.oscilacoes > thresholds.oscilacoes_alto // 2:
        return RuleResult(
            "Observam-se algumas oscilações locais ao longo da curva.",
            weight=0,
            section="Dispersão e Consenso",
        )
    return RuleResult()


def regra_spread_envelope(
    envelope: EnvelopeMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if envelope.spread_medio < thresholds.spread_muito_estreito:
        return RuleResult(
            "Existe elevado consenso do mercado sobre o nível "
            "esperado das taxas.",
            weight=1,
            section="Dispersão e Consenso",
        )
    if envelope.spread_medio <= thresholds.spread_padrao_max:
        return RuleResult(
            "A dispersão entre as taxas permanece dentro do padrão histórico.",
            weight=0,
            section="Dispersão e Consenso",
        )
    return RuleResult(
        "Há elevada dispersão entre as taxas negociadas para "
        "o mesmo horizonte temporal.",
        weight=2,
        section="Dispersão e Consenso",
    )


def regra_tendencia_envelope(
    envelope: EnvelopeMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if envelope.spread_tendencia == "crescente":
        return RuleResult(
            "A incerteza aumenta conforme se alonga o horizonte temporal.",
            weight=1,
            section="Dispersão e Consenso",
        )
    if envelope.spread_tendencia == "decrescente":
        return RuleResult(
            "O mercado demonstra maior convergência nas expectativas "
            "para os vencimentos longos.",
            weight=1,
            section="Dispersão e Consenso",
        )
    return RuleResult()


def regra_tendencia_evolucao(
    evolution: EvolutionMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if evolution.tendencia == "alta_continua":
        return RuleResult(
            "A curva vem sendo gradualmente reprecificada para "
            "cima nas últimas semanas.",
            weight=2,
            section="Evolução Recente",
        )
    if evolution.tendencia == "queda_continua":
        return RuleResult(
            "O mercado vem reduzindo consistentemente as "
            "expectativas de juros.",
            weight=2,
            section="Evolução Recente",
        )
    if evolution.tendencia == "instabilidade":
        return RuleResult(
            "As expectativas oscilaram significativamente ao "
            "longo das últimas semanas.",
            weight=1,
            section="Evolução Recente",
        )
    return RuleResult()


def regra_difusao(
    evolution: EvolutionMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if evolution.difusao == "disseminado":
        return RuleResult(
            "O movimento foi disseminado por praticamente toda a curva.",
            weight=2,
            section="Evolução Recente",
        )
    if evolution.difusao == "concentrado_longo":
        return RuleResult(
            "A alta concentrou-se nos vencimentos longos.",
            weight=1,
            section="Evolução Recente",
        )
    if evolution.difusao == "concentrado_curto":
        return RuleResult(
            "O ajuste ocorreu principalmente na parte curta da curva.",
            weight=1,
            section="Evolução Recente",
        )
    return RuleResult()


def regra_rotacao(
    evolution: EvolutionMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if evolution.rotacao == "bear_steepening":
        return RuleResult(
            "A parte longa da curva avançou mais intensamente que a curta, "
            "aumentando sua inclinação e indicando maior prêmio "
            "exigido para prazos longos.",
            weight=2,
            section="Qualidade do Movimento",
        )
    if evolution.rotacao == "bull_steepening":
        return RuleResult(
            "As taxas recuaram em toda a curva, porém a redução foi mais "
            "acentuada nos vencimentos curtos, elevando a inclinação relativa.",
            weight=2,
            section="Qualidade do Movimento",
        )
    if evolution.rotacao == "bear_flattening":
        return RuleResult(
            "A alta concentrou-se na parte curta da curva, reduzindo sua "
            "inclinação e sugerindo expectativa de juros elevados "
            "no curto prazo.",
            weight=2,
            section="Qualidade do Movimento",
        )
    if evolution.rotacao == "bull_flattening":
        return RuleResult(
            "As taxas caíram principalmente nos vencimentos longos, "
            "achatando a curva e indicando redução do prêmio de prazo.",
            weight=2,
            section="Qualidade do Movimento",
        )
    return RuleResult()


def regra_intensidade(
    evolution: EvolutionMetrics,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    i = evolution.intensidade
    if i > thresholds.intensidade_muito_grande:
        return RuleResult(
            "Houve reprecificação muito significativa da curva.",
            weight=2,
            section="Qualidade do Movimento",
        )
    if i > thresholds.intensidade_grande:
        return RuleResult(
            "Houve reprecificação significativa da curva.",
            weight=2,
            section="Qualidade do Movimento",
        )
    if i > thresholds.intensidade_moderada:
        return RuleResult(
            "O movimento semanal foi moderado.",
            weight=1,
            section="Qualidade do Movimento",
        )
    if i > thresholds.intensidade_pequena:
        return RuleResult(
            "O movimento semanal foi discreto.",
            weight=0,
            section="Qualidade do Movimento",
        )
    return RuleResult(
        "O movimento semanal foi praticamente inexistente.",
        weight=0,
        section="Qualidade do Movimento",
    )


def regra_score_agregado(
    score: int,
    thresholds: AnalysisThresholds,
) -> RuleResult:
    if score >= thresholds.score_expressivo:
        return RuleResult(
            "O conjunto dos indicadores aponta para uma reprecificação "
            "expressiva da curva de juros.",
            weight=0,
            section="Conclusão",
        )
    if score >= thresholds.score_relevante:
        return RuleResult(
            "O conjunto dos indicadores aponta para uma mudança "
            "relevante na estrutura da curva de juros.",
            weight=0,
            section="Conclusão",
        )
    if score >= thresholds.score_moderado:
        return RuleResult(
            "Observa-se mudança moderada nos indicadores da "
            "curva de juros.",
            weight=0,
            section="Conclusão",
        )
    return RuleResult(
        "Os indicadores apontam para um mercado estável.",
        weight=0,
        section="Conclusão",
    )
