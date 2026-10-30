"""Constants used across the b3_selic_pre application."""

B3_BASE_URL = "https://sistemaswebb3-derivativos.b3.com.br/"
DEFAULT_LANGUAGE = "pt-br"
DEFAULT_RATE_ID = "SLP"
DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 100
DEFAULT_B3_TIMEOUT_SECONDS = 60

EVOLUTION_DAYS = [28, 21, 14, 7, 0]

TESOURO_CKAN_BASE_URL = "https://www.tesourotransparente.gov.br/ckan"
TESOURO_DATASET_NAME = "vendas-do-tesouro-direto"
TESOURO_RESGATES_DATASET_NAME = "resgates-do-tesouro-direto"
TESOURO_ESTOQUE_DATASET_NAME = "estoque-do-tesouro-direto"
TESOURO_BTD_PUBLICATIONS_URL = (
    "https://www.tesourotransparente.gov.br/publicacoes/"
    "balanco-do-tesouro-direto-btd"
)
