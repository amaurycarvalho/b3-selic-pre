"""Configuração headless dos serviços de reservas internacionais."""

from __future__ import annotations

from dataclasses import dataclass, field

from b3_selic_pre.domain.reserves import ReservesThresholds

SCHEMA_VERSION = 1
JANELA_PADRAO = "12m"
JANELAS = ("12m", "3a")
MESES_JANELA = {"12m": 12, "3a": 36}
DIAS_SOBREPOSICAO = 5
RETENCAO_ANOS = 3


def meses_janela(janela: str) -> int:
    """Return how many months a named window covers."""
    return MESES_JANELA.get(janela, MESES_JANELA[JANELA_PADRAO])


@dataclass
class ReservesConfig:
    """Janela, revisões, TTLs, retenção e limiares de reservas."""

    janela: str = JANELA_PADRAO
    sobreposicao_dias: int = DIAS_SOBREPOSICAO
    recente_minutos: int = 20
    mes_horas: int = 3
    retencao_anos: int = RETENCAO_ANOS
    thresholds: ReservesThresholds = field(
        default_factory=ReservesThresholds
    )
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(
        cls: type[ReservesConfig], data: dict | None = None
    ) -> ReservesConfig:
        """Build the reserves configuration from a plain mapping."""
        values = data or {}
        cache = values.get("cache")
        cache_values = cache if isinstance(cache, dict) else {}
        janela = str(values.get("janela", JANELA_PADRAO))
        if janela not in JANELAS:
            janela = JANELA_PADRAO
        return cls(
            janela=janela,
            sobreposicao_dias=int(
                values.get("sobreposicao_dias", DIAS_SOBREPOSICAO)
            ),
            recente_minutos=int(
                values.get(
                    "recente_minutos",
                    cache_values.get("recente_minutos", 20),
                )
            ),
            mes_horas=int(
                values.get("mes_horas", cache_values.get("mes_horas", 3))
            ),
            retencao_anos=int(
                values.get(
                    "retencao_anos",
                    cache_values.get("retencao_anos", RETENCAO_ANOS),
                )
            ),
            thresholds=ReservesThresholds.from_mapping(
                values.get("limiares") or values.get("thresholds")
            ),
            schema_version=int(values.get("schema_version", SCHEMA_VERSION)),
        )

    def meses(self: ReservesConfig) -> int:
        """Return the configured display window in months."""
        return meses_janela(self.janela)

    def parametros(self: ReservesConfig) -> dict[str, object]:
        """Return the parameters that affect the precomputed hash."""
        return {
            "schema_version": self.schema_version,
            "retencao_anos": self.retencao_anos,
            "limiares": self.thresholds.as_dict(),
        }


__all__ = [
    "DIAS_SOBREPOSICAO",
    "JANELAS",
    "JANELA_PADRAO",
    "MESES_JANELA",
    "RETENCAO_ANOS",
    "SCHEMA_VERSION",
    "ReservesConfig",
    "meses_janela",
]
