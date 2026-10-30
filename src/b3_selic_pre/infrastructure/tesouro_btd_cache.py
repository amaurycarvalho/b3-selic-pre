"""Cache normalizado do estoque agregado do BTD."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from b3_selic_pre.domain.models import EstoqueMensalTitulo
from b3_selic_pre.infrastructure.cache_payload import write_atomic
from b3_selic_pre.infrastructure.tesouro_btd_types import BtdCacheEntry
from b3_selic_pre.infrastructure.tesouro_cache import tesouro_cache_dir

SCHEMA_VERSION = 2
CACHE_FILENAME = "estoque-btd.json"
TTL = timedelta(hours=24)
_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_REQUIRED = ("schema_version", "reference_month", "checked_at", "records")


def _valid_record(raw: object) -> bool:
    if not isinstance(raw, dict):
        return False
    title = raw.get("tipo_titulo")
    month = raw.get("mes")
    return (
        isinstance(title, str)
        and bool(title)
        and isinstance(month, str)
        and _MONTH.match(month) is not None
        and isinstance(raw.get("valor_estoque"), str)
    )


def _valid_month(value: object) -> bool:
    return isinstance(value, str) and _MONTH.match(value) is not None


def _valid_metadata(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("schema_version") != SCHEMA_VERSION:
        return False
    if any(key not in data for key in _REQUIRED):
        return False
    records = data.get("records")
    return (
        _valid_month(data.get("reference_month"))
        and isinstance(data.get("checked_at"), str)
        and isinstance(records, list)
        and bool(records)
        and all(_valid_record(item) for item in records)
    )


def _records(raw: list[object]) -> tuple[EstoqueMensalTitulo, ...]:
    result: list[EstoqueMensalTitulo] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            value = Decimal(str(item["valor_estoque"]))
        except (KeyError, InvalidOperation, ValueError):
            continue
        result.append(
            EstoqueMensalTitulo(
                str(item["tipo_titulo"]),
                str(item["mes"]),
                value,
            )
        )
    return tuple(result)


def _checked_at(metadata: dict[str, object]) -> datetime | None:
    raw = metadata.get("checked_at")
    if not isinstance(raw, str):
        return None
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class TesouroBtdCache:
    """Armazena atomicamente o estoque BTD normalizado e sua proveniência."""

    def __init__(
        self: TesouroBtdCache,
        cache_dir: str | Path | None = None,
    ) -> None:
        """Initialize the cache in the Tesouro cache directory."""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else tesouro_cache_dir()
        )
        self.path = self.cache_dir / CACHE_FILENAME

    def read(self: TesouroBtdCache) -> BtdCacheEntry | None:
        """Read a valid cache entry without modifying any file."""
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not _valid_metadata(payload):
            return None
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            return None
        records = _records(raw_records)
        if not records:
            return None
        metadata = {
            key: value for key, value in payload.items() if key != "records"
        }
        return BtdCacheEntry(records, metadata)

    def is_fresh(
        self: TesouroBtdCache,
        metadata: dict[str, object],
        now: datetime | None = None,
    ) -> bool:
        """Return whether ``checked_at`` is still inside the 24h TTL."""
        checked = _checked_at(metadata)
        if checked is None:
            return False
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        return current - checked < TTL

    def save(
        self: TesouroBtdCache,
        records: tuple[EstoqueMensalTitulo, ...],
        metadata: dict[str, object],
    ) -> None:
        """Write the normalized records and metadata atomically."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = dict(metadata)
        payload["schema_version"] = SCHEMA_VERSION
        payload["records"] = [
            {
                "tipo_titulo": item.tipo_titulo,
                "mes": item.mes,
                "valor_estoque": str(item.valor_estoque),
            }
            for item in records
        ]
        write_atomic(
            self.path,
            json.dumps(payload, ensure_ascii=False),
        )


__all__ = ["CACHE_FILENAME", "SCHEMA_VERSION", "TTL", "TesouroBtdCache"]
