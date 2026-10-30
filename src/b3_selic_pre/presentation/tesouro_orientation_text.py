"""Conteúdo textual orientativo das sub-abas do Tesouro Direto."""

from __future__ import annotations

from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
)

ORIENTATION_SECTIONS = {
    KIND_VISAO_GERAL: (
        (
            "Objetivo",
            (
                "Comparar a composição do estoque com o apetite do mercado "
                "por família de indexador."
            ),
        ),
        (
            "Responde a pergunta",
            (
                "O mercado está demandando cada família acima ou abaixo da "
                "participação que ela já ocupa no estoque?"
            ),
        ),
        (
            "Indicadores envolvidos",
            (
                "Estoque: participação percentual do último mês consolidado "
                "por família. Apetite: participação percentual das vendas na "
                "janela selecionada por família."
            ),
        ),
        (
            "Como interpretar",
            (
                "Barras de estoque e apetite próximas indicam demanda "
                "alinhada ao estoque. No gráfico de evolução, o gap é "
                "apetite menos estoque: valores positivos indicam famílias "
                "demandadas acima do estoque; valores negativos, abaixo."
            ),
        ),
    ),
    KIND_ESTOQUE: (
        (
            "Objetivo",
            (
                "Mostrar como o estoque do Tesouro Direto está distribuído "
                "entre famílias e títulos."
            ),
        ),
        (
            "Responde a pergunta",
            (
                "Qual é a composição do estoque no último mês e como ela "
                "evoluiu ao longo da janela selecionada?"
            ),
        ),
        (
            "Indicadores envolvidos",
            (
                "Percentual por valor de estoque (metodologia do Tesouro) "
                "por família e por título. A evolução usa buckets mensais."
            ),
        ),
        (
            "Como interpretar",
            (
                "No gráfico atual, cada barra é uma família e os segmentos "
                "são títulos. Na evolução, cada faixa é uma família ao longo "
                "dos meses. Compare a espessura das faixas para ver ganho ou "
                "perda de participação."
            ),
        ),
    ),
    KIND_APETITE: (
        (
            "Objetivo",
            (
                "Mostrar a composição da demanda (vendas) do Tesouro Direto "
                "na janela selecionada."
            ),
        ),
        (
            "Responde a pergunta",
            (
                "Quais famílias e títulos o mercado tem demandado e como "
                "essa composição evoluiu ao longo do tempo?"
            ),
        ),
        (
            "Indicadores envolvidos",
            (
                "Percentual por valor de vendas por família e por título. A "
                "evolução usa buckets diários (14d), semanais (3m) ou "
                "mensais (12m/3a). O fluxo líquido é vendas menos recompras."
            ),
        ),
        (
            "Como interpretar",
            (
                "O gráfico atual agrega toda a janela; a evolução mostra a "
                "participação ao longo do tempo. Aumentos de participação "
                "indicam maior apetite relativo pela família. O fluxo "
                "líquido resume entradas menos recompras no período."
            ),
        ),
    ),
}

ORIENTATION_TEXTS = {
    kind: "\n\n".join(f"{title}: {body}" for title, body in sections)
    for kind, sections in ORIENTATION_SECTIONS.items()
}


