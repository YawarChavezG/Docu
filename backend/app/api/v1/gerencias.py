"""
api/v1/gerencias.py — CRUD de gerencias (US-9.06).

Pensado para la pantalla Parametrizacion > Gerencias y Areas.
Reemplaza al mock `frontend/src/data/parametrosSistema.js`.

Endpoints (todos bajo prefix /api/v1/gerencias):
  GET    /              -> lista paginada con filtros ?q= ?activo= ?page= ?page_size=
  GET    /{id}          -> detalle (incluye conteo de areas)
  POST   /              -> crear (ETO o ADMIN)
  PATCH  /{id}          -> update parcial (ETO o ADMIN)
  DELETE /{id}          -> borrado logico (activo=false, ETO o ADMIN)

El router se monta con prefix=/api/v1 en main.py. Repetir el prefijo
aca provocaria rutas 404 porque FastAPI no las apila.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.core.audit import write_audit
from app.models.gerencia import Gerencia
from app.models.area import Area
from app.schemas.gerencia import (
    GerenciaCreate,
    GerenciaListResponse,
    GerenciaOut,
    GerenciaUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gerencias", tags=["Gerencias"])


# ─── Helpers ───

def _to_out(g: Gerencia, areas_count: int) -> GerenciaOut:
    return GerenciaOut(
        id=g.id,
        sigla=g.sigla,
        nombre=g.nombre,
        activo=g.activo,
        orden=g.orden,
        areas_count=areas_count,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )


async def _get_gerencia_with_count(db: AsyncSession, gerencia_id: int) -> tuple[Gerencia, int]:
    """Carga una gerencia + conteo de areas activas en una sola query."""
    g = (await db.execute(
        select(Gerencia).where(Gerencia.id == gerencia_id)
    )).scalar_one_or_none()
    if g is None:
        raise HTTPException(status_code=404, detail=f"Gerencia {gerencia_id} no encontrada")
    count = (await db.execute(
        select(func.count()).select_from(Area).where(
            Area.gerencia_id == gerencia_id, Area.activo == True
        )
    )).scalar_one()
    return g, count


# ─── Endpoints ───

@router.get("", response_model=GerenciaListResponse)
async def list_gerencias(
    q: Optional[str] = Query(None, description="Busca en sigla y nombre (case-insensitive)"),
    activo: Optional[str] = Query(None, description="'true', 'false', o 'all' (default: 'true')"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista gerencias con paginacion y filtros. No requiere autenticacion
    (los catalogos publicos pueden consumirse antes de login en algunos flujos).
    """
    base = select(Gerencia)

    if q:
        pat = f"%{q.lower()}%"
        base = base.where(or_(
            func.lower(Gerencia.sigla).like(pat),
            func.lower(Gerencia.nombre).like(pat),
        ))
    if activo is None or activo == "true":
        base = base.where(Gerencia.activo == True)
    elif activo == "false":
        base = base.where(Gerencia.activo == False)
    # activo == "all" -> no filtra

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    rows = (await db.execute(
        base.order_by(Gerencia.orden.asc(), Gerencia.sigla.asc())
            .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    # Conteo de areas por gerencia en una sola query (evita N+1)
    ids = [g.id for g in rows]
    counts_by_ger: dict[int, int] = {}
    if ids:
        count_rows = (await db.execute(
            select(Area.gerencia_id, func.count(Area.id))
            .where(Area.gerencia_id.in_(ids), Area.activo == True)
            .group_by(Area.gerencia_id)
        )).all()
        counts_by_ger = {gid: cnt for gid, cnt in count_rows}

    return GerenciaListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_out(g, counts_by_ger.get(g.id, 0)) for g in rows],
    )


@router.get("/{gerencia_id}", response_model=GerenciaOut)
async def get_gerencia(
    gerencia_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de una gerencia. No requiere auth (catalogo publico)."""
    g, count = await _get_gerencia_with_count(db, gerencia_id)
    return _to_out(g, count)


@router.post("", response_model=GerenciaOut, status_code=status.HTTP_201_CREATED)
async def create_gerencia(
    payload: GerenciaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una gerencia. Requiere rol ETO o ADMIN.
    409 si la sigla ya existe.
    """
    await require_eto_or_admin(request, db)

    existing = (await db.execute(
        select(Gerencia).where(Gerencia.sigla == payload.sigla)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una gerencia con la sigla '{payload.sigla}'",
        )

    g = Gerencia(
        sigla=payload.sigla,
        nombre=payload.nombre,
        orden=payload.orden,
        activo=payload.activo,
    )
    db.add(g)
    await db.commit()
    await db.refresh(g)
    user = await require_eto_or_admin(request, db)
    await write_audit(
        db, request, user,
        accion="CREATE", recurso="gerencia", recurso_id=g.id,
        descripcion=f"Gerencia {g.sigla} creada",
        detalles={"despues": {"sigla": g.sigla, "nombre": g.nombre, "orden": g.orden, "activo": g.activo}},
    )
    await db.commit()
    logger.info(f"Gerencia creada: {g.sigla} (id={g.id})")
    return _to_out(g, areas_count=0)


@router.patch("/{gerencia_id}", response_model=GerenciaOut)
async def update_gerencia(
    gerencia_id: int,
    payload: GerenciaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza parcialmente una gerencia. Requiere rol ETO o ADMIN.
    404 si no existe, 409 si cambia sigla y ya esta en uso.
    """
    user = await require_eto_or_admin(request, db)

    g = (await db.execute(
        select(Gerencia).where(Gerencia.id == gerencia_id)
    )).scalar_one_or_none()
    if g is None:
        raise HTTPException(status_code=404, detail=f"Gerencia {gerencia_id} no encontrada")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        # PATCH sin campos: devolver el recurso sin cambios
        _, count = await _get_gerencia_with_count(db, gerencia_id)
        return _to_out(g, count)

    # Snapshot del estado anterior para el audit
    antes = {"sigla": g.sigla, "nombre": g.nombre, "orden": g.orden, "activo": g.activo}

    if "sigla" in data and data["sigla"] != g.sigla:
        dup = (await db.execute(
            select(Gerencia).where(
                Gerencia.sigla == data["sigla"],
                Gerencia.id != gerencia_id,
            )
        )).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La sigla '{data['sigla']}' ya esta en uso por otra gerencia",
            )

    for field, value in data.items():
        setattr(g, field, value)

    await db.commit()
    await db.refresh(g)
    despues = {"sigla": g.sigla, "nombre": g.nombre, "orden": g.orden, "activo": g.activo}
    await write_audit(
        db, request, user,
        accion="UPDATE", recurso="gerencia", recurso_id=g.id,
        descripcion=f"Gerencia {g.sigla} actualizada (campos: {list(data.keys())})",
        detalles={"antes": antes, "despues": despues, "campos": list(data.keys())},
    )
    await db.commit()
    logger.info(f"Gerencia actualizada: {g.sigla} (id={g.id}, campos={list(data.keys())})")
    _, count = await _get_gerencia_with_count(db, g.id)
    return _to_out(g, count)


@router.delete("/{gerencia_id}", response_model=GerenciaOut)
async def delete_gerencia(
    gerencia_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Borrado logico de una gerencia. Setea activo=False.
    Si tiene areas activas vinculadas, las desactiva tambien
    (cascade logico; el cliente debe ver la advertencia de US-9.06).

    Requiere rol ETO o ADMIN.
    """
    user = await require_eto_or_admin(request, db)

    g, _ = await _get_gerencia_with_count(db, gerencia_id)

    if not g.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La gerencia '{g.sigla}' ya estaba inactiva",
        )

    # Cascade logico: desactivar areas hijas
    areas = (await db.execute(
        select(Area).where(Area.gerencia_id == gerencia_id, Area.activo == True)
    )).scalars().all()
    for a in areas:
        a.activo = False

    g.activo = False
    await db.commit()
    await db.refresh(g)
    await write_audit(
        db, request, user,
        accion="DELETE", recurso="gerencia", recurso_id=g.id,
        descripcion=f"Gerencia {g.sigla} borrada (logico, areas desactivadas: {len(areas)})",
        detalles={"sigla": g.sigla, "areas_desactivadas": [a.id for a in areas]},
    )
    await db.commit()
    logger.info(
        f"Gerencia borrada (logico): {g.sigla} (id={g.id}, "
        f"areas desactivadas: {len(areas)})"
    )
    _, count = await _get_gerencia_with_count(db, g.id)
    return _to_out(g, count)
