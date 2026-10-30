"""Modelos puros das reservas internacionais brasileiras."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

ATIVO_RESERVAS = "reservas"
FONTE_RESERVAS = "BCB SGS 13621"
UNIDADE_RESERVAS = "USD_milhoes"
UNIDADE_RESERVAS_BILHOES = "USD_bilhoes"
METODO_RESERVAS = "oficial"


class ReservesRegime(StrEnum):
    """Sinal direcional determinístico das reservas."""

    AUMENTO = "aumento"
    ESTAVEL = "estavel"
    DETERIORACAO = "deterioracao"


@dataclass(frozen=True)
class ReservesThresholds:
    """Limiares configuráveis do regime de reservas."""

    var_aumento: float = 2.0
    var_deterioracao: float = -2.0
    drawdown: float = -3.0
    media_dias: int = 90

    @classmethod
    def from_mapping(
        cls: type[ReservesThresholds], data: dict | None = None
    ) -> ReservesThresholds:
        """Build the regime thresholds from a plain mapping."""
        values = data or {}
        return cls(
            var_aumento=float(values.get("var_aumento", 2.0)),
            var_deterioracao=float(
                values.get("var_deterioracao", -2.0)
            ),
            drawdown=float(values.get("drawdown", -3.0)),
            media_dias=int(values.get("media_dias", 90)),
        )

    @property
    def limiar_aumento(self: ReservesThresholds) -> float:
        """Return the 3-month variation threshold for growth."""
        return self.var_aumento

    @property
    def limiar_deterioracao(self: ReservesThresholds) -> float:
        """Return the 3-month variation threshold for deterioration."""
        return self.var_deterioracao

    @property
    def limiar_drawdown(self: ReservesThresholds) -> float:
        """Return the 12-month drawdown threshold."""
        return self.drawdown

    def as_dict(self: ReservesThresholds) -> dict[str, float | int]:
        """Serialize the thresholds used by the regime."""
        return {
            "var_aumento": self.var_aumento,
            "var_deterioracao": self.var_deterioracao,
            "drawdown": self.drawdown,
            "media_dias": self.media_dias,
        }


@dataclass(frozen=True)
class ReservesIndicators:
    """Indicadores de direção e nível das reservas.

    Níveis são expressos em US$ bilhões; variações, tendência, drawdown e
    posição na faixa usam percentual ou fração explícita. Métricas sem
    histórico suficiente permanecem ``None``.
    """

    nivel_atual: float | None = None
    var_1m: float | None = None
    var_3m: float | None = None
    var_12m: float | None = None
    tendencia_90d: float | None = None
    drawdown_12m: float | None = None
    posicao_faixa_12m: float | None = None
    media_90d: float | None = None
    max_12m: float | None = None
    min_12m: float | None = None
    regime: ReservesRegime | None = None
    thresholds: ReservesThresholds | None = None
    referencia: str | None = None
    unidade: str = UNIDADE_RESERVAS_BILHOES

    @property
    def vazio(self: ReservesIndicators) -> bool:
        """Return whether no metric was computed."""
        return all(
            value is None
            for value in (
                self.nivel_atual,
                self.var_1m,
                self.var_3m,
                self.var_12m,
                self.tendencia_90d,
                self.drawdown_12m,
                self.posicao_faixa_12m,
            )
        )


__all__ = [
    "ATIVO_RESERVAS",
    "FONTE_RESERVAS",
    "METODO_RESERVAS",
    "UNIDADE_RESERVAS",
    "UNIDADE_RESERVAS_BILHOES",
    "ReservesIndicators",
    "ReservesRegime",
    "ReservesThresholds",
]
