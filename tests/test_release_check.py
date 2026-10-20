"""Testes headless da consulta à API de releases do GitHub."""

import json
from unittest import mock

from b3_selic_pre.infrastructure import release_check
from b3_selic_pre.infrastructure.release_check import (
    RELEASE_API_URL,
    USER_AGENT,
    fetch_latest_version,
)


class _Response:
    def __init__(self, status=200, body=b"{}"):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def _response(status=200, payload=None):
    body = json.dumps(payload if payload is not None else {}).encode("utf-8")
    return _Response(status=status, body=body)


class TestFetchLatestVersion:
    def test_returns_normalized_version(self):
        response = _response(payload={"tag_name": "1.2.3"})
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ):
            assert fetch_latest_version() == "1.2.3"

    def test_strips_prefix_v(self):
        response = _response(payload={"tag_name": "v1.2.3"})
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ):
            assert fetch_latest_version() == "1.2.3"

    def test_non_200_response_returns_none(self):
        response = _response(status=404, payload={"tag_name": "1.2.3"})
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ):
            assert fetch_latest_version() is None

    def test_timeout_returns_none(self):
        with mock.patch.object(
            release_check.urllib.request,
            "urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            assert fetch_latest_version() is None

    def test_network_error_returns_none(self):
        with mock.patch.object(
            release_check.urllib.request,
            "urlopen",
            side_effect=OSError("offline"),
        ):
            assert fetch_latest_version() is None

    def test_invalid_json_returns_none(self):
        response = _Response(body=b"not json")
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ):
            assert fetch_latest_version() is None

    def test_missing_tag_name_returns_none(self):
        response = _response(payload={"name": "release"})
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ):
            assert fetch_latest_version() is None

    def test_non_dict_payload_returns_none(self):
        response = _response(payload=["1.2.3"])
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ):
            assert fetch_latest_version() is None

    def test_uses_expected_url_user_agent_and_timeout(self):
        response = _response(payload={"tag_name": "1.2.3"})
        with mock.patch.object(
            release_check.urllib.request, "urlopen", return_value=response
        ) as opener:
            fetch_latest_version(timeout=2.5)
        request = opener.call_args.args[0]
        assert request.full_url == RELEASE_API_URL
        assert request.get_header("User-agent") == USER_AGENT
        assert opener.call_args.kwargs["timeout"] == 2.5
