"""Registro dos recursos lógicos do Tesouro Direto."""

from __future__ import annotations

from dataclasses import dataclass

from b3_selic_pre.domain.constants import (
    TESOURO_DATASET_NAME,
    TESOURO_ESTOQUE_DATASET_NAME,
    TESOURO_RESGATES_DATASET_NAME,
)

VENDAS_COLUMNS = (
    "Tipo Titulo",
    "Vencimento do Titulo",
    "Data de Liquidacao da Venda",
    "PU",
    "Quantidade",
    "Valor",
)
RECOMPRA_COLUMNS = (
    "Tipo Titulo",
    "Vencimento do Titulo",
    "Data Resgate",
    "Quantidade",
    "Valor",
)
RESGATE_COM_PU_COLUMNS = (
    "Tipo Titulo",
    "Vencimento do Titulo",
    "Data Resgate",
    "PU",
    "Quantidade",
    "Valor",
)
ESTOQUE_COLUMNS = (
    "Tipo Titulo",
    "Vencimento do Titulo",
    "Mes Estoque",
    "PU",
    "Quantidade",
    "Valor Estoque",
)

TTL_CONDITIONAL = "conditional"
TTL_DAILY = "daily"


@dataclass(frozen=True)
class TesouroResourceSpec:
    """Descreve um recurso lógico, seu pacote e seu cache."""

    key: str
    dataset_name: str
    resource_name: str
    csv_filename: str
    metadata_filename: str
    required_columns: tuple[str, ...]
    ttl_policy: str = TTL_DAILY
    has_pu: bool = True


VENDAS = TesouroResourceSpec(
    key="vendas",
    dataset_name=TESOURO_DATASET_NAME,
    resource_name="Vendas do Tesouro Direto",
    csv_filename="vendastesourodireto.csv",
    metadata_filename="metadata.json",
    required_columns=VENDAS_COLUMNS,
    ttl_policy=TTL_CONDITIONAL,
)
RECOMPRA = TesouroResourceSpec(
    key="recompra",
    dataset_name=TESOURO_RESGATES_DATASET_NAME,
    resource_name="Recompras do Tesouro Direto",
    csv_filename="recompras.csv",
    metadata_filename="recompras.metadata.json",
    required_columns=RECOMPRA_COLUMNS,
    ttl_policy=TTL_CONDITIONAL,
    has_pu=False,
)
CUPOM = TesouroResourceSpec(
    key="cupom",
    dataset_name=TESOURO_RESGATES_DATASET_NAME,
    resource_name="Pagamento de Cupom de Juros do Tesouro Direto",
    csv_filename="cupom.csv",
    metadata_filename="cupom.metadata.json",
    required_columns=RESGATE_COM_PU_COLUMNS,
)
VENCIMENTO = TesouroResourceSpec(
    key="vencimento",
    dataset_name=TESOURO_RESGATES_DATASET_NAME,
    resource_name="Vencimentos do Tesouro Direto",
    csv_filename="vencimentos.csv",
    metadata_filename="vencimentos.metadata.json",
    required_columns=RESGATE_COM_PU_COLUMNS,
)
ESTOQUE = TesouroResourceSpec(
    key="estoque",
    dataset_name=TESOURO_ESTOQUE_DATASET_NAME,
    resource_name="Estoque do Tesouro Direto",
    csv_filename="estoque.csv",
    metadata_filename="estoque.metadata.json",
    required_columns=ESTOQUE_COLUMNS,
)

RESOURCE_SPECS: dict[str, TesouroResourceSpec] = {
    spec.key: spec for spec in (VENDAS, RECOMPRA, CUPOM, VENCIMENTO, ESTOQUE)
}
RESGATE_KEYS = (RECOMPRA.key, CUPOM.key, VENCIMENTO.key)


def resource_spec(key: str) -> TesouroResourceSpec:
    """Return the spec for a logical resource key."""
    try:
        return RESOURCE_SPECS[key]
    except KeyError as exc:
        raise ValueError(f"Recurso do Tesouro desconhecido: {key}") from exc
