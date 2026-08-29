# Prérequis : uv
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 15 tests fermés, sans réseau ni donnée de marché
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

all:              ## le laboratoire complet (~3 min)
	$(UV) run vop lab
