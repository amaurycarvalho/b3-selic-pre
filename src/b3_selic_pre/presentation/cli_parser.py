"""Definição do parser de subcomandos da CLI."""

from __future__ import annotations

import argparse

from b3_selic_pre import __version__

SUBCOMMANDS = (
    "consultar",
    "atualizar",
    "exportar",
    "tesouro",
    "tesouro-resgates",
    "tesouro-estoque",
    "mercado",
    "mcp",
    "gui",
    "criar-atalho",
)
CURVAS = ("curta", "longa", "ambas")
TIPOS_RESGATE = ("recompra", "cupom", "vencimento")
ATIVOS = ("usd", "ouro", "ambos")
RESOLUCOES = ("auto", "dia", "semana", "mes")
FORMATOS = ("csv", "json")


def _add_data_options(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("Dados")
    group.add_argument(
        "--data",
        default=None,
        help="Data de referência no formato AAAA-MM-DD (padrão: hoje).",
    )
    group.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignora o cache em disco e baixa os dados da B3 novamente.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser raiz com os subcomandos da CLI."""
    parser = argparse.ArgumentParser(
        description="Consulta taxas referenciais SELIC Pré na B3."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"b3-selic-pre {__version__}",
        help="Exibe a versão do programa e sai.",
    )
    subparsers = parser.add_subparsers(dest="comando")

    consultar = subparsers.add_parser(
        "consultar", help="Consulta as taxas de uma data."
    )
    _add_data_options(consultar)
    consultar.add_argument(
        "--curva",
        choices=CURVAS,
        default="curta",
        help="Representação da curva a exibir (padrão: curta).",
    )

    atualizar = subparsers.add_parser(
        "atualizar", help="Carrega a evolução da curva e gera a análise."
    )
    _add_data_options(atualizar)
    atualizar.add_argument(
        "--silencioso",
        action="store_true",
        help="Carrega os dados sem imprimir a análise.",
    )

    exportar = subparsers.add_parser(
        "exportar", help="Exporta curvas, análise e log da aplicação."
    )
    _add_data_options(exportar)
    exportar.add_argument(
        "--curva",
        choices=CURVAS,
        default=None,
        help="Dados da evolução: curta, longa ou ambas.",
    )
    exportar.add_argument(
        "--analise",
        action="store_true",
        help="Inclui o texto determinístico da análise.",
    )
    exportar.add_argument(
        "--analise-curva",
        choices=("curta", "longa"),
        default=None,
        help=(
            "Representação usada na análise (padrão: curta); "
            "exige --analise."
        ),
    )
    exportar.add_argument(
        "--log",
        action="store_true",
        help="Inclui uma cópia do log ativo da aplicação.",
    )
    exportar.add_argument(
        "--saida",
        default=None,
        help="Arquivo ou diretório de destino; omitido imprime um artefato.",
    )

    tesouro = subparsers.add_parser(
        "tesouro", help="Consulta as vendas do Tesouro Direto."
    )
    tesouro.add_argument(
        "--titulo",
        default=None,
        help="Filtro parcial por título, sem caixa/acentos.",
    )
    tesouro.add_argument(
        "--inicio",
        default=None,
        help="Data inicial de liquidação no formato AAAA-MM-DD.",
    )
    tesouro.add_argument(
        "--fim",
        default=None,
        help="Data final de liquidação no formato AAAA-MM-DD.",
    )
    tesouro.add_argument(
        "--agregar",
        action="store_true",
        help="Agrupa as vendas por título.",
    )
    tesouro.add_argument(
        "--json",
        action="store_true",
        help="Emite um payload JSON estruturado.",
    )
    tesouro.add_argument(
        "--no-cache",
        action="store_true",
        help="Força uma verificação condicional no Tesouro Transparente.",
    )
    tesouro.add_argument(
        "--saida",
        default=None,
        help="Arquivo ou diretório de destino; omitido imprime no stdout.",
    )

    resgates = subparsers.add_parser(
        "tesouro-resgates",
        help="Consulta recompras, cupons e vencimentos do Tesouro Direto.",
    )
    resgates.add_argument(
        "--tipo",
        choices=TIPOS_RESGATE,
        default=None,
        help="Tipo de resgate (padrão: todos).",
    )
    resgates.add_argument(
        "--titulo",
        default=None,
        help="Filtro parcial por título, sem caixa/acentos.",
    )
    resgates.add_argument(
        "--inicio",
        default=None,
        help="Data inicial de resgate no formato AAAA-MM-DD.",
    )
    resgates.add_argument(
        "--fim",
        default=None,
        help="Data final de resgate no formato AAAA-MM-DD.",
    )
    resgates.add_argument(
        "--agregar",
        action="store_true",
        help="Agrupa por tipo de resgate e título.",
    )
    resgates.add_argument(
        "--json",
        action="store_true",
        help="Emite um payload JSON estruturado.",
    )
    resgates.add_argument(
        "--no-cache",
        action="store_true",
        help="Força uma verificação condicional no Tesouro Transparente.",
    )
    resgates.add_argument(
        "--saida",
        default=None,
        help="Arquivo ou diretório de destino; omitido imprime no stdout.",
    )

    estoque = subparsers.add_parser(
        "tesouro-estoque",
        help="Consulta o estoque mensal do Tesouro Direto.",
    )
    estoque.add_argument(
        "--titulo",
        default=None,
        help="Filtro parcial por título, sem caixa/acentos.",
    )
    estoque.add_argument(
        "--inicio",
        default=None,
        help="Mês inicial no formato AAAA-MM.",
    )
    estoque.add_argument(
        "--fim",
        default=None,
        help="Mês final no formato AAAA-MM.",
    )
    estoque.add_argument(
        "--mes",
        default=None,
        help="Seleciona um único mês no formato AAAA-MM.",
    )
    estoque.add_argument(
        "--agregar",
        action="store_true",
        help="Agrupa por título dentro de um único mês.",
    )
    estoque.add_argument(
        "--json",
        action="store_true",
        help="Emite um payload JSON estruturado.",
    )
    estoque.add_argument(
        "--no-cache",
        action="store_true",
        help="Força uma verificação condicional no Tesouro Transparente.",
    )
    estoque.add_argument(
        "--saida",
        default=None,
        help="Arquivo ou diretório de destino; omitido imprime no stdout.",
    )

    mercado = subparsers.add_parser(
        "mercado", help="Consulta ou exporta séries de dólar e ouro."
    )
    mercado.add_argument(
        "--ativo", choices=ATIVOS, default="ambos",
        help="Ativo consultado (padrão: ambos).",
    )
    mercado.add_argument(
        "--inicio", default=None,
        help="Data inicial no formato AAAA-MM-DD.",
    )
    mercado.add_argument(
        "--fim", default=None,
        help="Data final no formato AAAA-MM-DD.",
    )
    mercado.add_argument(
        "--resolucao", choices=RESOLUCOES, default="auto",
        help="Resolução temporal (padrão: auto).",
    )
    mercado.add_argument(
        "--prever", action="store_true",
        help="Inclui o cenário de 12 meses.",
    )
    mercado.add_argument(
        "--formato", choices=FORMATOS, default="csv",
        help="Formato de saída (padrão: csv).",
    )
    mercado.add_argument(
        "--saida", default=None,
        help="Arquivo ou diretório de destino; omitido imprime no stdout.",
    )
    mercado.add_argument(
        "--no-cache", action="store_true",
        help="Consulta as fontes mesmo que o cache esteja válido.",
    )
    mercado.add_argument(
        "--atualizar", action="store_true",
        help="Atualiza as fontes antes de emitir a saída.",
    )

    mcp = subparsers.add_parser(
        "mcp", help="Inicia o servidor MCP via stdio."
    )
    mcp.add_argument(
        "--atualizar",
        action="store_true",
        help="Carrega os dados de hoje antes de iniciar o servidor.",
    )
    mcp.add_argument(
        "--data",
        default=None,
        help="Data de referência AAAA-MM-DD para preparar antes do servidor.",
    )

    subparsers.add_parser("gui", help="Abre a interface gráfica desktop.")
    subparsers.add_parser(
        "criar-atalho", help="Cria o atalho no desktop e no menu de aplicações."
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Interpreta os argumentos da linha de comando e retorna as opções."""
    return build_parser().parse_args(argv)
