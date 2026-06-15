# PRD — COFAR SGD (Sistema de Gestión Documental)

> **Project Requirements Document** — Fuente única de verdad para que cualquier IA o developer humano sepa exactamente qué construir, cómo, y en qué orden.
> **Última actualización:** 2026-06-14
> **Stack confirmado:** FastAPI 0.137 + PostgreSQL 16 + Redis 7 + Celery 5.6 + Alpine.js 3.15 + Docker Compose
> **Objetivo inmediato:** R1 (Seguridad + Parametrización) y R2 (Wizard de creación) **completas para el martes 17 de junio de 2026** (luego del finde).

---

## 1. Resumen ejecutivo

| Campo | Valor |
|---|---|
| Cliente | COFAR SRL (Bolivia) |
| Industria | Farmacéutica (normativa ISO/GMP) |
| Usuarios objetivo | 750 (pico en exámenes) |
| Ambientes | DES (este repo) · QAS (Debian VM) · PRD (TBD) |
| Metodología | Iterativa por reuniones R1–R6 |
| Fecha objetivo R1+R2 | **17 de junio 2026** (3 días desde hoy) |
| Stack | FastAPI 0.137 / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / Celery 5.6 / Alpine.js / Docker |

---

## 2. Estructura del monorepo (NO modificar sin actualizar este doc)

```
C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES\
├── frontend/          # SPA Alpine.js (Vite 8) — copiado del original sin cambios funcionales
├── backend/           # FastAPI 0.137 + SQLAlchemy 2.0 async
│   ├── app/
│   │   ├── main.py
│   │   ├── core/         # config, database, security, deps
│   │   ├── api/v1/       # routers (auth, documentos, usuarios, organigrama, parametrizacion)
│   │   ├── models/       # SQLAlchemy ORM
│   │   ├── schemas/      # Pydantic
│   │   ├── services/     # lógica de negocio
│   │   ├── workers/      # Celery
│   │   └── middleware/   # CSP, rate limit, audit
│   ├── alembic/          # migraciones
│   ├── requirements/     # base.txt / dev.txt / prod.txt
│   ├── tests/
│   ├── scripts/          # seed_data.py, etc.
│   ├── Dockerfile
│   └── alembic.ini
├── deploy/
│   ├── docker-compose.yml       # DESARROLLO (este ambiente)
│   ├── docker-compose.prod.yml  # PRODUCCIÓN (futuro)
│   ├── nginx/
│   └── scripts/
├── docs/                          # documentación funcional
│   ├── ARQUITECTURA.md
│   ├── ARQUITECTURA-DB.md         # diagrama 24 tablas
│   ├── RUNBOOK.md
│   └── PR/                        # este folder (Project Requirements)
│       ├── PRD.md                 # este archivo
│       ├── DECISIONES.md          # ADRs
│       ├── PLAN-EJECUCION.md      # plan de tareas (LEGIBLE POR IA)
│       ├── ESTADO.md              # progreso actualizado
│       └── CHECKLIST-R1.md        # criterios de aceptación R1
├── scripts/                       # scripts auxiliares del repo
├── README.md
├── Makefile
├── .env.example
└── .gitignore
```

---

## 3. Convenciones obligatorias (toda IA que toque este proyecto debe respetarlas)

### 3.1 Idioma
- **Código:** identificadores en inglés (`get_user_by_id`, `authenticate`).
- **Comentarios:** español (es el idioma del equipo).
- **Mensajes al usuario:** español (es la app final).
- **Logs:** español con timestamps en ISO 8601.

### 3.2 Versiones (validadas el 2026-06-14 contra registries oficiales)
| Componente | Versión | Fuente |
|---|---|---|
| Python | 3.12-slim-bookworm | Docker Hub |
| FastAPI | 0.137.0 | PyPI |
| SQLAlchemy | 2.0.50 | PyPI |
| Pydantic | 2.13.4 | PyPI |
| Alembic | 1.18.4 | PyPI |
| Celery | 5.6.3 | PyPI |
| Uvicorn | 0.49.0 | PyPI |
| asyncpg | 0.31.0 | PyPI |
| redis-py | 5.2.1 | PyPI (NO 8.x — incompatible con Celery 5.6) |
| MSAL | 1.37.0 | PyPI |
| ldap3 | 2.9.1 | PyPI |
| PostgreSQL | 16-alpine | Docker Hub |
| Redis | 7-alpine | Docker Hub |
| Nginx | 1.27-alpine | Docker Hub |
| MailHog | latest | Docker Hub |
| Node | 22-alpine | Docker Hub |
| Vite | 8.0.16 | npm |
| Alpine.js | 3.15.12 | npm |
| Tailwind | 3.4.19 | npm (NO 4.x — API diferente) |
| DOMPurify | 3.4.10 | npm (CVE fix) |

### 3.3 Puertos (NO cambiar sin actualizar este doc)
- **8080** → Nginx (entrypoint navegador)
- **5173** → Vite HMR (frontend directo)
- **18000** → FastAPI (debug directo)
- **15432** → PostgreSQL
- **16379** → Redis
- **8025** → MailHog UI
- **1025** → MailHog SMTP

### 3.4 Patrón de Git
- `main` → rama protegida, solo PRs.
- `feat/RX-descripcion` → feature de la reunión RX.
- `fix/descripcion-corta` → bugfix.
- Commits: `tipo(scope): descripción` — ej. `feat(auth): añadir login con LDAP stub`.

### 3.5 Estilo Python
- PEP 8 + Black (line-length 100).
- Type hints obligatorios.
- Docstrings en español (Google style).
- Imports: stdlib → third-party → local.

### 3.6 Estilo Frontend
- ES modules (`type: module`).
- Sin TypeScript por ahora.
- Componentes Alpine en archivos `pages/*.js` (mantener patrón original).

---

## 4. Arquitectura objetivo (resumen ejecutivo)

```
┌─────────────────────────────────────────────────────┐
│ Nginx :8080 (reverse proxy + rate limit)            │
│   ├─ /  ──────────► Frontend (Vite dev :5173)       │
│   └─ /api/ ──────► Backend FastAPI :8000            │
│                       ├─ PostgreSQL :5432           │
│                       ├─ Redis :6379 (cache/broker) │
│                       └─ Celery worker/beat         │
└─────────────────────────────────────────────────────┘
```

**Capas:**
- **Frontend:** Alpine.js (SPA). Mantiene la lógica de UI/UX ya construida. Solo refactorizamos para llamar al backend.
- **Backend:** FastAPI con SQLAlchemy async. Endpoints REST documentados con OpenAPI.
- **DB:** PostgreSQL 16 con Alembic para migraciones. Diseño relacional estricto (24 tablas para R1+R2).
- **Cache/Broker:** Redis 7. Sirve para rate limit, sesiones y broker de Celery.
- **Workers:** Celery 5.6 con Redis broker. Tareas async (emails, IA) y cron (SLA, vencimientos).

---

## 5. Tablas de BD (R1+R2) — **28 tablas** agrupadas por dominio (ACTUALIZADO sesión 2)

> Detalle completo en `docs/ARQUITECTURA-DB.md`. Resumen aquí para que la IA sepa qué migrar primero.

### A. Organización (5)
- `gerencias` — gerencias de 1er nivel (8-10 sembradas)
- `areas` — sub-unidades (FK gerencia_id) (~25 sembradas con sigla)
- `usuarios` — sincronizados desde AD (con campos stub en DES)
- `roles` — **5 sembrados**: `ADMIN`, `ETO`, `ELABORADOR-REVISOR`, `ELABORADOR-REVISOR-APROBADOR`, `VISUALIZADOR-CL-EVAL`
- `usuario_roles` — N:M (un usuario puede tener varios roles en teoría, aunque COFAR usa 1)

### B. Permisos por módulo (2) — **NUEVO en sesión 2**
- `modulos` — catálogo de 10 módulos (`BANDEJA`, `LISTA_MAESTRA`, `CONSULTAR_DOCUMENTOS`, `MIS_EVALUACIONES`, `ASISTENTE_IA`, `NUEVA_SOLICITUD`, `PLANTILLAS_DOCUMENTALES`, `PARAMETRIZACION`, `REPORTES`, `TODOS`)
- `usuario_modulos` — N:M usuario↔módulo (la realidad de COFAR, no RBAC derivado del rol)

### C. Configuración global (3)
- `configuracion_global` — clave/valor (SLA, vigencia, semáforo, paginación, max_archivos_por_solicitud=20, max_mb_por_archivo=20, umbral_similitud_ia=0.60)
- `feriados` — calendario Bolivia (incluye los 11 del Gantt)
- `parametros_enlace` — links parametrizables

### D. Catálogos documentales (2) — **NUEVO en sesión 2**
- `tipos_documento` — **13 sembrados** con `codigo INT (1-14)`, `nombre`, `sigla_legacy` (MET, PRO, etc.), `vigencia_anos nullable`, `es_indefinido bool`, `max_descargas_dia`, `observacion`
- `plantillas_documentales` — catálogo de los 7 archivos reales (.docx/.xlsx) en `MATRICES/PLANTILLAS DOCUMENTALES/`

### E. Documentos y versiones (3)
- `documentos_familia` — agrupación por código
- `documento_versiones` — cada versión
- `codigo_contador` — **secuencia atómica por (area_id, tipo_documento_codigo)** (nomenclatura `{sigla_area}-{codigo_tipo}-{correlativo_3_digitos} v{version_2_digitos}`)

### F. Workflow (3)
- `workflow_tareas` — tareas asignadas
- `bitacora_timeline` — historial INMUTABLE
- `audit_log` — log general

### G. Archivos y descargas (2)
- `archivos_adjuntos` — archivos subidos
- `log_descargas` — contador diario (validación contra `tipos_documento.max_descargas_dia`)

### H. Plantillas email (1)
- `email_templates`

### I. Matriz de enrutamiento (1)
- `matriz_enrutamiento_eto` — 10 filas sembradas (Aracely + Cecilia, 8 gerencias)

### J. Firma digital y autenticación (2) — **NUEVO en sesión 2**
- `firmas_digitales` — log de verificaciones 2FA: id, usuario_id, accion, recurso_tipo, recurso_id, timestamp, ip, resultado_exito. Usado por todos los flujos que requieren firma (US-2.06, 3.03, 3.04, 6.03, 7.03, 7.06)
- `sesiones_activas` — opcional, alternativo a JWT-only (decidir en R1)

### K. Soporte R1-R2 (4)
- `delegaciones` — backup de cada usuario (156 usuarios con esta alerta activa)
- `ausencias` — vacaciones/licencias programadas
- `log_sincronizacion_ad` — historial de syncs con AD (manual + job 00:05)
- `notificaciones_email` — cola de emails a enviar

### L. SharePoint config (1)
- `sharepoint_config` — sitio + drive de COFAR (en QAS; stub en DES)

**Total R1+R2: 28 tablas.** Las 7 tablas restantes (capacitación, copias, reportes) se difieren a R3+.

---

## 5.1 Nomenclatura del código de documento (ADR-011)

```
{sigla_area}-{codigo_tipo}-{correlativo_3_digitos}  v{version_2_digitos}
```

**Ejemplo:** `CC-5-001 v01`
- `CC` = sigla del **área** (Control de Calidad)
- `5` = código numérico del **tipo de documento** (PROCEDIMIENTO)
- `001` = correlativo secuencial dentro de (área, tipo)
- `v01` = versión de 2 dígitos (`v00` = creación, `v01+` = actualización)

**Razón:** Compatibilidad con sistema legacy de COFAR. La sigla NO es del tipo sino del área.

**Tabla de equivalencias (nomenclatura legacy):**

| Sigla área | Gerencia |
|---|---|
| CC, DT, EST, GAC, MCB, REG, VAL, FV, BEQ, IDF, DEI | CALIDAD |
| ACD, BET, LE, LNE, SIMA, SMS, SNE, CB, PRO | PLANTA |
| MLB, TAL, ADM | RECURSOS HUMANOS |
| (por definir) | ADMIN-FINANCIERA, COMERCIAL, GENERAL, TERCIA, LOGISTICA, OPERACIONES, AUDITORIA INTERNA |

---

## 6. Alcance R1 (martes 17-jun) — Criterios de aceptación verificables

### US-1.01 a US-1.07 (Autenticación, perfil, delegaciones)
- [ ] Un usuario puede hacer login con credenciales corporativas (LDAP en QAS, stub en DES).
- [ ] El sistema reconoce el rol (eto/estandar/visualizador/admin) y muestra menú correspondiente.
- [ ] El usuario ve su perfil con avatar, nombre, cargo, área, gerencia.
- [ ] El usuario puede configurar un delegado (no puede ser él mismo).
- [ ] El usuario puede programar ausencia (fecha desde/hasta).
- [ ] Al ausentarse, las tareas que lleguen a su bandeja se redirigen al delegado.
- [ ] Tras 10 días hábiles sin atender una tarea, se reasigna al delegado (cron 23:59).

### US-9.05 y US-9.06 (Parametrización)
- [ ] El ETO puede listar/crear/editar gerencias y áreas.
- [ ] El ETO puede mover un área entre gerencias.
- [ ] El ETO puede promover un área a gerencia.
- [ ] El ETO puede gestionar usuarios (CRUD básico).

### US-1.07 (Matriz de enrutamiento)
- [ ] El ETO puede vincular cada gerencia con un analista ETO responsable.
- [ ] Si el ETO está ausente, se balancea round-robin a otro ETO disponible.

### Seguridad
- [ ] Sesión via cookie HttpOnly + Secure (en prod) + SameSite=Lax.
- [ ] CSRF token en cookie separada + header `X-CSRF-Token`.
- [ ] Rate limit en Nginx: 30 req/s por IP, 5 req/min para /auth/*.
- [ ] Rate limit en backend con `slowapi`: 100 req/min por usuario.

---

## 7. Alcance R2 (martes 17-jun) — Criterios de aceptación verificables

### US-2.00 a US-2.06 (Wizard 4 pasos)
- [ ] El usuario puede iniciar una solicitud nueva desde "Nueva Solicitud".
- [ ] Puede completar Paso 1: datos del documento (tipo, gerencia, área, título).
- [ ] Puede completar Paso 2: vigencia, requiere evaluación, requiere lectura, árbol de Outlook.
- [ ] Puede completar Paso 3: subir archivo principal (.docx) y anexos (.docx/.xlsx).
- [ ] Puede completar Paso 4: revisores y aprobadores (mínimo 1+1), reemplazos.
- [ ] Al firmar digitalmente, la solicitud se envía a la bandeja del ETO.

### Reglas de negocio
- [ ] Código correlativo automático: `PRO-CAL-001`, generado atómicamente (sin duplicados).
- [ ] Tamaño máximo de archivo: 20MB (HTTP 413 si excede).
- [ ] Tipo MIME: principal solo `.docx`, anexos `.docx`/`.xlsx`.
- [ ] El ETO ve la solicitud en su bandeja con su código asignado.
- [ ] El monitor de consulta de documentos muestra el nuevo proceso en su bitácora.

---

## 8. Plan de ejecución por tarea (LEGIBLE POR IA)

> **Cada vez que arranques una sesión conmigo, te voy a pedir:**
> 1. Lee `docs/PR/PLAN-EJECUCION.md` (este archivo)
> 2. Lee `docs/PR/ESTADO.md` para saber qué está hecho
> 3. Identifica la siguiente tarea PENDIENTE con `status: pendiente`
> 4. Ejecútala
> 5. Marca como `completada` en ESTADO.md

### Lista de tareas R1+R2 (en orden estricto de ejecución)

| # | Tarea | Tiempo est. | Dependencias | Estado |
|---|---|---|---|---|
| 0 | Validar entorno (Docker, Python, Node) | 5min | — | ✅ COMPLETADO 14-jun |
| 1 | Crear estructura monorepo | 15min | 0 | ✅ COMPLETADO 14-jun |
| 2 | Crear docker-compose.yml + Dockerfiles | 30min | 1 | ✅ COMPLETADO 14-jun |
| 3 | Crear requirements + scripts de init | 15min | 1 | ✅ COMPLETADO 14-jun |
| 4 | Crear backend/app/main.py + health + auth stub | 30min | 2,3 | ✅ COMPLETADO 14-jun |
| 5 | Crear .env raíz + .env.example | 10min | 1 | ✅ COMPLETADO 14-jun |
| 6 | **Levantar la stack y validar docker compose up** | 20min | 2,3,4,5 | ⏳ SIGUIENTE |
| 7 | Crear schema SQLAlchemy de las 5 tablas de Organización (A) | 30min | 4 | pendiente |
| 8 | Crear migración Alembic inicial | 20min | 7 | pendiente |
| 9 | Crear endpoints `/api/v1/auth/login` con stub de usuarios | 30min | 4 | pendiente |
| 10 | Crear endpoints `/api/v1/usuarios` (GET paginado, GET por id, PATCH admin) | 30min | 7,8 | pendiente |
| 11 | Crear endpoints `/api/v1/organigrama` (gerencias + áreas + jefe) | 30min | 7,8 | pendiente |
| 12 | Crear endpoints `/api/v1/gerencias` (CRUD) y `/api/v1/areas` (CRUD) | 40min | 7,8 | pendiente |
| 13 | Crear endpoints `/api/v1/usuarios/{id}/delegado` y `/ausencia` | 30min | 7,8 | pendiente |
| 14 | Crear seed_data.py con 4 usuarios + 2 gerencias + 4 áreas | 20min | 8 | pendiente |
| 15 | Frontend: crear `src/utils/api.js` con `apiFetch` robusto | 45min | 4 | pendiente |
| 16 | Frontend: refactorizar `src/store/auth.js` para usar API real | 30min | 15 | pendiente |
| 17 | Frontend: refactorizar `src/pages/Login.js` para usar API real | 20min | 15,16 | pendiente |
| 18 | Frontend: integrar `src/pages/Parametrizacion.js` pestaña Usuarios | 30min | 10,15 | pendiente |
| 19 | Sanear 4 `x-html` con DOMPurify en frontend | 20min | — | pendiente |
| 20 | Agregar CSP meta tag en `index.html` | 10min | — | pendiente |
| 21 | Configurar rate limit con `slowapi` en backend | 20min | 4 | pendiente |
| 22 | **TESTING R1: login, perfil, parametrización, end-to-end** | 60min | 6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21 | pendiente |
| 23 | Crear schema SQLAlchemy de las 3 tablas de Documentos (C) | 30min | 7 | pendiente |
| 24 | Crear schema SQLAlchemy de las 3 tablas de Workflow (D) | 30min | 7 | pendiente |
| 25 | Crear schema SQLAlchemy de las 2 tablas de Archivos (E) | 20min | 7 | pendiente |
| 26 | Crear schema SQLAlchemy de las 5 tablas de Soporte (I) | 30min | 7 | pendiente |
| 27 | Crear schema SQLAlchemy de las 6 tablas misceláneas (B, F, G, H) | 30min | 7 | pendiente |
| 28 | **Migración Alembic 002: 19 tablas restantes** | 30min | 23-27 | pendiente |
| 29 | Servicio `correlativo_service.py` con `SELECT FOR UPDATE` | 45min | 23 | pendiente |
| 30 | Trigger SQL de obsolescencia automática | 30min | 23 | pendiente |
| 31 | Endpoints `/api/v1/documentos` (CRUD borrador paso 1, 2, 3, 4) | 60min | 23,24,25,29 | pendiente |
| 32 | Endpoint `POST /api/v1/documentos/{id}/archivos` con validación MIME | 45min | 25,31 | pendiente |
| 33 | Endpoint `POST /api/v1/documentos/{id}/enviar` con firma | 30min | 24,31 | pendiente |
| 34 | Storage service: `LocalStorage` (volumen) + stub `SharePointStorage` | 30min | 32 | pendiente |
| 35 | Endpoint `GET /api/v1/bandeja?tipo=liberacion` para ETO | 30min | 24 | pendiente |
| 36 | Endpoint `POST /api/v1/documentos/{id}/liberar` (fan-out a revisores) | 45min | 24 | pendiente |
| 37 | Endpoint `GET /api/v1/bandeja` general (por tipo y estado) | 30min | 24 | pendiente |
| 38 | Frontend: refactorizar `src/pages/Bandeja.js` para usar API | 45min | 37,15 | pendiente |
| 39 | Frontend: refactorizar `src/pages/LiberacionDetalle.js` | 60min | 36,15 | pendiente |
| 40 | Frontend: refactorizar `src/pages/ListaMaestra.js` (estado en_revision/en_elaboracion) | 30min | 31,15 | pendiente |
| 41 | **TESTING R2: wizard completo, envío, bandeja ETO, liberación** | 90min | 6, todos los 2x-4x | pendiente |
| 42 | Documentación: actualizar `docs/RUNBOOK.md` con cómo usar la stack | 30min | 6 | pendiente |
| 43 | Documentación: actualizar `docs/ARQUITECTURA.md` y `ARQUITECTURA-DB.md` | 60min | 41 | pendiente |

**Total estimado: ~16 horas de trabajo efectivo.** Si la IA tarda ~3-5 min por tarea, son 1-2 sesiones intensivas.

---

## 9. Cómo arrancar cada sesión conmigo (CHECKLIST)

**Al inicio de cada sesión, dime literalmente:**

> "Lee docs/PR/PLAN-EJECUCION.md y docs/PR/ESTADO.md. Identifica la siguiente tarea pendiente y ejecútala."

Yo voy a:
1. Leer los dos archivos.
2. Reportarte el estado actual y la siguiente tarea.
3. Preguntarte si la ejecuto o si quieres que priorice otra cosa.
4. Ejecutar paso a paso con outputs visibles.
5. Actualizar `docs/PR/ESTADO.md` con el progreso.

**Al final de cada sesión, voy a:**
1. Marcar las tareas completadas en `ESTADO.md`.
2. Si la sesión fue muy larga, hacer commit con mensaje descriptivo.
3. Reportarte un resumen: qué se hizo, qué quedó pendiente, y si hay bloqueos.

---

## 10. Reglas de oro (NO ROMPER)

1. **No inventar datos.** Si una tabla no existe, créala con Alembic. No hardcodear arrays.
2. **No usar datos del frontend (src/data/*.js) en el backend.** El backend es la única fuente de verdad.
3. **Toda mutación pasa por API.** El frontend NUNCA modifica estado directamente sin pasar por backend.
4. **Validar con el cliente antes de cambiar stack.** Esto está en este PRD.
5. **No commitear secretos.** El `.env` está en `.gitignore`.
6. **Tests antes de marcar como hecho.** Cada US tiene criterios de aceptación que se prueban.
7. **Documentar decisiones en `docs/PR/DECISIONES.md`** (formato ADR: contexto, decisión, consecuencia).
8. **Versiones fijas, no `latest`.** Cualquier upgrade se documenta en este PRD.

---

## 11. Riesgos y mitigaciones

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | Docker Desktop se cae a media sesión | `docker info` antes de cada compose up |
| 2 | Falla una migración Alembic | `alembic downgrade -1` + fix + retry |
| 3 | El frontend original tiene errores que rompen el build | Si pasa, copiar backup antes de tocar; reportar |
| 4 | El QAS (Debian) no tiene las mismas versiones que DES | El docker-compose.prod.yml fija versiones de imagen (`postgres:16-alpine`, no `postgres:latest`) |
| 5 | El cliente cambia de opinión sobre alcance | Este PRD es la versión actual; cambios se negocian |
| 6 | Se acaban las horas y R1+R2 no está completo | Priorizar criterios de aceptación sobre extras |
| 7 | QAS no tiene acceso a Graph API (Office 365) | El `GRAPH_ENABLED=false` desactiva; stubs en su lugar |

---

## 12. Estado del proyecto (live tracker)

> **Actualizar este archivo al final de cada sesión.** Se renombra `ESTADO.md` para tracking.

### Versión actual
- **v0.1.0-dev** — 2026-06-14

### Progreso R1
- [x] Validar entorno
- [x] Crear estructura monorepo
- [x] Crear docker-compose.yml + Dockerfiles
- [x] Crear requirements
- [x] Crear backend/app/main.py + health + auth stub
- [x] Crear .env raíz + .env.example
- [ ] **Levantar la stack y validar `docker compose up`** (SIGUIENTE)

### Progreso R2
- [ ] (vacío hasta cerrar R1)

### Decisiones pendientes
- Ninguna bloqueante al momento.

---

## 13. Contactos

- **Product Owner:** Y. Chávez (Tercera SRL, en COFAR)
- **Tech Lead:** Mavis (asistente IA agentivo)
- **Cliente final:** COFAR SRL — Área de Sistemas
