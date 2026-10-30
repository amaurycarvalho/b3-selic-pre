import urllib.error

import pytest

from b3_selic_pre.application.errors import CommunicationError
from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.infrastructure.tesouro_btd_source import BtdSourceClient
from b3_selic_pre.infrastructure.tesouro_btd_types import BtdEdition
from tests.btd_fixtures import xlsx_bytes

EDITION = BtdEdition(
    reference_month="2026-09",
    published_at="2026-10-29",
    page_url="https://example.test/btd/2026/9",
    attachment_url="https://thot-arquivos.tesouro.gov.br/publicacao-anexo/1",
)


class FakeResponse:
    def __init__(self, body=b"", status=200, headers=None, url=EDITION.page_url):
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.url = url

    def read(self, size=-1):
        if size is None or size < 0:
            chunk, self.body = self.body, b""
            return chunk
        chunk, self.body = self.body[:size], self.body[size:]
        return chunk

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)

    def __call__(self, request, timeout):
        item = self.responses.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def test_download_accepts_spreadsheet_zip():
    body = xlsx_bytes()
    client = BtdSourceClient(
        opener=FakeOpener(
            [
                FakeResponse(
                    body,
                    headers={"Content-Type": "application/octet-stream"},
                )
            ]
        )
    )

    assert client.download(EDITION) == body


def test_download_404_is_communication_error():
    client = BtdSourceClient(
        opener=FakeOpener(
            [
                urllib.error.HTTPError(
                    EDITION.attachment_url, 404, "Not Found", {}, None
                )
            ]
        )
    )

    with pytest.raises(CommunicationError, match="404"):
        client.download(EDITION)


def test_download_rejects_non_spreadsheet_content_type():
    client = BtdSourceClient(
        opener=FakeOpener(
            [
                FakeResponse(
                    b"<html></html>",
                    headers={"Content-Type": "text/html"},
                )
            ]
        )
    )

    with pytest.raises(TesouroDataError, match="Content-Type"):
        client.download(EDITION)


def test_download_rejects_invalid_zip_body():
    client = BtdSourceClient(
        opener=FakeOpener(
            [
                FakeResponse(
                    b"not a zip",
                    headers={"Content-Type": "application/octet-stream"},
                )
            ]
        )
    )

    with pytest.raises(TesouroDataError, match="XLSX"):
        client.download(EDITION)


def test_download_timeout_is_communication_error():
    client = BtdSourceClient(opener=FakeOpener([TimeoutError("timeout")]))

    with pytest.raises(CommunicationError):
        client.download(EDITION)
