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


@dataclass(frozen=True)
class ResgateTesouroDireto:
    """One Tesouro Direto redemption (recompra, cupom or vencimento)."""

    tipo_resgate: str
    tipo_titulo: str
    vencimento: str
    data_resgate: str
    pu: Decimal | None
    quantidade: Decimal
    valor: Decimal


@dataclass(frozen=True)
class EstoqueTesouroDireto:
    """One monthly Tesouro Direto stock snapshot line."""

    tipo_titulo: str
    vencimento: str
    mes: str
    pu: Decimal
    quantidade: Decimal
    valor_estoque: Decimal


@dataclass(frozen=True)
class EstoqueMensalTitulo:
    """One monthly stock total by title from a complementary source."""

    tipo_titulo: str
    mes: str
    valor_estoque: Decimal
