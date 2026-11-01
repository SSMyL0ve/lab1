PYTHON := .venv/bin/python
SRC := src
export PYTHONPATH := src/ticketing
export MYPYPATH := src/ticketing

.PHONY: install lint typecheck check run

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m flake8 $(SRC)

typecheck:
	$(PYTHON) -m mypy --strict --explicit-package-bases $(SRC)/ticketing

check: lint typecheck

run:
	PYTHONPATH=src/ticketing .venv/bin/python src/ticketing/__main__.py
