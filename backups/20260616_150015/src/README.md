# COFAR SGD — Sistema de Gestión Documental

> Monorepo para el SGD de COFAR SRL (Bolivia). Stack: FastAPI + PostgreSQL + Redis + Celery + Alpine.js, todo contenerizado con Docker Compose.

## 🚀 Quick Start (desarrollo local en Windows)

```bash
# 1. Clonar o posicionarse en la raíz del proyecto
cd C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES

# 2. Crear archivo .env con tus variables (ya hay un .env.example)
copy .env.example .env

# 3. Levantar toda la stack
docker compose -f deploy/docker-compose.yml --env-file .env up -d

# 4. Ver logs
docker compose -f deploy/docker-compose.yml logs -f backend

# 5. Abrir en el navegador
# http://localhost:8080
```

## 📂 Estructura

```
SGD-DES/
├── frontend/          # SPA Alpine.js (Vite)
├── backend/           # FastAPI (Python 3.12)
├── deploy/            # docker-compose, nginx, scripts de despliegue
├── docs/              # Documentación + PRD
│   └── PR/            # Project Requirements
├── scripts/           # Scripts auxiliares del repo
└── README.md
```

## 🛠️ Servicios (puertos)

| Servicio | Puerto host | URL | Credenciales dev |
|---|---|---|---|
| Nginx (entrypoint) | **8080** | http://localhost:8080 | — |
| Frontend (Vite HMR) | 5173 | http://localhost:5173 | — |
| FastAPI directo (debug) | 18000 | http://localhost:18000/docs | — |
| PostgreSQL | 15432 | localhost:15432 | sgd / sgd |
| Redis | 16379 | localhost:16379 | — |

## 📚 Documentación

- [Arquitectura](docs/ARQUITECTURA.md)
- [Modelo de datos](docs/ARQUITECTURA-DB.md)
- [Runbook (operación)](docs/RUNBOOK.md)
- [PRD/Project Requirements](docs/PR/PRD.md)
- [Registro de decisiones (ADR)](docs/PR/DECISIONES.md)
- [Plan por reuniones R1-R6](docs/PR/PLAN-REUNIONES.md)

## 🔐 Stack

- **Backend:** Python 3.12, FastAPI 0.137, SQLAlchemy 2.0 (async), Alembic, Pydantic 2, Celery 5, Redis 7
- **DB:** PostgreSQL 16 (con pgvector para IA)
- **Auth:** JWT (HttpOnly cookies) + CSRF, LDAP3 para AD (stub por ahora)
- **Frontend:** Vite 5, Alpine.js 3, Tailwind CSS 3, DOMPurify
- **Proxy:** Nginx 1.27 con rate limit
- **PDF:** WeasyPrint + PyMuPDF (próximas fases)

## 🌍 Ambientes

| Ambiente | Ubicación | URL / Notas |
|---|---|---|
| **DES** (desarrollo) | Este repo, Windows del dev | http://localhost:8080 |
| **QAS** (pre-prod) | VM Debian del cliente, intranet | TBD |
| **PRD** (producción) | TBD | TBD |

## 📝 Licencia

Privado y confidencial — COFAR SRL © 2026.
