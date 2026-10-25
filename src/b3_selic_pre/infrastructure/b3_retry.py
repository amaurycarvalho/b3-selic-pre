"""Retry helpers for B3 requests that fail or return empty responses."""

from __future__ import annotations

import http.client
import random
import socket
import ssl
import time
import urllib.error
from collections.abc import Callable
from typing import TypeVar

from b3_selic_pre.application.errors import CommunicationError

EMPTY_RETRY_ATTEMPTS = 6
TRANSIENT_RETRY_ATTEMPTS = 3
EMPTY_RETRY_BACKOFF_SECONDS = (0.5, 1.0, 2.0, 4.0, 4.0)

TRANSIENT_ERRORS = (
    urllib.error.URLError,
    http.client.HTTPException,
    TimeoutError,
    ConnectionError,
    ssl.SSLError,
    socket.gaierror,
)

_T = TypeVar("_T")


def retry_empty(  # noqa: UP047
    operation: Callable[[], _T],
    *,
    date: str,
    source: str,
    result_is_empty: Callable[[_T], bool],
    attempts: int = EMPTY_RETRY_ATTEMPTS,
    transient_attempts: int = TRANSIENT_RETRY_ATTEMPTS,
    retry_on: tuple[type[BaseException], ...] = TRANSIENT_ERRORS,
    backoff: tuple[float, ...] = EMPTY_RETRY_BACKOFF_SECONDS,
    sleep: Callable[[float], object] = time.sleep,
    random_fn: Callable[[], float] = random.random,
) -> _T:
    """Retry empty results and transient failures with independent budgets."""
    empty_budget = attempts
    transient_budget = transient_attempts
    failures = 0
    last_error: BaseException | None = None
    while empty_budget > 0 and transient_budget > 0:
        try:
            result = operation()
        except retry_on as exc:
            transient_budget -= 1
            last_error = exc
        else:
            if not result_is_empty(result):
                return result
            empty_budget -= 1
            last_error = None
        failures += 1
        if empty_budget > 0 and transient_budget > 0:
            ceiling = backoff[min(failures - 1, len(backoff) - 1)]
            sleep(ceiling * random_fn())
    if last_error is not None:
        raise CommunicationError(
            f"{source} falhou para {date} após {transient_attempts} tentativas: "
            f"{last_error}"
        ) from last_error
    raise CommunicationError(
        f"{source} retornou resposta vazia para {date} "
        f"após {attempts} tentativas."
    )
