"""View-model headless com o estado derivado da interface gráfica."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from b3_selic_pre.application.use_cases import build_export_text, rate_statistics
from b3_selic_pre.domain.models import RateRecord


def historical_status(
    historical_data: dict[str, list[RateRecord]],
    source: str,
    timestamp: str,
) -> tuple[str, str]:
    """Monta a mensagem e o tipo de status do carregamento histórico."""
    available = [date for date, records in historical_data.items() if records]
    missing = sorted(
        date for date, records in historical_data.items() if not records
    )
    total = sum(len(records) for records in historical_data.values())
    if missing:
        message = (
            f"Dados históricos carregados: {len(available)} datas, "
            f"{total} registros; indisponíveis: {', '.join(missing)}.  |  "
            f"{source}  |  {timestamp}"
        )
        return message, "warning" if available else "error"
    message = (
        f"Dados históricos carregados: {len(available)} datas, "
        f"{total} registros.  |  {source}  |  {timestamp}"
    )
    return message, "success"


class ChartMode(str, Enum):
    """Modo de renderização selecionado a partir do estado da interface."""

    RAW = "raw"
    CONSOLIDATED = "consolidated"
    EVOLUTION_3D_CONSOLIDATED = "evolution-3d-consolidated"
    EVOLUTION_3D_DETAILED = "evolution-3d-detailed"
    EVOLUTION_CURVE = "evolution-curve"
    EVOLUTION_DETAILED = "evolution-detailed"


@dataclass(frozen=True)
class ControlState:
    """Estado de habilitação dos controles da janela."""

    copy_enabled: bool
    view_enabled: bool
    evolution_enabled: bool
    analysis_enabled: bool
    three_d_enabled: bool


@dataclass
class GuiViewModel:
    """Calcula estatísticas, exportação, controles e modo de gráfico sem Tk."""

    records: list[RateRecord] = field(default_factory=list)
    historical_data: dict[str, list[RateRecord]] | None = None
    view_mode: str = "raw"
    evolution_active: bool = False
    show_3d: bool = False
    reference_date: str = ""

    @property
    def has_single(self: GuiViewModel) -> bool:
        """Indica se há registros da data selecionada."""
        return bool(self.records)

    @property
    def has_historical(self: GuiViewModel) -> bool:
        """Indica se há pelo menos uma data histórica com registros."""
        return bool(self.historical_data) and any(
            bool(records) for records in self.historical_data.values()
        )

    @property
    def has_any(self: GuiViewModel) -> bool:
        """Indica se há qualquer dado que permita exportação."""
        return self.has_single or self.has_historical

    @property
    def controls(self: GuiViewModel) -> ControlState:
        """Estado de habilitação dos controles derivado dos dados atuais."""
        return ControlState(
            copy_enabled=self.has_any,
            view_enabled=self.has_single,
            evolution_enabled=self.has_single,
            analysis_enabled=self.has_single,
            three_d_enabled=self.evolution_active and self.has_historical,
        )

    @property
    def stats_text(self: GuiViewModel) -> str:
        """Texto de estatísticas exibido acima do gráfico."""
        stats = rate_statistics(self.records)
        if stats is None:
            return ""
        return (
            f"Data: {self.reference_date} | Maior: {stats.max_rate:.2f}% | "
            f"Menor: {stats.min_rate:.2f}%"
        )

    @property
    def export_text(self: GuiViewModel) -> str | None:
        """CSV que deve ser copiado para a área de transferência."""
        historical = self.historical_data if self.has_historical else None
        return build_export_text(
            self.records,
            historical_data=historical,
            view_mode=self.view_mode,
            evolution_active=self.evolution_active,
        )

    @property
    def chart_mode(self: GuiViewModel) -> ChartMode:
        """Modo de gráfico que a GUI deve renderizar."""
        if self.evolution_active and self.has_historical:
            if self.show_3d:
                if self.view_mode == "consolidated":
                    return ChartMode.EVOLUTION_3D_CONSOLIDATED
                return ChartMode.EVOLUTION_3D_DETAILED
            if self.view_mode == "consolidated":
                return ChartMode.EVOLUTION_CURVE
            return ChartMode.EVOLUTION_DETAILED
        if self.view_mode == "consolidated":
            return ChartMode.CONSOLIDATED
        return ChartMode.RAW
