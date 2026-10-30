"""Health check da fonte mensal de estoque do Tesouro Direto."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError, parse_estoque
from b3_selic_pre.infrastructure.tesouro_cache import TesouroCache
from b3_selic_pre.infrastructure.tesouro_client import TesouroSourceClient
from b3_selic_pre.infrastructure.tesouro_types import TesouroResource

logger = logging.getLogger(__name__)

MAX_MONTHS_LAG = 3


@dataclass(frozen=True)
class EstoqueSourceHealth:
    """Result of a successful stock source health check."""

    latest_month: str
    warning: str | None = None

    @property
    def message(self: EstoqueSourceHealth) -> str:
        """Return the consolidated-month label."""
        return f"Último mês consolidado: {self.latest_month}"


def _month_index(value: str) -> tuple[int, int]:
    year, month = value[:7].split("-")
    return int(year), int(month)


def month_lag(latest_month: str, reference: date) -> int:
    """Return how many months ``latest_month`` lags behind ``reference``."""
    latest_year, latest = _month_index(latest_month)
    return (
        reference.year * 12 + reference.month
        - (latest_year * 12 + latest)
    )


def avaliar_defasagem(
    latest_month: str,
    reference: date | None = None,
) -> str | None:
    """Return a warning when the latest consolidated month is too old."""
    current = reference or date.today()
    lag = month_lag(latest_month, current)
    if lag <= MAX_MONTHS_LAG:
        return None
    return (
        "Estoque do Tesouro defasado: último mês consolidado "
        f"{latest_month} está {lag} meses atrás de "
        f"{current.strftime('%Y-%m')}."
    )


def validar_estoque(data: bytes) -> str:
    """Validate the stock CSV and return its latest consolidated month."""
    records = parse_estoque(data)
    return max(item.mes for item in records)


class TesouroSourceHealth:
    """Validates the CKAN stock source before it is used by analytics."""

    def __init__(
        self: TesouroSourceHealth,
        source: TesouroSourceClient | None = None,
        cache: TesouroCache | None = None,
    ) -> None:
        """Initialize the health checker with injectable adapters."""
        self._source = source or TesouroSourceClient()
        self._cache = cache or TesouroCache(resource="estoque")

    def check_estoque(
        self: TesouroSourceHealth,
        reference: date | None = None,
    ) -> EstoqueSourceHealth:
        """Validate dataset, resource, header and consolidated month."""
        try:
            resource = self._source.discover_estoque()
            latest = validar_estoque(self._stock_data(resource))
        except CommunicationError as exc:
            logger.warning(
                "Falha de comunicação no health check do estoque: %s", exc
            )
            raise
        except TesouroDataError as exc:
            logger.warning("Fonte de estoque inválida: %s", exc)
            raise
        warning = avaliar_defasagem(latest, reference)
        if warning is not None:
            logger.warning(warning)
        return EstoqueSourceHealth(latest_month=latest, warning=warning)

    def _stock_data(
        self: TesouroSourceHealth,
        resource: TesouroResource,
    ) -> bytes:
        cached = self._cache.read()
        download = self._source.download(
            resource,
            etag=self._cached_value(cached, "etag"),
            last_modified=self._cached_value(cached, "last_modified"),
        )
        if download.status == 304:
            if cached is None:
                raise CommunicationError(
                    "Tesouro respondeu 304 sem cache de estoque disponível."
                )
            return cached[0]
        if download.data is None:
            raise CommunicationError("Download do estoque sem conteúdo.")
        return download.data

    @staticmethod
    def _cached_value(
        cached: tuple[bytes, dict[str, object]] | None,
        key: str,
    ) -> str | None:
        if cached is None:
            return None
        value = cached[1].get(key)
        return value if isinstance(value, str) and value else None
