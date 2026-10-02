.PHONY: install dev test lint format docker

install:
	pip install -r requirements-dev.txt

dev:
	flask --app app run --debug

test:
	pytest --cov=team_builder --cov-report=term-missing

lint:
	ruff check . && ruff format --check .

format:
	ruff check --fix . && ruff format .

docker:
	docker compose up --build
