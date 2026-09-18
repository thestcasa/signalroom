PYTHON ?= .venv/bin/python

.PHONY: setup test lint demo build-cases clean

setup:
	uv sync --python 3.12 --extra dev --extra pdf

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests app.py scripts

build-cases:
	$(PYTHON) -m signalroom.cli build --config configs/brighton_wsl_2023_24.toml
	$(PYTHON) -m signalroom.cli build --config configs/leverkusen_bundesliga_2023_24.toml

demo:
	$(PYTHON) -m streamlit run app.py --server.headless true

clean:
	rm -rf build .pytest_cache .ruff_cache
