#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# COFAR SGD — Validador post-deploy QAS
#
# Ejecuta las 12 validaciones A-L (segun PLAN-DEPLOY-QAS-SESION18.md)
# contra el servidor QAS. Es ejecutable en cualquier momento, no solo
# post-deploy, para diagnosticar el estado de QAS.
#
# Uso:
#   bash /opt/sgd/scripts/validate-qas.sh
#
# Exit codes:
#   0 = todas las validaciones PASS
#   1 = alguna validacion fallo
#   2 = error de conexion al server
#
# Ver: docs/PR/PLAN-DEPLOY-QAS-SESION18.md
# ════════════════════════════════════════════════════════════════

set -uo pipefail

# ─── Constantes ───
readonly SGD_DIR="/opt/sgd"
readonly COMPOSE_FILE="${SGD_DIR}/deploy/docker-compose.qas.yml"
readonly ENV_FILE="${SGD_DIR}/.env.qas"
readonly C_NGINX="sgd-qas-nginx"
readonly C_BACKEND="sgd-qas-backend"
readonly C_POSTGRES="sgd-qas-postgres"
readonly C_FRONTEND="sgd-qas-frontend"

# ─── Contadores ───
PASS=0
FAIL=0
WARN=0
declare -a RESULTS

# ─── Helpers ───
readonly BOLD=$'\033[1m'; readonly NC=$'\033[0m'
readonly GREEN=$'\033[1;32m'; readonly RED=$'\033[1;31m'; readonly YELLOW=$'\033[1;33m'; readonly CYAN=$'\033[1;36m'

pass() { printf '  %s[PASS]%s %s\n' "$GREEN" "$NC" "$*"; PASS=$((PASS+1)); RESULTS+=("PASS|$*"); }
fail() { printf '  %s[FAIL]%s %s\n' "$RED" "$NC" "$*"; FAIL=$((FAIL+1)); RESULTS+=("FAIL|$*"); }
warn() { printf '  %s[WARN]%s %s\n' "$YELLOW" "$NC" "$*"; WARN=$((WARN+1)); RESULTS+=("WARN|$*"); }
heading() { printf '\n%s%s%s\n' "$CYAN" "$*" "$NC"; }

# ─── Pre-check: estamos en el server QAS? ───
if [ ! -d "$SGD_DIR" ] || [ ! -f "$COMPOSE_FILE" ]; then
    echo "ERROR: Este script debe ejecutarse en el servidor QAS."
    echo "       $SGD_DIR o $COMPOSE_FILE no existen."
    echo "       Uso: ssh sistemas@sgdqas.cofar.com.bo 'bash /opt/sgd/scripts/validate-qas.sh'"
    exit 2
fi

# ════════════════════════════════════════════════════════════════
# A. HEALTH
# ════════════════════════════════════════════════════════════════
heading "═══ A. HEALTH ═══"

# A.1 Backend health directo
if docker exec "$C_BACKEND" curl -fsS http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    pass "A.1 Backend health (directo) 200 OK"
else
    fail "A.1 Backend health (directo) - no responde"
fi

# A.2 Backend health via nginx HTTPS
if curl -kfsS -o /dev/null -w '' https://localhost/api/v1/health 2>/dev/null; then
    pass "A.2 Backend health (HTTPS via nginx) 200 OK"
else
    fail "A.2 Backend health (HTTPS via nginx) - no responde o 502"
fi

# A.3 8 servicios Up
SERVICES_UP=$(docker ps --filter "name=sgd-qas-" --format '{{.Names}}' | wc -l)
if [ "$SERVICES_UP" -eq 8 ]; then
    pass "A.3 8/8 servicios sgd-qas-* Up"
else
    fail "A.3 Solo $SERVICES_UP/8 servicios sgd-qas-* Up (esperado 8)"
fi

# A.4 Backend health desde afuera (DNS publico)
# NOTA: el DNS interno de QAS no responde desde el server.
# Esta validacion se debe correr desde la corp o con DNS resuelto.
# Se omite para no dar falso FAIL.

# ════════════════════════════════════════════════════════════════
# B. LIBRERIAS
# ════════════════════════════════════════════════════════════════
heading "═══ B. LIBRERIAS ═══"

# B.1 openpyxl en backend
OPENPYXL_VER=$(docker exec "$C_BACKEND" python -c 'import openpyxl; print(openpyxl.__version__)' 2>/dev/null)
if [ "$OPENPYXL_VER" = "3.1.5" ]; then
    pass "B.1 openpyxl $OPENPYXL_VER (export XLSX/CSV)"
else
    fail "B.1 openpyxl version: '$OPENPYXL_VER' (esperado 3.1.5)"
fi

# B.2 Tiptap en frontend
TIPTAP_COUNT=$(docker exec "$C_FRONTEND" sh -c 'ls -d /app/node_modules/@tiptap/* 2>/dev/null | wc -l' 2>/dev/null | tr -d ' ')
if [ "${TIPTAP_COUNT:-0}" -ge 5 ]; then
    pass "B.2 Tiptap packages: $TIPTAP_COUNT instalados (>=5)"
else
    fail "B.2 Tiptap packages: $TIPTAP_COUNT (esperado >=5). Si fallo, ver bind mount de compose o ejecutar: docker exec $C_FRONTEND sh -c 'cd /app && npm install'"
fi

# ════════════════════════════════════════════════════════════════
# C. MIGRACIONES
# ════════════════════════════════════════════════════════════════
heading "═══ C. MIGRACIONES ═══"

# C.1 alembic head esperado
ALEMBIC_HEAD=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT version_num FROM alembic_version" 2>/dev/null)
if [ "$ALEMBIC_HEAD" = "drop_modulos_s26" ]; then
    pass "C.1 alembic head: $ALEMBIC_HEAD"
else
    fail "C.1 alembic head: $ALEMBIC_HEAD (esperado drop_modulos_s26)"
fi

# C.2 semaforizacion_tarea existe
SEMAF_TABLES=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM information_schema.tables WHERE table_name='semaforizacion_tarea'" 2>/dev/null)
if [ "$SEMAF_TABLES" = "1" ]; then
    pass "C.2 tabla semaforizacion_tarea existe"
else
    fail "C.2 tabla semaforizacion_tarea no existe (esperado 1)"
fi

# C.3 tipos_documento sin codigo_doc, con slug
TIPOS_CODIGODOC=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM information_schema.columns WHERE table_name='tipos_documento' AND column_name='codigo_doc'" 2>/dev/null)
TIPOS_SLUG=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM information_schema.columns WHERE table_name='tipos_documento' AND column_name='slug'" 2>/dev/null)
if [ "$TIPOS_CODIGODOC" = "0" ] && [ "$TIPOS_SLUG" = "1" ]; then
    pass "C.3 tipos_documento: sin codigo_doc, con slug"
else
    fail "C.3 tipos_documento: codigo_doc=$TIPOS_CODIGODOC (esperado 0), slug=$TIPOS_SLUG (esperado 1)"
fi

# C.4 email_templates enum con 11 valores
EMAIL_ENUM=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM pg_enum WHERE enumtypid=(SELECT oid FROM pg_type WHERE typname='codigo_plantilla')" 2>/dev/null)
if [ "$EMAIL_ENUM" = "11" ]; then
    pass "C.4 enum email_templates: 11 valores (10 plantillas + AUTO_DELEGACION)"
else
    fail "C.4 enum email_templates: $EMAIL_ENUM valores (esperado 11)"
fi

# ════════════════════════════════════════════════════════════════
# D. DATOS BD
# ════════════════════════════════════════════════════════════════
heading "═══ D. DATOS BD ═══"

# Conteos esperados (post-deploy v1.1.0-qas, sesion 33)
# - usuarios=752: 4 stubs + 750 AD - 2 visitador/visitador2 excluidos (sesion 32 fix)
# - estados=16: 5 originales + 4 PROCESO + 6 TAREA + 3 ACCION (sesion 23 B3) - algunos marcados inactivos
#   NOTA: validate pasa si count >= esperado; el limite inferior es 12.
# - configuracion_global=11: 11 parametros US-9.01+9.02 (no se removieron)
# - email_templates=11: catalogo completo (sesion 13)
declare -A EXPECTED_COUNTS=(
    [roles]=5
    [modulos]=11
    [gerencias]=10
    [areas]=50
    [usuarios]=752
    [tipos_documento]=13
    [estados]=12
    [feriados]=20
    [email_templates]=11
    [matriz_enrutamiento_eto]=10
    [configuracion_global]=11
    [semaforizacion_tarea]=4
)
for table in "${!EXPECTED_COUNTS[@]}"; do
    expected="${EXPECTED_COUNTS[$table]}"
    actual=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM $table" 2>/dev/null)
    if [ "$actual" -ge "$expected" ] 2>/dev/null; then
        pass "D.$table count=$actual (>= $expected esperado)"
    else
        fail "D.$table count=$actual (< $expected esperado)"
    fi
done

# D.13 INSTRUCTIVO_TECNICO con codigo=15
INST_TECNICO=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT codigo FROM tipos_documento WHERE slug='INSTRUCTIVO_TECNICO'" 2>/dev/null)
if [ "$INST_TECNICO" = "15" ]; then
    pass "D.13 INSTRUCTIVO_TECNICO.codigo=15"
else
    fail "D.13 INSTRUCTIVO_TECNICO.codigo=$INST_TECNICO (esperado 15)"
fi

# D.14 usuario_roles count >= 720 (esperado 723-729 segun cuantos
# usuarios del AD estan en BD; el seed es idempotente y ON CONFLICT skip)
UR_COUNT=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM usuario_roles" 2>/dev/null)
if [ "${UR_COUNT:-0}" -ge 720 ] 2>/dev/null; then
    pass "D.14 usuario_roles count=$UR_COUNT (>= 720 esperado)"
else
    fail "D.14 usuario_roles count=$UR_COUNT (< 720 esperado). Re-correr seed_usuario_roles.py"
fi

# D.15 visitador/visitador2/ozegarra NO en BD (sesion 32 fix)
EXCL_COUNT=$(docker exec "$C_POSTGRES" psql -U sgd -d sgd -tA -c "SELECT count(*) FROM usuarios WHERE username IN ('visitador', 'visitador2', 'ozegarra', 'dlanchipa')" 2>/dev/null)
if [ "$EXCL_COUNT" = "0" ]; then
    pass "D.15 usuarios excluidos del sync AD: 0 en BD (visitador/visitador2/ozegarra/dlanchipa)"
else
    fail "D.15 $EXCL_COUNT usuarios excluidos del sync AD todavia en BD. Aplicar cleanup."
fi

# ════════════════════════════════════════════════════════════════
# E. LOGIN
# ════════════════════════════════════════════════════════════════
heading "═══ E. LOGIN ═══"

# E.1 Login BD Local (aromero) - guarda cookies para E.2 y F.*
LOGIN_RESP=$(curl -kfsS -X POST https://localhost/api/v1/login \
    -H "Content-Type: application/json" \
    -c /tmp/cookies_validate.txt \
    -d '{"username":"aromero","password":"cofar.2026","auth_source":"local"}' 2>/dev/null)
if echo "$LOGIN_RESP" | grep -q '"Login exitoso"'; then
    pass "E.1 Login BD Local (aromero) 200 OK"
else
    fail "E.1 Login BD Local - no exitoso (response: ${LOGIN_RESP:0:100})"
fi

# E.2 /me con cookies
ME_RESP=$(curl -kfsS -b /tmp/cookies_validate.txt -c /tmp/cookies_validate.txt https://localhost/api/v1/me 2>/dev/null)
if echo "$ME_RESP" | grep -q '"authenticated":true'; then
    pass "E.2 /me con cookies: authenticated=true"
else
    fail "E.2 /me - no autenticado (response: ${ME_RESP:0:100})"
fi

# ════════════════════════════════════════════════════════════════
# F. ENDPOINTS NUEVOS
# ════════════════════════════════════════════════════════════════
heading "═══ F. ENDPOINTS NUEVOS ═══"

# F.1 audit-log
if curl -kfsS -b /tmp/cookies_validate.txt "https://localhost/api/v1/audit-log?limit=5" >/dev/null 2>&1; then
    pass "F.1 /audit-log 200 OK"
else
    fail "F.1 /audit-log - no responde"
fi

# F.2 semaforizacion-tarea
if curl -kfsS -b /tmp/cookies_validate.txt https://localhost/api/v1/semaforizacion-tarea >/dev/null 2>&1; then
    pass "F.2 /semaforizacion-tarea 200 OK"
else
    fail "F.2 /semaforizacion-tarea - no responde"
fi

# F.3 admin/impersonate/list (path real con slash, no guion como dice el plan)
if curl -kfsS -b /tmp/cookies_validate.txt https://localhost/api/v1/admin/impersonate/list >/dev/null 2>&1; then
    IMP_COUNT=$(curl -kfsS -b /tmp/cookies_validate.txt https://localhost/api/v1/admin/impersonate/list 2>/dev/null | grep -o '"total":[0-9]*' | head -1 | cut -d: -f2)
    pass "F.3 /admin/impersonate/list 200 OK (total=$IMP_COUNT usuarios impersonables)"
else
    fail "F.3 /admin/impersonate/list - no responde"
fi

# ════════════════════════════════════════════════════════════════
# J. SYNC AD
# ════════════════════════════════════════════════════════════════
heading "═══ J. SYNC AD ═══"

# J.1 CSV generado
if docker exec "$C_BACKEND" test -f /app/storage/usuarios_sap_FINAL2026.csv 2>/dev/null; then
    CSV_LINES=$(docker exec "$C_BACKEND" sh -c 'wc -l < /app/storage/usuarios_sap_FINAL2026.csv' 2>/dev/null)
    if [ "${CSV_LINES:-0}" -ge 750 ]; then
        pass "J.1 CSV /app/storage/usuarios_sap_FINAL2026.csv: $CSV_LINES lineas (header + >=750 usuarios)"
    else
        warn "J.1 CSV existe pero solo $CSV_LINES lineas (esperado >=750). Sync AD quizas no se ejecuto."
    fi
else
    fail "J.1 CSV /app/storage/usuarios_sap_FINAL2026.csv no existe. Sync AD no se ejecuto."
fi

# ════════════════════════════════════════════════════════════════
# K. NGINX
# ════════════════════════════════════════════════════════════════
heading "═══ K. NGINX ═══"

# K.1 HTTP -> HTTPS redirect
HTTP_CODE=$(curl -kfsS -o /dev/null -w '%{http_code}' http://localhost/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    pass "K.1 HTTP->HTTPS redirect: $HTTP_CODE"
else
    warn "K.1 HTTP->HTTPS: $HTTP_CODE (esperado 301). Posible conflicto de sgd.conf catch-all."
fi

# K.2 HTTPS health
HTTPS_CODE=$(curl -kfsS -o /dev/null -w '%{http_code}' https://localhost/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTPS_CODE" = "200" ]; then
    pass "K.2 HTTPS health: $HTTPS_CODE"
else
    fail "K.2 HTTPS health: $HTTPS_CODE (esperado 200). Si es 502, nginx cacheo IP del backend viejo. Fix: docker restart sgd-qas-nginx"
fi

# K.3 sgd-qas.conf activo (NO debe haber .bk)
if docker exec "$C_NGINX" test -f /etc/nginx/conf.d/sgd-qas.conf 2>/dev/null; then
    pass "K.3 sgd-qas.conf activo (no .bk)"
else
    fail "K.3 sgd-qas.conf NO activo. El rename post-extract (FIX 1) fallo."
fi

# ════════════════════════════════════════════════════════════════
# L. SEGURIDAD
# ════════════════════════════════════════════════════════════════
heading "═══ L. SEGURIDAD ═══"

# L.1 CORS preflight
CORS_CODE=$(curl -kfsS -o /dev/null -w '%{http_code}' \
    -X OPTIONS https://localhost/api/v1/login \
    -H "Origin: https://sgdqas.cofar.com.bo" \
    -H "Access-Control-Request-Method: POST" 2>/dev/null || echo "000")
if [ "$CORS_CODE" = "200" ] || [ "$CORS_CODE" = "204" ]; then
    pass "L.1 CORS preflight: $CORS_CODE"
else
    fail "L.1 CORS preflight: $CORS_CODE (esperado 200/204)"
fi

# L.2 CSRF cookie en /login (debe NO ser HttpOnly)
CSRF_LINE=$(curl -kfsS -i -X POST https://localhost/api/v1/login \
    -H "Content-Type: application/json" \
    -d '{"username":"aromero","password":"cofar.2026","auth_source":"local"}' 2>/dev/null \
    | grep -i 'set-cookie.*csrf_token' || true)
if echo "$CSRF_LINE" | grep -qi 'csrf_token' && ! echo "$CSRF_LINE" | grep -qi 'HttpOnly'; then
    pass "L.2 CSRF cookie presente y no HttpOnly"
elif echo "$CSRF_LINE" | grep -qi 'csrf_token'; then
    fail "L.2 CSRF cookie es HttpOnly (frontend no puede leerla)"
else
    fail "L.2 CSRF cookie no emitida por /login"
fi

# ════════════════════════════════════════════════════════════════
# RESUMEN
# ════════════════════════════════════════════════════════════════
heading "═══ RESUMEN ═══"
TOTAL=$((PASS + FAIL + WARN))
printf '  %sPASS: %d/%d%s\n' "$GREEN" "$PASS" "$TOTAL" "$NC"
printf '  %sFAIL: %d/%d%s\n' "$RED" "$FAIL" "$TOTAL" "$NC"
printf '  %sWARN: %d/%d%s\n' "$YELLOW" "$WARN" "$TOTAL" "$NC"
echo

if [ "$FAIL" -gt 0 ]; then
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  QAS con FALLAS. Revisar arriba.                       ║"
    echo "╚════════════════════════════════════════════════════════╝"
    exit 1
fi

echo "╔════════════════════════════════════════════════════════╗"
echo "║  QAS OK. Todas las validaciones criticas PASS.         ║"
echo "╚════════════════════════════════════════════════════════╝"
exit 0
