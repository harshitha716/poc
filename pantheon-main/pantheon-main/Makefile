# Get the current directory and root directory
CURRENT_DIR := $(shell pwd)
ROOT_DIR := $(shell git rev-parse --show-toplevel 2>/dev/null || echo $(CURRENT_DIR))

# Automatically determine Python path based on project root
PYTHON_PATH := $(ROOT_DIR)/pantheon

# Default eval folder if none specified
EVAL_FOLDER ?= .

.PHONY: eval dev dev-build dev-stop dev-clean

eval:
	@if [ "$(CURRENT_DIR)" != "$(ROOT_DIR)" ]; then \
		cd $(ROOT_DIR) && PYTHONPATH=$(PYTHON_PATH) promptfoo eval -c $(EVAL_FOLDER)/promptfooconfig.yaml --no-cache --no-table	; \
	else \
		PYTHONPATH=$(PYTHON_PATH) promptfoo eval -c $(EVAL_FOLDER)/promptfooconfig.yaml --no-cache --no-table; \
	fi

dev:
	docker compose -f docker-compose-dev.yaml up

dev-build:
	docker compose -f docker-compose-dev.yaml up --build

dev-stop:
	docker compose -f docker-compose-dev.yaml down

dev-clean:
	docker compose -f docker-compose-dev.yaml down -v --remove-orphans
