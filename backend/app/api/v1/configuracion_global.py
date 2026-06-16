"""
api/v1/configuracion_global.py — CRUD clave-valor de parametros globales.

US-9.01 (Tiempos y SLAs) + US-9.02 (Restricciones).
Cubre plazos, semaforo, limites de archivos, limites de descarga, paginacion.

Endpoints (todos bajo prefix /api/v1/configuracion-global):
  GET    /                       -> lista todas (filtros ?categoria= ?tipo=)
  GET    /{clave}                -> detalle de una clave
  POST   /                       -> upsert: crea si no existe, actualiza si existe
  PATCH  /{clave}                -> update de valor (y opcionalmente descripcion)
  POST   /bulk                   -> upsert masivo por categoria (US-9.01 "Guardar Vigencia y Flujo")
  DELETE /{clave}                -> borrado logico (activo=false)

GETs no requieren auth (catalogos publicos). Mutaciones requieren ETO o ADMIN.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.configuracion_global import (
    ConfiguracionGlobal,
    CategoriaConfiguracion,
    TipoConfiguracion,
)
from app.schemas.configuracion_global import (
    ConfiguracionGlobalCreate,
    ConfiguracionGlobalListResponse,
    ConfiguracionGlobalOut,
    ConfiguracionGlobalUpdate,
    ConfiguracionBulkRequest,
    ConfiguracionBulkResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/configuracion-global", tags=["Configuracion Global"])


# ─── Helpers ───

async def _get_by_clave(db: AsyncSession, clave: str) -> ConfiguracionGlobal:
    cfg = (await db.execute(
        select(ConfiguracionGlobal).where(ConfiguracionGlobal.clave == clave)
    )).scalar_one_or_none()
    if cfg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clave de configuracion '{clave}' no existe",
        )
    return cfg


# ─── Endpoints ───

@router.get("", response_model=ConfiguracionGlobalListResponse)
async def list_configuracion(
    categoria: Optional[CategoriaConfiguracion] = Query(None),
    tipo: Optional[TipoConfiguracion] = Query(None),
    solo_activos: bool = Query(True, description="Si false, incluye desactivados"),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los parametros. No requiere auth (catalogo publico)."""
    base = select(ConfiguracionGlobal)
    if categoria is not None:
        base = base.where(ConfiguracionGlobal.categoria == categoria)
    if tipo is not None:
        base = base.where(ConfiguracionGlobal.tipo == tipo)
    if solo_activos:
        base = base.where(ConfiguracionGlobal.activo == True)

    rows = (await db.execute(
        base.order_by(ConfiguracionGlobal.categoria, ConfiguracionGlobal.clave)
    )).scalars().all()

    return ConfiguracionGlobalListResponse(
        total=len(rows),
        items=[ConfiguracionGlobalOut.model_validate(r) for r in rows],
    )


@router.get("/{clave}", response_model=ConfiguracionGlobalOut)
async def get_configuracion(
    clave: str,
    db: AsyncSession = Depends(get_db),
):
    """Detalle de un parametro. No requiere auth."""
    cfg = await _get_by_clave(db, clave)
    return ConfiguracionGlobalOut.model_validate(cfg)


@router.post("", response_model=ConfiguracionGlobalOut, status_code=status.HTTP_200_OK)
async def upsert_configuracion(
    payload: ConfiguracionGlobalCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea o actualiza un parametro (UPSERT). Requiere ETO o ADMIN.
    Devuelve 200 (no 201) si la clave ya existia.
    """
    user = await require_eto_or_admin(request, db)

    existing = (await db.execute(
        select(ConfiguracionGlobal).where(ConfiguracionGlobal.clave == payload.clave)
    )).scalar_one_or_none()

    if existing is None:
        cfg = ConfiguracionGlobal(
            clave=payload.clave,
            valor=payload.valor,
            tipo=payload.tipo,
            categoria=payload.categoria,
            descripcion=payload.descripcion,
            activo=True,
            updated_by_id=user.id,
        )
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
        logger.info(f"Config creada: {cfg.clave} = {cfg.valor!r} (tipo={cfg.tipo.value})")
        return ConfiguracionGlobalOut.model_validate(cfg)
    else:
        existing.valor = payload.valor
        existing.tipo = payload.tipo
        existing.categoria = payload.categoria
        existing.descripcion = payload.descripcion
        existing.activo = True
        existing.updated_by_id = user.id
        await db.commit()
        await db.refresh(existing)
        logger.info(
            f"Config actualizada: {existing.clave} = {existing.valor!r} "
            f"(por user_id={user.id})"
        )
        return ConfiguracionGlobalOut.model_validate(existing)


@router.patch("/{clave}", response_model=ConfiguracionGlobalOut)
async def update_configuracion(
    clave: str,
    payload: ConfiguracionGlobalUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza solo el valor (y opcionalmente descripcion). Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    cfg = await _get_by_clave(db, clave)

    cfg.valor = payload.valor
    if payload.descripcion is not None:
        cfg.descripcion = payload.descripcion
    cfg.updated_by_id = user.id
    await db.commit()
    await db.refresh(cfg)
    logger.info(
        f"Config PATCH: {cfg.clave} = {cfg.valor!r} (por user_id={user.id})"
    )
    return ConfiguracionGlobalOut.model_validate(cfg)


@router.post("/bulk", response_model=ConfiguracionBulkResponse)
async def bulk_upsert_configuracion(
    payload: ConfiguracionBulkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Upsert masivo por categoria. Usado por US-9.01 "Guardar Vigencia y Flujo"
    donde el cliente envia 4 plazos de golpe.

    Si la clave existe -> actualiza valor. Si no existe -> crea con tipo=STR
    (el cliente debe especificar tipo en POST unitario si necesita INT/JSON).
    """
    user = await require_eto_or_admin(request, db)

    actualizadas = 0
    creadas = 0
    claves_procesadas: list[str] = []

    for item in payload.items:
        existing = (await db.execute(
            select(ConfiguracionGlobal).where(ConfiguracionGlobal.clave == item.clave)
        )).scalar_one_or_none()

        if existing is None:
            cfg = ConfiguracionGlobal(
                clave=item.clave,
                valor=item.valor,
                tipo=TipoConfiguracion.STR,  # default; usar POST unitario para tipos estrictos
                categoria=payload.categoria,
                descripcion=None,
                activo=True,
                updated_by_id=user.id,
            )
            db.add(cfg)
            creadas += 1
        else:
            existing.valor = item.valor
            existing.updated_by_id = user.id
            actualizadas += 1
        claves_procesadas.append(item.clave)
        await db.flush()

    await db.commit()
    logger.info(
        f"Config bulk: categoria={payload.categoria.value} "
        f"creadas={creadas} actualizadas={actualizadas} "
        f"(por user_id={user.id})"
    )
    return ConfiguracionBulkResponse(
        actualizadas=actualizadas,
        creadas=creadas,
        claves=claves_procesadas,
    )


@router.delete("/{clave}", response_model=ConfiguracionGlobalOut)
async def delete_configuracion(
    clave: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Borrado logico (activo=false). Requiere ETO o ADMIN.
    404 si no existe, 409 si ya estaba inactiva.
    """
    await require_eto_or_admin(request, db)
    cfg = await _get_by_clave(db, clave)
    if not cfg.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La clave '{clave}' ya estaba inactiva",
        )
    cfg.activo = False
    await db.commit()
    await db.refresh(cfg)
    logger.info(f"Config borrada (logico): {clave}")
    return ConfiguracionGlobalOut.model_validate(cfg)
