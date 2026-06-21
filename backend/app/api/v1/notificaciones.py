"""
API v1: Notificaciones del workflow (R3 Fase 2).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_authenticated
from app.services.notificacion_service import (
    contar_no_leidas, listar_notificaciones, marcar_leida,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


class NotificacionOut(BaseModel):
    id: int
    usuario_destino_id: int
    usuario_origen_id: Optional[int] = None
    documento_flujo_id: Optional[int] = None
    tarea_id: Optional[int] = None
    titulo: str
    mensaje: str
    tipo_notificacion: str
    leida: bool
    created_at: str

    model_config = {"from_attributes": True}


class NotificacionListResponse(BaseModel):
    total: int
    items: list[NotificacionOut]


class CountResponse(BaseModel):
    total: int


@router.get("", response_model=NotificacionListResponse)
async def list_notificaciones(
    request: Request,
    solo_no_leidas: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista notificaciones del usuario autenticado."""
    user = await require_authenticated(request, db)
    rows, total = await listar_notificaciones(
        db, user.id, solo_no_leidas=solo_no_leidas,
        limit=page_size, offset=(page - 1) * page_size,
    )
    items = []
    for n in rows:
        items.append(NotificacionOut(
            id=n.id, usuario_destino_id=n.usuario_destino_id,
            usuario_origen_id=n.usuario_origen_id,
            documento_flujo_id=n.documento_flujo_id,
            tarea_id=n.tarea_id, titulo=n.titulo,
            mensaje=n.mensaje, tipo_notificacion=n.tipo_notificacion,
            leida=n.leida, created_at=n.created_at.isoformat(),
        ))
    return NotificacionListResponse(total=total, items=items)


@router.get("/no-leidas/count", response_model=CountResponse)
async def count_no_leidas(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Cuantas notificaciones no leidas tiene el usuario."""
    user = await require_authenticated(request, db)
    total = await contar_no_leidas(db, user.id)
    return CountResponse(total=total)


@router.post("/{notificacion_id}/leer")
async def marcar_notificacion_leida(
    notificacion_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Marca una notificacion como leida."""
    await require_authenticated(request, db)
    n = await marcar_leida(db, notificacion_id, request.client.host if request.client else None)
    if not n:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    await db.commit()
    return {"ok": True}
