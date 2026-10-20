"""Consulta best-effort da última release publicada no GitHub."""

from __future__ import annotations

import json
import urllib.request

from b3_selic_pre.application.about import normalize_version

RELEASE_API_URL = (
    "https://api.github.com/repos/amaurycarvalho/b3-selic-pre/releases/latest"
)
USER_AGENT = "b3-selic-pre"
TIMEOUT_SECONDS = 5


def _payload_version(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    return normalize_version(payload.get("tag_name"))


def fetch_latest_version(timeout: float = TIMEOUT_SECONDS) -> str | None:
    """Return the latest release version, or ``None`` on any failure."""
    request = urllib.request.Request(
        RELEASE_API_URL, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return None
            body = response.read()
    except (OSError, ValueError):
        return None
    try:
        payload = json.loads(body)
    except (TypeError, ValueError):
        return None
    return _payload_version(payload)
