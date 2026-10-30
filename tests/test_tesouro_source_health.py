import logging
from datetime import date

import pytest

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.infrastructure.tesouro_cache import TesouroCache
from b3_selic_pre.infrastructure.tesouro_client import (
    TesouroDownload,
    TesouroResource,
)
from b3_selic_pre.infrastructure.tesouro_source_health import (
    MAX_MONTHS_LAG,
    EstoqueSourceHealth,
    TesouroSourceHealth,
    avaliar_defasagem,
    month_lag,
    validar_estoque,
)

HEADER = (
    "Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade;Valor Estoque"
)
RESOURCE = TesouroResource(
    dataset_name="estoque-do-tesouro-direto",
    dataset_id="dataset-id",
    resource_id="resource-id",
    resource_url="https://example.test/estoque.csv",
    last_modified="2026-10-16T10:29:05",
)


def _csv(*rows):
    return ("\n".join((HEADER, *rows)) + "\n").encode("utf-8")


class FakeSource:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error
        self.download_calls = 0

    def discover_estoque(self):
        if self.error is not None:
            raise self.error
        return RESOURCE

    def download(self, resource, etag=None, last_modified=None):
        self.download_calls += 1
        return TesouroDownload(200, self.data, None, None)


def _health(tmp_path, source):
    return TesouroSourceHealth(
        source=source,
        cache=TesouroCache(tmp_path, resource="estoque"),
    )


class TestMonthLag:
    def test_month_lag_and_warning(self):
        assert month_lag("2026-09", date(2026, 10, 1)) == 1
        assert avaliar_defasagem("2026-07", date(2026, 10, 1)) is None
        warning = avaliar_defasagem("2026-06", date(2026, 10, 1))

        assert warning is not None
        assert "2026-06" in warning

    def test_max_lag_constant(self):
        assert MAX_MONTHS_LAG == 3

    def test_validar_estoque_returns_latest_month(self):
        data = _csv(
            "Tesouro Selic 2029;02/01/2029;08/2026;1,00;1,00;10,00",
            "Tesouro Selic 2029;02/01/2029;09/2026;1,00;1,00;10,00",
        )
        assert validar_estoque(data) == "2026-09"


class TestSourceHealth:
    def test_fonte_saudavel(self, tmp_path):
        data = _csv(
            "Tesouro Selic 2029;02/01/2029;09/2026;1,00;1,00;10,00"
        )
        source = FakeSource(data)

        result = _health(tmp_path, source).check_estoque(
            reference=date(2026, 10, 1)
        )

        assert isinstance(result, EstoqueSourceHealth)
        assert result.latest_month == "2026-09"
        assert result.warning is None
        assert result.message == "Último mês consolidado: 2026-09"
        assert source.download_calls == 1

    def test_fonte_ausente_levanta_tesouro_data_error_sem_fallback(
        self, tmp_path
    ):
        source = FakeSource(error=TesouroDataError("dataset ausente"))

        with pytest.raises(TesouroDataError, match="ausente"):
            _health(tmp_path, source).check_estoque()

        assert source.download_calls == 0

    def test_schema_alterado_levanta_tesouro_data_error(self, tmp_path):
        data = (
            "Tipo Titulo;Vencimento do Titulo;Mes Estoque;PU;Quantidade\n"
            "Tesouro Selic 2029;02/01/2029;09/2026;1,00;1,00\n"
        ).encode("utf-8")
        source = FakeSource(data)

        with pytest.raises(TesouroDataError, match="Valor Estoque"):
            _health(tmp_path, source).check_estoque()

    def test_defasagem_registra_aviso_mas_usa_dado(self, tmp_path, caplog):
        data = _csv(
            "Tesouro Selic 2029;02/01/2029;12/2025;1,00;1,00;10,00"
        )
        source = FakeSource(data)

        with caplog.at_level(logging.WARNING):
            result = _health(tmp_path, source).check_estoque(
                reference=date(2026, 10, 1)
            )

        assert result.latest_month == "2025-12"
        assert result.warning is not None
        assert "defasado" in result.warning
        assert "defasado" in caplog.text

    def test_falha_de_comunicacao_mantem_tipo_e_log_em_uma_linha(
        self, tmp_path, caplog
    ):
        class FailingSource(FakeSource):
            def download(self, resource, etag=None, last_modified=None):
                raise CommunicationError("offline")

        with caplog.at_level(logging.WARNING):
            with pytest.raises(CommunicationError, match="offline"):
                _health(tmp_path, FailingSource()).check_estoque()

        records = [
            record
            for record in caplog.records
            if "health check" in record.getMessage()
        ]
        assert len(records) == 1
        assert records[0].exc_info is None

    def test_304_sem_cache_e_erro_de_comunicacao(self, tmp_path):
        class NotModifiedSource(FakeSource):
            def download(self, resource, etag=None, last_modified=None):
                return TesouroDownload(304, None, None, None)

        with pytest.raises(CommunicationError, match="304"):
            _health(tmp_path, NotModifiedSource()).check_estoque()
