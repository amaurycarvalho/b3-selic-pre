"""Descoberta da edição mais recente do BTD a partir da página pública."""

from __future__ import annotations

import re
import urllib.parse
from datetime import date

from b3_selic_pre.application.tesouro import TesouroDataError, normalizar_texto
from b3_selic_pre.infrastructure.tesouro_btd_html import ParsedPage, parse_html
from b3_selic_pre.infrastructure.tesouro_btd_types import BtdEdition

_EDITION = re.compile(
    r"/balanco-do-tesouro-direto-btd/(\d{4})/(\d{1,2})(?:[/?#]|$)",
    re.IGNORECASE,
)
_PUBLISHED_TEXT = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_ATTACHMENT_PATH = "/publicacao-anexo/"
_NON_SPREADSHEET = (".pdf", ".doc", ".docx", ".odt", ".html", ".htm")


def _month_from_url(url: str) -> tuple[str, str] | None:
    path = urllib.parse.urlparse(url).path
    match = _EDITION.search(path)
    if match is None:
        return None
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return f"{year:04d}-{month:02d}", url


def _latest_edition(urls: list[str]) -> tuple[str, str] | None:
    found = [item for item in map(_month_from_url, urls) if item]
    if not found:
        return None
    return max(found, key=lambda item: item[0])


def _looks_xlsx(href: str, text: str) -> bool:
    return ".xlsx" in f"{href} {text}".casefold()


def _is_non_spreadsheet(href: str, text: str) -> bool:
    combined = f"{href} {text}".casefold()
    return any(suffix in combined for suffix in _NON_SPREADSHEET)


def _xlsx_candidates(
    page: ParsedPage,
) -> list[tuple[str, str]]:
    return [
        (href, text) for href, text in page.links if _looks_xlsx(href, text)
    ]


def _attachment_candidates(
    page: ParsedPage,
) -> list[tuple[str, str]]:
    return [
        (href, text)
        for href, text in page.links
        if _ATTACHMENT_PATH in urllib.parse.urlparse(href).path
        and not _is_non_spreadsheet(href, text)
    ]


def _attachment(page: ParsedPage) -> str | None:
    candidates = _xlsx_candidates(page) or _attachment_candidates(page)
    if not candidates:
        return None
    preferred = [
        item
        for item in candidates
        if "anexo" in normalizar_texto(item[1])
    ]
    selected = preferred or candidates
    if len(selected) > 1:
        raise TesouroDataError("Página do BTD com mais de um anexo XLSX.")
    return selected[0][0]


def _published_from_text(page: ParsedPage) -> str | None:
    if page.published_at:
        return page.published_at
    for _href, text in page.links:
        match = _PUBLISHED_TEXT.search(text)
        if match is None:
            continue
        day, month, year = match.groups()
        try:
            return date(int(year), int(month), int(day)).isoformat()
        except ValueError:
            continue
    return None


def parse_btd_page(data: bytes, page_url: str) -> BtdEdition:
    """Extract edition month, publication date and XLSX link from the page."""
    page = parse_html(data)
    urls = [page_url]
    if page.canonical:
        urls.append(page.canonical)
    urls.extend(href for href, _text in page.links)
    edition = _latest_edition(urls)
    if edition is None:
        raise TesouroDataError("Página do BTD sem edição identificável.")
    reference_month, edition_url = edition
    attachment = _attachment(page)
    if attachment is None:
        raise TesouroDataError("Publicação do BTD sem anexo XLSX.")
    return BtdEdition(
        reference_month=reference_month,
        published_at=_published_from_text(page),
        page_url=urllib.parse.urljoin(page_url, edition_url),
        attachment_url=urllib.parse.urljoin(page_url, attachment),
    )


__all__ = ["parse_btd_page"]
