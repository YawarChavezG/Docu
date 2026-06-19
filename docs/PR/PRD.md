# PRD — COFAR SGD (Sistema de Gestión Documental)

> **Project Requirements Document** — Fuente única de verdad para saber qué se construyó y qué falta.
> **Última actualización:** 2026-06-18 (sesión 29)
> **Stack confirmado:** FastAPI 0.137 + PostgreSQL 16 + Redis 7 + Celery 5.6 + Alpine.js 3.15 + Docker Compose
> **Estado actual:** R1+R2 100% cerrados · 22 fixes validados · 217/228 tests PASS · Pendiente: R3 (workflow) + deploy QAS v1.1.0-qas

---

## 1. Resumen ejecutivo

| Campo | Valor |
|---|---|
| Cliente | COFAR SRL (Bolivia) — Industria farmacéutica |
| Usuarios objetivo | ~750 (pico en exámenes) |
| Ambientes | DES (localhost:8080) · QAS (sgdqas.cofar.com.bo) · PRD (TBD) |
| Metodología | Iterativa por reuniones R1–R6 |
| R1+R2 | ✅ **Cerrados al 100%** (incluye 22 fixes post-testing) |
| Tag actual | `v1.0.0-qas` (sesión 19). Pendiente `v1.1.0-qas` |
| Sesiones totales | 29 sesiones (14-jun → 18-jun 2026) |

---

## 2. Estructura del monorepo

```
C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES\
├── frontend/          # SPA Alpine.js (Vite 8) — 86 archivos, ~15K líneas
│   ├── src/
│   │   ├── pages/     # 29 páginas (2,759 líneas solo Parametrizacion.js)
│   │   ├── components/# 23 componentes (ProfileModal 570 líneas)
│   │   ├── services/  # 3 servicios API
│   │   ├── store/     # 4 stores (auth 377 líneas)
│   │   ├── data/      # 16 archivos mock legacy (código muerto)
│   │   └── utils/     # api.js, config.js, icons.js, exportExcel.js
│   └── tailwind.config.js, vite.config.js, postcss.config.js
├── backend/           # FastAPI 0.137 + SQLAlchemy 2.0 async — 91 archivos .py
│   ├── app/
│   │   ├── api/v1/    # 19 routers, 87 endpoints REST
│   │   ├── models/    # ~22 tablas + 16 enums
│   │   ├── schemas/   # 14 archivos Pydantic v2
│   │   ├── services/  # 8 servicios (AD, storage, correlativo, etc.)
│   │   ├── core/      # 5 archivos (config, database, permissions, audit, excel_export)
│   │   └── workers/   # Celery (beat schedule: desactivar ausencias 00:05)
│   ├── alembic/       # 18 migraciones (head: drop_modulos_s26)
│   ├── tests/         # 23 archivos, ~228 tests
│   └── scripts/       # 8 seeds + 3 CLI + 3 rotos (B7)
├── deploy/
│   ├── docker-compose.yml      # DES (8 servicios)
│   ├── docker-compose.qas.yml  # QAS (HTTPS, workers=2)
│   └── nginx/                  # proxy + SSL
├── docs/PR/
│   ├── RADIOGRAFIA-TOTAL-18-06-2026.md  # Radiografía completa
│   ├── BITACORA.md              # Historial de sesiones
│   ├── ESTADO.md                # Progreso actual
│   ├── DECISIONES.md            # ADRs activos
│   ├── INICIO-SESION.md         # Prompt maestro
│   ├── PRD.md                   # Este archivo
│   └── R2-PLAN-EJECUCION.md     # Plan R2 (histórico)
└── scripts/           # .bat/.sh orquestadores
```

---

## 3. Lo que está construido (R1 + R2)

### Backend (87 endpoints)
- Auth (login LDAP/local + logout + /me + verify-password 2FA + impersonate)
- Usuarios (CRUD + sync AD + export XLSX/CSV)
- Gerencias + Áreas (CRUD + mover + promover a gerencia)
- Catálogos: tipos_documento, estados, roles, configuracion_global, feriados, email_templates, matriz_enrutamiento_eto, semaforizacion_tarea
- Documentos (CRUD + búsqueda + preview-código + upload archivos + firma 2FA + envío a liberación)
- Bandeja (elaboración, revisión, aprobación, liberación)
- Ausencias (CRUD + vigente + flag usuario.ausente)
- Plantillas documentales (lista + download + audit)
- Audit log (lista + export)
- Admin impersonate (list + start + stop)

### Frontend (29 páginas)
- ✅ Login + Parametrización (7 tabs, consume API real)
- ✅ Wizard aprobación documento (3 pasos + firma 2FA)
- ✅ Versión editable (autocomplete real desde BD)
- ✅ Plantillas documentales (grid responsive 1/2/3/4 cols)
- ✅ Mi Perfil (ausencias, delegado, área con fallback AD)
- ❌ Bandeja, LiberacionDetalle, ListaMaestra, Revision, AprobacionFinal, Correccion (usan datos mock — pendiente R3)

### 22 fixes de sesión 25 validados
Todos los issues reportados por el cliente post-testing (17-jun) fueron resueltos y validados. Ver `RADIOGRAFIA-TOTAL.md` §8.

---

## 4. Lo que falta (R3+)

### 🔴 P0 — Bloqueantes
- B7: 3 scripts seed rotos (`seed_data.py`, `seed_local_test_users.py`, `seed_matriz_eto.py` importan `usuario_modulos` eliminado)
- CSRF middleware ausente (seguridad)
- Certificado HTTPS QAS (autofirmado → Let's Encrypt)
- Bumpear tag `v1.1.0-qas`

### 🟡 P1 — R3 (Workflow ETO)
- Refactor Bandeja.js, LiberacionDetalle.js, ListaMaestra.js, Revision.js, AprobacionFinal.js, Correccion.js (6 páginas con datos mock)
- Encadenar flujo completo: revisión → aprobación → liberación
- Tablas N:M para tareas individuales con timestamps
- Cron SLA (reasignación por deadline)
- Árbol Outlook dinámico desde BD
- #13 Deuda delegado (139 usuarios sin delegado)

### 🟢 P2 — Mejoras / Cleanup
- 16 archivos mock en `frontend/src/data/` (código muerto)
- B1: `Gerencia.areas` cascade cleanup
- B3: `vite.config.js` manualChunks (falla en build)
- Modelos SQLAlchemy sin `__repr__`

### Backlog (R4-R6)
- R4: Office 365 + IA similitud + embeddings + webhook + cron sync AD
- R5: PDF custodiado + marca de agua + obsolescencia + lista maestra + vencimientos
- R6: Capacitación + exámenes + certificados + copias CC/CN + BI + chat RAG

---

## 5. BD Actual (22 tablas, head: drop_modulos_s26)

Organización: gerencias, areas, usuarios, roles, usuario_roles, modulos
Documentos: documentos, documento_flujo, archivos_adjuntos
Workflow: audit_log, ausencias, firmas_digitales, delegaciones, log_sincronizacion_ad
Catálogos: configuracion_global, feriados, email_templates, matriz_enrutamiento_eto, tipos_documento, estados, semaforizacion_tarea

> Tabla `usuario_modulos` eliminada (migración s26). Control de acceso por rol vía `auth.js:canAccess()`.

---

## 6. Stack Docker (8 servicios)

Nginx(:8080) → Frontend Vite(:5173) + Backend FastAPI(:18000) + PostgreSQL(:25432) + Redis(:26379) + MailHog(:8025) + Celery Worker + Celery Beat
