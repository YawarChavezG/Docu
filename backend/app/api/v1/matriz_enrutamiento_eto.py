"""
api/v1/matriz_enrutamiento_eto.py — CRUD de la matriz ETO (US-9.03).

Define QUE analista ETO recibe la solicitud de cada gerencia.

Endpoints (todos bajo prefix /api/v1/matriz-enrutamiento-eto):
  GET    /                          lista (con JOINs a gerencia + usuarios)
  GET    /{id}                      detalle por id
  GET    /gerencia/{gerencia_id}    busca por gerencia (US-9.03 Paso 4 del flujo)
  POST   /                          crear (ETO o ADMIN)
  PATCH  /{id}                      update parcial
  DELETE /{id}                      eliminar (fisico; el seed permite re-crear)

GETs no requieren auth (catalogos publicos). Mutaciones requieren ETO o ADMIN.
El seed esta en backend/scripts/seed_matriz_eto.py.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.gerencia import Gerencia
from app.models.matriz_enrutamiento_eto import (
    MatrizEnrutamientoEto, DisponibilidadEto,
)
from app.models.rol import CodigoRol, Rol
from app.models.usuario import Usuario, usuario_roles
from app.schemas.matriz_enrutamiento_eto import (
    MatrizEnrutamientoEtoCreate,
    MatrizEnrutamientoEtoListResponse,
    MatrizEnrutamientoEtoOut,
    MatrizEnrutamientoEtoUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matriz-enrutamiento-eto", tags=["Matriz ETO"])


# ─── Helpers ───

async def _gerencia_exists(db: AsyncSession, gerencia_id: int) -> bool:
    return (await db.execute(
        select(Gerencia.id).where(Gerencia.id == gerencia_id).limit(1)
    )).first() is not None


async def _usuario_exists(db: AsyncSession, usuario_id: int) -> bool:
    return (await db.execute(
        select(Usuario.id).where(Usuario.id == usuario_id).limit(1)
    )).first() is not None


async def _user_has_role_eto(db: AsyncSession, usuario_id: int) -> bool:
    """Verifica que el usuario tenga rol ETO (rol valido para esta tabla)."""
    return (await db.execute(
        select(usuario_roles.c.rol_id)
        .join(Rol, Rol.id == usuario_roles.c.rol_id)
        .where(usuario_roles.c.usuario_id == usuario_id, Rol.codigo == CodigoRol.ETO)
        .limit(1)
    )).first() is not None


async def _build_out(db: AsyncSession, m: MatrizEnrutamientoEto) -> MatrizEnrutamientoEtoOut:
    """Carga JOINs (gerencia + usuarios) y arma el out."""
    ger = (await db.execute(
        select(Gerencia).where(Gerencia.id == m.gerencia_id)
    )).scalar_one_or_none()

    user_ids = {m.analista_usuario_id}
    if m.delegado_usuario_id:
        user_ids.add(m.delegado_usuario_id)
    if m.updated_by_id:
        user_ids.add(m.updated_by_id)
    users = (await db.execute(
        select(Usuario).where(Usuario.id.in_(user_ids))
    )).scalars().all() if user_ids else []
    user_by_id = {u.id: u for u in users}

    a = user_by_id.get(m.analista_usuario_id)
    d = user_by_id.get(m.delegado_usuario_id) if m.delegado_usuario_id else None

    return MatrizEnrutamientoEtoOut(
        id=m.id,
        gerencia_id=m.gerencia_id,
        gerencia_sigla=ger.sigla if ger else None,
        gerencia_nombre=ger.nombre if ger else None,
        analista_usuario_id=m.analista_usuario_id,
        analista_username=a.username if a else None,
        analista_nombre=a.nombre_completo if a else None,
        disponibilidad=m.disponibilidad,
        delegado_usuario_id=m.delegado_usuario_id,
        delegado_username=d.username if d else None,
        delegado_nombre=d.nombre_completo if d else None,
        created_at=m.created_at,
        updated_at=m.updated_at,
        updated_by_id=m.updated_by_id,
    )


# ─── Endpoints ───

@router.get("", response_model=MatrizEnrutamientoEtoListResponse)
async def list_matriz(
    solo_disponibles: bool = Query(False, description="Si true, excluye AUSENTE/LICENCIA"),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas las filas de la matriz. No requiere auth (catalogo publico)."""
    base = select(MatrizEnrutamientoEto)
    if solo_disponibles:
        base = base.where(MatrizEnrutamientoEto.disponibilidad == DisponibilidadEto.DISPONIBLE)

    rows = (await db.execute(
        base.order_by(MatrizEnrutamientoEto.gerencia_id)
    )).scalars().all()

    items = []
    for r in rows:
        items.append(await _build_out(db, r))
    return MatrizEnrutamientoEtoListResponse(total=len(items), items=items)


@router.get("/gerencia/{gerencia_id}", response_model=MatrizEnrutamientoEtoOut)
async def get_matriz_by_gerencia(
    gerencia_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Busca la fila de la matriz para una gerencia especifica.
    US-9.03: 'el sistema consulta esta matriz en el Paso 4 del flujo'.
    Devuelve 404 si la gerencia no tiene ETO asignado.
    """
    m = (await db.execute(
        select(MatrizEnrutamientoEto).where(MatrizEnrutamientoEto.gerencia_id == gerencia_id)
    )).scalar_one_or_none()
    if m is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gerencia {gerencia_id} no tiene ETO asignado en la matriz",
        )
    return await _build_out(db, m)


@router.get("/{matriz_id}", response_model=MatrizEnrutamientoEtoOut)
async def get_matriz(
    matriz_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle por id. No requiere auth."""
    m = (await db.execute(
        select(MatrizEnrutamientoEto).where(MatrizEnrutamientoEto.id == matriz_id)
    )).scalar_one_or_none()
    if m is None:
        raise HTTPException(404, f"Matriz ETO {matriz_id} no existe")
    return await _build_out(db, m)


@router.post("", response_model=MatrizEnrutamientoEtoOut, status_code=status.HTTP_201_CREATED)
async def create_matriz(
    payload: MatrizEnrutamientoEtoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una fila. Requiere ETO o ADMIN.
    Validaciones:
      - gerencia_id existe y no tiene ya una fila (unique)
      - analista_usuario_id existe y tiene rol ETO
      - delegado_usuario_id (si se manda) existe
    """
    user = await require_eto_or_admin(request, db)

    if not await _gerencia_exists(db, payload.gerencia_id):
        raise HTTPException(404, f"Gerencia {payload.gerencia_id} no existe")

    if not await _usuario_exists(db, payload.analista_usuario_id):
        raise HTTPException(404, f"Analista usuario {payload.analista_usuario_id} no existe")

    if not await _user_has_role_eto(db, payload.analista_usuario_id):
        raise HTTPException(
            422,
            f"Usuario {payload.analista_usuario_id} no tiene rol ETO "
            f"(no se le pueden asignar tareas de liberacion)",
        )

    if payload.delegado_usuario_id is not None:
        if not await _usuario_exists(db, payload.delegado_usuario_id):
            raise HTTPException(404, f"Delegado usuario {payload.delegado_usuario_id} no existe")
        if payload.delegado_usuario_id == payload.analista_usuario_id:
            raise HTTPException(422, "El delegado no puede ser el mismo analista")

    existing = (await db.execute(
        select(MatrizEnrutamientoEto).where(MatrizEnrutamientoEto.gerencia_id == payload.gerencia_id)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Gerencia {payload.gerencia_id} ya tiene ETO asignado (matriz_id={existing.id})",
        )

    m = MatrizEnrutamientoEto(
        gerencia_id=payload.gerencia_id,
        analista_usuario_id=payload.analista_usuario_id,
        disponibilidad=payload.disponibilidad,
        delegado_usuario_id=payload.delegado_usuario_id,
        updated_by_id=user.id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    logger.info(
        f"Matriz ETO creada: gerencia_id={m.gerencia_id} "
        f"analista={m.analista_usuario_id} (por user_id={user.id})"
    )
    return await _build_out(db, m)


@router.patch("/{matriz_id}", response_model=MatrizEnrutamientoEtoOut)
async def update_matriz(
    matriz_id: int,
    payload: MatrizEnrutamientoEtoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza una fila. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    m = (await db.execute(
        select(MatrizEnrutamientoEto).where(MatrizEnrutamientoEto.id == matriz_id)
    )).scalar_one_or_none()
    if m is None:
        raise HTTPException(404, f"Matriz ETO {matriz_id} no existe")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return await _build_out(db, m)

    if "analista_usuario_id" in data:
        if not await _usuario_exists(db, data["analista_usuario_id"]):
            raise HTTPException(404, f"Analista usuario {data['analista_usuario_id']} no existe")
        if not await _user_has_role_eto(db, data["analista_usuario_id"]):
            raise HTTPException(422, f"Usuario {data['analista_usuario_id']} no tiene rol ETO")

    if "delegado_usuario_id" in data and data["delegado_usuario_id"] is not None:
        if not await _usuario_exists(db, data["delegado_usuario_id"]):
            raise HTTPException(404, f"Delegado usuario {data['delegado_usuario_id']} no existe")
        target_analista = data.get("analista_usuario_id", m.analista_usuario_id)
        if data["delegado_usuario_id"] == target_analista:
            raise HTTPException(422, "El delegado no puede ser el mismo analista")

    for field, value in data.items():
        setattr(m, field, value)
    m.updated_by_id = user.id
    await db.commit()
    await db.refresh(m)
    logger.info(f"Matriz ETO actualizada: id={m.id} (campos={list(data.keys())})")
    return await _build_out(db, m)


@router.delete("/{matriz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_matriz(
    matriz_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina una fila (fisico, no logico). El seed permite re-crear.
    Requiere ETO o ADMIN.
    """
    await require_eto_or_admin(request, db)
    m = (await db.execute(
        select(MatrizEnrutamientoEto).where(MatrizEnrutamientoEto.id == matriz_id)
    )).scalar_one_or_none()
    if m is None:
        raise HTTPException(404, f"Matriz ETO {matriz_id} no existe")
    await db.delete(m)
    await db.commit()
    logger.info(f"Matriz ETO eliminada: id={matriz_id}")
    return None
