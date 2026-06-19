#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# COFAR SGD — Orquestador de stack para QAS (Debian 12 + Docker)
#
# Punto unico de entrada para levantar el entorno QAS en
# sgdqas.cofar.com.bo. Hace 8 cosas en orden:
#
#   1. Verifica prerequisitos (Docker, .env.qas, scripts/seed/).
#   2. Provisiona el directorio storage del backend (permisos 755/644,
#      ownership 1000:1000 = sgduser). NO usa chmod 777.
#   3. Levanta la stack Docker (postgres, redis, mailhog, backend,
#      celery-W/B, frontend, nginx) con --env-file .env.qas.
#   4. Espera health-checks de postgres y backend.
#   5. Aplica permisos correctos al /app/storage dentro del container
#      (chown sgduser, chmod 755/644). Sin esto celery-beat no puede
#      escribir el schedule file.
#   6. Aplica las 8 migraciones-seed en orden de dependencias FK.
#   7. Ejecuta sync_ad_oficial.py si LDAP_ENABLED=true (genera CSV
#      de usuarios desde el AD de COFAR).
#   8. Imprime resumen + URLs.
#
# Este script es la version oficial de lo que se hacia manualmente
# en sesion 10. Es idempotente: se puede correr multiples veces.
#
# Uso:
#   bash /opt/sgd/scripts/start-stack-qas.sh
#
# Detener:
#   bash /opt/sgd/scripts/stop-stack-qas.sh   (a crear si hace falta)
#   docker compose -f /opt/sgd/deploy/docker-compose.qas.yml \
#       --env-file /opt/sgd/.env.qas down
#
# Ver: docs/PR/DEPLOY-QAS.md
# ════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Constantes ───
readonly SGD_DIR="/opt/sgd"
readonly ENV_FILE="${SGD_DIR}/.env.qas"
readonly COMPOSE_FILE="${SGD_DIR}/deploy/docker-compose.qas.yml"
readonly STORAGE_DIR="${SGD_DIR}/backend/storage"
readonly SCRIPTS_DIR="${SGD_DIR}/backend/scripts"

# Container names (deben coincidir con docker-compose.qas.yml)
readonly C_POSTGRES="sgd-qas-postgres"
readonly C_BACKEND="sgd-qas-backend"
readonly C_CELERY_BEAT="sgd-qas-celery-beat"
readonly C_CELERY_WORKER="sgd-qas-celery-worker"

# Container user (sgduser, uid 1000 segun Dockerfile)
readonly APP_UID=1000
readonly APP_GID=1000

# ─── Helpers ───
# Usamos $'...' (ANSI-C quoting) para que bash interprete \033 como ESC real.
readonly BOLD=$'\033[1m'
readonly NC=$'\033[0m'
readonly BLUE=$'\033[1;34m'
readonly GREEN=$'\033[1;32m'
readonly YELLOW=$'\033[1;33m'
readonly RED=$'\033[1;31m'
readonly CYAN=$'\033[1;36m'
log()  { printf '%s[INFO]%s  %s\n' "$BLUE" "$NC" "$*"; }
ok()   { printf '%s[OK]%s    %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%s[WARN]%s  %s\n' "$YELLOW" "$NC" "$*" >&2; }
err()  { printf '%s[ERROR]%s %s\n' "$RED" "$NC" "$*" >&2; }
die()  { err "$*"; exit 1; }

banner() {
    printf '\n%s╔════════════════════════════════════════════════════════════════╗%s\n' "$CYAN" "$NC"
    printf '%s║%s  %-66s%s║%s\n' "$CYAN" "$NC" "$1" "$CYAN" "$NC"
    printf '%s╚════════════════════════════════════════════════════════════════╝%s\n\n' "$CYAN" "$NC"
}

step() {
    local n="$1" total="$2" desc="$3"
    printf '\n%s[%d/%d]%s %s%s%s\n' "$CYAN" "$n" "$total" "$NC" "$BOLD" "$desc" "$NC"
    printf -- '---------------------------------------------------------------\n'
}

# ─── 1. Prerequisitos ───
step 1 8 "Verificando prerequisitos..."

# 1.1 Docker
command -v docker >/dev/null 2>&1 || die "Docker no instalado. Correr primero scripts/qas-setup-docker.sh"
docker info >/dev/null 2>&1 || die "Docker daemon no responde. systemctl status docker"

# 1.2 .env.qas
[ -f "$ENV_FILE" ] || die "No existe ${ENV_FILE}. Copiar .env.example -> .env.qas y completar secrets."
chmod 600 "$ENV_FILE" 2>/dev/null || true

# 1.3 docker-compose.qas.yml
[ -f "$COMPOSE_FILE" ] || die "No existe ${COMPOSE_FILE}"

# 1.4 Cert autofirmado (HTTPS)
if [ ! -f "${SGD_DIR}/deploy/nginx/ssl/sgdqas.crt" ]; then
    warn "No se encontro cert autofirmado en deploy/nginx/ssl/. HTTPS fallara."
fi

# 1.5 Validar que todos los scripts/seeders existen fisicamente
REQUIRED_FILES=(
    "${SCRIPTS_DIR}/seed_data.py"
    "${SCRIPTS_DIR}/seed_organizacion.py"
    "${SCRIPTS_DIR}/seed_tipos_documento.py"
    "${SCRIPTS_DIR}/seed_estados.py"
    "${SCRIPTS_DIR}/seed_feriados.py"
    "${SCRIPTS_DIR}/seed_email_templates.py"
    "${SCRIPTS_DIR}/seed_matriz_eto.py"
    "${SCRIPTS_DIR}/seed_configuracion_global.py"
    "${SCRIPTS_DIR}/seed_usuario_roles.py"
    "${SCRIPTS_DIR}/seed_usuario_roles.sql"
    "${SCRIPTS_DIR}/sync_ad_oficial.py"
)
MISSING=()
for f in "${REQUIRED_FILES[@]}"; do
    [ -f "$f" ] || MISSING+=("$f")
done
if [ "${#MISSING[@]}" -gt 0 ]; then
    err "Faltan archivos de seed/sync requeridos:"
    printf '       - %s\n' "${MISSING[@]}" >&2
    die "Re-deployar codigo o restaurar los archivos faltantes."
fi
ok "Prerequisitos OK. ${#REQUIRED_FILES[@]} archivos de seed validados."

# ─── 2. Provisionar storage (permisos correctos, NO 777) ───
step 2 8 "Provisionando ${STORAGE_DIR} (uid ${APP_UID}:${APP_GID}, sin chmod 777)..."

mkdir -p "$STORAGE_DIR"

# Ownership: sgduser:sgduser (uid 1000:1000 segun Dockerfile).
# Si el host user no es root, no podemos chown a un uid arbitrario
# directamente — pero Docker lo hara al ejecutar como root en el container.
# En este caso, el script NO modifica owner en host (seria inutil:
# el container es el que escribe).
#
# Lo que SI podemos (y debemos) hacer: limpiar archivos corruptos de
# celerybeat-schedule con permisos inconsistentes.
if [ -f "${STORAGE_DIR}/celerybeat-schedule" ]; then
    if [ ! -w "${STORAGE_DIR}/celerybeat-schedule" ]; then
        warn "celerybeat-schedule existe sin permisos de escritura. Eliminando para regenerar."
        rm -f "${STORAGE_DIR}/celerybeat-schedule"
        rm -f "${STORAGE_DIR}/celerybeat-schedule.db"
        rm -f "${STORAGE_DIR}/celerybeat-schedule.bak"
    fi
fi
ok "Storage provisionado."

# ─── 3. Levantar stack Docker ───
step 3 8 "Levantando stack QAS con ${ENV_FILE}..."

cd "$SGD_DIR"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
ok "8 servicios iniciandose."

# ─── 4. Esperar health-checks ───
step 4 8 "Esperando health-checks..."

log "Esperando PostgreSQL..."
for i in {1..30}; do
    if docker exec "$C_POSTGRES" pg_isready -U "$(grep ^POSTGRES_USER "$ENV_FILE" | cut -d= -f2)" \
            -d "$(grep ^POSTGRES_DB "$ENV_FILE" | cut -d= -f2)" >/dev/null 2>&1; then
        ok "PostgreSQL ready."
        break
    fi
    [ "$i" -eq 30 ] && die "PostgreSQL no respondio en 60s. Revisar: docker logs $C_POSTGRES"
    sleep 2
done

log "Esperando backend..."
for i in {1..30}; do
    if curl -fsS -k "https://localhost/api/v1/health" >/dev/null 2>&1; then
        ok "Backend ready (HTTPS via nginx)."
        break
    fi
    if curl -fsS "http://localhost:8000/api/v1/health" >/dev/null 2>&1; then
        ok "Backend ready (directo)."
        break
    fi
    [ "$i" -eq 30 ] && die "Backend no respondio en 60s. Revisar: docker logs $C_BACKEND"
    sleep 2
done

# ─── 5. Fijar permisos de storage DENTRO del container (forma correcta) ───
step 5 8 "Aplicando permisos correctos a /app/storage dentro del container..."

# Esta es la forma correcta (vs chmod 777 que es la "trampa" que usamos
# manualmente en sesion 10). chown al usuario sgduser que creo el Dockerfile,
# y chmod restrictivo (755 dirs, 644 files).
docker exec --user root "$C_BACKEND" \
    sh -c '
        set -e
        # Asegurar que el directorio existe y es propiedad de sgduser
        mkdir -p /app/storage
        chown -R '"${APP_UID}"':'"${APP_GID}"' /app/storage
        # Permisos restrictivos: solo owner puede escribir
        find /app/storage -type d -exec chmod 755 {} +
        find /app/storage -type f -exec chmod 644 {} +
        echo "Permisos aplicados:"
        ls -la /app/storage
    '
ok "Storage con permisos correctos (755/644, owner sgduser)."

# Reiniciar celery-beat para que regenere el schedule con los nuevos perms
log "Reiniciando celery-beat para regenerar schedule file..."
docker restart "$C_CELERY_BEAT" >/dev/null
sleep 3
ok "celery-beat reiniciado."

# ─── 6. Aplicar 9 seeds en orden de dependencias FK ───
step 6 8 "Aplicando seeds (orden por dependencias FK)..."

# Orden de ejecucion: las tablas sin FK primero, las con FK dependen
# de las anteriores. Verificado contra app/models/__init__.py y los
# scripts individuales.
SEEDS=(
    "seed_data.py:Roles + Modulos + Gerencias + Areas + 4 usuarios stub"
    "seed_organizacion.py:27 areas adicionales (de la matriz abril)"
    "seed_tipos_documento.py:13 tipos de documento del Excel"
    "seed_estados.py:5 estados del flujo documental"
    "seed_feriados.py:20 feriados Bolivia 2026 (11 nac + 9 dptos)"
    "seed_email_templates.py:6 plantillas de notificacion (US-9.04)"
    "seed_matriz_eto.py:10 filas matriz ETO + usuario cecEspinoza"
    "seed_configuracion_global.py:11 parametros US-9.01+9.02 (VIGENCIA, SEMAFORO, ARCHIVOS, DESCARGAS)"
    "seed_usuario_roles.py:729 asignaciones snapshot (idempotente, sesion 33)"
)
SEED_FAILED=0
for entry in "${SEEDS[@]}"; do
    script="${entry%%:*}"
    desc="${entry#*:}"
    log "Ejecutando ${script} (${desc})..."
    if docker exec "$C_BACKEND" python "scripts/${script}" 2>&1 | tail -3; then
        ok "${script} OK."
    else
        err "${script} FALLO. Continuando con el siguiente (algunos seeds son idempotentes)."
        SEED_FAILED=$((SEED_FAILED + 1))
    fi
done
if [ "$SEED_FAILED" -gt 0 ]; then
    warn "${SEED_FAILED} seed(s) fallaron. Verificar manualmente: docker exec ${C_BACKEND} python scripts/seed_*.py"
else
    ok "9/9 seeds aplicados correctamente."
fi

# ─── 7. Sync AD (opcional, solo si LDAP_ENABLED=true) ───
step 7 8 "Sincronizacion AD (solo si LDAP_ENABLED=true)..."

if grep -q '^LDAP_ENABLED=true' "$ENV_FILE"; then
    log "LDAP_ENABLED=true. Ejecutando sync_ad_oficial.py para validar bind..."
    log "Pasando .env.qas al container con --env-file (necesario porque el bind"
    log "mount del backend no expone /opt/sgd/.env.qas al filesystem del container)."
    if docker exec --env-file "$ENV_FILE" "$C_BACKEND" \
        python scripts/sync_ad_oficial.py 2>&1 | tail -25; then
        # El script genera /app/storage/usuarios_sap_FINAL2026.csv
        # (por defecto; ver SYNC_AD_OUTPUT_DIR en sync_ad_oficial.py).
        # y muestra conteos. Verificamos que el CSV existe.
        if docker exec "$C_BACKEND" test -f /app/storage/usuarios_sap_FINAL2026.csv; then
            # wc debe correr DENTRO del container (el path es del container, no del host).
            ROWS=$(docker exec "$C_BACKEND" sh -c 'wc -l < /app/storage/usuarios_sap_FINAL2026.csv')
            ok "CSV generado en /app/storage/: ${ROWS} lineas (incluye header)."
            # Tambien copiamos al host (visible desde fuera del container) para auditoria
            docker cp "$C_BACKEND:/app/storage/usuarios_sap_FINAL2026.csv" \
                "${SGD_DIR}/backend/scripts/usuarios_sap_FINAL2026.csv" 2>/dev/null \
                && ok "CSV copiado a ${SGD_DIR}/backend/scripts/ (host)." \
                || warn "No se pudo copiar el CSV al host (no critico)."
        else
            warn "sync_ad_oficial.py termino pero no genero el CSV en /app/storage/."
        fi
    else
        err "sync_ad_oficial.py fallo. Verificar conectividad AD:"
        err "  - LDAP_SERVER reachable: nc -zv \$(grep ^LDAP_SERVER $ENV_FILE | cut -d= -f2) 389"
        err "  - LDAP_BIND_USER/PASSWORD correctos en .env.qas"
        warn "Continuando — la app funciona con los 4 stubs DES, pero el sync AD no estara disponible."
    fi
else
    log "LDAP_ENABLED=false. Saltando sync AD (modo stub con 4 usuarios locales)."
fi

# ─── 8. Resumen final ───
step 8 8 "Resumen final"

# Conteos de BD
log "Conteos de BD:"
docker exec "$C_POSTGRES" psql -U "$(grep ^POSTGRES_USER "$ENV_FILE" | cut -d= -f2)" \
    -d "$(grep ^POSTGRES_DB "$ENV_FILE" | cut -d= -f2)" -tA -c "
        SELECT '  roles:           ' || count(*) FROM roles;
        SELECT '  modulos:         ' || count(*) FROM modulos;
        SELECT '  gerencias:       ' || count(*) FROM gerencias;
        SELECT '  areas:           ' || count(*) FROM areas;
        SELECT '  usuarios:        ' || count(*) FROM usuarios;
        SELECT '  tipos_documento: ' || count(*) FROM tipos_documento;
        SELECT '  estados:         ' || count(*) FROM estados;
        SELECT '  feriados:        ' || count(*) FROM feriados;
        SELECT '  email_templates: ' || count(*) FROM email_templates;
        SELECT '  matriz_eto:      ' || count(*) FROM matriz_enrutamiento_eto;
        SELECT '  configuracion:   ' || count(*) FROM configuracion_global;
        SELECT '  semaforizacion:  ' || count(*) FROM semaforizacion_tarea;
        SELECT '  alembic:         ' || version_num FROM alembic_version;
    " 2>/dev/null | grep -v '^$'

# Servicios
log "Servicios:"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps --format "  {{.Service}}: {{.Status}}" 2>/dev/null

# URLs
# printf (no heredoc) para que bash interprete correctamente los ANSI escape codes.
printf '\n'
printf '%s╔════════════════════════════════════════════════════════════════╗%s\n' "$BOLD" "$NC"
printf '%s║  QAS desplegado y validado                                    ║%s\n' "$BOLD" "$NC"
printf '%s║                                                                ║%s\n' "$BOLD" "$NC"
printf '%s║  App (HTTPS):    https://sgdqas.cofar.com.bo                   ║%s\n' "$BOLD" "$NC"
printf '%s║  Health:         https://sgdqas.cofar.com.bo/api/v1/health    ║%s\n' "$BOLD" "$NC"
printf '%s║  Backend (int):  http://localhost:8000 (dentro del container) ║%s\n' "$BOLD" "$NC"
printf '%s║  Swagger:        http://localhost:8000/docs                    ║%s\n' "$BOLD" "$NC"
printf '%s║  PostgreSQL:     container %s:5432 (interno)        ║%s\n' "$BOLD" "$C_POSTGRES" "$NC"
printf '%s║  Redis:          container sgd-qas-redis:6379 (interno)       ║%s\n' "$BOLD" "$NC"
printf '%s║  MailHog:        container sgd-qas-mailhog:8025 (interno)      ║%s\n' "$BOLD" "$NC"
printf '%s║                                                                ║%s\n' "$BOLD" "$NC"
printf '%s║  Credenciales DEV (4 stubs locales):                           ║%s\n' "$BOLD" "$NC"
printf '%s║    aromero / cofar.2026         (ETO)                          ║%s\n' "$BOLD" "$NC"
printf '%s║    admin / cofar.2026           (ADMIN)                        ║%s\n' "$BOLD" "$NC"
printf '%s║    solicitante / cofar.2026     (ELABORADOR)                   ║%s\n' "$BOLD" "$NC"
printf '%s║    visualizador / cofar.2026    (VISUALIZADOR)                 ║%s\n' "$BOLD" "$NC"
printf '%s║                                                                ║%s\n' "$BOLD" "$NC"
printf '%s║  Monitoreo:                                                    ║%s\n' "$BOLD" "$NC"
printf '%s║    docker compose -f %-40s║%s\n' "$BOLD" "$COMPOSE_FILE" "$NC"
printf '%s║        --env-file %-39s║%s\n' "$BOLD" "$ENV_FILE" "$NC"
printf '%s╚════════════════════════════════════════════════════════════════╝%s\n' "$BOLD" "$NC"
printf '\n'

ok "Stack QAS listo."
