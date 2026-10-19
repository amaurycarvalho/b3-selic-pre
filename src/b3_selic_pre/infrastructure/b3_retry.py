"""Retry helpers for B3 responses that arrive empty."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from b3_selic_pre.application.errors import CommunicationError

EMPTY_RETRY_ATTEMPTS = 6
EMPTY_RETRY_BACKOFF_SECONDS = (0.5, 1.0, 2.0, 4.0, 4.0)

_T = TypeVar("_T")


def retry_empty(
    operation: Callable[[], _T],
    *,
    date: str,
    source: str,
    result_is_empty: Callable[[_T], bool],
    attempts: int = EMPTY_RETRY_ATTEMPTS,
    backoff: tuple[float, ...] = EMPTY_RETRY_BACKOFF_SECONDS,
    sleep: Callable[[float], object] = time.sleep,
    random_fn: Callable[[], float] = random.random,
) -> _T:
    """Retry an operation while it keeps returning an empty result."""
    for attempt in range(attempts):
        result = operation()
        if not result_is_empty(result):
            return result
        if attempt < attempts - 1:
            ceiling = backoff[min(attempt, len(backoff) - 1)]
            sleep(ceiling * random_fn())
    raise CommunicationError(
        f"{source} retornou resposta vazia para {date} "
        f"após {attempts} tentativas."
    )
