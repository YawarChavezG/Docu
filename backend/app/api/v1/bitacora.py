"""
API v1: Bitácora / Timeline del flujo documental (Fase 4)
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_authenticated
from app.models.bitacora_timeline import BitacoraTimeline
from app.models.documento_flujo import DocumentoFlujo
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bitacora", tags=["Bitacora"])


class BitacoraNodoOut(BaseModel):
    id: int
    documento_flujo_id: int
    tarea_id: Optional[int] = None
    usuario_id: int
    usuario_nombre: Optional[str] = None
    accion: str
    estado_origen: Optional[str] = None
    estado_destino: Optional[str] = None
    color_nodo: str
    observacion: Optional[str] = None
    adjunto_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BitacoraResponse(BaseModel):
    total: int
    items: list[BitacoraNodoOut]


@router.get("", response_model=BitacoraResponse)
async def get_bitacora(
    request: Request,
    documento_flujo_id: int = Query(..., description="ID del flujo documental"),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el timeline completo de un flujo documental, ordenado DESC (mas reciente primero)."""
    await require_authenticated(request, db)

    result = await db.execute(
        select(BitacoraTimeline)
        .where(BitacoraTimeline.documento_flujo_id == documento_flujo_id)
        .options(selectinload(BitacoraTimeline.usuario))
        .order_by(BitacoraTimeline.created_at.desc())
    )
    rows = result.scalars().all()

    items = []
    for r in rows:
        usuario_nombre = r.usuario.nombre_completo if r.usuario else None
        items.append(BitacoraNodoOut(
            id=r.id,
            documento_flujo_id=r.documento_flujo_id,
            tarea_id=r.tarea_id,
            usuario_id=r.usuario_id,
            usuario_nombre=usuario_nombre,
            accion=r.accion,
            estado_origen=r.estado_origen,
            estado_destino=r.estado_destino,
            color_nodo=r.color_nodo,
            observacion=r.observacion,
            adjunto_url=r.adjunto_url,
            created_at=r.created_at,
        ))

    return BitacoraResponse(total=len(items), items=items)
