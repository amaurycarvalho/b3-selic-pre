"""Testes headless dos metadados e da comparação de versões do diálogo Sobre."""

import pytest

from b3_selic_pre.application.about import (
    APP_NAME,
    DESCRIPTION,
    LICENSE_TEXT,
    REPOSITORY_URL,
    build_about_info,
    is_newer_version,
    new_version_notice,
    normalize_version,
    release_page_url,
)


class TestAboutInfo:
    def test_builds_metadata_from_version_and_release_date(self):
        info = build_about_info("1.0.0", "2026-10-19")

        assert info.name == APP_NAME
        assert info.version == "1.0.0"
        assert info.release_date == "2026-10-19"
        assert info.license_text == LICENSE_TEXT
        assert info.description == DESCRIPTION
        assert info.repository_url == REPOSITORY_URL

    def test_title_combines_name_and_version(self):
        info = build_about_info("2.3.4", "2026-10-19")

        assert info.title == "Taxas Referenciais SELIC (B3) v2.3.4"


class TestNormalizeVersion:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("1.2.3", "1.2.3"),
            ("v1.2.3", "1.2.3"),
            ("V1.2.3", "1.2.3"),
            ("v1.2", "1.2.0"),
            ("7", "7.0.0"),
            ("  v01.02.03  ", "1.2.3"),
        ],
    )
    def test_normalizes_valid_versions(self, value, expected):
        assert normalize_version(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "",
            "   ",
            "v",
            "1.2.3.4",
            "1.a.3",
            "1..3",
            "-1.2.3",
            "1.2.3-beta",
            "versão 1.2.3",
        ],
    )
    def test_rejects_malformed_versions(self, value):
        assert normalize_version(value) is None


class TestVersionComparison:
    def test_newer_candidate(self):
        assert is_newer_version("1.0.0", "1.0.1") is True

    def test_equal_versions_are_not_newer(self):
        assert is_newer_version("1.0.0", "v1.0.0") is False

    def test_older_candidate_is_not_newer(self):
        assert is_newer_version("1.2.3", "1.2.2") is False

    def test_prefix_and_missing_segments_are_compared(self):
        assert is_newer_version("1.2", "v1.2.1") is True

    def test_malformed_versions_are_not_newer(self):
        assert is_newer_version("1.0.0", "not-a-version") is False
        assert is_newer_version("bad", "1.0.0") is False
        assert is_newer_version("1.0.0", None) is False


class TestNewVersionNotice:
    def test_returns_notice_for_newer_version(self):
        assert new_version_notice("1.0.0", "v1.2.3") == (
            "Nova versão v1.2.3 disponível"
        )

    def test_no_notice_for_equal_older_missing_or_malformed(self):
        assert new_version_notice("1.0.0", "1.0.0") is None
        assert new_version_notice("1.0.0", "0.9.9") is None
        assert new_version_notice("1.0.0", None) is None
        assert new_version_notice("1.0.0", "malformed") is None


class TestReleasePageUrl:
    def test_release_page_url_uses_tag(self):
        assert release_page_url("v1.2.3") == (
            "https://github.com/amaurycarvalho/b3-selic-pre/releases/tag/v1.2.3"
        )

    def test_release_page_url_falls_back_to_latest(self):
        assert release_page_url(None) == (
            "https://github.com/amaurycarvalho/b3-selic-pre/releases/latest"
        )
