# Reuniones R3-R6 — Análisis completo del backlog

> **Fecha:** 2026-06-15
> **Fuentes:**
> - `docs/SISTEMA DE GESTION DOCUMENTAL - HISTORIAS DE USUARIO.pdf` (historias de usuario completas, R1-R6)
> - `docs/Sistema de Gestion Documental - Gantt_SGDv4.xlsx` hoja "Detalle de entregable" (Gantt y dependencias)
>
> **Propósito:** Complementar el `PRD.md` (que cubre solo R1+R2) con el backlog completo de las reuniones futuras, para que el equipo (humano + IA) tenga visibilidad del 100% del proyecto y pueda planificar dependencias.

---

## Estado de las reuniones

| Reunión | Estado | Fecha objetivo | Dependencias |
|---|---|---|---|
| R1 — Seguridad + Parametrización | 🟡 ~50% | **17-jun-2026** (3 días) | — |
| R2 — Wizard de creación | 🔴 0% | **17-jun-2026** (3 días) | R1 |
| R3 — Workflow ETO + Revisión/Aprobación | 🔴 0% | 1-jul-2026 (2 sem) | R1, R2 |
| R4 — Office 365 + IA + SLA | 🔴 0% | 15-jul-2026 (2 sem) | R3 |
| R5 — PDF + Lista Maestra + Vencimientos | 🔴 0% | 29-jul-2026 (2 sem) | R4 |
| R6 — Capacitación + Copias + BI + Chat | 🔴 0% | 12-ago-2026 (2 sem) | R5 |

---

## R3 — Control ETO + Workflow Base
**Complejidad:** 8.5 / 10 | **Estado:** PENDIENTE | **Dependencias:** R1, R2

### Épica(s) cubierta(s)
- Épica 4 (Control y Liberación ETO) — completa
- Épica 3 (Workflow de Revisión y Aprobación) — parcialmente

### Historias de Usuario pendientes
- **US-4.01:** Gestión de las tareas de Liberación (Bandeja ETO con tabla de tareas de Liberación ETO)
- **US-4.03:** Modificación del Árbol de Difusión, Revisores y Parámetros (Rol ETO)
- **US-4.05:** Devolución por Incumplimiento de Formato (Rechazo) por ETO al solicitante
- **US-4.06:** Liberación Oficial y Enrutamiento Paralelo (fan-out a revisores/aprobadores)
- **US-3.01:** Gestión de "Mi Bandeja" y Tipos de Tareas Activas (bandeja centralizada con SLA semaforizado)
- **US-3.03:** Aprobación Positiva y Transición de Etapas en Paralelo
- **US-3.04:** Rechazo / Devolución con Observaciones Obligatorias (mín. 10 caracteres)
- **US-3.05:** Corrección en Office 365 y Bypass Directo (Retorno al Observador)

### Modelos SQLAlchemy necesarios (no creados aún)
- `workflow_tareas` (3 tablas)
- `bitacora_timeline` (inmutable)
- `audit_log`
- `arbol_difusion_outlook`
- `matriz_enrutamiento_eto`

### Endpoints necesarios
- `GET /api/v1/bandeja?tipo={liberacion,revision,aprobacion,correccion}`
- `POST /api/v1/documentos/{id}/liberar` (fan-out)
- `POST /api/v1/documentos/{id}/devolver` (con observaciones)
- `POST /api/v1/documentos/{id}/aprobar`
- `POST /api/v1/documentos/{id}/corregir` (bypass al observador)
- `GET /api/v1/bandeja/mi-bandeja` (tareas del usuario actual)
- Cron Celery Beat: `reasignar_tareas_vencidas` a las 23:59 cada día

### Skills a invocar
- `fastapi-patterns`, `api-design`, `error-handling`
- `database-migrations` (crear nuevas tablas)
- `tdd-workflow` (tests del cron SLA)
- `verification-loop` (validar el bypass)

---

## R4 — Office 365 + IA Similitud + SLA
**Complejidad:** 9.5 / 10 | **Estado:** PENDIENTE | **Dependencias:** R3

### Épica(s) cubierta(s)
- Épica 3 (Workflow) — parcialmente
- Épica 4 (Liberación ETO) — parcialmente

### Historias de Usuario pendientes
- **US-3.02:** Interfaz de Revisión y Visualización Office 365 Integrado (iframe con control de cambios)
- **US-3.06:** Ejecución de la Regla de "Timeout" (Cron Job de reasignación por SLA de 10 días hábiles / 15 calendario)
- **US-4.02:** Análisis de Similitud por Inteligencia Artificial (Prevención de Duplicidad con embeddings + búsqueda coseno, umbral 0.60)

### Componentes técnicos nuevos
- **Integración Microsoft Graph** (`msal` + `httpx`): edición en línea de Word, lock/unlock de archivos, webhooks
- **IA embeddings** (`sentence-transformers` + `pgvector`): búsqueda semántica de duplicados
- **Webhooks Graph** para enterarnos cuando un usuario termina de editar (en vez de polling)
- **iframe de Office 365** con CSP que permita `frame-src https://*.sharepoint.com https://*.office.com`

### Endpoints nuevos
- `GET /api/v1/documentos/{id}/office-iframe-url` (devuelve URL con token de un solo uso)
- `POST /api/v1/documentos/{id}/similitud-ia` (calcula similitud contra la lista maestra, devuelve los N más cercanos)
- `GET /api/v1/sla/estado/{tarea_id}` (devuelve días hábiles restantes + color del semáforo)
- `POST /api/v1/webhook/graph` (recibe notificaciones de Microsoft Graph)

### Skills a invocar
- `api-design` (diseñar contratos de la integración Graph)
- `error-handling` (timeouts de Graph API, retry con backoff)
- `security-review` (CSP, tokens, webhooks firmados)
- `postgres-patterns` (pgvector)
- `verification-loop` (probar similitud con documentos reales)

### Decisión pendiente
- ¿IA local con `sentence-transformers` o API de OpenAI/Azure? (recomendado: local para mantener datos en Bolivia)
- ¿Permisos delegados (cada usuario) o de aplicación (service account)? (recomendado: delegados para edición, aplicación para sync)

---

## R5 — Publicación + PDF + Lista Maestra
**Complejidad:** 9.0 / 10 | **Estado:** PENDIENTE | **Dependencias:** R4

### Épica(s) cubierta(s)
- Épica 5 (Publicación, Lista Maestra y Visor Documental) — completa

### Historias de Usuario pendientes
- **US-5.01:** Publicación Automática, Cálculo de Fechas (caducidad) y Difusión vía Outlook
- **US-5.02:** Interfaz y Filtros de Lista Maestra (Rol Usuario Solicitante/Lector) con KPIs
- **US-5.03:** Interfaz Avanzada de Lista Maestra (Rol Gestor ETO) con KPIs de Obsoletos y botones CV/CC/CN
- **US-5.04:** Visor PDF Interactivo con Zoom/Rotación y Puntero de Retorno Dinámico (SPA)
- **US-5.05:** Gestión de Obsolescencia (Automática por reemplazo + Manual por toggle ETO)
- **US-5.06:** Control de Vencimientos y Bloqueo de Riesgo (Modal de alerta + marca de agua "VENCIDO")
- **US-5.07:** Inyección Dinámica de Carátula y Carimbos (encabezado con logo, código, versión, paginación)

### Componentes técnicos nuevos
- **Motor PDF** (WeasyPrint + PyMuPDF): carátula con tabla de firmas, carimbo por página, marca de agua dinámica
- **Trigger SQL de obsolescencia** (BEFORE INSERT en documento_versiones + BEFORE UPDATE de estado)
- **Difusión por árbol de Outlook** (consulta `memberOf` del AD + notifica a cada gerencia/área afectada)
- **Cálculo de fechas hábiles** (cuenta solo lunes-viernes, excluye `feriados` Bolivia)
- **Visor PDF en SPA** (pdf.js o PDFTron, con lazy loading)

### Endpoints nuevos
- `POST /api/v1/documentos/{id}/publicar` (calcula caducidad, dispara difusión, pre-genera PDF custodiado)
- `GET /api/v1/lista-maestra?filtros...` (con KPIs)
- `GET /api/v1/documentos/{id}/pdf?vigencia=actual|vencido` (con marca de agua dinámica)
- `POST /api/v1/documentos/{id}/marcar-obsoleto` (manual, solo ETO)
- `GET /api/v1/difusion/arbol/{gerencia_id}` (devuelve árbol de Outlook)

### Skills a invocar
- `fastapi-patterns` (cálculo de fechas hábiles)
- `api-design` (filtros de lista maestra)
- `error-handling` (generación de PDF con timeout)
- `database-migrations` (trigger SQL)
- `verification-loop` (probar obsolescencia automática)

### Decisiones pendientes
- ¿Motor PDF: WeasyPrint + PyMuPDF (recomendado) o ReportLab puro (más código)?
- ¿Generar PDF on-the-fly o pre-generar al pasar a Vigente? (recomendado: pre-generar)
- ¿Visor PDF: pdf.js open-source o PDFTron comercial?

---

## R6 — Capacitación + Copias + BI + Chat
**Complejidad:** 7.5 / 10 (RAG puede ser fase 2) | **Estado:** PENDIENTE | **Dependencias:** R5

### Épica(s) cubierta(s)
- Épica 6 (Capacitación y Certificación)
- Épica 7 (Trazabilidad de Copias Físicas)
- Épica 8 (Monitoreo, Consultas e IA) — **excepto RAG (fase 2)**
- Épica 9 (Administración y Parametrización Global) — la mayoría ya cubierta en R1

### Historias de Usuario pendientes

#### Épica 6 (Capacitación)
- **US-6.01:** Monitor de Evaluaciones y Habilitación Paramétrica (Rol ETO) con bloqueo de 30 días
- **US-6.02:** Configuración del Examen y Asistente IA (sugerencia de preguntas con NLP, intentos, nota mínima)
- **US-6.03:** Recepción y Ejecución de "Control de Lectura" (Regla antifraude con scroll + firma digital)
- **US-6.04:** Recepción y Ejecución de "Evaluación Temporizada" (cronómetro regresivo + bloqueo al cerrar navegador)
- **US-6.05:** Lógica de Resultados, "Nota más Alta" y Vencimientos (MAX(nota) y estado NO EJECUTADO)
- **US-6.06:** Emisión Automática del Certificado Oficial y Expediente Académico (PDF con ID de verificación)

#### Épica 7 (Copias)
- **US-7.01:** Módulo de Configuración y Generación de Copias Físicas (CC/CN) — Rol ETO
- **US-7.02:** Motor de Previsualización y Sellado PDF Dinámico (marca de agua + footer legal)
- **US-7.03:** Recepción y Firma Digital del Papel Físico Copia Controlada — Rol Usuario
- **US-7.04:** Monitor de Copias No Controladas (Tracking Unidireccional) — Rol ETO
- **US-7.05:** Monitor de Copias Controladas (Ciclo de Vida Cerrado) — Rol ETO
- **US-7.06:** Firma Digital de Destrucción / Devolución de CC — Rol ETO
- **US-7.07:** Catálogo y Descarga de Plantillas Documentales Oficiales (7 plantillas reales)

#### Épica 8 (BI + IA)
- **US-8.01:** Buscador Global, Filtros Avanzados y Despliegue de Bitácora Histórica (Timeline)
- **US-8.02:** Intervención Administrativa, Reasignación Secuencial y Monitoreo ETO (5 formas de reasignación)
- **US-8.03:** Generación de Reportes Dinámicos (Rol ETO) con gráficos interactivos (4 KPIs + 2 series temporales)
- **US-8.04:** Interacción con el Asistente Inteligente de Base de Datos (NLP → SQL, solo SELECT)
- **US-8.05:** Intervención Administrativa (Reasignación Secuencial) — **duplicado de US-8.02**
- **US-8.06:** Suspensión de Flujo por Rechazo Crítico (Eliminación Definitiva) — solo procesos "En Ejecución"

#### Épica 9 (Parametrización Global) — mayormente en R1
- **US-9.01:** Configuración de Variables de Tiempo y SLA
- **US-9.02:** Panel de Restricciones Físicas, Descargas e Interfaz (límite 20MB, 20 archivos, 1 descarga/día con excepciones)
- **US-9.03:** Gestión de Diccionarios y Matriz de Enrutamiento
- **US-9.04:** Gestor de Plantillas de Notificación Email
- **US-9.05:** Gestión Centralizada de Usuarios y Roles (sincronización AD/LDAP, override vacaciones) — **ya implementado en R1**
- **US-9.06:** Mantenimiento de la Estructura Organizacional (Gerencias y Áreas)

### Componentes técnicos nuevos
- **Motor de exámenes** (cronómetro en frontend, antifraude con scroll detection, persistencia en BD)
- **Generador de certificados PDF** (con QR de verificación, ID único)
- **Trazabilidad de copias físicas** (firma digital al recibir, destrucción/devolución firmada)
- **Motor de reportes** (4 KPIs + 2 series temporales con filtros por fecha, gerencia, área)
- **Chat NLP→SQL** (LangChain + agent que solo permite SELECT, jamás INSERT/UPDATE/DELETE)

### Endpoints nuevos
- `POST /api/v1/examenes` (configurar examen)
- `POST /api/v1/examenes/{id}/responder` (enviar respuestas)
- `GET /api/v1/examenes/{id}/resultado`
- `GET /api/v1/certificado/{usuario_id}/{documento_id}` (PDF con QR de verificación)
- `POST /api/v1/copias/cc` (generar copia controlada)
- `POST /api/v1/copias/cn` (generar copia no controlada)
- `POST /api/v1/copias/{id}/recibir` (firma digital de recepción)
- `POST /api/v1/copias/{id}/destruir` (firma digital de destrucción)
- `GET /api/v1/reportes/kpis` (4 KPIs)
- `GET /api/v1/reportes/aprobados-por-mes?year=2026&tipo=general`
- `GET /api/v1/reportes/kpi-detalle?kpi=revision`
- `POST /api/v1/chat/ask` (LangChain agent, solo SELECT)

### Skills a invocar
- `api-design` (muchos endpoints nuevos)
- `error-handling` (timeouts de LangChain, manejo de SQL injection)
- `verification-loop` (chat NLP debe estar probado contra SQL injection)
- `webapp-testing` (E2E del flujo completo de examen)
- `e2e-testing` (Playwright para copias, certificados)
- `security-review` (chat NLP es vector de ataque #1)

### Decisión crítica
- ¿Implementar chat NLP→SQL en R6 o dejarlo para fase 2 post-productivo? (recomendado: fase 2, alto riesgo/bajo valor inicial)

---

## Roadmap visual

```
Semana 1 (16-22 jun) ─── R1 cierre (50%) ──── L1
Semana 2 (23-29 jun) ─── R2 wizard completo ── L2
Semana 3 (30 jun-6 jul) ── R3 workflow ETO ─── L3
Semana 4 (7-13 jul) ── R4 Graph + IA ──── L4
Semana 5 (14-20 jul) ── R5 PDF + lista ─── L5
Semana 6 (21-27 jul) ── R6 capacitación + copias ── L6
Semana 7 (28 jul-3 ago) ── R6 BI + chat (fase 2 opcional)
```

---

## Métricas globales del proyecto

- **Total US:** 6 reuniones × ~10 US = **~60 US** en el backlog completo
- **Cubiertas en código:** ~10 US (las de R1 implementadas)
- **Pendientes:** ~50 US
- **Velocidad objetivo:** 5-8 US/sesión intensiva (1-2 sesiones de 4-6 horas)
- **Tests objetivo:** 80% coverage mínimo

---

## Riesgos macro (consolidado)

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | QAS sin internet (no se puede instalar pip/npm) | Media | R4-R5 no funcionan | Confirmar AHORA con TI de COFAR. Plan B: `sentence-transformers` 100% local, Office 365 via VPN si hay |
| 2 | AD no permite LDAP simple (fuerza Kerberos o MFA) | Alta | Login no funciona | Pedir service account + LDAPS (636) + bind password. Plan B: MSAL/OIDC contra Azure AD |
| 3 | SharePoint bloquea service account | Media | R4 no funciona | Empezar con permisos delegados (cada usuario) en vez de aplicación |
| 4 | Cron SLA se cae | Media | Tareas vencidas no se reasignan | Healthcheck + alerta por email si último run >25h |
| 5 | IA similitud da muchos falsos positivos | Media | ETO devuelve innecesariamente | US-4.02 lo dice: "IA no bloquea, solo sugiere". Mantener siempre al ETO como decisor final |
| 6 | PDF engine no soporta todas las features (carimbo, marca de agua) | Media | R5 se atrasa | Probar WeasyPrint + PyMuPDF al inicio de R5, no al final |
| 7 | Cambio de requisitos del cliente | Alta | Replanificación | Adoptar "vertical slices": cada semana entrega algo end-to-end testeable, no features sueltas |
