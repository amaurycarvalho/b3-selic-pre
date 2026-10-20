"""Informações institucionais e comparação de versões do diálogo Sobre."""

from __future__ import annotations

from dataclasses import dataclass

APP_NAME = "Taxas Referenciais SELIC (B3)"
LICENSE_TEXT = "Software livre e de código aberto (GNU GPLv3)"
DESCRIPTION = "Curva de juros (taxa referencial SELIC) conforme a B3."
REPOSITORY_URL = "https://github.com/amaurycarvalho/b3-selic-pre"
RELEASES_URL = f"{REPOSITORY_URL}/releases"

_VERSION_SEGMENTS = 3


@dataclass(frozen=True)
class AboutInfo:
    """Dados exibidos na janela de informações da aplicação."""

    name: str
    version: str
    release_date: str
    license_text: str
    description: str
    repository_url: str

    @property
    def title(self: AboutInfo) -> str:
        """Return the application name and version shown as the heading."""
        return f"{self.name} v{self.version}"


def build_about_info(version: str, release_date: str) -> AboutInfo:
    """Build the dialog metadata from the package version and release date."""
    return AboutInfo(
        name=APP_NAME,
        version=version,
        release_date=release_date,
        license_text=LICENSE_TEXT,
        description=DESCRIPTION,
        repository_url=REPOSITORY_URL,
    )


def normalize_version(value: str | None) -> str | None:
    """Normalize a version to ``X.Y.Z`` without a ``v`` prefix."""
    if value is None:
        return None
    text = value.strip()
    if text[:1] in {"v", "V"}:
        text = text[1:]
    parts = text.split(".")
    if not parts or len(parts) > _VERSION_SEGMENTS:
        return None
    if any(not part.isdigit() for part in parts):
        return None
    numbers = [int(part) for part in parts]
    numbers.extend([0] * (_VERSION_SEGMENTS - len(numbers)))
    return ".".join(str(number) for number in numbers)


def _version_key(value: str | None) -> tuple[int, int, int] | None:
    normalized = normalize_version(value)
    if normalized is None:
        return None
    first, second, third = normalized.split(".")
    return int(first), int(second), int(third)


def is_newer_version(current: str | None, candidate: str | None) -> bool:
    """Return whether ``candidate`` is a valid version newer than ``current``."""
    current_key = _version_key(current)
    candidate_key = _version_key(candidate)
    if current_key is None or candidate_key is None:
        return False
    return candidate_key > current_key


def new_version_notice(
    current_version: str | None,
    latest_version: str | None,
) -> str | None:
    """Return the update notice when a newer valid version is available."""
    latest = normalize_version(latest_version)
    if latest is None or not is_newer_version(current_version, latest):
        return None
    return f"Nova versão v{latest} disponível"


def release_page_url(version: str | None) -> str:
    """Return the release page URL for a version, falling back to releases."""
    normalized = normalize_version(version)
    if normalized is None:
        return f"{RELEASES_URL}/latest"
    return f"{RELEASES_URL}/tag/v{normalized}"
