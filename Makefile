.PHONY: install run lint build package-install

install:
	uv sync

run:
	uv run database

lint:
	uv run ruff check .

build:
	uv build

package-install:
	uv tool install --force dist/*.whl
