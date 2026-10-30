"""Taxonomia pura dos indexadores dos títulos do Tesouro Direto."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from b3_selic_pre.application.tesouro._parsing import normalizar_texto

logger = logging.getLogger(__name__)

SELIC = "SELIC"
SELIC_RESERVA = "SELIC_RESERVA"
IPCA = "IPCA"
IPCA_JUROS = "IPCA_JUROS"
RENDA = "RENDA"
EDUCA = "EDUCA"
PREFIXADO = "PREFIXADO"
PREFIXADO_JUROS = "PREFIXADO_JUROS"
IGP_M = "IGP-M"
IGP_M_JUROS = "IGP_M"
OUTROS = "OUTROS"

FAMILIAS = (SELIC, IPCA, PREFIXADO, IGP_M, OUTROS)
SUBFAMILIAS = (
    SELIC,
    SELIC_RESERVA,
    IPCA,
    IPCA_JUROS,
    RENDA,
    EDUCA,
    PREFIXADO,
    PREFIXADO_JUROS,
    IGP_M_JUROS,
    OUTROS,
)
REGISTRY_VERSION = 1


@dataclass(frozen=True)
class FamiliaIndexador:
    """Família e subfamília de indexador de um título."""

    familia: str
    subfamilia: str


REGISTRY: dict[str, FamiliaIndexador] = {
    "tesouro selic": FamiliaIndexador(SELIC, SELIC),
    "tesouro reserva": FamiliaIndexador(SELIC, SELIC_RESERVA),
    "tesouro ipca+": FamiliaIndexador(IPCA, IPCA),
    "tesouro ipca+ com juros semestrais": FamiliaIndexador(IPCA, IPCA_JUROS),
    "tesouro renda+": FamiliaIndexador(IPCA, RENDA),
    "tesouro educa+": FamiliaIndexador(IPCA, EDUCA),
    "tesouro prefixado": FamiliaIndexador(PREFIXADO, PREFIXADO),
    "tesouro prefixado com juros semestrais": FamiliaIndexador(
        PREFIXADO, PREFIXADO_JUROS
    ),
    "tesouro igpm+ com juros semestrais": FamiliaIndexador(IGP_M, IGP_M_JUROS),
}
_ORDERED_KEYS = tuple(sorted(REGISTRY, key=len, reverse=True))
_DESCONHECIDO = FamiliaIndexador(OUTROS, OUTROS)


def classificar_familia(tipo_titulo: str) -> FamiliaIndexador:
    """Classify a title into its indexer family, falling back to ``OUTROS``."""
    normalizado = normalizar_texto(tipo_titulo)
    for chave in _ORDERED_KEYS:
        if normalizado == chave or normalizado.startswith(f"{chave} "):
            return REGISTRY[chave]
    logger.warning(
        "Título do Tesouro desconhecido '%s' classificado como %s.",
        tipo_titulo,
        OUTROS,
    )
    return _DESCONHECIDO
