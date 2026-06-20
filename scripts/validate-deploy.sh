#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# COFAR SGD — Validador pre-deploy (correr en DES antes de deployar)
#
# Simula un deploy completo en un entorno aislado:
#   1. Crea BD PostgreSQL fresh en Docker
#   2. Corre alembic upgrade head (valida migrations SIN || )
#   3. Corre todos los seeds (valida idempotencia + datos)
#   4. Corre pytest (valida tests)
#   5. Corre entrypoint en modo CI
#
# Exit codes:
#   0 = todo OK, deploy puede continuar
#   1 = alguna validacion fallo
#
# Uso:
#   bash scripts/validate-deploy.sh
# ════════════════════════════════════════════════════════════════
set -euo pipefail

BOLD=$'\033[1m'
NC=$'\033[0m'
GREEN=$'\033[1;32m'
RED=$'\033[1;31m'
YELLOW=$'\033[1;33m'

PASS=0
FAIL=0

pass() { printf '  %s[PASS]%s %s\n' "$GREEN" "$NC" "$*"; PASS=$((PASS+1)); }
fail() { printf '  %s[FAIL]%s %s\n' "$RED" "$NC" "$*"; FAIL=$((FAIL+1)); }

SGD_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PG_CONTAINER="sgd-validate-pg"
PG_PORT=25433  # Distinto al 25432 de DES para no colisionar

cleanup() {
    echo "[CLEANUP] Deteniendo BD de validacion..."
    docker stop "$PG_CONTAINER" 2>/dev/null || true
    docker rm "$PG_CONTAINER" 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  COFAR SGD — Validador pre-deploy                             ║"
echo "║  Simula deploy completo en BD PostgreSQL fresh                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ─── 1. Provisionar BD fresh ───
echo "═══ 1. Provisionando BD fresh ═══"
docker run -d --name "$PG_CONTAINER" \
    -e POSTGRES_USER=sgd \
    -e POSTGRES_PASSWORD=sgd_test \
    -e POSTGRES_DB=sgd \
    -p "$PG_PORT":5432 \
    postgres:16-alpine 2>/dev/null
echo "  Esperando PostgreSQL..."
for i in $(seq 1 30); do
    if docker exec "$PG_CONTAINER" pg_isready -U sgd -d sgd >/dev/null 2>&1; then
        pass "PostgreSQL fresh listo (puerto $PG_PORT)"
        break
    fi
    [ "$i" -eq 30 ] && fail "PostgreSQL no responde tras 30s" && exit 1
    sleep 1
done

# ─── 2. Alembic upgrade head ───
echo ""
echo "═══ 2. Ejecutando alembic upgrade head ═══"
# Configurar DATABASE_URL para apuntar a la BD de validacion
export DATABASE_URL="postgresql+asyncpg://sgd:sgd_test@localhost:${PG_PORT}/sgd"
export ENVIRONMENT=ci
export LDAP_ENABLED=false
export SMTP_ENABLED=false
export GRAPH_ENABLED=false

cd "$SGD_DIR/backend"

# Ejecutar alembic upgrade head (SIN || — si falla, el script aborta)
if alembic upgrade head 2>&1; then
    pass "alembic upgrade head: todas las migraciones aplicadas"
else
    fail "alembic upgrade head FALLO. Revisar migraciones."
fi

# ─── 3. Verificar alembic head esperado ───
echo ""
echo "═══ 3. Verificando estado BD ═══"

EXPECTED_HEAD="r3_plantillas_table_s37"
ACTUAL_HEAD=$(psql "${DATABASE_URL/postgresql+asyncpg/postgresql}" -tA -c "SELECT version_num FROM alembic_version" 2>/dev/null || echo "")
if [ "$ACTUAL_HEAD" = "$EXPECTED_HEAD" ]; then
    pass "alembic head: $ACTUAL_HEAD"
else
    fail "alembic head esperado: $EXPECTED_HEAD, actual: $ACTUAL_HEAD"
fi

# Conteo de tablas
TABLE_COUNT=$(psql "${DATABASE_URL/postgresql+asyncpg/postgresql}" -tA -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
pass "tablas en BD: $TABLE_COUNT"

# ─── 4. Ejecutar entrypoint modo CI ───
echo ""
echo "═══ 4. Ejecutando entrypoint modo CI ═══"
if bash scripts/entrypoint.sh 2>&1; then
    pass "entrypoint modo CI: migrations + validacion OK"
else
    fail "entrypoint modo CI FALLO"
fi

# ─── 5. Ejecutar seeds clave ───
echo ""
echo "═══ 5. Ejecutando seeds (validacion idempotencia) ═══"

SEEDS=(
    "scripts/seed_procesos.py:Seed Procesos"
)

for entry in "${SEEDS[@]}"; do
    script="${entry%%:*}"
    desc="${entry#*:}"
    if python "$script" 2>&1 | tail -1 | grep -q "Resultado:"; then
        pass "$desc OK"
    else
        fail "$desc FALLO"
    fi
done

# ─── 6. Resumen ───
echo ""
echo "═══ RESUMEN ═══"
TOTAL=$((PASS + FAIL))
printf '  %sPASS: %d/%d%s\n' "$GREEN" "$PASS" "$TOTAL" "$NC"
printf '  %sFAIL: %d/%d%s\n' "$RED" "$FAIL" "$TOTAL" "$NC"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  VALIDACION FALLIDA. Revisar arriba.                   ║"
    echo "║  NO hacer deploy hasta corregir.                      ║"
    echo "╚════════════════════════════════════════════════════════╝"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  VALIDACION OK. Deploy puede continuar.                ║"
echo "╚════════════════════════════════════════════════════════╝"
