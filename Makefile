.PHONY: install build test lint clean

VENV = .venv

ifeq ($(OS),Windows_NT)
	PYTHON = python
	VENV_PYTHON = $(VENV)/Scripts/python
	PIP = $(VENV)/Scripts/pip
else
	PYTHON = python3
	VENV_PYTHON = $(VENV)/bin/python
	PIP = $(VENV)/bin/pip
endif

$(VENV):
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -q -e .
	$(VENV_PYTHON) -m pip install -q pyinstaller

install: $(VENV)

build: $(VENV)
	MPLBACKEND=Agg $(VENV_PYTHON) -m PyInstaller b3-selic-pre.spec

test: $(VENV)
	$(VENV_PYTHON) -m pytest --tb=short

lint: $(VENV)
	$(PIP) install -q ruff
	$(VENV)/bin/ruff check .

clean:
	rm -rf dist/ build/ __pycache__/ src/*.egg-info/
