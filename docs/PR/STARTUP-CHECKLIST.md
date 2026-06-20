# STARTUP CHECKLIST — COFAR SGD (QAS / PRD)

> **Proposito:** checklist operacional para arrancar (o re-arrancar) el stack
> QAS/PRD en orden, validando cada paso, y registrando los pasos POST-DEPLOY
> que son responsabilidad del operador (no del script automatizado).
>
> **Ultima actualizacion:** 2026-06-20 (sesion 38 — R3 Fase 1 + 30 tablas + plantillas BD + seed_procesos).

---

## Cuando usar este checklist

- Primer deploy de un tag nuevo en QAS.
- Re-arranque de QAS tras un fix o incidente.
- Migracion a PRD (cuando se autorice).

**NO usar para DES** — DES usa `scripts\start-stack-des.bat` y todo el codigo
se monta en bind, no requiere seeds ni sync AD real.

---

## FASE 0 — Pre-deploy (en DES, ANTES de tocar QAS)

- [ ] Working tree limpio en rama `r3/workflow-revision-aprobacion`.
- [ ] Tests pytest verde: `cd backend && .venv\Scripts\python -m pytest tests/`.
- [ ] Tag nuevo creado: `git tag v1.1.1-qas` (o el que corresponda).
- [ ] Codigo commit + push a origin.
- [ ] `deploy/docker-compose.qas.yml` actualizado con TZ + healthchecks
      (validar contra este repo: `deploy/docker-compose.qas.yml`).
- [ ] `scripts/validate-qas.sh` actualizado: alembic head `r3_plantillas_table_s37`, conteos (semaforo=6, usuarios=757, estados=16, etc.), nuevas tablas R3.
- [ ] `scripts/start-stack-qas.sh` corregido (12 seeds, ver REQUIRED_FILES y SEEDS).

---

## FASE 1 — Deploy en QAS (ejecutar en el server)

```bash
# 1. Clonar / actualizar codigo en /opt/sgd/
ssh sistemas@sgdqas.cofar.com.bo
cd /opt/sgd
git fetch origin
git checkout v1.1.0-qas

# 2. Levantar stack
bash /opt/sgd/scripts/start-stack-qas.sh
```

**El script hace (en orden):**
1. Verifica prerequisitos.
2. Provisiona `/opt/sgd/backend/storage` con permisos correctos.
3. Levanta 8 servicios Docker (postgres, redis, mailhog, backend, celery-W/B, frontend, nginx).
4. Espera healthchecks.
5. Aplica permisos de storage dentro del container.
6. Aplica **12 seeds** idempotentes (seed_data, seed_organizacion, seed_tipos_documento, seed_estados, seed_feriados, seed_email_templates, seed_matriz_eto, seed_configuracion_global, seed_usuario_roles, **seed_procesos**, **seed_plantillas_db**, **seed_documentos** — este último opcional post-deploy, sesion 34).
7. Ejecuta `sync_ad_oficial.py` (solo si `LDAP_ENABLED=true`).
8. Imprime resumen + URLs.

---

## FASE 2 — Validacion automatica

```bash
bash /opt/sgd/scripts/validate-qas.sh
```

**Cubre las 12 categorias A-L:**
- A. Health (backend directo + via HTTPS, 8 servicios Up, openpyxl, Tiptap).
- B. Librerias.
- C. Migraciones (alembic head, semaforizacion_tarea existe, tipos_documento sin codigo_doc, enum 11).
- D. Datos BD (conteos esperados: roles=5, modulos=11, gerencias=10, areas=50, **usuarios=757**, tipos_documento=13, **estados=16**, feriados=20, **email_templates=11**, matriz_eto=10, **configuracion=11**, **semaforizacion_tarea=6**, **documentos=10**).
- E. Login (aromero BD Local + /me con cookies).
- F. Endpoints nuevos (audit-log, semaforizacion, impersonate/list).
- J. Sync AD (CSV generado con >=750 lineas).
- K. Nginx (HTTP->HTTPS redirect, HTTPS health, sgd-qas.conf activo).
- L. Seguridad (CORS preflight, CSRF cookie).

**Exit code:**
- `0` = todas las validaciones criticas PASS.
- `1` = alguna validacion fallo.
- `2` = error de conexion al server.

---

## FASE 3 — POST-DEPLOY (responsabilidad del OPERADOR)

> **Estos pasos NO los hace `start-stack-qas.sh`.**
> Requieren decision humana y/o archivos externos (Excel matriz).

### 3.1 CRITICO: Asignar roles reales con `run_matriz_import.py`

**Por que es critico:** durante el fresh-install de QAS, los 750+ usuarios
sincronizados del AD tienen rol `visualizador` por defecto (el seed
`seed_data.py` no asigna roles). El Excel `USUARIOS EXISTENTES A ABRIL.xlsx`
contiene la matriz oficial de roles por persona — hay que correrla para que
los usuarios tengan los permisos correctos.

**Comando (dentro del container backend):**

```bash
docker exec sgd-qas-backend python scripts/run_matriz_import.py \
    --excel "/app/docs/Diagramas_Matrices/MATRICES/USUARIOS EXISTENTES A ABRIL.xlsx"
```

**Pre-condiciones:**
- El Excel debe estar disponible en `/app/docs/` dentro del container.
  Si no esta, copiar primero:
  ```bash
  docker cp "/opt/sgd/docs/Diagramas_Matrices/MATRICES/USUARIOS EXISTENTES A ABRIL.xlsx" \
      sgd-qas-backend:/app/docs/Diagramas_Matrices/MATRICES/
  ```

**Comportamiento:**
- **Idempotente** sin `--update-existing`: solo agrega asignaciones nuevas.
- **Reporta counts** antes/despues (SELECT pre + post).
- Si la cantidad a aplicar difiere de la esperada, **pregunta** antes de commit.
- Si Excel no se encuentra o header es invalido, exit code 1.
- Si se cancela, exit code 2.

**Verificacion post-ejecucion:**

```bash
docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "
    SELECT u.username, r.codigo
    FROM usuarios u
    JOIN usuario_roles ur ON ur.usuario_id = u.id
    JOIN roles r ON r.id = ur.rol_id
    ORDER BY r.codigo, u.username
    LIMIT 50;
"
```

**Resultado esperado:** ~750 usuarios con su rol real (ETO, ELABORADOR-REVISOR,
ELABORADOR-REVISOR-APROBADOR, ADMIN, VISUALIZADOR), NO todos visualizador.

**Exit code:** `0` exito, `1` error fatal, `2` cancelado por usuario.

**NO OLVIDAR:** documentar en BITACORA.md la fecha y conteos finales
(roles asignados, warnings generados).

### 3.2 Validar manualmente con un usuario real

- [ ] Login en `https://sgdqas.cofar.com.bo` con un usuario NO stub
      (ej: usuario AD con rol ETO real).
- [ ] Verificar que la bandeja muestra documentos esperados para ese rol.
- [ ] Verificar que Parametrizacion > Usuarios muestra al usuario con
      su rol correcto (no "visualizador").
- [ ] Probar firma 2FA end-to-end (crear documento borrador + firmar).

### 3.3 Verificar certificado HTTPS

- [ ] Si el cert autofirmado expira, regenerar antes del deploy publico.
- [ ] Para QAS-public, considerar cert corporativo o Let's Encrypt
      (pendiente ADR).

### 3.4 Limpiar `usuarios_sap_FINAL2026.csv` (auditoria)

El sync AD genera el CSV en `/app/storage/` dentro del container. Si se desea
auditoria historica, copiar al host:
```bash
docker cp sgd-qas-backend:/app/storage/usuarios_sap_FINAL2026.csv \
    /opt/sgd/auditoria/sync_ad_$(date +%Y%m%d).csv
```

---

## FASE 4 — Smoke tests manuales (opcional, 5 min)

- [ ] Login aromero (stub local) — verifica 4 stubs DES funcionando.
- [ ] Login un usuario AD real — verifica LDAP contra `rodc.cofar.com.bo`.
- [ ] Crear documento borrador (wizard paso 1+2) — verifica catalogos BD.
- [ ] Firmar 2FA — verifica `FirmaDigital` insertada.
- [ ] Verificar MailHog recibe email de notificacion
      (en QAS, ver logs SMTP corporativo si `SMTP_ENABLED=true`).

---

## Tareas recurrentes

| Frecuencia | Tarea | Comando |
|---|---|---|
| Diaria 00:05 | Desactivar ausencias vencidas (cron celery-beat) | automatico |
| Cada 6 horas | Sync AD desde COFAR (cron celery-beat, sesion 33) | automatico |
| Manual | Sync AD on-demand desde UI | Parametrizacion > Usuarios > Sincronizar AD |
| Manual | Import matriz (si se actualiza el Excel) | seccion 3.1 |
| Bajo demanda | Restore BD QAS al clean state | `ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/restore_clean_state_qas.sh"` (sesion 34; requiere `docker restart sgd-qas-nginx` post-restore para fix 502) |

---

## Pendientes pre-PRD

- [ ] CSRF middleware (B2, sesion 28 backlog) — bloqueante pre-PRD.
- [ ] Cert HTTPS corporativo o Let's Encrypt (QAS publica).
- [ ] `restore_clean_state.sh` para QAS (solo existe `.bat` para DES).
- [ ] Hardening: rate limits, CSP, DOMPurify (R1 issues 19-21).

---

## Referencias

- `docs/PR/DEPLOY-QAS.md` — guia historica de deploy.
- `docs/PR/BITACORA.md` — bitacora de sesiones (incluye deploys pasados).
- `docs/PR/ESTADO.md` — estado actual de las tareas R1+R2+R3.
- `scripts/start-stack-qas.sh` — orquestador 1-click.
- `scripts/validate-qas.sh` — validador post-deploy 12 categorias.
- `backend/scripts/run_matriz_import.py` — asignador masivo de roles.

---

## Limitaciones conocidas (verificadas sesión 32)

### TZ display en `docker exec ... date`

`TZ: ${TZ}` está seteada en todos los servicios, pero `date(1)` muestra
`UTC` en:
- `sgd-qas-mailhog` (binario Go, no llama `time.LoadLocation`).
- `sgd-qas-frontend` (Node.js / Vite, el PID 1 es el proceso Node, no sh).

**El tiempo (epoch) es correcto.** Solo el label es UTC. Esto NO afecta:
- Timestamps de BD (`created_at`, `updated_at` en BD son -04).
- Logs de Python (formateo respeta TZ).
- Logs de nginx.
- Conexiones asyncpg/psycopg.

**Verificación real de TZ funcional:**
```bash
docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "SELECT created_at FROM audit_log ORDER BY id DESC LIMIT 1;"
# Muestra timestamp en -04 (America/La_Paz).
```

Referencia: ADR-066.

### Healthchecks QAS usan comandos Alpine-safe

Sesión 32 descubrió que 3 specs originales de healthcheck fallaban en las
imágenes Alpine. Versiones finales:

| Servicio | Healthcheck | Notas |
|---|---|---|
| celery-worker | `celery -A app.workers.celery_app inspect ping` | OK, retorna "1 node online" |
| celery-beat | `xargs -0 echo < /proc/1/cmdline \| grep -q 'celery_app beat'` | Alpine-safe (sin `ps`) |
| frontend | `wget -q --spider http://127.0.0.1:5173` | Alpine-safe (sin `curl`, sin DNS IPv6) |
| nginx | `pgrep -f 'nginx: master'` | Alpine-safe (sin `service`) |

Referencia: ADR-067, LEARNINGS X06 y X08.
