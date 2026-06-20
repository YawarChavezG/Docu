"""
API v1: Catalogo de Procesos (Fase 3)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.proceso import Proceso
from app.schemas.proceso import ProcesoListResponse, ProcesoOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/procesos", tags=["Procesos"])


@router.get("", response_model=ProcesoListResponse)
async def list_procesos(
    db: AsyncSession = Depends(get_db),
):
    """Lista los procesos activos."""
    rows = (await db.execute(
        select(Proceso)
        .where(Proceso.activo == True)
        .order_by(Proceso.codigo.asc())
    )).scalars().all()
    return ProcesoListResponse(
        total=len(rows),
        items=[ProcesoOut.model_validate(r) for r in rows],
    )


@router.get("/{proceso_id}", response_model=ProcesoOut)
async def get_proceso(
    proceso_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de un proceso."""
    p = await db.get(Proceso, proceso_id)
    if not p or not p.activo:
        raise HTTPException(status_code=404, detail="Proceso no encontrado")
    return ProcesoOut.model_validate(p)
