"""Modelos puros de mercado para câmbio e ouro."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

OUNCES_PER_GRAM = 31.1034768
ATIVO_USD = "usd"
ATIVO_OURO = "ouro"
UNIDADE_USD = "BRL/USD"
UNIDADE_OURO = "BRL/g"
METODO_OFICIAL = "oficial"
METODO_DERIVADO = "derivado"
METODO_CACHE_DEFASADO = "cache_defasado"
METODO_MERCADO = "cenario_mercado"
METODO_ESTATISTICO = "projecao_estatistica"


class Resolution(StrEnum):
    """Resolução temporal da série de mercado."""

    AUTO = "auto"
    DIA = "dia"
    SEMANA = "semana"
    MES = "mes"


@dataclass(frozen=True)
class SourceRef:
    """Referência de origem de um dado de mercado."""

    fonte: str
    url: str | None = None
    unidade: str = ""
    metodo: str = METODO_OFICIAL
    extraido_em: str = ""


@dataclass(frozen=True)
class MarketQuote:
    """Um ponto de mercado com proveniência explícita."""

    data: str
    ativo: str
    valor: float
    unidade: str
    origem: str
    metodo: str = METODO_OFICIAL
    extraido_em: str = ""
    defasagem_horas: float | None = None

    @property
    def defasado(self: MarketQuote) -> bool:
        """Return whether the quote reuses an older cached value."""
        return self.metodo == METODO_CACHE_DEFASADO


@dataclass(frozen=True)
class Bucket:
    """Agregação temporal OHLC de uma série de mercado."""

    inicio: str
    fim: str
    abertura: float
    minimo: float
    maximo: float
    fechamento: float
    ultimo: float

    @property
    def data(self: Bucket) -> str:
        """Return the bucket end date used as its representative date."""
        return self.fim


@dataclass(frozen=True)
class MarketSeries:
    """Série de mercado com resolução e proveniência."""

    ativo: str
    unidade: str
    resolucao: Resolution
    pontos: tuple[MarketQuote, ...] = ()
    origem: str = ""
    metodo: str = METODO_OFICIAL
    extraido_em: str = ""

    @property
    def vazia(self: MarketSeries) -> bool:
        """Return whether the series has no points."""
        return not self.pontos

    @property
    def defasada(self: MarketSeries) -> bool:
        """Return whether any point reuses a stale cached value."""
        return any(point.defasado for point in self.pontos)


@dataclass(frozen=True)
class ForecastBand:
    """Banda de incerteza de um cenário."""

    nivel: int
    inferior: float
    superior: float


@dataclass(frozen=True)
class ForecastPoint:
    """Ponto mensal de um cenário de preço."""

    data: str
    ativo: str
    cenario: str
    metodo: str
    centro: float
    bandas: tuple[ForecastBand, ...] = ()

    def banda(self: ForecastPoint, nivel: int) -> ForecastBand | None:
        """Return the band for ``nivel`` or ``None`` when absent."""
        for band in self.bandas:
            if band.nivel == nivel:
                return band
        return None


@dataclass(frozen=True)
class PolicyIndicators:
    """Sinais determinísticos de política cambial."""

    premio_termo: float | None = None
    premio_dol: float | None = None
    gap_focus: float | None = None
    vol30: float | None = None
    vol90: float | None = None
    regime: bool | None = None
    limiar_regime: float | None = None
    referencia: str | None = None

    @property
    def vazio(self: PolicyIndicators) -> bool:
        """Return whether no signal was computed."""
        return all(
            value is None
            for value in (
                self.premio_termo,
                self.premio_dol,
                self.gap_focus,
                self.vol30,
                self.vol90,
                self.regime,
            )
        )
