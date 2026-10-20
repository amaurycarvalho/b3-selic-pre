from pathlib import Path

from b3_selic_pre.presentation.gui_reference import record_reference


class _Settings(dict):
    pass


def test_records_reference_when_data_exists():
    settings = _Settings()
    record_reference(settings, "2026-06-17", True)
    assert settings["data_referencia"] == "2026-06-17"


def test_does_not_record_without_data():
    settings = _Settings()
    record_reference(settings, "2026-06-17", False)
    assert "data_referencia" not in settings


def test_does_not_record_without_date():
    settings = _Settings()
    record_reference(settings, "", True)
    assert "data_referencia" not in settings


def test_gui_fetch_uses_the_headless_helper():
    source = Path(
        "src/b3_selic_pre/presentation/gui/fetch.py"
    ).read_text(encoding="utf-8")
    assert "from b3_selic_pre.presentation.gui_reference import" in source
    assert "record_reference(" in source
