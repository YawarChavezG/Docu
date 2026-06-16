"""
api/v1/feriados.py — CRUD de feriados (US-9.01 calendario Bolivia).

Cubre:
  - GET /feriados (lista con filtros ?anio= ?tipo= ?departamento=)
  - GET /feriados/{id}
  - POST /feriados (ETO o ADMIN)
  - PATCH /feriados/{id}
  - DELETE /feriados/{id} (borrado logico)

Los GETs no requieren auth (catalogo publico). Mutaciones requieren ETO o ADMIN.

El seed con los 16 feriados oficiales de Bolivia 2026 esta en
backend/scripts/seed_feriados.py.
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.feriado import Feriado, TipoFeriado
from app.schemas.feriado import (
    FeriadoCreate,
    FeriadoListResponse,
    FeriadoOut,
    FeriadoUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feriados", tags=["Feriados"])


# ─── Helpers ───

async def _get_or_404(db: AsyncSession, feriado_id: int) -> Feriado:
    f = (await db.execute(
        select(Feriado).where(Feriado.id == feriado_id)
    )).scalar_one_or_none()
    if f is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feriado {feriado_id} no existe",
        )
    return f


# ─── Endpoints ───

@router.get("", response_model=FeriadoListResponse)
async def list_feriados(
    anio: Optional[int] = Query(None, ge=1900, le=2200,
                                  description="Filtra por anio (ej: 2026)"),
    tipo: Optional[TipoFeriado] = Query(None),
    departamento: Optional[str] = Query(None, max_length=50),
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Lista feriados. No requiere auth (catalogo publico)."""
    base = select(Feriado)
    if anio is not None:
        # PostgreSQL: extract year from date. Funciona tambien si fecha es DATE.
        from sqlalchemy import extract
        base = base.where(extract("year", Feriado.fecha) == anio)
    if tipo is not None:
        base = base.where(Feriado.tipo == tipo)
    if departamento is not None:
        base = base.where(Feriado.departamento == departamento)
    if solo_activos:
        base = base.where(Feriado.activo == True)

    rows = (await db.execute(
        base.order_by(Feriado.fecha.asc())
    )).scalars().all()

    return FeriadoListResponse(
        total=len(rows),
        items=[FeriadoOut.model_validate(r) for r in rows],
    )


@router.get("/{feriado_id}", response_model=FeriadoOut)
async def get_feriado(
    feriado_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle. No requiere auth."""
    f = await _get_or_404(db, feriado_id)
    return FeriadoOut.model_validate(f)


@router.post("", response_model=FeriadoOut, status_code=status.HTTP_201_CREATED)
async def create_feriado(
    payload: FeriadoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un feriado. Requiere ETO o ADMIN.
    409 si la fecha ya existe. 422 si tipo=DEPARTAMENTAL sin departamento.
    """
    await require_eto_or_admin(request, db)

    # Validacion logica
    if payload.tipo == TipoFeriado.DEPARTAMENTAL and not payload.departamento:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Si tipo=DEPARTAMENTAL, debe especificar 'departamento'",
        )
    if payload.tipo != TipoFeriado.DEPARTAMENTAL and payload.departamento:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'departamento' solo aplica a tipo=DEPARTAMENTAL (recibido tipo={payload.tipo.value})",
        )

    existing = (await db.execute(
        select(Feriado).where(Feriado.fecha == payload.fecha)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un feriado en la fecha {payload.fecha.isoformat()} "
                   f"({existing.nombre})",
        )

    f = Feriado(
        fecha=payload.fecha,
        nombre=payload.nombre,
        tipo=payload.tipo,
        departamento=payload.departamento,
        activo=payload.activo,
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    logger.info(f"Feriado creado: {f.fecha} {f.nombre!r} ({f.tipo.value})")
    return FeriadoOut.model_validate(f)


@router.patch("/{feriado_id}", response_model=FeriadoOut)
async def update_feriado(
    feriado_id: int,
    payload: FeriadoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un feriado. Requiere ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    f = await _get_or_404(db, feriado_id)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return FeriadoOut.model_validate(f)

    # Si cambia fecha, validar que no choque
    if "fecha" in data and data["fecha"] != f.fecha:
        dup = (await db.execute(
            select(Feriado).where(
                Feriado.fecha == data["fecha"],
                Feriado.id != feriado_id,
            )
        )).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un feriado en la fecha {data['fecha'].isoformat()}",
            )

    for field, value in data.items():
        setattr(f, field, value)

    # Validar coherencia tipo/departamento post-merge
    if f.tipo == TipoFeriado.DEPARTAMENTAL and not f.departamento:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Si tipo=DEPARTAMENTAL, debe especificar 'departamento'",
        )

    await db.commit()
    await db.refresh(f)
    logger.info(f"Feriado actualizado: {f.fecha} {f.nombre!r} (campos={list(data.keys())})")
    return FeriadoOut.model_validate(f)


@router.delete("/{feriado_id}", response_model=FeriadoOut)
async def delete_feriado(
    feriado_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Borrado logico (activo=false). Requiere ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    f = await _get_or_404(db, feriado_id)
    if not f.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El feriado del {f.fecha.isoformat()} ya estaba inactivo",
        )
    f.activo = False
    await db.commit()
    await db.refresh(f)
    logger.info(f"Feriado borrado (logico): {f.fecha} {f.nombre!r}")
    return FeriadoOut.model_validate(f)
