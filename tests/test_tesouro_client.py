import json
import urllib.error
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.infrastructure.cache_payload import write_atomic_bytes
from b3_selic_pre.infrastructure.tesouro_cache import (
    TesouroCache,
    is_current,
    ttl_for,
)
from b3_selic_pre.infrastructure.tesouro_cached_client import (
    TesouroDiretoClient,
)
from b3_selic_pre.infrastructure.tesouro_client import (
    TesouroDownload,
    TesouroResource,
    TesouroSourceClient,
)

HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Data de Liquidacao da Venda;"
    "PU;Quantidade;Valor"
)
CSV = (
    HEADER
    + "\nTesouro Selic 2029;02/01/2029;01/10/2026;15.000,00;2,00;30.000,00\n"
).encode()
RESOURCE = TesouroResource(
    dataset_name="vendas-do-tesouro-direto",
    dataset_id="dataset-id",
    resource_id="resource-id",
    resource_url="https://example.test/vendas.csv",
    last_modified="2026-10-16T10:29:05",
)


class FakeResponse:
    def __init__(self, body=b"", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def read(self, size=-1):
        if size is None or size < 0:
            chunk, self.body = self.body, b""
            return chunk
        chunk, self.body = self.body[:size], self.body[size:]
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        item = self.responses.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def _last_business_day(today):
    current = today
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def _metadata(**overrides):
    now = datetime.now(UTC).isoformat()
    data = {
        "schema_version": 1,
        "dataset_name": "vendas-do-tesouro-direto",
        "dataset_id": "dataset-id",
        "resource_id": "resource-id",
        "resource_url": "https://example.test/vendas.csv",
        "etag": "etag-1",
        "last_modified": "2026-10-16T10:29:05",
        "downloaded_at": now,
        "checked_at": now,
        "size_bytes": len(CSV),
        "sha256": "abc",
        "row_count": 1,
        "first_data_date": "2026-10-01",
        "last_data_date": date.today().isoformat(),
    }
    data.update(overrides)
    return data


class TestDiscovery:
    def test_discovers_single_csv(self):
        payload = {
            "success": True,
            "result": {
                "id": "dataset-id",
                "name": "vendas-do-tesouro-direto",
                "resources": [
                    {"id": "pdf", "format": "PDF", "url": "p"},
                    {
                        "id": "resource-id",
                        "format": "CSV",
                        "url": "https://example.test/vendas.csv",
                        "last_modified": "2026-10-16T10:29:05",
                    },
                ],
            },
        }
        opener = FakeOpener(
            [FakeResponse(json.dumps(payload).encode(), headers={})]
        )
        resource = TesouroSourceClient(opener=opener).discover()

        assert resource.resource_id == "resource-id"
        assert resource.resource_url == "https://example.test/vendas.csv"

    def test_success_false_is_data_error(self):
        opener = FakeOpener(
            [FakeResponse(json.dumps({"success": False}).encode())]
        )
        with pytest.raises(TesouroDataError):
            TesouroSourceClient(opener=opener).discover()

    @pytest.mark.parametrize(
        "resources",
        [[], [{"format": "CSV"}, {"format": "csv"}]],
    )
    def test_requires_exactly_one_csv(self, resources):
        payload = {
            "success": True,
            "result": {"resources": resources},
        }
        opener = FakeOpener([FakeResponse(json.dumps(payload).encode())])
        with pytest.raises(TesouroDataError, match="exatamente um"):
            TesouroSourceClient(opener=opener).discover()


class TestDownload:
    def test_valid_download(self):
        opener = FakeOpener([
            FakeResponse(
                CSV,
                headers={
                    "Content-Type": "text/csv",
                    "ETag": "etag-1",
                    "Last-Modified": "now",
                },
            )
        ])
        result = TesouroSourceClient(opener=opener).download(RESOURCE)

        assert result.status == 200
        assert result.data == CSV
        assert result.etag == "etag-1"

    def test_304_is_returned(self):
        error = urllib.error.HTTPError(
            "https://example.test", 304, "Not Modified", {}, None
        )
        opener = FakeOpener([error])
        result = TesouroSourceClient(opener=opener).download(
            RESOURCE, etag="etag-1"
        )

        assert result.status == 304
        assert result.data is None

    def test_empty_body_is_retried(self):
        opener = FakeOpener([
            FakeResponse(b"", headers={"Content-Type": "text/csv"}),
            FakeResponse(CSV, headers={"Content-Type": "text/csv"}),
        ])
        client = TesouroSourceClient(opener=opener, sleep=lambda _: None)
        assert client.download(RESOURCE).data == CSV

    def test_non_csv_after_retries_is_communication_error(self):
        responses = [
            FakeResponse(b"x", headers={"Content-Type": "application/json"})
            for _ in range(3)
        ]
        client = TesouroSourceClient(
            opener=FakeOpener(responses), sleep=lambda _: None
        )
        with pytest.raises(CommunicationError):
            client.download(RESOURCE)

    def test_partial_content_range_is_retried(self):
        headers = {
            "Content-Type": "text/csv",
            "Content-Range": "bytes 0-1/999",
        }
        responses = [FakeResponse(CSV, headers=headers) for _ in range(3)]
        client = TesouroSourceClient(
            opener=FakeOpener(responses), sleep=lambda _: None
        )
        with pytest.raises(CommunicationError):
            client.download(RESOURCE)

    def test_non_transient_http_error_is_not_retried(self):
        opener = FakeOpener([
            urllib.error.HTTPError(
                "https://example.test", 404, "Not Found", {}, None
            )
        ])
        with pytest.raises(CommunicationError):
            TesouroSourceClient(opener=opener).download(RESOURCE)


class TestCache:
    def test_save_and_read(self, tmp_path):
        cache = TesouroCache(tmp_path)
        metadata = _metadata()
        cache.save(CSV, metadata)

        data, stored = cache.read()

        assert data == CSV
        assert stored["row_count"] == 1

    def test_freshness_is_conditional(self, tmp_path):
        cache = TesouroCache(tmp_path)
        now = datetime(2026, 10, 19, 12, tzinfo=UTC)
        current = _metadata(last_data_date=_last_business_day(now.date()).isoformat())
        historical = _metadata(last_data_date="2020-01-01")

        assert is_current(current, now.date())
        assert not is_current(historical, now.date())
        assert ttl_for(current, now.date()) == timedelta(hours=1)
        assert ttl_for(historical, now.date()) == timedelta(hours=6)
        assert cache.is_fresh(current, now)
        assert cache.is_fresh(
            _metadata(
                last_data_date="2020-01-01",
                checked_at=(now - timedelta(hours=2)).isoformat(),
            ),
            now,
        )
        assert not cache.is_fresh(
            _metadata(
                last_data_date="2020-01-01",
                checked_at=(now - timedelta(hours=7)).isoformat(),
            ),
            now,
        )

    def test_corrupted_metadata_is_a_miss_without_deletion(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata())
        cache.metadata_path.write_text("not json", encoding="utf-8")

        assert cache.read() is None
        assert cache.metadata_path.exists()

    def test_update_checked_at(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata(checked_at="old"))
        updated = cache.update_checked_at(_metadata(checked_at="old"), "new")

        assert updated["checked_at"] == "new"
        assert cache.read()[1]["checked_at"] == "new"

    def test_write_atomic_bytes_creates_no_temp(self, tmp_path):
        target = tmp_path / "file.bin"
        write_atomic_bytes(target, b"data")

        assert target.read_bytes() == b"data"
        assert list(tmp_path.glob("*.tmp")) == []


class FakeSource:
    def __init__(self, download):
        self.download_result = download
        self.download_args = None

    def discover(self):
        return RESOURCE

    def download(self, resource, etag=None, last_modified=None):
        self.download_args = (etag, last_modified)
        return self.download_result


class TestCachedClient:
    def test_fresh_cache_hit_skips_source(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata())
        source = FakeSource(TesouroDownload(200, CSV, None, None))
        client = TesouroDiretoClient(cache=cache, source=source)

        sales, _metadata_result, origem = client.fetch_vendas()

        assert len(sales) == 1
        assert origem == "cache"
        assert source.download_args is None

    def test_force_downloads_and_saves(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata(checked_at="2000-01-01T00:00:00+00:00"))
        source = FakeSource(
            TesouroDownload(200, CSV, "etag-2", "2026-10-20T00:00:00")
        )
        client = TesouroDiretoClient(cache=cache, source=source)

        sales, metadata, origem = client.fetch_vendas(force=True)

        assert len(sales) == 1
        assert origem == "Tesouro Transparente"
        assert metadata["etag"] == "etag-2"
        assert source.download_args[0] == "etag-1"

    def test_304_reuses_cache_and_updates_checked_at(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata(checked_at="2000-01-01T00:00:00+00:00"))
        source = FakeSource(TesouroDownload(304, None, None, None))
        client = TesouroDiretoClient(cache=cache, source=source)

        _sales, metadata, origem = client.fetch_vendas(force=True)

        assert origem == "cache"
        assert metadata["checked_at"] != "2000-01-01T00:00:00+00:00"
        assert cache.read()[0] == CSV

    def test_invalid_download_preserves_previous_cache(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata())
        source = FakeSource(TesouroDownload(200, b"invalid", None, None))
        client = TesouroDiretoClient(cache=cache, source=source)

        with pytest.raises(TesouroDataError):
            client.fetch_vendas(force=True)

        assert cache.read()[0] == CSV

    def test_communication_failure_preserves_previous_cache(self, tmp_path):
        cache = TesouroCache(tmp_path)
        cache.save(CSV, _metadata())

        class FailingSource(FakeSource):
            def download(self, *args, **kwargs):
                raise CommunicationError("offline")

        client = TesouroDiretoClient(
            cache=cache, source=FailingSource(None)
        )
        with pytest.raises(CommunicationError):
            client.fetch_vendas(force=True)
        assert cache.read()[0] == CSV
