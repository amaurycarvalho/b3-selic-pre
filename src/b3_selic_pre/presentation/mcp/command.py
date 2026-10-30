"""Composição do subcomando ``mcp``, incluindo a preparação opcional."""

from __future__ import annotations

import sys
from collections.abc import Callable

from b3_selic_pre.presentation.cli_commands import load_update
from b3_selic_pre.presentation.cli_data import resolve_data
from b3_selic_pre.presentation.mcp.server import McpServer
from b3_selic_pre.presentation.settings import Settings


def _progress(current: int, total: int) -> None:
    print(
        f"Preparando dados... ({current}/{total} datas)",
        file=sys.stderr,
    )


def _source(source: str) -> None:
    print(f"Fonte: {source}", file=sys.stderr)


def run_mcp_command(
    args: object,
    settings: Settings,
    cache: object,
    client_factory: Callable[[], object],
    lock_factory: Callable[[], object],
    settings_factory: Callable[[], Settings] = Settings,
    tesouro_cache: object | None = None,
    tesouro_cache_factory: object | None = None,
    market_services: object | None = None,
    reserves_services: object | None = None,
) -> int:
    """Prepare data when requested and run the MCP stdio server."""
    if getattr(args, "atualizar", False) or getattr(args, "data", None) is not None:
        try:
            data = resolve_data(getattr(args, "data", None))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        try:
            with lock_factory():
                records, _historical = load_update(
                    client_factory(),
                    data,
                    no_cache=False,
                    source_callback=_source,
                    progress_callback=_progress,
                )
                if not records:
                    print(
                        f"Nenhum registro encontrado para {data}.",
                        file=sys.stderr,
                    )
                    return 1
                settings["data_referencia"] = data
        except Exception as exc:
            print(f"Falha na preparação: {exc}", file=sys.stderr)
            return 1
    return McpServer(
        cache=cache,
        settings_factory=settings_factory,
        tesouro_cache=tesouro_cache,
        tesouro_cache_factory=tesouro_cache_factory,
        market_services=market_services,
        reserves_services=reserves_services,
    ).run()
