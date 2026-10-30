"""Domain models for b3_selic_pre."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RateRecord:
    """SELIC reference rate record for a business day."""

    day252: int
    day360: int
    rate: str


@dataclass(frozen=True)
class VendaTesouroDireto:
    """One Tesouro Direto sale settlement record."""

    tipo_titulo: str
    vencimento: str
    data_liquidacao: str
    pu: Decimal
    quantidade: Decimal
    valor: Decimal
