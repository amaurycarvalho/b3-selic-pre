"""Classificação de falhas e hooks de logging da camada de apresentação."""

from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Iterator
from types import TracebackType

from b3_selic_pre.application.errors import CommunicationError

_LOG_MARKER = "_b3_selic_logged"


def _iter_exception_chain(exc: BaseException) -> Iterator[BaseException]:
    stack = [exc]
    seen: set[int] = set()
    while stack:
        current = stack.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        cause = current.__cause__
        context = current.__context__
        if cause is not None:
            stack.append(cause)
        if context is not None and context is not cause:
            stack.append(context)


def is_communication_error(exc: BaseException) -> bool:
    """Return whether the exception chain contains a communication error."""
    return any(
        isinstance(item, CommunicationError)
        for item in _iter_exception_chain(exc)
    )


def _communication_origin(exc: BaseException) -> BaseException:
    for item in _iter_exception_chain(exc):
        if not isinstance(item, CommunicationError):
            continue
        cause = item.__cause__
        if cause is None:
            return item
        if isinstance(cause, CommunicationError):
            return _communication_origin(cause)
        return cause
    return exc


def _normalize_message(exc: BaseException) -> str:
    message = " ".join(str(exc).splitlines())
    return message or type(exc).__name__


def _mark_logged(exc: BaseException) -> None:
    try:
        setattr(exc, _LOG_MARKER, True)
    except (AttributeError, TypeError):
        pass


def was_logged(exc: BaseException | None) -> bool:
    """Return whether the exception was already logged."""
    return bool(getattr(exc, _LOG_MARKER, False))


def log_exception(
    logger: logging.Logger,
    exc: BaseException,
    context: str,
) -> None:
    """Log an exception, keeping communication failures on a single line."""
    if is_communication_error(exc):
        origin = _communication_origin(exc)
        logger.error(
            "%s: %s: %s",
            context,
            type(origin).__name__,
            _normalize_message(origin),
        )
    else:
        logger.error(
            context,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
    _mark_logged(exc)


def log_exception_once(
    logger: logging.Logger,
    exc: BaseException,
    context: str,
) -> None:
    """Log an exception only when it was not logged before."""
    if was_logged(exc):
        return
    log_exception(logger, exc, context)


def _log_uncaught(
    logger: logging.Logger,
    exc: BaseException | None,
    context: str,
) -> None:
    if exc is None or was_logged(exc):
        return
    log_exception(logger, exc, context)


def log_invocation(
    logger: logging.Logger,
    comando: str,
    argumentos: str,
    inicio: str,
    fim: str,
    duracao: float,
    codigo_saida: int,
) -> None:
    """Registra uma única linha INFO com os metadados de uma invocação."""
    try:
        logger.info(
            "CLI comando=%s argumentos=%s inicio=%s fim=%s "
            "duracao=%.3fs codigo_saida=%s",
            comando,
            argumentos,
            inicio,
            fim,
            duracao,
            codigo_saida,
        )
    except Exception:
        return


def install_exception_hooks(logger: logging.Logger | None = None) -> None:
    """Install main-thread and secondary-thread exception hooks."""
    target = logger or logging.getLogger(__name__)
    previous_sys = sys.excepthook
    previous_thread = threading.excepthook

    def sys_hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        _log_uncaught(target, exc_value, "Exceção não tratada")
        if sys.stderr is not None:
            previous_sys(exc_type, exc_value, exc_tb)

    def thread_hook(args: threading.ExceptHookArgs) -> None:
        _log_uncaught(
            target,
            args.exc_value,
            "Exceção não tratada em thread",
        )
        if sys.stderr is not None:
            previous_thread(args)

    sys.excepthook = sys_hook
    threading.excepthook = thread_hook


def install_tk_exception_hook(
    root: object,
    logger: logging.Logger | None = None,
) -> None:
    """Install a Tk callback exception hook that writes to the application log."""
    target = logger or logging.getLogger(__name__)
    previous = getattr(root, "report_callback_exception", None)

    def tk_hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        _log_uncaught(
            target,
            exc_value,
            "Exceção não tratada em callback do Tk",
        )
        if sys.stderr is not None and callable(previous):
            previous(exc_type, exc_value, exc_tb)

    root.report_callback_exception = tk_hook


def communication_exit_code(
    logger: logging.Logger, exc: Exception
) -> int | None:
    """Log an exception and return 1 for communication failures, else None."""
    log_exception(logger, exc, "Erro ao executar comando")
    if is_communication_error(exc):
        print(f"Erro ao buscar dados: {exc}", file=sys.stderr)
        return 1
    return None
