"""Leitura restrita do HTML da publicação BTD."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser


@dataclass(frozen=True)
class ParsedPage:
    """Links, canonical e data de publicação extraídos da página."""

    links: tuple[tuple[str, str], ...]
    canonical: str | None
    published_at: str | None


class _BtdPageParser(HTMLParser):
    """Coleta apenas links, data de publicação e canonical da página."""

    def __init__(self: _BtdPageParser) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.canonical: str | None = None
        self.published_at: str | None = None
        self._href: str | None = None
        self._text: list[str] = []

    def _start_link(self: _BtdPageParser, values: dict[str, str]) -> None:
        self._href = values.get("href", "")
        self._text = []

    def _read_canonical(
        self: _BtdPageParser, values: dict[str, str]
    ) -> None:
        if "canonical" in values.get("rel", "").lower():
            self.canonical = values.get("href") or None

    def _read_time(self: _BtdPageParser, values: dict[str, str]) -> None:
        if not self.published_at:
            self.published_at = _iso_date(values.get("datetime", ""))

    def _read_meta(self: _BtdPageParser, values: dict[str, str]) -> None:
        if self.published_at:
            return
        family = (
            values.get("property", "") + values.get("name", "")
        ).lower()
        if "published" in family or "publish" in family:
            self.published_at = _iso_date(values.get("content", ""))

    def handle_starttag(
        self: _BtdPageParser, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {name: value or "" for name, value in attrs}
        handlers = {
            "a": self._start_link,
            "link": self._read_canonical,
            "time": self._read_time,
            "meta": self._read_meta,
        }
        handler = handlers.get(tag)
        if handler is not None:
            handler(values)

    def handle_data(self: _BtdPageParser, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self: _BtdPageParser, tag: str) -> None:
        if tag != "a" or self._href is None:
            return
        text = " ".join("".join(self._text).split())
        self.links.append((self._href, text))
        self._href = None
        self._text = []


def _iso_date(value: str) -> str | None:
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def parse_html(data: bytes) -> ParsedPage:
    """Parse the publication page without interpreting page content."""
    parser = _BtdPageParser()
    parser.feed(_decode(data))
    return ParsedPage(
        tuple(parser.links),
        parser.canonical,
        parser.published_at,
    )


__all__ = ["ParsedPage", "parse_html"]
