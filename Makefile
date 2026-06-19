.PHONY: install backend frontend lint format typecheck test test-coverage \
        security docs migrate ci

install: backend frontend ## Install all dependencies

backend:
	python3 -m pip install -r requirements.txt

frontend:
	cd src/frontend && npm install

lint:
	python3 -m ruff check

format:
	python3 -m ruff format

typecheck:
	python3 -m mypy src

test:
	python3 -m pytest --cov=src --cov-report=term-missing

test-coverage:
	python3 -m pytest --cov=src --cov-report=html --cov-report=term-missing

security:
	python3 -m bandit -r src/ -q -ll
	python3 -m pip_audit

docs:
	cd docs && make html

migrate:
	alembic upgrade head

ci: lint format typecheck test security ## Run all CI checks locally
