.PHONY: local-setup
local-setup:
	@echo Creating virtual environment
	@poetry shell
	@pre-commit install

.PHONY: install
install:
	@echo Installing dependencies
	@poetry install --sync

.PHONY: lint
lint:
	@echo Linting code
	@pre-commit run ruff -a

.PHONY: test
test:
	@echo Running tests
	@poetry run pytest -v