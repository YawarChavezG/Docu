#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# COFAR SGD — Restaura BD de QAS a estado limpio (snapshot v1.1.0-qas)
#
# Uso:
#   ssh sistemas@sgdqas.cofar.com.bo 'bash -s' < scripts/restore_clean_state_qas.sh
#
# O localmente en el server QAS:
#   bash /opt/sgd/scripts/restore_clean_state_qas.sh
#
# Requiere:
#   - Dump en /opt/sgd/backups/clean_state_qas_20260619.dump
#   - Docker compose corriendo
# ════════════════════════════════════════════════════════════════

set -euo pipefail

SGD_DIR="/opt/sgd"
DUMP="${SGD_DIR}/backups/clean_state_qas_20260619.dump"
COMPOSE_FILE="${SGD_DIR}/deploy/docker-compose.qas.yml"
ENV_FILE="${SGD_DIR}/.env.qas"
POSTGRES_CONTAINER="sgd-qas-postgres"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  COFAR SGD — Restaurar BD QAS a estado limpio                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar dump
if [ ! -f "$DUMP" ]; then
    echo "[ERROR] No se encontro dump en ${DUMP}"
    echo "        Generar con: docker exec ${POSTGRES_CONTAINER} pg_dump ..."
    exit 1
fi
echo "[OK] Dump encontrado: $(ls -lh "${DUMP}" | awk '{print $5}')"

# Detener servicios que usan BD
echo "[restore] Deteniendo backend + celery (liberan conexiones a la BD)..."
docker stop sgd-qas-backend sgd-qas-celery-worker sgd-qas-celery-beat 2>/dev/null || true
sleep 2

# Copiar dump al container
echo "[restore] Copiando dump al container postgres..."
docker cp "${DUMP}" "${POSTGRES_CONTAINER}:/tmp/clean_state.dump"

# Restaurar
echo "[restore] Ejecutando pg_restore --clean --if-exists --single-transaction..."
echo "          (WARNING sobre objetos no encontrados son NORMALES con --clean)"
docker exec "${POSTGRES_CONTAINER}" pg_restore \
    --clean --if-exists --single-transaction \
    --no-owner --no-acl \
    -U sgd -d sgd \
    /tmp/clean_state.dump \
    2>&1 | grep -v "WARNING:.*does not exist" || true

# Levantar servicios
echo "[restore] Levantando backend + celery..."
docker start sgd-qas-celery-beat sgd-qas-celery-worker sgd-qas-backend 2>/dev/null || true

# Esperar health
echo "[restore] Esperando healthcheck del backend..."
for i in $(seq 1 15); do
    if curl -fsS -k "https://localhost/api/v1/health" >/dev/null 2>&1; then
        echo "[OK] Backend healthy."
        break
    fi
    [ "$i" -eq 15 ] && echo "[WARN] Backend no respondio en 45s. Revisar: docker logs sgd-qas-backend"
    sleep 3
done

# Verificar
echo ""
echo "[OK] Restore completado. Verificando estado..."
docker exec "${POSTGRES_CONTAINER}" psql -U sgd -d sgd -c \
    "SELECT tabla, filas FROM verify_clean_state() WHERE tabla IN ('audit_log','usuarios','gerencias','documentos');"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  QAS restaurado a estado limpio (snapshot v1.1.0-qas)        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
