from b3_selic_pre.presentation.tesouro_chart_data import (
    KIND_APETITE,
    KIND_ESTOQUE,
    KIND_VISAO_GERAL,
)
from b3_selic_pre.presentation.tesouro_orientation_text import (
    ORIENTATION_SECTIONS,
    ORIENTATION_TEXTS,
)

REQUIRED = (
    "Objetivo",
    "Responde a pergunta",
    "Indicadores envolvidos",
    "Como interpretar",
)


def test_every_sub_tab_has_the_required_sections():
    for kind in (KIND_VISAO_GERAL, KIND_ESTOQUE, KIND_APETITE):
        titles = tuple(title for title, _ in ORIENTATION_SECTIONS[kind])

        assert titles == REQUIRED


def test_section_titles_end_with_colon_in_rendered_text():
    for kind in (KIND_VISAO_GERAL, KIND_ESTOQUE, KIND_APETITE):
        text = ORIENTATION_TEXTS[kind]

        for title in REQUIRED:
            assert f"{title}:" in text
