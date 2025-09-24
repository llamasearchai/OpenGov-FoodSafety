.PHONY: help
help:
	@echo "Commands:"
	@echo "  run       : Run the application with docker-compose"
	@echo "  stop      : Stop the application"
	@echo "  test      : Run tests"
	@echo "  lint      : Run linters"
	@echo "  format    : Format code"
	@echo "  pre-commit: Install pre-commit hooks"

.PHONY: run
run:
	docker-compose up -d

.PHONY: stop
stop:
	docker-compose down

.PHONY: test
test:
	poetry run pytest

.PHONY: lint
lint:
	poetry run flake8 .
	poetry run mypy .
	poetry run bandit -c pyproject.toml -r .
	poetry run pylint .

.PHONY: format
format:
	poetry run black .
	poetry run isort .

.PHONY: pre-commit
pre-commit:
	poetry run pre-commit install
