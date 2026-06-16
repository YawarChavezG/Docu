"""
api/v1/tipos_documento.py — CRUD del catalogo de tipos de documento (US-9.03 sub-1).

13 tipos del Excel TIPOS DE DOCUMENTO, CÓDIGO Y VIGENCIA.xlsx.
2 comparten codigo_doc=6 (INSTRUCTIVO e INSTRUCTIVO TECNICO) — `codigo_doc` es logico, no unique.

Endpoints (todos bajo prefix /api/v1/tipos-documento):
  GET    /              lista con ?q= ?activo=
  GET    /{id}          detalle
  POST   /              crear (ETO o ADMIN)
  PATCH  /{id}          update parcial
  DELETE /{id}          borrado logico

GETs no requieren auth. Mutaciones requieren ETO o ADMIN.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.models.tipo_documento import TipoDocumento
from app.schemas.tipo_documento import (
    TipoDocumentoCreate,
    TipoDocumentoListResponse,
    TipoDocumentoOut,
    TipoDocumentoUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tipos-documento", tags=["Tipos Documento"])


@router.get("", response_model=TipoDocumentoListResponse)
async def list_tipos(
    q: str | None = Query(None, description="Busca en codigo y nombre"),
    activo: str | None = Query(None, description="'true', 'false', o 'all' (default: 'true')"),
    db: AsyncSession = Depends(get_db),
):
    """Lista los 13 tipos. No requiere auth (catalogo publico)."""
    base = select(TipoDocumento)
    if q:
        pat = f"%{q.lower()}%"
        base = base.where(or_(
            func.lower(TipoDocumento.codigo).like(pat),
            func.lower(TipoDocumento.nombre).like(pat),
        ))
    if activo is None or activo == "true":
        base = base.where(TipoDocumento.activo == True)
    elif activo == "false":
        base = base.where(TipoDocumento.activo == False)
    # activo == "all" -> no filtra

    rows = (await db.execute(
        base.order_by(TipoDocumento.codigo_doc.asc(), TipoDocumento.codigo.asc())
    )).scalars().all()

    return TipoDocumentoListResponse(
        total=len(rows),
        items=[TipoDocumentoOut.model_validate(r) for r in rows],
    )


@router.get("/{tipo_id}", response_model=TipoDocumentoOut)
async def get_tipo(
    tipo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Detalle. No requiere auth."""
    t = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.id == tipo_id)
    )).scalar_one_or_none()
    if t is None:
        raise HTTPException(404, f"TipoDocumento {tipo_id} no existe")
    return TipoDocumentoOut.model_validate(t)


@router.post("", response_model=TipoDocumentoOut, status_code=status.HTTP_201_CREATED)
async def create_tipo(
    payload: TipoDocumentoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Crea un tipo. Requiere ETO o ADMIN. 409 si codigo duplicado."""
    await require_eto_or_admin(request, db)

    # Validacion: periodo_vigencia e indefinido no pueden ser ambos True
    if payload.indefinido and payload.periodo_vigencia is not None:
        raise HTTPException(
            422,
            "Si 'indefinido' es True, 'periodo_vigencia' debe ser None",
        )

    existing = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == payload.codigo)
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ya existe un tipo con codigo '{payload.codigo}'",
        )

    t = TipoDocumento(
        codigo=payload.codigo,
        nombre=payload.nombre,
        codigo_doc=payload.codigo_doc,
        periodo_vigencia=payload.periodo_vigencia,
        indefinido=payload.indefinido,
        max_descargas_dia=payload.max_descargas_dia,
        observacion=payload.observacion,
        activo=payload.activo,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    logger.info(f"TipoDocumento creado: {t.codigo} (cod_doc={t.codigo_doc})")
    return TipoDocumentoOut.model_validate(t)


@router.patch("/{tipo_id}", response_model=TipoDocumentoOut)
async def update_tipo(
    tipo_id: int,
    payload: TipoDocumentoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un tipo. Requiere ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    t = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.id == tipo_id)
    )).scalar_one_or_none()
    if t is None:
        raise HTTPException(404, f"TipoDocumento {tipo_id} no existe")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return TipoDocumentoOut.model_validate(t)

    for field, value in data.items():
        setattr(t, field, value)

    # Validar consistencia post-merge
    if t.indefinido and t.periodo_vigencia is not None:
        raise HTTPException(
            422,
            "Si 'indefinido' es True, 'periodo_vigencia' debe ser None",
        )

    await db.commit()
    await db.refresh(t)
    logger.info(f"TipoDocumento actualizado: {t.codigo} (campos={list(data.keys())})")
    return TipoDocumentoOut.model_validate(t)


@router.delete("/{tipo_id}", response_model=TipoDocumentoOut)
async def delete_tipo(
    tipo_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Borrado logico (activo=false). Requiere ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    t = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.id == tipo_id)
    )).scalar_one_or_none()
    if t is None:
        raise HTTPException(404, f"TipoDocumento {tipo_id} no existe")
    if not t.activo:
        raise HTTPException(409, f"TipoDocumento {t.codigo} ya estaba inactivo")
    t.activo = False
    await db.commit()
    await db.refresh(t)
    logger.info(f"TipoDocumento borrado (logico): {t.codigo}")
    return TipoDocumentoOut.model_validate(t)
