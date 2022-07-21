SHELL := /usr/bin/env bash
POETRY_OK := $(shell type -P poetry)
POETRY_PATH := $(shell poetry env info --path)
POETRY_REQUIRED := $(shell cat .poetry-version)
POETRY_VIRTUALENVS_IN_PROJECT ?= true
PYTHON_OK := $(shell type -P python)
PYTHON_REQUIRED := $(shell cat .python-version)
PYTHON_VERSION ?= $(shell python -V | cut -d' ' -f2)
ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

help: ## The help text you're reading
	@grep --no-filename -E '^[a-zA-Z1-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

bandit: ## Run bandit against python code
	@poetry run bandit -r ./main.py -c .bandit
.PHONY: bandit

black: ## Run black against python code
	@poetry run black ./
.PHONY: black

check_poetry: check_python ## Check Poetry installation
    ifeq ('$(POETRY_OK)','')
	    $(error package 'poetry' not found!)
    else
	    @echo Found Poetry ${POETRY_REQUIRED}
    endif
.PHONY: check_poetry

check_python: ## Check Python installation
    ifeq ('$(PYTHON_OK)','')
	    $(error python interpreter: 'python' not found!)
    else
	    @echo Found Python
    endif
    ifneq ('$(PYTHON_REQUIRED)','$(PYTHON_VERSION)')
	    $(error incorrect version of python found: '${PYTHON_VERSION}'. Expected '${PYTHON_REQUIRED}'!)
    else
	    @echo Found Python ${PYTHON_REQUIRED}
    endif
.PHONY: check_python

debug_log_groups: ## Show list of log groups that target log_handler lambda
	@aws-profile poetry run python main.py "debug_subscription_filters"
.PHONY: debug_log_groups

delete_duplicate_filters: ## Find occurrences of log groups that have log_handler lambda declared twice then delete the duplicates
	@DRY_RUN=false aws-profile poetry run python main.py "delete_duplicate_filters"
.PHONY: delete_duplicate_filters

display_duplicate_filters: ## Find occurrences of log groups that have log_handler lambda declared twice
	@DRY_RUN=true aws-profile poetry run python main.py "delete_duplicate_filters"
.PHONY: delete_duplicate_filters_dry_run

get_formatted_filters: ## Get a formatted list of log groups that have subscriptions to log_handler lambda
	@aws-profile poetry run python main.py "get_formatted_subscription_filters"
.PHONY: get_formatted_subscription_filters

setup: check_poetry ## Setup virtualenv & dependencies using poetry and set-up the git hook scripts
	@export POETRY_VIRTUALENVS_IN_PROJECT=$(POETRY_VIRTUALENVS_IN_PROJECT) && poetry run pip install --upgrade pip
	@poetry install --no-root
	@poetry run pre-commit install
.PHONY: setup
