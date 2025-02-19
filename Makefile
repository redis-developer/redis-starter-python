install:
	@uv sync --all-extras

dev: install
	@fastapi dev src/app/main.py

serve: install
	@fastapi run src/app/main.py

test:
	@pytest -rxP

docker:
	@docker compose up -d

format: install
	@ruff check src/app --fix
	@ruff format src/app

lint: install
	@mypy src/app
	@ruff check src/app
	@ruff format src/app --check

lock: install
	@uv lock

clean:
	@rm -rf .venv/ .mypy_cache/ .ruff_cache/ .pytest_cache/
	@find . -type d -name __pycache__ -exec rm -r {} \+
