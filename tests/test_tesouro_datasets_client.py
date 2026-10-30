import json
from datetime import UTC, datetime, timedelta

import pytest

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError, resource_spec
from b3_selic_pre.infrastructure.tesouro_cache import TesouroCache, ttl_for
from b3_selic_pre.infrastructure.tesouro_cached_client import (
    TesouroDiretoClient,
)
from b3_selic_pre.infrastructure.tesouro_client import (
    TesouroDownload,
    TesouroResource,
    TesouroSourceClient,
)

RECOMPRA_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;Quantidade;Valor\n"
    "Tesouro Selic 2029;02/01/2029;01/10/2026;2,00;30.000,00\n"
).encode()
CUPOM_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor\n"
    "Tesouro IPCA+ 2035;15/05/2035;01/10/2026;3.000,00;1,00;3.000,00\n"
).encode()
VENCIMENTO_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Data Resgate;PU;Quantidade;Valor\n"
    "Tesouro Selic 2029;02/01/2029;02/10/2026;15.000,00;1,00;15.000,00\n"
).encode()
ESTOQUE_CSV = (
    "Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;"
    "Valor Estoque\n"
    "Tesouro Selic 2029;02/01/2029;09/2026;15.000,00;2,00;30.000,00\n"
).encode()
CSVS = {
    "recompra": RECOMPRA_CSV,
    "cupom": CUPOM_CSV,
    "vencimento": VENCIMENTO_CSV,
    "estoque": ESTOQUE_CSV,
}


class FakeResponse:
    def __init__(self, body=b"", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def read(self, size=-1):
        chunk, self.body = self.body[:size], self.body[size:]
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)

    def __call__(self, request, timeout):
        return self.responses.pop(0)


def _resource(key, resource_id=None):
    spec = resource_spec(key)
    return TesouroResource(
        dataset_name=spec.dataset_name,
        dataset_id="dataset-id",
        resource_id=resource_id or f"id-{key}",
        resource_url=f"https://example.test/{spec.csv_filename}",
        last_modified="2026-10-16T10:29:05",
    )


def _metadata(resource_id, **overrides):
    now = datetime.now(UTC).isoformat()
    data = {
        "schema_version": 1,
        "dataset_name": "dataset",
        "dataset_id": "dataset-id",
        "resource_id": resource_id,
        "resource_url": "https://example.test/file.csv",
        "etag": "etag",
        "last_modified": "2026-10-16T10:29:05",
        "downloaded_at": now,
        "checked_at": now,
        "size_bytes": 10,
        "sha256": "abc",
        "row_count": 1,
    }
    data.update(overrides)
    return data


class TestDiscovery:
    def _payload(self, resources):
        return {
            "success": True,
            "result": {
                "id": "dataset-id",
                "name": "resgates-do-tesouro-direto",
                "resources": resources,
            },
        }

    def _discover(self, resources):
        payload = self._payload(resources)
        opener = FakeOpener(
            [FakeResponse(json.dumps(payload).encode())]
        )
        return TesouroSourceClient(opener=opener).discover_resgates()

    def test_discovers_three_resources_and_newest_cupom(self):
        resources = [
            {"format": "PDF", "url": "p.pdf"},
            {
                "id": "recompra",
                "name": "Recompras do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/recompras.csv",
            },
            {
                "id": "cupom-old",
                "name": "Pagamento de Cupom de Juros do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/cupom.csv",
                "last_modified": "2025-01-01",
            },
            {
                "id": "cupom-new",
                "name": "Pagamento de Cupom de Juros do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/cupom.csv",
                "last_modified": "2026-01-01",
            },
            {
                "id": "vencimento",
                "name": "Vencimentos do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/vencimentos.csv",
            },
        ]
        found = self._discover(resources)

        assert set(found) == {"recompra", "cupom", "vencimento"}
        assert found["cupom"].resource_id == "cupom-new"

    def test_missing_resource(self):
        resources = [
            {
                "id": "recompra",
                "name": "Recompras do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/recompras.csv",
            }
        ]
        with pytest.raises(TesouroDataError, match="ausente"):
            self._discover(resources)

    def test_ambiguous_resource(self):
        resources = [
            {
                "id": "a",
                "name": "Recompras do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/recompras.csv",
            },
            {
                "id": "b",
                "name": "Recompras do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/recompras2.csv",
            },
        ]
        with pytest.raises(TesouroDataError, match="ambíguo"):
            self._discover(resources)

    def test_ambiguous_cupom_with_same_last_modified(self):
        resources = [
            {
                "id": "a",
                "name": "Pagamento de Cupom de Juros do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/cupom.csv",
                "last_modified": "2026-01-01",
            },
            {
                "id": "b",
                "name": "Pagamento de Cupom de Juros do Tesouro Direto",
                "format": "CSV",
                "url": "https://example.test/cupom2.csv",
                "last_modified": "2026-01-01",
            },
        ]
        payload = self._payload(resources)
        opener = FakeOpener(
            [FakeResponse(json.dumps(payload).encode())]
        )
        with pytest.raises(TesouroDataError, match="ambíguo"):
            TesouroSourceClient(opener=opener).discover_resource("cupom")

    def test_discovers_estoque(self):
        payload = {
            "success": True,
            "result": {
                "id": "dataset-id",
                "name": "estoque-do-tesouro-direto",
                "resources": [
                    {"format": "PDF", "url": "p.pdf"},
                    {
                        "id": "estoque",
                        "name": "Estoque do Tesouro Direto",
                        "format": "CSV",
                        "url": "https://example.test/estoque.csv",
                    },
                ],
            },
        }
        opener = FakeOpener([FakeResponse(json.dumps(payload).encode())])
        resource = TesouroSourceClient(opener=opener).discover_estoque()

        assert resource.resource_id == "estoque"


class TestCacheTTL:
    def test_daily_resources_use_24_hours(self, tmp_path):
        now = datetime(2026, 10, 19, 12, tzinfo=UTC)
        metadata = _metadata("id", checked_at=now.isoformat())
        assert ttl_for(metadata, now.date(), "cupom") == timedelta(hours=24)
        assert ttl_for(metadata, now.date(), "estoque") == timedelta(hours=24)

        cache = TesouroCache(tmp_path, resource="estoque")
        cache.save(ESTOQUE_CSV, metadata)
        assert cache.is_fresh(metadata, now)
        old = _metadata(
            "id",
            checked_at=(now - timedelta(hours=25)).isoformat(),
        )
        cache.save(ESTOQUE_CSV, old)
        assert not cache.is_fresh(old, now)

    def test_resources_have_independent_files(self, tmp_path):
        recompras = TesouroCache(tmp_path, resource="recompra")
        cupom = TesouroCache(tmp_path, resource="cupom")
        recompras.save(RECOMPRA_CSV, _metadata("r"))
        cupom.save(CUPOM_CSV, _metadata("c"))

        assert recompras.csv_path.name == "recompras.csv"
        assert recompras.metadata_path.name == "recompras.metadata.json"
        assert cupom.csv_path.name == "cupom.csv"
        assert cupom.metadata_path.name == "cupom.metadata.json"
        assert recompras.read()[0] == RECOMPRA_CSV
        assert cupom.read()[0] == CUPOM_CSV


class FakeSource:
    def __init__(self, downloads=None, failing=(), latest=False):
        self.downloads = downloads or {}
        self.failing = set(failing)
        self.latest = latest
        self.download_args = {}

    def discover_resgates(self):
        return {key: _resource(key) for key in ("recompra", "cupom", "vencimento")}

    def discover_estoque(self):
        return _resource("estoque")

    def download(self, resource, etag=None, last_modified=None):
        self.download_args[resource.resource_id] = (etag, last_modified)
        if resource.resource_id in self.failing:
            raise CommunicationError("offline")
        return self.downloads[resource.resource_id]


def _cached(client, key):
    cache = TesouroCache(client.cache_dir, resource=key)
    cache.save(CSVS[key], _metadata(f"id-{key}"))
    return cache


class TestCachedClient:
    def test_fresh_resgates_skip_downloads(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path), source=FakeSource()
        )
        for key in ("recompra", "cupom", "vencimento"):
            _cached(client, key)

        records, metadata, origem = client.fetch_resgates()

        assert len(records) == 3
        assert origem == "cache"
        assert client._source.download_args == {}
        assert set(metadata["resources"]) == {
            "recompra",
            "cupom",
            "vencimento",
        }

    def test_force_downloads_each_resource(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path),
            source=FakeSource(
                {
                    "id-recompra": TesouroDownload(200, RECOMPRA_CSV, "e", None),
                    "id-cupom": TesouroDownload(200, CUPOM_CSV, "e", None),
                    "id-vencimento": TesouroDownload(
                        200, VENCIMENTO_CSV, "e", None
                    ),
                }
            ),
        )

        records, _metadata_result, origem = client.fetch_resgates(force=True)

        assert len(records) == 3
        assert origem == "Tesouro Transparente"
        assert len(client._source.download_args) == 3
        for key in ("recompra", "cupom", "vencimento"):
            assert TesouroCache(
                tmp_path, resource=key
            ).read() is not None

    def test_304_reuses_cache_and_updates_checked_at(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path),
            source=FakeSource(
                {
                    key: TesouroDownload(304, None, None, None)
                    for key in ("id-recompra", "id-cupom", "id-vencimento")
                }
            ),
        )
        caches = {
            key: _cached(client, key)
            for key in ("recompra", "cupom", "vencimento")
        }
        before = {
            key: cache.read()[1]["checked_at"]
            for key, cache in caches.items()
        }

        _records, _metadata, origem = client.fetch_resgates(force=True)

        assert origem == "cache"
        for key, cache in caches.items():
            assert cache.read()[1]["checked_at"] != before[key]
            assert cache.read()[0] == CSVS[key]

    def test_isolated_failure_preserves_only_that_resource(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path),
            source=FakeSource(
                {
                    "id-cupom": TesouroDownload(200, CUPOM_CSV, "e", None),
                    "id-vencimento": TesouroDownload(
                        200, VENCIMENTO_CSV, "e", None
                    ),
                },
                failing={"id-recompra"},
            ),
        )
        _cached(client, "recompra")

        records, metadata, _origem = client.fetch_resgates(force=True)

        assert len(records) == 3
        assert metadata["resources"]["recompra"]["resource_id"] == "id-recompra"
        assert set(metadata["resources"]) == {
            "recompra",
            "cupom",
            "vencimento",
        }

    def test_all_resgates_failing_without_cache_raises(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path),
            source=FakeSource(
                failing={"id-recompra", "id-cupom", "id-vencimento"}
            ),
        )
        with pytest.raises(CommunicationError):
            client.fetch_resgates(force=True)

    def test_fetch_estoque_downloads_and_saves(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path),
            source=FakeSource(
                {"id-estoque": TesouroDownload(200, ESTOQUE_CSV, "e", None)}
            ),
        )

        records, metadata, origem = client.fetch_estoque(force=True)

        assert records[0].mes == "2026-09"
        assert metadata["last_data_date"] == "2026-09"
        assert origem == "Tesouro Transparente"
        assert TesouroCache(tmp_path, resource="estoque").read() is not None

    def test_fetch_estoque_failure_preserves_cache(self, tmp_path):
        client = TesouroDiretoClient(
            cache=TesouroCache(tmp_path),
            source=FakeSource(failing={"id-estoque"}),
        )
        cache = _cached(client, "estoque")

        with pytest.raises(CommunicationError):
            client.fetch_estoque(force=True)

        assert cache.read()[0] == ESTOQUE_CSV
