"""
audit_log.py — Router para consultar el registro de auditoria (EPICA 9 - US-9.05).

El audit_log es append-only desde el punto de vista de la API: solo lectura.
La escritura se hace desde `app.core.audit.write_audit()` instrumentado en
los routers de gerencias, areas, configuracion_global, feriados, etc.

Filtros soportados:
  - usuario_id (int)
  - usuario_username (str, exacto)
  - accion (str, exacto)
  - recurso (str, exacto)
  - recurso_id (int)
  - exitoso (bool)
  - desde / hasta (ISO 8601)
  - limit (default 50, max 200)
  - offset (default 0)
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogOut, AuditLogPaginado

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/audit-log", response_model=AuditLogPaginado)
async def listar_audit_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario_id: Optional[int] = Query(None, description="ID del usuario que ejecuto la accion"),
    usuario_username: Optional[str] = Query(None, description="Username exacto"),
    accion: Optional[str] = Query(None, description="CREATE, UPDATE, DELETE, LOGIN, EXPORT, SYNC, etc."),
    recurso: Optional[str] = Query(None, description="gerencia, area, configuracion_global, etc."),
    recurso_id: Optional[int] = Query(None, description="ID del recurso afectado"),
    exitoso: Optional[bool] = Query(None, description="True=exitosos, False=fallidos"),
    desde: Optional[datetime] = Query(None, description="ISO 8601, ej: 2026-06-01T00:00:00"),
    hasta: Optional[datetime] = Query(None, description="ISO 8601, ej: 2026-06-15T23:59:59"),
    limit: int = Query(50, ge=1, le=200, description="Tamano de pagina (max 200)"),
    offset: int = Query(0, ge=0, description="Desplazamiento"),
):
    """
    Lista entradas del audit-log ordenadas por fecha DESC.
    Solo accesible para ETO o ADMIN.
    """
    await require_eto_or_admin(request, db)

    condiciones = []

    if usuario_id is not None:
        condiciones.append(AuditLog.usuario_id == usuario_id)
    if usuario_username:
        condiciones.append(AuditLog.usuario_username == usuario_username)
    if accion:
        condiciones.append(AuditLog.accion == accion.upper())
    if recurso:
        condiciones.append(AuditLog.recurso == recurso)
    if recurso_id is not None:
        condiciones.append(AuditLog.recurso_id == recurso_id)
    if exitoso is not None:
        condiciones.append(AuditLog.exitoso == exitoso)
    if desde is not None:
        condiciones.append(AuditLog.created_at >= desde)
    if hasta is not None:
        condiciones.append(AuditLog.created_at <= hasta)

    where_clause = and_(*condiciones) if condiciones else None

    count_stmt = select(func.count(AuditLog.id))
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    if where_clause is not None:
        items_stmt = items_stmt.where(where_clause)
    items = (await db.execute(items_stmt)).scalars().all()

    return AuditLogPaginado(
        total=total,
        limit=limit,
        offset=offset,
        items=[AuditLogOut.model_validate(it) for it in items],
    )
