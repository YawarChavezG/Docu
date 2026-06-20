# COFAR SGD — Agent Instructions

> Reglas operativas para que cualquier agente IA (Mavis, Cursor, etc.) trabaje correctamente en este monorepo.
> Última actualización: 2026-06-14 (sesión 1)

## Arquitectura

- **Monorepo** en `C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES\` con `frontend/` (Alpine.js + Vite) y `backend/` (FastAPI 0.137 + SQLAlchemy 2.0 async).
- **Stack completo en Docker Compose** (`deploy/docker-compose.yml`): nginx + frontend + backend + celery-worker + celery-beat + postgres + redis + mailhog.
- **Entry point navegador:** `http://localhost:8080` (Nginx).
- **DB:** PostgreSQL 16-alpine, expuesta en `localhost:25432` (no 5432 default — ver "Puertos" abajo).
- **Cache/Broker:** Redis 7-alpine, expuesto en `localhost:26379` (no 6379 default).

## Puertos NO estándar (importante)

Por error de binding en Docker Desktop sobre Windows, **NO usar 15432 ni 16379** como host ports. Ya están configurados a **25432** y **26379** en `.env`. NO cambiarlos a los "default" sin verificar antes con `netstat -ano | Select-String "<puerto>"`.

## Convenciones de archivos

- **Bitácora de sesión:** `docs/PR/BITACORA.md` — actualízala al cerrar sesión. Es la primera cosa que lee una nueva sesión para retomar contexto.
- **Estado del proyecto:** `docs/PR/ESTADO.md` — live tracker de las 43 tareas de R1+R2. Actualizar tabla cuando se completa una tarea.
- **Decisiones:** `docs/PR/DECISIONES.md` — ADRs en formato contexto/decisión/consecuencia.
- **Plan completo:** `docs/PR/PRD.md` § 8 — Lista de 43 tareas en orden estricto de ejecución.
- **Stack detail:** `docs/PR/PRD.md` § 3 — versiones validadas, convenciones de código, idioma.

## Comandos frecuentes

```bash
# Levantar todo
cd "C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES"
docker compose -f deploy/docker-compose.yml --env-file .env up -d

# Ver logs
docker compose -f deploy/docker-compose.yml logs -f backend

# Ver estado
docker compose -f deploy/docker-compose.yml ps

# Bajar todo
docker compose -f deploy/docker-compose.yml down

# Probar backend
curl.exe http://localhost:18000/health
curl.exe -X POST http://localhost:18000/api/v1/login -H "Content-Type: application/json" -d '{"username":"aromero","password":"cofar.2026"}'

# Probar a través de Nginx
curl.exe http://localhost:8080/api/v1/login -X POST -H "Content-Type: application/json" --data-binary @test_login.json
```

## Trampas conocidas

1. **PowerShell aliasa `curl` a `Invoke-WebRequest`**. Usar `curl.exe` directamente.
2. **JSON inline en PowerShell falla** (convierte comillas). Usar archivo: `echo '{"k":"v"}' > file.json` y luego `--data-binary @file.json`.
3. **El `docker-compose.yml` se valida al hacer `up`** — si el backend no tiene `app/workers/celery_app.py`, el comando celery falla. Mantener sincronizados los entrypoints del compose con los archivos de código.
4. **El prefijo del API es `/api/v1/`** y se aplica a nivel de router en `main.py`. Los archivos de routers individuales NO deben tener prefijo `/auth/` adicional — solo `@router.post("/login")` sin prefijo.
5. **Las migraciones Alembic no existen todavía** (R1 tarea #8). El comando `alembic upgrade head` está envuelto en `|| echo 'Sin migraciones aún'` para no romper el arranque.

## Stubs en DES (se reemplazan en QAS con vars de entorno)

- **LDAP/AD:** `LDAP_ENABLED=false` → 4 usuarios hardcoded en `app/api/v1/auth.py` (aromero, solicitante, admin, visualizador; todos con password `cofar.2026`).
- **Microsoft 365:** `GRAPH_ENABLED=false` → no se llama a Graph.
- **SMTP:** `SMTP_ENABLED=false` → emails van a MailHog en `localhost:8025`.

## Próxima sesión (tarea #7)

Crear schema SQLAlchemy de Organización: 5 tablas (`gerencias`, `areas`, `usuarios`, `roles`, `usuario_roles`).

**Archivos a crear:**
- `backend/app/models/gerencia.py`
- `backend/app/models/area.py`
- `backend/app/models/usuario.py`
- `backend/app/models/rol.py`
- `backend/app/models/__init__.py` (actualizar para exportar todo)

**Convenciones SQLAlchemy 2.0:**
- `from sqlalchemy.orm import Mapped, mapped_column`
- Usar tipos SQLAlchemy 2.0: `Mapped[int]`, `mapped_column(primary_key=True)`, etc.
- `relationship()` con `back_populates`.
- Timestamps: `created_at: Mapped[datetime] = mapped_column(server_default=func.now())`
- `__tablename__` en singular minúscula.

**No olvidar:** registrar los modelos en `backend/app/models/__init__.py` para que Alembic los detecte con `autogenerate`.
