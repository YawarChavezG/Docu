"""
api/v1/areas.py — CRUD de areas (US-9.06).

Pensado para la pantalla Parametrizacion > Gerencias y Areas (panel derecho).
Reemplaza al mock `frontend/src/data/parametrosSistema.js`.

Endpoints (todos bajo prefix /api/v1/areas):
  GET    /              -> lista paginada con filtros ?q= ?gerencia_id= ?activo=
  GET    /{id}          -> detalle (incluye gerencia y conteo de usuarios)
  POST   /              -> crear (ETO o ADMIN). Valida gerencia_id existe.
  PATCH  /{id}          -> update parcial (ETO o ADMIN)
  DELETE /{id}          -> borrado logico (activo=false, ETO o ADMIN)

El router se monta con prefix=/api/v1 en main.py. NO repetir el prefijo.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.area import Area
from app.models.gerencia import Gerencia
from app.models.usuario import Usuario
from app.schemas.area import (
    AreaCreate,
    AreaListResponse,
    AreaOut,
    AreaUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/areas", tags=["Areas"])


# ─── Helpers ───

def _to_out(
    a: Area,
    gerencia_sigla: Optional[str],
    gerencia_nombre: Optional[str],
    usuarios_count: int,
) -> AreaOut:
    return AreaOut(
        id=a.id,
        gerencia_id=a.gerencia_id,
        gerencia_sigla=gerencia_sigla,
        gerencia_nombre=gerencia_nombre,
        sigla=a.sigla,
        nombre=a.nombre,
        activo=a.activo,
        orden=a.orden,
        jefe_id=a.jefe_id,
        usuarios_count=usuarios_count,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


async def _resolve_gerencia(
    db: AsyncSession, gerencia_id: int
) -> tuple[str, str]:
    """Devuelve (sigla, nombre) de la gerencia o 404."""
    g = (await db.execute(
        select(Gerencia.sigla, Gerencia.nombre).where(Gerencia.id == gerencia_id)
    )).one_or_none()
    if g is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gerencia {gerencia_id} no existe",
        )
    return g


async def _get_area_with_relations(
    db: AsyncSession, area_id: int
) -> tuple[Area, str, str, int]:
    """Carga area + sigla/nombre gerencia + conteo usuarios en 3 queries."""
    a = (await db.execute(
        select(Area).where(Area.id == area_id)
    )).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail=f"Area {area_id} no encontrada")

    g_row = (await db.execute(
        select(Gerencia.sigla, Gerencia.nombre).where(Gerencia.id == a.gerencia_id)
    )).one()
    sigla, nombre = g_row

    users_count = (await db.execute(
        select(func.count()).select_from(Usuario).where(Usuario.area_id == area_id)
    )).scalar_one()

    return a, sigla, nombre, users_count


# ─── Endpoints ───

@router.get("", response_model=AreaListResponse)
async def list_areas(
    q: Optional[str] = Query(None, description="Busca en sigla y nombre (case-insensitive)"),
    gerencia_id: Optional[int] = Query(None, ge=1, description="Filtra por gerencia"),
    activo: Optional[str] = Query(None, description="'true', 'false', o 'all' (default: 'true')"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista areas con paginacion y filtros. No requiere autenticacion
    (catalogos publicos se consumen antes de login en algunos flujos).
    """
    base = select(Area).options(selectinload(Area.gerencia))

    if q:
        pat = f"%{q.lower()}%"
        base = base.where(or_(
            func.lower(Area.sigla).like(pat),
            func.lower(Area.nombre).like(pat),
        ))
    if gerencia_id is not None:
        base = base.where(Area.gerencia_id == gerencia_id)
    if activo is None or activo == "true":
        base = base.where(Area.activo == True)
    elif activo == "false":
        base = base.where(Area.activo == False)
    # activo == "all" -> no filtra

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    rows = (await db.execute(
        base.order_by(Area.gerencia_id.asc(), Area.orden.asc(), Area.sigla.asc())
            .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    # Conteo de usuarios por area en una sola query
    ids = [a.id for a in rows]
    counts_by_area: dict[int, int] = {}
    if ids:
        count_rows = (await db.execute(
            select(Usuario.area_id, func.count(Usuario.id))
            .where(Usuario.area_id.in_(ids))
            .group_by(Usuario.area_id)
        )).all()
        counts_by_area = {aid: cnt for aid, cnt in count_rows}

    items = [
        _to_out(
            a,
            a.gerencia.sigla if a.gerencia else None,
            a.gerencia.nombre if a.gerencia else None,
            counts_by_area.get(a.id, 0),
        )
        for a in rows
    ]

    return AreaListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{area_id}", response_model=AreaOut)
async def get_area(
    area_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de un area. No requiere auth (catalogo publico)."""
    a, sigla, nombre, users_count = await _get_area_with_relations(db, area_id)
    return _to_out(a, sigla, nombre, users_count)


@router.post("", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
async def create_area(
    payload: AreaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un area. Requiere rol ETO o ADMIN.
    404 si gerencia_id no existe, 409 si sigla duplicada.

    NOTA: el constraint `areas.sigla UNIQUE` es global (no se libera al
    hacer borrado logico). Si necesitas "recrear" un area con la misma
    sigla despues de borrarla, primero renombrala (PATCH con sigla nueva)
    o espera a Sesion B para que se libere la sigla en el schema.
    """
    await require_eto_or_admin(request, db)

    # Validar gerencia existe
    await _resolve_gerencia(db, payload.gerencia_id)

    existing = (await db.execute(
        select(Area).where(Area.sigla == payload.sigla)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un area con la sigla '{payload.sigla}'",
        )

    a = Area(
        gerencia_id=payload.gerencia_id,
        sigla=payload.sigla,
        nombre=payload.nombre,
        orden=payload.orden,
        jefe_id=payload.jefe_id,
        activo=payload.activo,
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)

    logger.info(
        f"Area creada: {a.sigla} (id={a.id}, gerencia_id={a.gerencia_id})"
    )
    _, sigla, nombre, _ = await _get_area_with_relations(db, a.id)
    return _to_out(a, sigla, nombre, usuarios_count=0)


@router.patch("/{area_id}", response_model=AreaOut)
async def update_area(
    area_id: int,
    payload: AreaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza parcialmente un area. Requiere rol ETO o ADMIN.
    404 si area/gerencia no existen, 409 si sigla choca con otra area.
    """
    await require_eto_or_admin(request, db)

    a = (await db.execute(
        select(Area).where(Area.id == area_id)
    )).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail=f"Area {area_id} no encontrada")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        _, sigla, nombre, users_count = await _get_area_with_relations(db, a.id)
        return _to_out(a, sigla, nombre, users_count)

    if "gerencia_id" in data and data["gerencia_id"] != a.gerencia_id:
        await _resolve_gerencia(db, data["gerencia_id"])

    if "sigla" in data and data["sigla"] != a.sigla:
        dup = (await db.execute(
            select(Area).where(
                Area.sigla == data["sigla"],
                Area.id != area_id,
            )
        )).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La sigla '{data['sigla']}' ya esta en uso por otra area",
            )

    for field, value in data.items():
        setattr(a, field, value)

    await db.commit()
    await db.refresh(a)
    logger.info(f"Area actualizada: {a.sigla} (id={a.id}, campos={list(data.keys())})")
    _, sigla, nombre, users_count = await _get_area_with_relations(db, a.id)
    return _to_out(a, sigla, nombre, users_count)


@router.delete("/{area_id}", response_model=AreaOut)
async def delete_area(
    area_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Borrado logico de un area. Setea activo=False.
    Si tiene usuarios vinculados, NO los modifica (la FK Area->Usuario es
    ON DELETE SET NULL; aqui solo desactivamos). Los usuarios quedan
    visibles en consultas con su area_id, pero el area aparece inactiva.

    Requiere rol ETO o ADMIN.
    """
    await require_eto_or_admin(request, db)

    a, sigla, nombre, users_count = await _get_area_with_relations(db, area_id)

    if not a.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El area '{a.sigla}' ya estaba inactiva",
        )

    a.activo = False
    await db.commit()
    await db.refresh(a)
    logger.info(
        f"Area borrada (logico): {a.sigla} (id={a.id}, usuarios vinculados: {users_count})"
    )
    return _to_out(a, sigla, nombre, users_count)
