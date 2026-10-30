"""Catálogo determinístico das tools MCP e seus schemas de entrada."""

from __future__ import annotations

_READ_ONLY = {
    "readOnlyHint": True,
    "openWorldHint": False,
    "idempotentHint": True,
}

_DATA = {
    "type": "string",
    "description": "Data de referência no formato AAAA-MM-DD.",
}
_CURVA = {
    "type": "string",
    "enum": ["curta", "longa"],
    "description": "Representação da curva.",
}
_CURSOR = {
    "type": "string",
    "description": "Cursor opaco de continuação.",
}
_LIMITE = {
    "type": "integer",
    "minimum": 1,
    "description": "Máximo de itens na página.",
}
_TITULO = {
    "type": "string",
    "description": "Filtro parcial por título, sem caixa/acentos.",
}
_INICIO = {
    "type": "string",
    "description": "Data inicial de liquidação AAAA-MM-DD (inclusiva).",
}
_FIM = {
    "type": "string",
    "description": "Data final de liquidação AAAA-MM-DD (inclusiva).",
}
_AGREGAR = {
    "type": "boolean",
    "description": "Agrupa as vendas por título.",
}
_TIPO_RESGATE = {
    "type": "string",
    "enum": ["recompra", "cupom", "vencimento"],
    "description": "Tipo de resgate do Tesouro Direto.",
}
_AGREGAR_RESGATES = {
    "type": "boolean",
    "description": "Agrupa por tipo de resgate e título.",
}
_AGREGAR_ESTOQUE = {
    "type": "boolean",
    "description": "Agrupa por título dentro de um único mês.",
}
_INICIO_MES = {
    "type": "string",
    "description": "Mês inicial AAAA-MM (inclusivo).",
}
_FIM_MES = {
    "type": "string",
    "description": "Mês final AAAA-MM (inclusivo).",
}
_MES = {
    "type": "string",
    "description": "Mês único AAAA-MM.",
}


def _schema(
    properties: dict[str, object] | None = None,
    required: list[str] | None = None,
) -> dict[str, object]:
    schema: dict[str, object] = {
        "type": "object",
        "properties": properties or {},
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


TOOL_DEFINITIONS: list[dict[str, object]] = [
    {
        "name": "data_referencia",
        "title": "Data de referência",
        "description": (
            "Devolve a data de referência resolvida da última carga de dados, "
            "lendo apenas o settings local e o cache."
        ),
        "inputSchema": _schema(),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "consultar_curva",
        "title": "Consultar curva",
        "description": (
            "Consulta a curva de uma data a partir do cache local. "
            "Use curva=curta para registros brutos ou curva=longa para "
            "menor/média/maior taxa por ano."
        ),
        "inputSchema": _schema(
            {"data": _DATA, "curva": _CURVA, "cursor": _CURSOR, "limite": _LIMITE}
        ),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "exportar_curva_curta",
        "title": "Exportar curva curta",
        "description": (
            "Devolve o CSV detalhado da janela de evolução "
            "(DATA;DU252;DC365;TAXA), sem gravar arquivos."
        ),
        "inputSchema": _schema({"data": _DATA}),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "exportar_curva_longa",
        "title": "Exportar curva longa",
        "description": (
            "Devolve o CSV de taxa média por ano e data "
            "(DATA;ANO;TAXA_MEDIA), sem gravar arquivos."
        ),
        "inputSchema": _schema({"data": _DATA}),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "analise",
        "title": "Análise da curva",
        "description": (
            "Devolve o texto determinístico da análise e da evolução. "
            "Use curva=curta para registros brutos ou curva=longa para "
            "a série de taxas médias por ano."
        ),
        "inputSchema": _schema({"data": _DATA, "curva": _CURVA}),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "evolucao",
        "title": "Evolução da curva",
        "description": (
            "Devolve um resumo estruturado da janela de evolução, com "
            "indicadores por data e datas indisponíveis."
        ),
        "inputSchema": _schema(
            {"data": _DATA, "cursor": _CURSOR, "limite": _LIMITE}
        ),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "estatisticas",
        "title": "Estatísticas da curva",
        "description": (
            "Devolve menor/máxima taxa, taxa curta/longa, inclinação em "
            "pontos-base e juro real implícito."
        ),
        "inputSchema": _schema({"data": _DATA}),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "tesouro_vendas",
        "title": "Vendas do Tesouro Direto",
        "description": (
            "Consulta as vendas do Tesouro Direto apenas no cache local, "
            "com filtros por título e período, agregação e paginação."
        ),
        "inputSchema": _schema(
            {
                "titulo": _TITULO,
                "inicio": _INICIO,
                "fim": _FIM,
                "agregar": _AGREGAR,
                "cursor": _CURSOR,
                "limite": _LIMITE,
            }
        ),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "tesouro_resgates",
        "title": "Resgates do Tesouro Direto",
        "description": (
            "Consulta recompras, cupons e vencimentos do Tesouro Direto "
            "apenas no cache local, com filtros por tipo, título e período, "
            "agregação e paginação."
        ),
        "inputSchema": _schema(
            {
                "tipo": _TIPO_RESGATE,
                "titulo": _TITULO,
                "inicio": _INICIO,
                "fim": _FIM,
                "agregar": _AGREGAR_RESGATES,
                "cursor": _CURSOR,
                "limite": _LIMITE,
            }
        ),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "tesouro_estoque",
        "title": "Estoque do Tesouro Direto",
        "description": (
            "Consulta o estoque mensal do Tesouro Direto apenas no cache "
            "local, com filtros por título e mês, agregação e paginação."
        ),
        "inputSchema": _schema(
            {
                "titulo": _TITULO,
                "inicio": _INICIO_MES,
                "fim": _FIM_MES,
                "mes": _MES,
                "agregar": _AGREGAR_ESTOQUE,
                "cursor": _CURSOR,
                "limite": _LIMITE,
            }
        ),
        "annotations": dict(_READ_ONLY),
    },
    {
        "name": "listar_datas",
        "title": "Listar datas em cache",
        "description": (
            "Lista as datas válidas no cache local, da mais recente para a "
            "mais antiga, com metadados e paginação."
        ),
        "inputSchema": _schema({"cursor": _CURSOR, "limite": _LIMITE}),
        "annotations": dict(_READ_ONLY),
    },
]

TOOL_NAMES = frozenset(tool["name"] for tool in TOOL_DEFINITIONS)
