import os


B3_BASE_URL = "https://sistemaswebb3-derivativos.b3.com.br/"
DEFAULT_LANGUAGE = "pt-br"
DEFAULT_RATE_ID = "SLP"
DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 100

EVOLUTION_DAYS = [28, 21, 14, 7, 0]

SHORTCUT_CHECK_PATH = os.path.expanduser(
    "~/.local/share/applications/b3-selic-pre.desktop"
)
