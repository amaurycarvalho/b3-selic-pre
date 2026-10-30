"""API pública headless para vendas do Tesouro Direto."""

from b3_selic_pre.application.tesouro._errors import (
    PeriodoInvalidoError,
    TesouroDataError,
)
from b3_selic_pre.application.tesouro._formatting import (
    aggregate_item,
    build_agregados_payload,
    build_vendas_payload,
    format_agregados_csv,
    format_vendas_csv,
    sale_item,
)
from b3_selic_pre.application.tesouro._processamento import (
    DEFAULT_PERIOD_DAYS,
    VendaAgregada,
    agregar_por_titulo,
    filtrar_por_periodo,
    filtrar_por_titulo,
    maior_data_liquidacao,
    normalizar_texto,
    ordenar_vendas,
    parse_vendas,
    periodo_padrao,
    resolver_periodo,
    validar_periodo,
)

__all__ = [
    "DEFAULT_PERIOD_DAYS",
    "PeriodoInvalidoError",
    "TesouroDataError",
    "VendaAgregada",
    "aggregate_item",
    "agregar_por_titulo",
    "build_agregados_payload",
    "build_vendas_payload",
    "filtrar_por_periodo",
    "filtrar_por_titulo",
    "format_agregados_csv",
    "format_vendas_csv",
    "maior_data_liquidacao",
    "normalizar_texto",
    "ordenar_vendas",
    "parse_vendas",
    "periodo_padrao",
    "resolver_periodo",
    "sale_item",
    "validar_periodo",
]
