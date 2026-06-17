.PHONY: install build test clean

.venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt pyinstaller

install: .venv

build: .venv
	MPLBACKEND=Agg .venv/bin/pyinstaller b3-selic-pre.spec

test: .venv
	.venv/bin/python -m unittest discover -s tests

clean:
	rm -rf dist/ build/ __pycache__/
