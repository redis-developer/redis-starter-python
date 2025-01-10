install:
	@uv sync

dev: install
	@fastapi dev app/main.py

serve: install
	@fastapi run app/main.py

docker:
	@docker compose up -d

format: install
	@ruff check app --fix
	@ruff format app

lint: install
	@mypy app
	@ruff check app
	@ruff format app --check

clean:
	@rm -rf .venv/ .mypy_cache/ .ruff_cache/