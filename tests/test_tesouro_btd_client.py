from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.domain.models import EstoqueMensalTitulo
from b3_selic_pre.infrastructure.tesouro_btd import TesouroBtdClient
from b3_selic_pre.infrastructure.tesouro_btd_cache import TesouroBtdCache
from b3_selic_pre.infrastructure.tesouro_btd_types import BtdEdition
from tests.btd_fixtures import xlsx_bytes

NOW = datetime(2026, 10, 30, 12, tzinfo=UTC)
EDITION = BtdEdition(
    reference_month="2026-09",
    published_at="2026-10-29",
    page_url="https://example.test/btd/2026/9",
    attachment_url="https://example.test/anexo/1",
)
OLD_RECORD = EstoqueMensalTitulo(
    "Tesouro Selic 2029", "2026-08", Decimal("100000000")
)


def _metadata(checked_at: datetime = NOW):
    return {
        "reference_month": "2026-08",
        "published_at": "2026-09-29",
        "page_url": "https://example.test/btd/2026/8",
        "attachment_url": "https://example.test/anexo/0",
        "sha256": "old",
        "size_bytes": 10,
        "checked_at": checked_at.isoformat(),
    }


class FakeSource:
    def __init__(self, data=None, discovery_error=None, download_error=None):
        self.data = data if data is not None else xlsx_bytes()
        self.discovery_error = discovery_error
        self.download_error = download_error
        self.calls = []

    def discover(self):
        self.calls.append("discover")
        if self.discovery_error is not None:
            raise self.discovery_error
        return EDITION

    def download(self, edition):
        self.calls.append("download")
        if self.download_error is not None:
            raise self.download_error
        return self.data


def _client(tmp_path, source, now=NOW):
    cache = TesouroBtdCache(tmp_path)
    cache.save((OLD_RECORD,), _metadata())
    return TesouroBtdClient(cache=cache, source=source, now=lambda: now), cache


def test_fresh_cache_is_reused_without_network(tmp_path):
    source = FakeSource()
    client, _cache = _client(tmp_path, source)

    entry = client.refresh()

    assert entry.records == (OLD_RECORD,)
    assert source.calls == []


def test_expired_cache_is_updated_and_saved(tmp_path):
    source = FakeSource()
    expired = NOW - timedelta(hours=25)
    cache = TesouroBtdCache(tmp_path)
    cache.save((OLD_RECORD,), _metadata(expired))
    client = TesouroBtdClient(cache=cache, source=source, now=lambda: NOW)

    entry = client.refresh()

    assert source.calls == ["discover", "download"]
    assert entry.records != (OLD_RECORD,)
    assert cache.read().records == entry.records


def test_force_ignores_fresh_cache(tmp_path):
    source = FakeSource()
    client, _cache = _client(tmp_path, source)

    client.refresh(force=True)

    assert source.calls == ["discover", "download"]


def test_discovery_failure_keeps_previous_cache(tmp_path):
    source = FakeSource(discovery_error=TesouroDataError("sem edição"))
    client, cache = _client(tmp_path, source)

    with pytest.raises(TesouroDataError):
        client.refresh(force=True)

    assert cache.read().records == (OLD_RECORD,)


def test_download_failure_keeps_previous_cache(tmp_path):
    source = FakeSource(download_error=TesouroDataError("anexo inválido"))
    client, cache = _client(tmp_path, source)

    with pytest.raises(TesouroDataError):
        client.refresh(force=True)

    assert cache.read().records == (OLD_RECORD,)


def test_parsing_failure_keeps_previous_cache(tmp_path):
    source = FakeSource(data=b"not a zip")
    client, cache = _client(tmp_path, source)

    with pytest.raises(TesouroDataError):
        client.refresh(force=True)

    assert cache.read().records == (OLD_RECORD,)


def test_saved_cache_has_provenance_metadata(tmp_path):
    source = FakeSource()
    client, cache = _client(tmp_path, source)

    entry = client.refresh(force=True)
    metadata = entry.metadata

    assert metadata["reference_month"] == "2026-09"
    assert metadata["published_at"] == "2026-10-29"
    assert metadata["page_url"] == EDITION.page_url
    assert metadata["attachment_url"] == EDITION.attachment_url
    assert len(str(metadata["sha256"])) == 64
