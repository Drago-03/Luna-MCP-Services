# Common developer commands for Luna MCP Server

.PHONY: help install lint type test format serve docker-build acceptance pre-commit coverage

help:
	@echo "Targets:"
	@echo "  install        Create venv (uv) & install deps"
	@echo "  lint           Run ruff check"
	@echo "  format         Run ruff format"
	@echo "  type           Run mypy"
	@echo "  test           Run pytest"
	@echo "  coverage       Run pytest with coverage (branch) + xml report"
	@echo "  serve          Start dev server"
	@echo "  docker-build   Build docker image"
	@echo "  acceptance     Run acceptance test script (needs BASE_URL + TOKEN)"
	@echo "  pre-commit     Install pre-commit hooks"

install:
	uv venv || true
	. .venv/bin/activate && uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

type:
	uv run mypy mcp-bearer-token/luna_mcp.py tools/

test:
	uv run pytest -q

coverage:
	uv run pytest --cov --cov-branch --cov-report=term-missing --cov-report=xml

serve:
	uv run uvicorn mcp-bearer-token.luna_mcp:app --host 0.0.0.0 --port 8086 --reload

docker-build:
	docker build -t luna-mcp:latest .

acceptance:
	@if [ -z "$$BASE_URL" ] || [ -z "$$TOKEN" ]; then echo "Usage: make acceptance BASE_URL=<url> TOKEN=<token>"; exit 1; fi
	bash acceptance_test.sh $$BASE_URL $$TOKEN

pre-commit:
	pre-commit install
