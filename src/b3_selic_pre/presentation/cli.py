"""Interface de linha de comando do b3-selic-pre."""

from __future__ import annotations

import argparse
import logging
import shlex
import sys
import time
from datetime import datetime
from pathlib import Path

from b3_selic_pre import __version__
from b3_selic_pre.infrastructure.action_lock import ActionLock
from b3_selic_pre.infrastructure.cached_client import CachedB3Client
from b3_selic_pre.infrastructure.desktop import create_shortcut
from b3_selic_pre.infrastructure.disk_cache import DiskCache
from b3_selic_pre.infrastructure.logging_setup import (
    LOG_ACTIVE_NAME,
    configure_logging,
    configure_stderr_logging,
    log_dir,
)
from b3_selic_pre.infrastructure.tesouro_cache import (
    TesouroCache,
    default_tesouro_lock_path,
)
from b3_selic_pre.infrastructure.tesouro_cached_client import (
    TesouroDiretoClient,
)
from b3_selic_pre.presentation import cli_commands, cli_parser
from b3_selic_pre.presentation.logging_utils import (
    communication_exit_code,
    install_exception_hooks,
    log_invocation,
)
from b3_selic_pre.presentation.settings import Settings

_SHORTCUT_MESSAGE = "Atalho criado em ~/Desktop/ e ~/.local/share/applications/"
_TESOURO_HANDLERS = {
    "tesouro": "tesouro",
    "tesouro-resgates": "tesouro_resgates",
    "tesouro-estoque": "tesouro_estoque",
}


def launch_gui(*args: object, **kwargs: object) -> None:
    """Importa e inicia a GUI apenas quando o modo gráfico é solicitado."""
    from b3_selic_pre.presentation.gui import launch_gui as _launch_gui

    _launch_gui(*args, **kwargs)


def _wait_message() -> None:
    print("Aguardando outra ação de dados...", file=sys.stderr)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Interpreta os argumentos da linha de comando e retorna as opções."""
    return cli_parser.parse_args(argv)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _exit_code(code: object) -> int:
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    return 1


def _command_hint(argv: list[str]) -> str:
    if not argv:
        return "gui"
    first = argv[0]
    if first in cli_parser.SUBCOMMANDS:
        return first
    if first in ("--help", "-h"):
        return "help"
    if first == "--version":
        return "version"
    return "desconhecido"


def _format_argv(argv: list[str]) -> str:
    return shlex.join(argv) if argv else "(nenhum)"


def _format_args(args: argparse.Namespace) -> str:
    pairs = []
    for key, value in sorted(vars(args).items()):
        if key == "comando" or value is None or value is False:
            continue
        pairs.append(key if value is True else f"{key}={value}")
    return " ".join(pairs) if pairs else "(nenhum)"


def _log_startup(
    logger: logging.Logger, active_log: Path | None, mode: str
) -> None:
    if active_log is not None:
        logger.info(
            "Iniciando b3-selic-pre %s (%s); log em %s",
            __version__,
            mode,
            active_log,
        )
    else:
        logger.info("Iniciando b3-selic-pre %s (%s)", __version__, mode)


def _log_text(active_log: Path | None) -> str | None:
    path = active_log or (log_dir() / LOG_ACTIVE_NAME)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _run_mcp(args: argparse.Namespace, settings: Settings) -> int:
    from b3_selic_pre.infrastructure.market import build_market_services
    from b3_selic_pre.presentation.mcp.command import run_mcp_command

    return run_mcp_command(
        args,
        settings,
        cache=DiskCache(),
        client_factory=CachedB3Client,
        lock_factory=lambda: ActionLock(on_wait=_wait_message),
        tesouro_cache=TesouroCache(),
        tesouro_cache_factory=lambda resource: TesouroCache(resource=resource),
        market_services=build_market_services(),
    )


def _dispatch_tesouro(
    args: argparse.Namespace, handler: object
) -> int:
    try:
        with ActionLock(
            path=default_tesouro_lock_path(), on_wait=_wait_message
        ):
            return handler(args, TesouroDiretoClient())
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _dispatch_mercado(args: argparse.Namespace) -> int:
    from b3_selic_pre.infrastructure.market import build_market_services
    from b3_selic_pre.presentation.market_tab import MarketTabController

    return cli_commands.mercado(
        args, MarketTabController(build_market_services())
    )


def _dispatch_curve(
    args: argparse.Namespace, settings: Settings, active_log: Path | None
) -> int | None:
    if args.comando == "consultar":
        return cli_commands.consultar(args, CachedB3Client())
    if args.comando == "atualizar":
        try:
            with ActionLock(on_wait=_wait_message):
                return cli_commands.atualizar(
                    args, settings, CachedB3Client()
                )
        except TimeoutError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if args.comando == "exportar":
        log_content = _log_text(active_log) if args.log else None
        return cli_commands.exportar(
            args, settings, CachedB3Client(), log_content
        )
    return None


def _dispatch_other(
    args: argparse.Namespace, settings: Settings, active_log: Path | None
) -> int | None:
    if args.comando in _TESOURO_HANDLERS:
        handler = getattr(cli_commands, _TESOURO_HANDLERS[args.comando])
        return _dispatch_tesouro(args, handler)
    if args.comando == "mercado":
        return _dispatch_mercado(args)
    if args.comando == "mcp":
        return _run_mcp(args, settings)
    if args.comando == "criar-atalho":
        create_shortcut()
        print(_SHORTCUT_MESSAGE)
        return 0
    if args.comando == "gui":
        launch_gui(settings=settings, active_log=active_log, configure=False)
        return 0
    return None


def _dispatch(
    args: argparse.Namespace, settings: Settings, active_log: Path | None
) -> int:
    for dispatcher in (_dispatch_curve, _dispatch_other):
        code = dispatcher(args, settings, active_log)
        if code is not None:
            return code
    print("Informe um subcomando. Use --help para ver as opções.", file=sys.stderr)
    return 2



def _configure_logging_mode(
    argv: list[str], settings: Settings
) -> Path | None:
    """Configure file logging or stderr-only logging for MCP."""
    # MCP must not create or write the active file log while serving.
    if argv and argv[0] == "mcp":
        configure_stderr_logging()
        return None
    return configure_logging(
        retention_days=settings.log_retention_days()
    )


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI: despacha subcomandos e registra a invocação."""
    if argv is None:
        argv = sys.argv[1:]
    settings = Settings()
    # The MCP command has its own logging contract; all others share the file log.
    active_log = _configure_logging_mode(argv, settings)
    logger = logging.getLogger(__name__)
    install_exception_hooks(logger)
    mode = "GUI" if not argv or argv[0] == "gui" else "CLI"
    _log_startup(logger, active_log, mode)
    inicio = _now_iso()
    started = time.monotonic()
    comando = _command_hint(argv)
    argumentos = _format_argv(argv)
    codigo = 0
    try:
        if not argv:
            launch_gui(
                settings=settings,
                active_log=active_log,
                configure=False,
            )
            return 0
        args = parse_args(argv)
        comando = args.comando or "gui"
        argumentos = _format_args(args)
        codigo = _dispatch(args, settings, active_log)
        return codigo
    except SystemExit as exc:
        codigo = _exit_code(exc.code)
        return codigo
    except Exception as exc:
        codigo = 1
        code = communication_exit_code(logger, exc)
        if code is not None:
            return code
        raise
    finally:
        log_invocation(
            logger,
            comando,
            argumentos,
            inicio,
            _now_iso(),
            time.monotonic() - started,
            codigo,
        )
