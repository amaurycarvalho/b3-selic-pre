"""Serviços headless que montam os payloads estruturados do servidor MCP."""

from __future__ import annotations

from b3_selic_pre.application.analyze import CurvaJurosConfig
from b3_selic_pre.application.cli_services import (
    PrecomputedAnalysis,
    build_export_artifacts,
)
from b3_selic_pre.application.formatting import (
    format_detailed_evolution_csv,
    format_evolution_csv,
)
from b3_selic_pre.application.mcp_pagination import paginate
from b3_selic_pre.application.use_cases import (
    average_rate_by_year,
    consolidate_by_year,
    rate_statistics,
)
from b3_selic_pre.domain.models import RateRecord


class DomainError(Exception):
    """Erro de domínio recuperável devolvido como conteúdo estruturado."""

    def __init__(
        self: DomainError,
        motivo: str,
        detalhe: str,
        dica: str,
    ) -> None:
        """Crie um erro de domínio com motivo, detalhe e dica."""
        super().__init__(motivo, detalhe, dica)
        self.motivo = motivo
        self.detalhe = detalhe
        self.dica = dica

    def payload(self: DomainError) -> dict[str, str]:
        """Return the structured error envelope."""
        return {
            "motivo": self.motivo,
            "detalhe": self.detalhe,
            "dica": self.dica,
        }


def _rate(record: RateRecord) -> float:
    return float(record.rate.replace(",", "."))


def _with_cursor(payload: dict[str, object], next_cursor: str | None) -> dict[str, object]:
    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    return payload


def curve_items_curta(records: list[RateRecord]) -> list[dict[str, object]]:
    """Return numeric raw curve items preserving the original rate text."""
    return [
        {
            "du252": record.day252,
            "dc365": record.day360,
            "taxa": _rate(record),
            "taxa_texto": record.rate,
        }
        for record in records
    ]


def curve_items_longa(records: list[RateRecord]) -> list[dict[str, object]]:
    """Return one yearly item with min, max and average rates."""
    averages = average_rate_by_year(records)
    return [
        {
            "ano": row["year"],
            "menor_taxa": float(row["min_rate"]),
            "maior_taxa": float(row["max_rate"]),
            "taxa_media": float(averages[row["year"]]),
        }
        for row in consolidate_by_year(records)
    ]


def curve_payload(
    records: list[RateRecord],
    data: str,
    curva: str,
    cursor: str | None,
    limit: int | None,
) -> dict[str, object]:
    """Build the ``consultar_curva`` payload."""
    if not records:
        raise DomainError(
            "sem_dados",
            f"Não há registros em cache para {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    items = (
        curve_items_longa(records)
        if curva == "longa"
        else curve_items_curta(records)
    )
    page, next_cursor = paginate(items, cursor, limit)
    payload = {"data": data, "curva": curva, "itens": page}
    return _with_cursor(payload, next_cursor)


def missing_dates(
    historical: dict[str, list[RateRecord]] | None,
) -> list[str]:
    """Return dates without records, sorted."""
    return sorted(
        date_str
        for date_str, records in (historical or {}).items()
        if not records
    )


def _has_any(historical: dict[str, list[RateRecord]] | None) -> bool:
    return any(bool(records) for records in (historical or {}).values())


def export_payload(
    historical: dict[str, list[RateRecord]],
    data: str,
    curva: str,
) -> dict[str, object]:
    """Build the CSV export payload without writing files."""
    if not _has_any(historical):
        raise DomainError(
            "sem_dados",
            f"Não há registros em cache para a janela de {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    if curva == "longa":
        name = "curva-longa.csv"
        content = format_evolution_csv(historical)
    else:
        name = "curva-curta.csv"
        content = format_detailed_evolution_csv(historical)
    return {
        "nome": name,
        "content_type": "text/csv",
        "conteudo": content,
        "datas_indisponiveis": missing_dates(historical),
    }


def analysis_payload(
    records: list[RateRecord],
    historical: dict[str, list[RateRecord]],
    data: str,
    curva: str,
    config: CurvaJurosConfig | None = None,
    precomputed: PrecomputedAnalysis | None = None,
) -> dict[str, object]:
    """Build the analysis payload for the requested curve representation."""
    if not records:
        raise DomainError(
            "sem_dados",
            f"Não há registros em cache para {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    artifacts = build_export_artifacts(
        records,
        historical_data=historical,
        include_analise=True,
        config=config,
        analise_curva=curva,
        precomputed=precomputed,
    )
    analysis = next(
        (artifact for artifact in artifacts if artifact.name == "analise.txt"),
        None,
    )
    if analysis is None:
        raise DomainError(
            "sem_dados",
            f"Não foi possível gerar a análise para {data}.",
            "Verifique se há dados da curva e do histórico em cache.",
        )
    return {
        "data": data,
        "curva": curva,
        "texto": analysis.content,
        "datas_indisponiveis": missing_dates(historical),
    }


def evolution_item(data: str, records: list[RateRecord]) -> dict[str, object]:
    """Build one evolution summary item from a curve."""
    stats = rate_statistics(records)
    first = _rate(records[0])
    last = _rate(records[-1])
    return {
        "data": data,
        "total_registros": len(records),
        "menor_taxa": stats.min_rate if stats else None,
        "maior_taxa": stats.max_rate if stats else None,
        "taxa_curta": first,
        "taxa_longa": last,
        "inclinacao_bps": (last - first) * 100,
    }


def evolution_payload(
    historical: dict[str, list[RateRecord]],
    data: str,
    cursor: str | None,
    limit: int | None,
) -> dict[str, object]:
    """Build the structured evolution summary payload."""
    items = [
        evolution_item(date_str, records)
        for date_str, records in sorted(historical.items())
        if records
    ]
    if not items:
        raise DomainError(
            "sem_dados",
            f"Não há registros em cache para a janela de {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    page, next_cursor = paginate(items, cursor, limit)
    payload = {
        "data_base": data,
        "itens": page,
        "datas_indisponiveis": missing_dates(historical),
    }
    return _with_cursor(payload, next_cursor)


def statistics_payload(
    records: list[RateRecord],
    data: str,
    config: CurvaJurosConfig | None = None,
) -> dict[str, object]:
    """Build the statistics payload for one curve."""
    if not records:
        raise DomainError(
            "sem_dados",
            f"Não há registros em cache para {data}.",
            f"Execute `b3-selic-pre mcp --data {data}` para preparar o cache.",
        )
    stats = rate_statistics(records)
    first = _rate(records[0])
    last = _rate(records[-1])
    inflation = (config or CurvaJurosConfig()).expected_inflation
    return {
        "data": data,
        "total_registros": len(records),
        "menor_taxa": stats.min_rate if stats else None,
        "maior_taxa": stats.max_rate if stats else None,
        "taxa_curta": first,
        "taxa_longa": last,
        "inclinacao_bps": (last - first) * 100,
        "juro_real": first - inflation,
    }


def dates_payload(
    entries: list[object],
    cursor: str | None,
    limit: int | None,
) -> dict[str, object]:
    """Build the cached dates payload, newest first."""
    ordered = sorted(entries, key=lambda entry: entry.date, reverse=True)
    items = [
        {
            "data": entry.date,
            "total_registros": entry.count,
            "cached_at": entry.cached_at,
            "fonte": entry.source,
        }
        for entry in ordered
    ]
    page, next_cursor = paginate(items, cursor, limit)
    return _with_cursor({"itens": page}, next_cursor)


def reference_payload(
    data: str,
    origem: str,
    disponivel: bool,
    cached_at: str | None = None,
) -> dict[str, object]:
    """Build the ``data_referencia`` payload."""
    payload: dict[str, object] = {
        "data_referencia": data,
        "origem": origem,
        "disponivel": disponivel,
    }
    if cached_at is not None:
        payload["cached_at"] = cached_at
    return payload
