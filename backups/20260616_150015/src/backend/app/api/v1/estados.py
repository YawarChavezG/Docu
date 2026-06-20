"""
api/v1/estados.py — CRUD de estados de proceso/tarea (US-9.03 sub-tarjeta 2).

5 estados del flujo del SGD:
  ELABORACION -> LIBERACION_ETO -> REVISION_PARALELA -> FINALIZADO
  (ANULADO como estado terminal alternativo)

Endpoints (todos bajo prefix /api/v1/estados):
  GET    /              lista con ?contexto=
  GET    /{id}          detalle
  POST   /              crear (ETO/ADMIN)
  PATCH  /{id}          update parcial
  DELETE /{id}          borrado logico
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.core.audit import write_audit
from app.models.estado import Estado, ContextoEstado
from app.schemas.estado import (
    EstadoCreate,
    EstadoListResponse,
    EstadoOut,
    EstadoUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estados", tags=["Estados"])


@router.get("", response_model=EstadoListResponse)
async def list_estados(
    q: str | None = Query(None),
    contexto: ContextoEstado | None = Query(None),
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Lista los 5 estados. No requiere auth (catalogo publico)."""
    base = select(Estado)
    if q:
        pat = f"%{q.lower()}%"
        base = base.where(or_(
            func.lower(Estado.codigo).like(pat),
            func.lower(Estado.nombre).like(pat),
        ))
    if contexto is not None:
        # Filtra por contexto exacto O AMBOS (que aplica a todos)
        if contexto == ContextoEstado.AMBOS:
            pass  # no filtra
        else:
            base = base.where(
                (Estado.contexto == contexto) | (Estado.contexto == ContextoEstado.AMBOS)
            )
    if solo_activos:
        base = base.where(Estado.activo == True)

    rows = (await db.execute(
        base.order_by(Estado.orden.asc(), Estado.codigo.asc())
    )).scalars().all()

    return EstadoListResponse(
        total=len(rows),
        items=[EstadoOut.model_validate(r) for r in rows],
    )


@router.get("/{estado_id}", response_model=EstadoOut)
async def get_estado(
    estado_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle. No requiere auth."""
    e = (await db.execute(
        select(Estado).where(Estado.id == estado_id)
    )).scalar_one_or_none()
    if e is None:
        raise HTTPException(404, f"Estado {estado_id} no existe")
    return EstadoOut.model_validate(e)


@router.post("", response_model=EstadoOut, status_code=status.HTTP_201_CREATED)
async def create_estado(
    payload: EstadoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Crea un estado. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)

    existing = (await db.execute(
        select(Estado).where(Estado.codigo == payload.codigo)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, f"Ya existe un estado con codigo '{payload.codigo}'")

    e = Estado(
        codigo=payload.codigo,
        nombre=payload.nombre,
        contexto=payload.contexto,
        orden=payload.orden,
        descripcion=payload.descripcion,
        activo=payload.activo,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    await write_audit(
        db, request, user,
        accion="CREATE", recurso="estado", recurso_id=e.id,
        descripcion=f"Estado {e.codigo} ({e.contexto.value}) creado",
        detalles={"despues": {"codigo": e.codigo, "nombre": e.nombre, "contexto": e.contexto.value, "orden": e.orden, "activo": e.activo}},
    )
    await db.commit()
    logger.info(f"Estado creado: {e.codigo} ({e.contexto.value})")
    return EstadoOut.model_validate(e)


@router.patch("/{estado_id}", response_model=EstadoOut)
async def update_estado(
    estado_id: int,
    payload: EstadoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un estado. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    e = (await db.execute(
        select(Estado).where(Estado.id == estado_id)
    )).scalar_one_or_none()
    if e is None:
        raise HTTPException(404, f"Estado {estado_id} no existe")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return EstadoOut.model_validate(e)

    antes = {"codigo": e.codigo, "nombre": e.nombre, "contexto": e.contexto.value, "orden": e.orden, "activo": e.activo}

    for field, value in data.items():
        setattr(e, field, value)
    await db.commit()
    await db.refresh(e)
    despues = {"codigo": e.codigo, "nombre": e.nombre, "contexto": e.contexto.value, "orden": e.orden, "activo": e.activo}
    await write_audit(
        db, request, user,
        accion="UPDATE", recurso="estado", recurso_id=e.id,
        descripcion=f"Estado {e.codigo} actualizado (campos={list(data.keys())})",
        detalles={"antes": antes, "despues": despues, "campos": list(data.keys())},
    )
    await db.commit()
    logger.info(f"Estado actualizado: {e.codigo} (campos={list(data.keys())})")
    return EstadoOut.model_validate(e)


@router.delete("/{estado_id}", response_model=EstadoOut)
async def delete_estado(
    estado_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Borrado logico. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    e = (await db.execute(
        select(Estado).where(Estado.id == estado_id)
    )).scalar_one_or_none()
    if e is None:
        raise HTTPException(404, f"Estado {estado_id} no existe")
    if not e.activo:
        raise HTTPException(409, f"Estado {e.codigo} ya estaba inactivo")
    e.activo = False
    await db.commit()
    await db.refresh(e)
    await write_audit(
        db, request, user,
        accion="DELETE", recurso="estado", recurso_id=e.id,
        descripcion=f"Estado {e.codigo} borrado (logico)",
        detalles={"codigo": e.codigo, "contexto": e.contexto.value},
    )
    await db.commit()
    logger.info(f"Estado borrado (logico): {e.codigo}")
    return EstadoOut.model_validate(e)
