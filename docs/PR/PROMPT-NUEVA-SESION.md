Lee ABSOLUTAMENTE TODO en este orden:

Documentación del proyecto (OBLIGATORIO, en este orden)
1. docs/PR/RADIOGRAFIA-TOTAL-18-06-2026.md — radiografía completa del proyecto
2. docs/PR/INICIO-SESION.md — prompt maestro, forma de trabajo, skills, clean state
3. docs/PR/LEARNINGS-ERRORES.md — errores documentados por categoría (LEER ANTES DE CUALQUIER CAMBIO)
4. docs/PR/DECISIONES.md — ADRs activos
5. docs/PR/ESTADO.md — estado actual del código (última actualización: sesión 38)
6. docs/PR/BITACORA.md — historial completo de sesiones (prestar atención a sesión 37-38)
7. docs/PR/PROPUESTA-R3-TABLAS.md — propuesta técnica de R3
8. docs/PR/CHECKLIST-R3-FASES.md — fases de R3 (Fase 0 ✅, Fase 1 ✅, Fase 2 ⏳ pendiente)
9. docs/PR/PROMPT-NUEVA-SESION.md — este archivo

Contexto actual del proyecto
- Rama activa: r3/workflow-revision-aprobacion
- Tests: 300/300 PASS
- Tablas BD: 30 (23 originales + 7 Fase 1 workflow + 1 plantillas)
- Migraciones Alembic: 24 aplicadas (head: r3_plantillas_table_s37)
- Endpoints: 90+ REST
- Usuarios: 757 (724 usuario_roles)
- Documentos semilla: 10
- Plantillas documentales: 8 en BD
- Fase 0 (R2 wizard completado): código completo, actualización documental, formularios -F01, validación carátula, vigencia desde BD, flujo LIBERACION_ETO ✅
- Fase 1 (Modelos R3): 7 tablas workflow + enums + semáforo corregido ✅
- Fase 2: PENDIENTE (servicios core R3)

Skills (LEER ANTES DE ESCRIBIR CÓDIGO)
10. docs/PR/SKILL-FRONTEND-CONVENCIONES.md — diseño system frontend (colores, tipografía, badges, modales)
11. docs/PR/SKILL-MCP-TESTING.md — patrones de prueba Chrome MCP

REGLAS DURAS para escribir código

FRONTEND (Alpine.js + Tailwind):
- NO usar confirm() nativo del browser. Usar modales existentes:
  * window.confirmDeleteModal?.abrir({ titulo, mensaje, onConfirm })
  * window.confirmImpersonate?.abrir({ target, me, onConfirm })
  * window.confirmDelegadoModal?.abrir({ mensaje, onConfirm })
- NO usar <template x-if> dentro de x-teleport (causa error _x_dataStack). Usar <span x-show> con doble control (F12 en LEARNINGS).
- NO usar $refs para trigger de file input. Usar document.querySelector('[x-ref=name]')?.click()
- x-show en elementos con x-for: ponerlo en el span PADRE, no en el botón individual.
- Paleta de colores: brand-500 (#1a5fb4), slate-50/100/200/400/600/800, emerald para confirmaciones, amber para advertencias, red para errores.
- Tipografía: text-xs (11px), text-[11px], font-semibold, font-mono para códigos.
- Para modales de confirmación: z-index 8600 (sobre otros modales).
- dropdowns custom: mantener form-input text-xs, con ▼, shadow-xl, hover:bg-blue-50.

BACKEND (FastAPI + SQLAlchemy 2.0 async):
- SQLite en tests (conftest.py). JSONB usar JSON().with_variant(JSONB(), "postgresql").
- Toda mutación pasa por write_audit() y deja audit_log.
- No DELETE físico. Borrado lógico (activo=False).
- SELECT FOR UPDATE para operaciones concurrentes (correlativo_service).
- Los endpoints admin de plantillas requieren require_eto_or_admin.
- Al crear endpoints nuevos, registrar en main.py con prefix /api/v1.

BD (PostgreSQL 16):
- 30 tablas actuales (listar con \dt en psql).
- Siempre verificar estado actual con consultas SQL antes de asumir.
- Las migraciones se aplican manualmente via docker exec sgd-postgres psql (mismo patrón ADR-069).

TESTS:
- Siempre correr al inicio: cd backend && .venv\Scripts\python -m pytest tests/ -q
- Tests de FK en SQLite requieren PRAGMA foreign_keys=ON en conftest.
- No romper tests existentes. 300/300 debe seguir pasando.

Próxima tarea: Fase 2 — Servicios core R3
1. tarea_service.py (crear/completar/rechazar/reasignar tarea)
2. timeline_service.py (bitácora append-only)
3. notificacion_service.py (crear/marcar leída)
4. Integrar envio_service.liberar_documento() con tabla tareas
5. Helper calcular_color_sla(tarea) — días hábiles vs feriados
6. Tests: 8-10 de servicios

Objetivo
Tenés el contexto COMPLETO del proyecto actualizado a sesión 38. Estás listo para continuar con Fase 2 de R3. Preguntá cuál es la siguiente tarea o esperá instrucciones.
