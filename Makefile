.PHONY: install backend frontend lint format typecheck test docs

install: backend frontend ## Install all dependencies

backend:
	python -m pip install -r requirements.txt

frontend:
	cd src/frontend && npm install

lint:
	ruff check

format:
	ruff format

typecheck:
	mypy src

test:
	pytest --cov=src --cov-report=term-missing

docs:
	cd docs && make html

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing
