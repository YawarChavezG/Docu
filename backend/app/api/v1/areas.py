"""
api/v1/areas.py — CRUD de areas (US-9.06) + operaciones jerarquicas (Sesion B - #9d).

Pensado para la pantalla Parametrizacion > Gerencias y Areas (panel derecho).
Reemplaza al mock `frontend/src/data/parametrosSistema.js`.

Endpoints (todos bajo prefix /api/v1/areas):
  GET    /                              -> lista paginada con filtros ?q= ?gerencia_id= ?activo=
  GET    /{id}                          -> detalle (incluye gerencia y conteo de usuarios)
  POST   /                              -> crear (ETO o ADMIN). Valida gerencia_id existe.
  PATCH  /{id}                          -> update parcial (ETO o ADMIN)
  DELETE /{id}?fisico=true|false        -> borrado logico (default) o fisico (ETO o ADMIN)
  POST   /{id}/mover                    -> mover area a otra gerencia (ETO o ADMIN)
  POST   /{id}/promover-a-gerencia      -> convertir area en la primera de una nueva gerencia (ETO o ADMIN)

El router se monta con prefix=/api/v1 en main.py. NO repetir el prefijo.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.core.audit import write_audit
from app.models.area import Area
from app.models.gerencia import Gerencia
from app.models.usuario import Usuario
from app.schemas.area import (
    AreaCreate,
    AreaListResponse,
    AreaMoverRequest,
    AreaOut,
    AreaPromoverRequest,
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
    404 si gerencia_id no existe, 409 si sigla duplicada DENTRO de la gerencia.

    Desde Sesion B (fix B1): la sigla es unica POR GERENCIA, no global. Asi se
    puede "revivir" un area con la misma sigla en otra gerencia.
    """
    user = await require_eto_or_admin(request, db)

    # Validar gerencia existe
    await _resolve_gerencia(db, payload.gerencia_id)

    existing = (await db.execute(
        select(Area).where(
            and_(Area.gerencia_id == payload.gerencia_id, Area.sigla == payload.sigla)
        )
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un area con la sigla '{payload.sigla}' en la gerencia {payload.gerencia_id}",
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
    await write_audit(
        db, request, user,
        accion="CREATE", recurso="area", recurso_id=a.id,
        descripcion=f"Area {a.sigla} creada en gerencia {a.gerencia_id}",
        detalles={"despues": {"sigla": a.sigla, "nombre": a.nombre, "gerencia_id": a.gerencia_id, "orden": a.orden, "activo": a.activo}},
    )
    await db.commit()

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
    404 si area/gerencia no existen, 409 si sigla choca con OTRA area de la misma gerencia.
    """
    user = await require_eto_or_admin(request, db)

    a = (await db.execute(
        select(Area).where(Area.id == area_id)
    )).scalar_one_or_none()
    if a is None:
        raise HTTPException(status_code=404, detail=f"Area {area_id} no encontrada")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        _, sigla, nombre, users_count = await _get_area_with_relations(db, a.id)
        return _to_out(a, sigla, nombre, users_count)

    antes = {"sigla": a.sigla, "nombre": a.nombre, "gerencia_id": a.gerencia_id, "orden": a.orden, "activo": a.activo, "jefe_id": a.jefe_id}

    target_gerencia_id = data.get("gerencia_id", a.gerencia_id)
    if "gerencia_id" in data and data["gerencia_id"] != a.gerencia_id:
        await _resolve_gerencia(db, data["gerencia_id"])

    if "sigla" in data and data["sigla"] != a.sigla:
        dup = (await db.execute(
            select(Area).where(
                and_(
                    Area.gerencia_id == target_gerencia_id,
                    Area.sigla == data["sigla"],
                    Area.id != area_id,
                )
            )
        )).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"La sigla '{data['sigla']}' ya esta en uso por otra area de la gerencia {target_gerencia_id}",
            )

    for field, value in data.items():
        setattr(a, field, value)

    await db.commit()
    await db.refresh(a)
    despues = {"sigla": a.sigla, "nombre": a.nombre, "gerencia_id": a.gerencia_id, "orden": a.orden, "activo": a.activo, "jefe_id": a.jefe_id}
    await write_audit(
        db, request, user,
        accion="UPDATE", recurso="area", recurso_id=a.id,
        descripcion=f"Area {a.sigla} actualizada (campos: {list(data.keys())})",
        detalles={"antes": antes, "despues": despues, "campos": list(data.keys())},
    )
    await db.commit()
    logger.info(f"Area actualizada: {a.sigla} (id={a.id}, campos={list(data.keys())})")
    _, sigla, nombre, users_count = await _get_area_with_relations(db, a.id)
    return _to_out(a, sigla, nombre, users_count)


@router.delete("/{area_id}", response_model=AreaOut)
async def delete_area(
    area_id: int,
    request: Request,
    fisico: bool = Query(False, description="Si true, borrado fisico. Si false (default), borrado logico (activo=false)."),
    db: AsyncSession = Depends(get_db),
):
    """
    Borrado de un area. Por default es borrado LOGICO (activo=False).
    Pasar ?fisico=true para borrado FISICO (no se puede deshacer).

    Si tiene usuarios vinculados y se hace borrado LOGICO: los usuarios quedan
    visibles en consultas con su area_id, pero el area aparece inactiva.
    Si se hace borrado FISICO con usuarios: 409 (hay que reasignarlos antes).
    """
    user = await require_eto_or_admin(request, db)

    a, sigla, nombre, users_count = await _get_area_with_relations(db, area_id)

    if not fisico:
        if not a.activo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El area '{a.sigla}' ya estaba inactiva",
            )
        a.activo = False
        await db.commit()
        await db.refresh(a)
        await write_audit(
            db, request, user,
            accion="DELETE", recurso="area", recurso_id=a.id,
            descripcion=f"Area {a.sigla} borrada (logico, usuarios vinculados: {users_count})",
            detalles={"sigla": a.sigla, "usuarios_vinculados": users_count, "tipo": "logico"},
        )
        await db.commit()
        logger.info(
            f"Area borrada (logico): {a.sigla} (id={a.id}, usuarios vinculados: {users_count})"
        )
        return _to_out(a, sigla, nombre, users_count)

    # Borrado FISICO
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede borrar fisicamente el area '{a.sigla}': "
                f"tiene {users_count} usuarios vinculados. "
                f"Reasignarlos primero o usar borrado logico (sin ?fisico=true)."
            ),
        )
    snapshot = {"sigla": a.sigla, "nombre": a.nombre, "gerencia_id": a.gerencia_id}
    # Escribir audit LOG y borrar area en la misma transaccion (atomico)
    await write_audit(
        db, request, user,
        accion="DELETE", recurso="area", recurso_id=area_id,
        descripcion=f"Area {snapshot['sigla']} borrada (FISICO, irrecuperable)",
        detalles={**snapshot, "tipo": "fisico"},
    )
    await db.delete(a)
    await db.commit()
    logger.info(f"Area borrada (FISICO): {snapshot['sigla']} (id={area_id})")
    raise HTTPException(
        status_code=status.HTTP_204_NO_CONTENT,
        detail=None,
    )


# ─── Operaciones jerarquicas (Sesion B - tarea #9d) ───

@router.post("/{area_id}/mover", response_model=AreaOut)
async def mover_area(
    area_id: int,
    payload: AreaMoverRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Mueve un area a otra gerencia. Cambia gerencia_id.
    404 si area o gerencia destino no existen, 422 si origen == destino,
    409 si en la gerencia destino ya existe un area con la misma sigla.

    Nota: la sigla se preserva. Si en la gerencia destino ya existe un area
    con esa sigla, primero PATCH la sigla actual y despues mover.
    """
    user = await require_eto_or_admin(request, db)

    a = (await db.execute(
        select(Area).where(Area.id == area_id)
    )).scalar_one_or_none()
    if a is None:
        raise HTTPException(404, f"Area {area_id} no encontrada")

    if payload.gerencia_id_destino == a.gerencia_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El area ya pertenece a la gerencia {a.gerencia_id}",
        )

    # Validar gerencia destino existe
    await _resolve_gerencia(db, payload.gerencia_id_destino)

    # Validar no choque de sigla en gerencia destino
    dup = (await db.execute(
        select(Area).where(
            and_(
                Area.gerencia_id == payload.gerencia_id_destino,
                Area.sigla == a.sigla,
            )
        )
    )).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"No se puede mover: la gerencia {payload.gerencia_id_destino} "
                f"ya tiene un area con la sigla '{a.sigla}' (id={dup.id})"
            ),
        )

    gerencia_origen_id = a.gerencia_id
    a.gerencia_id = payload.gerencia_id_destino
    await db.commit()
    await db.refresh(a)
    await write_audit(
        db, request, user,
        accion="MOVE", recurso="area", recurso_id=a.id,
        descripcion=f"Area {a.sigla} movida de gerencia {gerencia_origen_id} -> {payload.gerencia_id_destino}",
        detalles={
            "gerencia_id_anterior": gerencia_origen_id,
            "gerencia_id_nueva": payload.gerencia_id_destino,
            "sigla": a.sigla,
        },
    )
    await db.commit()
    logger.info(
        f"Area {a.sigla} (id={a.id}) movida gerencia {gerencia_origen_id} -> {payload.gerencia_id_destino}"
    )
    _, sigla_g, nombre_g, users_count = await _get_area_with_relations(db, a.id)
    return _to_out(a, sigla_g, nombre_g, users_count)


@router.post("/{area_id}/promover-a-gerencia", response_model=AreaOut)
async def promover_area_a_gerencia(
    area_id: int,
    payload: AreaPromoverRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Promueve esta area a ser la primera area de una NUEVA gerencia.

    Flujo:
      1. Crea la nueva gerencia (sigla + nombre del body).
      2. Mueve esta area a esa nueva gerencia.
      3. Devuelve el area (ahora con gerencia_id = nueva gerencia).

    404 si area no existe, 409 si la sigla de la nueva gerencia ya existe.
    """
    user = await require_eto_or_admin(request, db)

    a = (await db.execute(
        select(Area).where(Area.id == area_id)
    )).scalar_one_or_none()
    if a is None:
        raise HTTPException(404, f"Area {area_id} no encontrada")

    # Validar sigla de nueva gerencia no exista
    dup_g = (await db.execute(
        select(Gerencia).where(Gerencia.sigla == payload.sigla_gerencia)
    )).scalar_one_or_none()
    if dup_g is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una gerencia con la sigla '{payload.sigla_gerencia}'",
        )

    # 1. Crear la nueva gerencia
    nueva_ger = Gerencia(
        sigla=payload.sigla_gerencia,
        nombre=payload.nombre_gerencia,
        orden=0,
        activo=True,
    )
    db.add(nueva_ger)
    await db.commit()
    await db.refresh(nueva_ger)
    await write_audit(
        db, request, user,
        accion="CREATE", recurso="gerencia", recurso_id=nueva_ger.id,
        descripcion=f"Gerencia {nueva_ger.sigla} creada (auto, al promover area {a.sigla})",
        detalles={"despues": {"sigla": nueva_ger.sigla, "nombre": nueva_ger.nombre, "origen": "promover_area", "area_origen_id": a.id}},
    )
    await db.commit()

    # 2. Mover el area
    gerencia_origen_id = a.gerencia_id
    a.gerencia_id = nueva_ger.id
    await db.commit()
    await db.refresh(a)
    await write_audit(
        db, request, user,
        accion="MOVE", recurso="area", recurso_id=a.id,
        descripcion=(
            f"Area {a.sigla} promovida a gerencia {nueva_ger.sigla} "
            f"(gerencia_origen_id={gerencia_origen_id} -> {nueva_ger.id})"
        ),
        detalles={
            "gerencia_id_anterior": gerencia_origen_id,
            "gerencia_id_nueva": nueva_ger.id,
            "gerencia_nueva_sigla": nueva_ger.sigla,
            "gerencia_nueva_nombre": nueva_ger.nombre,
            "sigla": a.sigla,
        },
    )
    await db.commit()
    logger.info(
        f"Area {a.sigla} (id={a.id}) promovida a nueva gerencia "
        f"{nueva_ger.sigla} (id={nueva_ger.id}) desde gerencia {gerencia_origen_id}"
    )
    _, sigla_g, nombre_g, users_count = await _get_area_with_relations(db, a.id)
    return _to_out(a, sigla_g, nombre_g, users_count)
