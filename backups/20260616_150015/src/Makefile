# ════════════════════════════════════════════════════════════════
# Makefile — COFAR SGD (Windows-friendly con make de Chocolatey)
# Si no tienes make, los scripts en scripts/ son equivalentes
# ════════════════════════════════════════════════════════════════

# ─── Variables ───
COMPOSE_FILE = deploy/docker-compose.yml
COMPOSE = docker compose -f $(COMPOSE_FILE) --env-file .env

# ─── Comandos principales ───
.PHONY: help up down restart logs ps build rebuild clean

help:           ## Mostrar ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

up:             ## Levantar toda la stack
	$(COMPOSE) up -d

down:           ## Bajar toda la stack
	$(COMPOSE) down

restart:        ## Reiniciar servicios
	$(COMPOSE) restart

logs:           ## Ver logs agregados (Ctrl+C para salir)
	$(COMPOSE) logs -f

ps:             ## Ver estado de servicios
	$(COMPOSE) ps

build:          ## Build de imágenes
	$(COMPOSE) build

rebuild:        ## Rebuild sin caché
	$(COMPOSE) build --no-cache

clean:          ## Bajar y eliminar volúmenes (¡CUIDADO! borra datos)
	$(COMPOSE) down -v

# ─── Servicios individuales ───
.PHONY: logs-backend logs-frontend logs-db logs-nginx shell-backend shell-db

logs-backend:
	$(COMPOSE) logs -f backend

logs-frontend:
	$(COMPOSE) logs -f frontend

logs-db:
	$(COMPOSE) logs -f postgres

logs-nginx:
	$(COMPOSE) logs -f nginx

shell-backend:  ## Shell dentro del contenedor backend
	$(COMPOSE) exec backend bash

shell-db:       ## psql dentro del contenedor postgres
	$(COMPOSE) exec postgres psql -U sgd -d sgd

# ─── DB / migraciones ───
.PHONY: migrate makemigration seed-db reset-db

migrate:        ## Aplicar migraciones Alembic
	$(COMPOSE) exec backend alembic upgrade head

makemigration:  ## Crear nueva migración (uso: make makemigration msg="descripcion")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(msg)"

seed-db:        ## Cargar datos seed (usuarios de prueba)
	$(COMPOSE) exec backend python scripts/seed_data.py

reset-db:       ## Resetear DB (borrar y volver a migrar)
	$(COMPOSE) down
	docker volume rm sgd-des_postgres_data
	$(COMPOSE) up -d postgres
	sleep 5
	$(COMPOSE) up -d backend
	$(MAKE) migrate
	$(MAKE) seed-db

# ─── Tests ───
.PHONY: test test-backend test-frontend

test: test-backend ## Todos los tests

test-backend:
	$(COMPOSE) exec backend pytest

test-frontend:
	cd frontend && npm test
