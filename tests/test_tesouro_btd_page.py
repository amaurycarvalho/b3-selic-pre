import pytest

from b3_selic_pre.application.tesouro import TesouroDataError
from b3_selic_pre.infrastructure.tesouro_btd_page import parse_btd_page

PAGE_URL = (
    "https://www.tesourotransparente.gov.br/publicacoes/"
    "balanco-do-tesouro-direto-btd"
)
HTML = """
<html><head>
<link rel="canonical" href="https://www.tesourotransparente.gov.br/publicacoes/balanco-do-tesouro-direto-btd/2026/9">
<meta property="article:published_time" content="2026-10-29T10:00:00">
</head><body>
<time datetime="2026-10-29">29/10/2026</time>
<a href="https://thot-arquivos.tesouro.gov.br/publicacao-anexo/29563">
Anexos_Balanço_TD - Set 2026.xlsx
</a>
</body></html>
""".encode()


def test_discovers_latest_edition_and_xlsx_attachment():
    edition = parse_btd_page(HTML, PAGE_URL)

    assert edition.reference_month == "2026-09"
    assert edition.published_at == "2026-10-29"
    assert edition.page_url.endswith("/2026/9")
    assert edition.attachment_url == (
        "https://thot-arquivos.tesouro.gov.br/publicacao-anexo/29563"
    )


def test_final_redirect_url_can_identify_the_edition():
    edition = parse_btd_page(
        b"<html><body><a href='/publicacao-anexo/1'>Anexo Set/26.xlsx</a>"
        b"</body></html>",
        PAGE_URL + "/2026/9",
    )

    assert edition.reference_month == "2026-09"


def test_page_without_attachment_fails():
    page = HTML.replace(b".xlsx", b".pdf")

    with pytest.raises(TesouroDataError, match="anexo"):
        parse_btd_page(page, PAGE_URL)


def test_page_without_recognizable_edition_fails():
    with pytest.raises(TesouroDataError, match="edição"):
        parse_btd_page(
            b"<html><body><a href='/publicacao-anexo/1'>x.xlsx</a>"
            b"</body></html>",
            "https://example.test/outra-publicacao",
        )


def test_multiple_xlsx_attachments_are_rejected():
    page = HTML.replace(
        b"</body>",
        b"<a href='/publicacao-anexo/2'>Anexo 2.xlsx</a></body>",
    )

    with pytest.raises(TesouroDataError, match="mais de um"):
        parse_btd_page(page, PAGE_URL)
