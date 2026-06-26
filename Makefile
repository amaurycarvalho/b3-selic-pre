.PHONY: install build test clean

PYTHON = python3
VENV_PYTHON = .venv/bin/python

ifeq ($(OS),Windows_NT)
PYTHON = python
VENV_PYTHON = .venv/Scripts/python
endif

.venv:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -e .
	$(VENV_PYTHON) -m pip install pyinstaller

install: .venv

build: .venv
	MPLBACKEND=Agg $(VENV_PYTHON) -m PyInstaller b3-selic-pre.spec

test: .venv
	$(VENV_PYTHON) -m pytest

clean:
	rm -rf dist/ build/ __pycache__/ src/*.egg-info/
