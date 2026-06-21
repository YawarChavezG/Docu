"""
API v1: Tareas del workflow documental (R3 Fase 2).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_authenticated
from app.models.tarea import Tarea
from app.models.documento_flujo import DocumentoFlujo
from app.schemas.tarea import TareaOut, TareaListResponse
from app.services.tarea_service import completar_tarea, rechazar_tarea, reasignar_tarea

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tareas", tags=["Tareas"])


class AprobarRequest(BaseModel):
    password: str = Field(..., min_length=1)


class RechazarRequest(BaseModel):
    password: str = Field(..., min_length=1)
    observacion: str = Field(..., min_length=10)


class ReasignarRequest(BaseModel):
    nuevo_usuario_id: int = Field(..., gt=0)
    motivo: str = Field(..., min_length=5)


@router.get("", response_model=TareaListResponse)
async def list_tareas(
    request: Request,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    tipo_tarea: Optional[str] = Query(None, description="Filtrar por tipo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista tareas del usuario autenticado."""
    user = await require_authenticated(request, db)

    query = select(Tarea).where(Tarea.usuario_id == user.id).where(Tarea.activo == True)
    count_query = select(func.count(Tarea.id)).where(Tarea.usuario_id == user.id).where(Tarea.activo == True)

    if estado:
        query = query.where(Tarea.estado == estado)
        count_query = count_query.where(Tarea.estado == estado)
    if tipo_tarea:
        query = query.where(Tarea.tipo_tarea == tipo_tarea)
        count_query = count_query.where(Tarea.tipo_tarea == tipo_tarea)

    total = (await db.execute(count_query)).scalar_one() or 0

    rows = (await db.execute(
        query.options(selectinload(Tarea.documento_flujo))
        .order_by(Tarea.fecha_asignacion.desc())
        .limit(page_size).offset((page - 1) * page_size)
    )).scalars().all()

    items = []
    for t in rows:
        codigo_completo = ""
        titulo_doc = ""
        if t.documento_flujo:
            codigo_completo = f"{t.documento_flujo.codigo_snapshot} V{t.documento_flujo.version_snapshot}"
            titulo_doc = t.documento_flujo.titulo or ""
        items.append(TareaOut(
            id=t.id, documento_flujo_id=t.documento_flujo_id,
            usuario_id=t.usuario_id, tipo_tarea=t.tipo_tarea,
            estado=t.estado, fecha_asignacion=t.fecha_asignacion,
            fecha_vencimiento=t.fecha_vencimiento,
            fecha_completado=t.fecha_completado,
            codigo_completo=codigo_completo, titulo_documento=titulo_doc,
        ))

    return TareaListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{tarea_id}", response_model=TareaOut)
async def get_tarea(
    tarea_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de una tarea."""
    await require_authenticated(request, db)
    t = await db.get(Tarea, tarea_id)
    if not t or not t.activo:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    codigo_completo = ""
    titulo_doc = ""
    if t.documento_flujo:
        codigo_completo = f"{t.documento_flujo.codigo_snapshot} V{t.documento_flujo.version_snapshot}"
        titulo_doc = t.documento_flujo.titulo or ""

    return TareaOut(
        id=t.id, documento_flujo_id=t.documento_flujo_id,
        usuario_id=t.usuario_id, tipo_tarea=t.tipo_tarea,
        estado=t.estado, fecha_asignacion=t.fecha_asignacion,
        fecha_vencimiento=t.fecha_vencimiento,
        fecha_completado=t.fecha_completado,
        codigo_completo=codigo_completo, titulo_documento=titulo_doc,
    )


@router.post("/{tarea_id}/aprobar")
async def aprobar_tarea(
    tarea_id: int,
    body: AprobarRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Aprueba una tarea pendiente (firma 2FA requerida)."""
    user = await require_authenticated(request, db)
    tarea, accion = await completar_tarea(db, request, user, tarea_id, body.password)
    await db.commit()
    return {
        "ok": True,
        "tarea_id": tarea.id,
        "estado": tarea.estado,
        "accion_siguiente": accion,
    }


@router.post("/{tarea_id}/rechazar")
async def rechazar_tarea_endpoint(
    tarea_id: int,
    body: RechazarRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Rechaza una tarea pendiente con observacion (firma 2FA requerida)."""
    user = await require_authenticated(request, db)
    tarea, accion = await rechazar_tarea(db, request, user, tarea_id, body.observacion, body.password)
    await db.commit()
    return {
        "ok": True,
        "tarea_id": tarea.id,
        "estado": tarea.estado,
        "accion_siguiente": accion,
    }


@router.post("/{tarea_id}/reasignar")
async def reasignar_tarea_endpoint(
    tarea_id: int,
    body: ReasignarRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Reasigna una tarea a otro usuario (solo ETO/ADMIN)."""
    from app.core.permissions import require_eto_or_admin
    user = await require_eto_or_admin(request, db)
    nueva = await reasignar_tarea(db, request, user, tarea_id, body.nuevo_usuario_id, body.motivo)
    await db.commit()
    return {
        "ok": True,
        "nueva_tarea_id": nueva.id,
        "usuario_id": nueva.usuario_id,
        "estado": nueva.estado,
    }
