"""
api/v1/roles.py — Catalogo de roles (5 entradas definidas en sesion 2).

Endpoint publico (catalogo cerrado, sin auth) — se consume en parametrizacion
y en gestion de usuarios para el dropdown de roles.

Endpoints (todos bajo prefix /api/v1/roles):
  GET   /              lista los 5 roles
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.rol import Rol
from app.schemas.rol import RolListResponse, RolOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=RolListResponse)
async def list_roles(
    db: AsyncSession = Depends(get_db),
):
    """
    Lista los 5 roles del sistema. No requiere auth (catalogo cerrado).
    Usado por el frontend (Parametrizacion, Gestion de Usuarios) para poblar
    el dropdown de seleccion de rol.
    """
    rows = (await db.execute(
        select(Rol).order_by(Rol.codigo.asc())
    )).scalars().all()
    return RolListResponse(
        total=len(rows),
        items=[RolOut.model_validate(r) for r in rows],
    )
