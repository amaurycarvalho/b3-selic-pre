"""Configuração headless dos serviços de mercado."""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 1
DIAS_JANELA = 365
MESES_CENARIO = 12


@dataclass
class ResolutionConfig:
    """Limiares de recência que definem a resolução em camadas."""

    diario_dias: int = 14
    semanal_dias: int = 90

    @classmethod
    def from_mapping(
        cls: type[ResolutionConfig], data: dict | None = None
    ) -> ResolutionConfig:
        """Build the resolution thresholds from a mapping."""
        values = data or {}
        return cls(
            diario_dias=values.get("diario_dias", 14),
            semanal_dias=values.get("semanal_dias", 90),
        )


@dataclass
class ProjectionConfig:
    """Parâmetros determinísticos do cenário e dos sinais."""

    meses: int = MESES_CENARIO
    janela_dias: int = DIAS_JANELA
    drift_shrink: float = 0.5
    ewma_lambda: float = 0.94
    z80: float = 1.2816
    z95: float = 1.96
    min_retornos: int = 20
    vol_curta: int = 30
    vol_longa: int = 90
    regime_ratio: float = 1.5
    dias_uteis_ano: int = 252
    dol_dias_vencimento: int = 30

    @classmethod
    def from_mapping(
        cls: type[ProjectionConfig], data: dict | None = None
    ) -> ProjectionConfig:
        """Build the projection parameters from a mapping."""
        values = data or {}
        return cls(
            meses=values.get("meses", MESES_CENARIO),
            janela_dias=values.get("janela_dias", DIAS_JANELA),
            drift_shrink=values.get("drift_shrink", 0.5),
            ewma_lambda=values.get("ewma_lambda", 0.94),
            z80=values.get("z80", 1.2816),
            z95=values.get("z95", 1.96),
            min_retornos=values.get("min_retornos", 20),
            vol_curta=values.get("vol_curta", 30),
            vol_longa=values.get("vol_longa", 90),
            regime_ratio=values.get("regime_ratio", 1.5),
            dias_uteis_ano=values.get("dias_uteis_ano", 252),
            dol_dias_vencimento=values.get("dol_dias_vencimento", 30),
        )


@dataclass
class CacheTtlConfig:
    """TTLs por recência do cache bruto de mercado."""

    recente_minutos: int = 20
    mes_horas: int = 3
    retencao_anos: int = 3

    @classmethod
    def from_mapping(
        cls: type[CacheTtlConfig], data: dict | None = None
    ) -> CacheTtlConfig:
        """Build the cache TTL configuration from a mapping."""
        values = data or {}
        return cls(
            recente_minutos=values.get("recente_minutos", 20),
            mes_horas=values.get("mes_horas", 3),
            retencao_anos=values.get("retencao_anos", 3),
        )


@dataclass
class MarketConfig:
    """Configuração completa dos serviços de mercado."""

    resolucao: ResolutionConfig = field(default_factory=ResolutionConfig)
    projecao: ProjectionConfig = field(default_factory=ProjectionConfig)
    cache: CacheTtlConfig = field(default_factory=CacheTtlConfig)
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_mapping(
        cls: type[MarketConfig], data: dict | None = None
    ) -> MarketConfig:
        """Build the market configuration from plain mappings."""
        values = data or {}
        return cls(
            resolucao=ResolutionConfig.from_mapping(values.get("resolucao")),
            projecao=ProjectionConfig.from_mapping(values.get("projecao")),
            cache=CacheTtlConfig.from_mapping(values.get("cache")),
            schema_version=values.get("schema_version", SCHEMA_VERSION),
        )

    def parametros_resolucao(self: MarketConfig) -> dict[str, object]:
        """Return the resolution parameters that affect the cache key."""
        return {
            "diario_dias": self.resolucao.diario_dias,
            "semanal_dias": self.resolucao.semanal_dias,
        }

    def parametros_projecao(self: MarketConfig) -> dict[str, object]:
        """Return the projection parameters that affect the cache key."""
        return {
            "meses": self.projecao.meses,
            "janela_dias": self.projecao.janela_dias,
            "drift_shrink": self.projecao.drift_shrink,
            "ewma_lambda": self.projecao.ewma_lambda,
            "z80": self.projecao.z80,
            "z95": self.projecao.z95,
            "min_retornos": self.projecao.min_retornos,
            "vol_curta": self.projecao.vol_curta,
            "vol_longa": self.projecao.vol_longa,
            "regime_ratio": self.projecao.regime_ratio,
            "dol_dias_vencimento": self.projecao.dol_dias_vencimento,
        }
