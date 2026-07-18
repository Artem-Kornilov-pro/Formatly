COMPOSE = docker compose

.PHONY: env up down build logs ps shell-backend shell-frontend test test-backend test-frontend lint lint-backend lint-frontend clean

env:
	@test -f .env || cp .env.example .env

up: env
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

build: env
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

shell-backend: env
	$(COMPOSE) run --rm backend bash

shell-frontend: env
	$(COMPOSE) run --rm frontend sh

test: test-backend test-frontend

test-backend: env
	$(COMPOSE) run --rm backend pytest

test-frontend: env
	$(COMPOSE) run --rm frontend npm run test

lint: lint-backend lint-frontend

lint-backend: env
	$(COMPOSE) run --rm backend ruff check .

lint-frontend: env
	$(COMPOSE) run --rm frontend npm run lint

clean:
	$(COMPOSE) down -v
