#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# COFAR SGD — Entrypoint compartido (DES + QAS + CI)
#
# Punto unico de entrada para el container backend.
# Usos:
#   ENVIRONMENT=development  → uvicorn --reload (DES)
#   ENVIRONMENT=qas          → uvicorn --workers 2 (QAS)
#   ENVIRONMENT=ci           → solo valida (no arranca servidor)
#
# Comportamiento:
#   1. Espera a PostgreSQL (max 60s)
#   2. Aplica migraciones Alembic (si falla, aborta — FATAL)
#   3. Arranca uvicorn segun el environment
#
# Uso:
#   docker compose up  (usa este entrypoint via command: del compose)
#   ENVIRONMENT=ci bash scripts/entrypoint.sh  (CI mode, valida solo migrations)
# ════════════════════════════════════════════════════════════════
set -euo pipefail

ENV="${ENVIRONMENT:-development}"
RETRIES=30

echo "[ENTRYPOINT] Environment: ${ENV}"
echo "[ENTRYPOINT] Esperando a PostgreSQL..."

for i in $(seq 1 $RETRIES); do
    if nc -z postgres 5432 2>/dev/null; then
        echo "[ENTRYPOINT] PostgreSQL listo."
        break
    fi
    if [ "$i" -eq "$RETRIES" ]; then
        echo "[ENTRYPOINT] ERROR: PostgreSQL no responde tras ${RETRIES}s."
        exit 1
    fi
    sleep 1
done

echo "[ENTRYPOINT] Aplicando migraciones Alembic..."
alembic upgrade head 2>&1
echo "[ENTRYPOINT] Migraciones aplicadas correctamente."

# CI mode: solo validar, no arrancar servidor
if [ "$ENV" = "ci" ]; then
    echo "[ENTRYPOINT] Modo CI: validacion completa, servidor no arrancado."
    exit 0
fi

# Production-like: workers fijos
if [ "$ENV" = "qas" ] || [ "$ENV" = "production" ]; then
    echo "[ENTRYPOINT] Iniciando uvicorn (workers=2, sin reload)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
fi

# Development: hot-reload
echo "[ENTRYPOINT] Iniciando uvicorn (--reload)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
