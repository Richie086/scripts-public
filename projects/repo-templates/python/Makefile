.PHONY: setup lint test run

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e .[dev]

lint:
	. .venv/bin/activate && ruff check .

test:
	. .venv/bin/activate && pytest

run:
	. .venv/bin/activate && python src/main.py
