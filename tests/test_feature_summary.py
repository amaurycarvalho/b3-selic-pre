"""Paridade entre o resumo de funcionalidades do README e da aba Sobre."""

from pathlib import Path

from b3_selic_pre.application.about import (
    FEATURES_SUMMARY,
    FEATURES_TITLE,
    features_text,
)

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ABOUT_TAB = (
    ROOT / "src" / "b3_selic_pre" / "presentation" / "gui" / "about_tab.py"
)


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _readme_section() -> str:
    content = README.read_text(encoding="utf-8")
    marker = f"## {FEATURES_TITLE}"
    start = content.index(marker) + len(marker)
    rest = content[start:]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_readme_features_section_matches_about_summary():
    assert _normalize(_readme_section()) == _normalize(features_text())


def test_readme_features_section_appears_before_install_and_use():
    content = README.read_text(encoding="utf-8")
    section = content.index(f"## {FEATURES_TITLE}")

    assert section < content.index("Como Instalar")
    assert section < content.index("Como Usar")


def test_features_summary_covers_the_main_areas():
    summary = " ".join(FEATURES_SUMMARY).lower()

    for term in (
        "interface gráfica",
        "selic pré",
        "tesouro direto",
        "dólar e ouro",
        "câmbio e reserva",
        "reservas internacionais",
        "feriados",
        "linha de comando",
        "mcp",
        "cache local",
    ):
        assert term in summary


def test_about_tab_uses_the_shared_summary_source():
    source = ABOUT_TAB.read_text(encoding="utf-8")

    assert "FEATURES_TITLE" in source
    assert "features_text" in source
    sections = source.index("ABOUT_SECTIONS")
    assert source.index('"Aplicação"', sections) < source.index(
        "FEATURES_TITLE", sections
    )
