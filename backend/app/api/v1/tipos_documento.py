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
from app.core.audit import write_audit
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
            func.cast(TipoDocumento.codigo, __import__("sqlalchemy").String).like(pat),
            func.lower(TipoDocumento.slug).like(pat),
            func.lower(TipoDocumento.nombre).like(pat),
        ))
    if activo is None or activo == "true":
        base = base.where(TipoDocumento.activo == True)
    elif activo == "false":
        base = base.where(TipoDocumento.activo == False)
    # activo == "all" -> no filtra

    rows = (await db.execute(
        base.order_by(TipoDocumento.codigo.asc(), TipoDocumento.slug.asc())
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
    user = await require_eto_or_admin(request, db)

    # Validacion: periodo_vigencia e indefinido no pueden ser ambos True
    if payload.indefinido and payload.periodo_vigencia is not None:
        raise HTTPException(
            422,
            "Si 'indefinido' es True, 'periodo_vigencia' debe ser None",
        )

    # Validar unicidad de codigo y slug
    existing_codigo = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == payload.codigo)
    )).scalar_one_or_none()
    if existing_codigo is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ya existe un tipo con codigo '{payload.codigo}' ({existing_codigo.slug})",
        )
    existing_slug = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.slug == payload.slug)
    )).scalar_one_or_none()
    if existing_slug is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ya existe un tipo con slug '{payload.slug}'",
        )
    existing_nombre = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.nombre == payload.nombre)
    )).scalar_one_or_none()
    if existing_nombre is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ya existe un tipo con nombre '{payload.nombre}'",
        )

    t = TipoDocumento(
        codigo=payload.codigo,
        slug=payload.slug,
        nombre=payload.nombre,
        periodo_vigencia=payload.periodo_vigencia,
        indefinido=payload.indefinido,
        max_descargas_dia=payload.max_descargas_dia,
        observacion=payload.observacion,
        activo=payload.activo,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    await write_audit(
        db, request, user,
        accion="CREATE", recurso="tipo_documento", recurso_id=t.id,
        descripcion=f"TipoDocumento codigo={t.codigo} slug={t.slug!r} creado",
        detalles={"despues": {"codigo": t.codigo, "slug": t.slug, "nombre": t.nombre, "periodo_vigencia": t.periodo_vigencia, "indefinido": t.indefinido, "max_descargas_dia": t.max_descargas_dia, "activo": t.activo}},
    )
    await db.commit()
    logger.info(f"TipoDocumento creado: codigo={t.codigo} slug={t.slug!r}")
    return TipoDocumentoOut.model_validate(t)


@router.patch("/{tipo_id}", response_model=TipoDocumentoOut)
async def update_tipo(
    tipo_id: int,
    payload: TipoDocumentoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un tipo. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    t = (await db.execute(
        select(TipoDocumento).where(TipoDocumento.id == tipo_id)
    )).scalar_one_or_none()
    if t is None:
        raise HTTPException(404, f"TipoDocumento {tipo_id} no existe")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return TipoDocumentoOut.model_validate(t)

    # Validar unicidad si cambia codigo o slug
    if "codigo" in data and data["codigo"] != t.codigo:
        if (await db.execute(
            select(TipoDocumento).where(TipoDocumento.codigo == data["codigo"], TipoDocumento.id != t.id)
        )).scalar_one_or_none() is not None:
            raise HTTPException(409, f"Ya existe un tipo con codigo '{data['codigo']}'")
    if "slug" in data and data["slug"] != t.slug:
        if (await db.execute(
            select(TipoDocumento).where(TipoDocumento.slug == data["slug"], TipoDocumento.id != t.id)
        )).scalar_one_or_none() is not None:
            raise HTTPException(409, f"Ya existe un tipo con slug '{data['slug']}'")
    if "nombre" in data and data["nombre"] != t.nombre:
        if (await db.execute(
            select(TipoDocumento).where(TipoDocumento.nombre == data["nombre"], TipoDocumento.id != t.id)
        )).scalar_one_or_none() is not None:
            raise HTTPException(409, f"Ya existe un tipo con nombre '{data['nombre']}'")

    antes = {"codigo": t.codigo, "slug": t.slug, "nombre": t.nombre, "periodo_vigencia": t.periodo_vigencia, "indefinido": t.indefinido, "max_descargas_dia": t.max_descargas_dia, "activo": t.activo}

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
    despues = {"codigo": t.codigo, "slug": t.slug, "nombre": t.nombre, "periodo_vigencia": t.periodo_vigencia, "indefinido": t.indefinido, "max_descargas_dia": t.max_descargas_dia, "activo": t.activo}
    await write_audit(
        db, request, user,
        accion="UPDATE", recurso="tipo_documento", recurso_id=t.id,
        descripcion=f"TipoDocumento codigo={t.codigo} slug={t.slug!r} actualizado (campos={list(data.keys())})",
        detalles={"antes": antes, "despues": despues, "campos": list(data.keys())},
    )
    await db.commit()
    logger.info(f"TipoDocumento actualizado: codigo={t.codigo} (campos={list(data.keys())})")
    return TipoDocumentoOut.model_validate(t)


@router.delete("/{tipo_id}", response_model=TipoDocumentoOut)
async def delete_tipo(
    tipo_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Borrado logico (activo=false). Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
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
    await write_audit(
        db, request, user,
        accion="DELETE", recurso="tipo_documento", recurso_id=t.id,
        descripcion=f"TipoDocumento codigo={t.codigo} slug={t.slug!r} borrado (logico)",
        detalles={"codigo": t.codigo, "slug": t.slug},
    )
    await db.commit()
    logger.info(f"TipoDocumento borrado (logico): codigo={t.codigo} slug={t.slug!r}")
    return TipoDocumentoOut.model_validate(t)
