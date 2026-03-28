PYTHON := .venv/bin/python
PIP := .venv/bin/pip
UVICORN := .venv/bin/uvicorn

.PHONY: venv install test run worker stack-up stack-down bootstrap migrate setup

venv:
	python3 -m venv .venv

install: venv
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests

run:
	$(UVICORN) app.main:app --reload

worker:
	$(PYTHON) -m app.workers.tasks

stack-up:
	docker compose up -d

stack-down:
	docker compose down

migrate:
	$(PYTHON) -m alembic upgrade head

bootstrap:
	$(PYTHON) scripts/bootstrap_local.py

setup: install stack-up bootstrap
