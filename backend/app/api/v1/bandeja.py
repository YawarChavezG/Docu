"""
API v1: Bandejas
Sesion 22 R2 - FASE 2 - Tarea 2.5.

GET /api/v1/bandeja?tipo=elaboracion -> mis docs en EN_ELABORACION
GET /api/v1/bandeja?tipo=revision    -> docs donde soy revisor
GET /api/v1/bandeja?tipo=aprobacion  -> docs donde soy aprobador
GET /api/v1/bandeja?tipo=liberacion  -> docs finalizados (cualquier ETO)

RBAC:
- elaboracion, revision, aprobacion: cualquier usuario autenticado
- liberacion: solo ETO/ADMIN
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_authenticated
from app.models.area import Area
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo
from app.models.gerencia import Gerencia
from app.models.tipo_documento import TipoDocumento
from app.models.usuario import Usuario
from app.schemas.bandeja import BandejaItem, BandejaResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bandeja", tags=["bandeja"])

TIPOS_VALIDOS = ("elaboracion", "revision", "aprobacion", "liberacion")


@router.get("", response_model=BandejaResponse, summary="Bandeja de documentos segun tipo")
async def get_bandeja(
    request: Request,
    tipo: str = Query(..., description="elaboracion | revision | aprobacion | liberacion"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve los documentos de la bandeja correspondiente al usuario actual."""
    user = await require_authenticated(request, db)

    if tipo not in TIPOS_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail=f"tipo invalido. Valores: {list(TIPOS_VALIDOS)}",
        )

    # RBAC: liberacion solo ETO/ADMIN
    if tipo == "liberacion":
        from app.models.rol import CodigoRol
        is_eto_or_admin = user.roles and any(
            r.codigo in (CodigoRol.ETO, CodigoRol.ADMIN) for r in user.roles
        )
        if not is_eto_or_admin:
            raise HTTPException(
                status_code=403,
                detail="La bandeja de liberacion solo esta disponible para ETO o ADMIN",
            )

    # ─── Construir query segun tipo ───
    # Base: JOIN Documento + TipoDocumento + Area + Gerencia
    # Para revision/aprobacion: JOIN DocumentoFlujo (el mas reciente activo)
    base_columns = (
        Documento.id,
        Documento.codigo,
        Documento.version,
        Documento.titulo,
        DocumentoFlujo.revisor_ids,
        DocumentoFlujo.aprobador_ids,
        TipoDocumento.codigo.label("tipo_codigo"),
        TipoDocumento.nombre.label("tipo_nombre"),
        Gerencia.sigla.label("gerencia_sigla"),
        Area.sigla.label("area_sigla"),
        Documento.vigencia,
        Documento.estatus,
        Documento.created_by_id,
    )

    items_query = (
        select(
            *base_columns,
            DocumentoFlujo.fecha_solicitud,
            DocumentoFlujo.elaborador_id,
        )
        .join(TipoDocumento, TipoDocumento.id == Documento.tipo_documento_id)
        .join(Area, Area.id == Documento.area_id)
        .join(Gerencia, Gerencia.id == Documento.gerencia_id)
        .outerjoin(
            DocumentoFlujo,
            and_(
                DocumentoFlujo.documento_id == Documento.id,
                DocumentoFlujo.activo == True,
            ),
        )
        .where(Documento.activo == True)
    )

    count_query = select(func.count(Documento.id)).where(Documento.activo == True)

    if tipo == "elaboracion":
        # Mis docs en EN_ELABORACION (creados por mi)
        items_query = items_query.where(
            and_(
                Documento.estatus == EstatusDocumento.EN_ELABORACION,
                Documento.created_by_id == user.id,
            )
        )
        count_query = count_query.where(
            and_(
                Documento.estatus == EstatusDocumento.EN_ELABORACION,
                Documento.created_by_id == user.id,
            )
        )

    elif tipo == "revision":
        # Docs donde soy revisor Y estan en EN_REVISION.
        # NOTA: revisor_ids es JSONB. En PostgreSQL usariamos el operador @>
        # pero para compatibilidad con SQLite (tests) hacemos un filtro en Python
        # cargando todos los EN_REVISION y filtrando. Dataset esperado: <100 docs.
        items_query = items_query.where(
            Documento.estatus == EstatusDocumento.EN_REVISION
        )
        count_query = count_query.where(
            Documento.estatus == EstatusDocumento.EN_REVISION
        )

    elif tipo == "aprobacion":
        # Docs donde soy aprobador Y estan en EN_REVISION (idem, filtro en Python)
        items_query = items_query.where(
            Documento.estatus == EstatusDocumento.EN_REVISION
        )
        count_query = count_query.where(
            Documento.estatus == EstatusDocumento.EN_REVISION
        )

    elif tipo == "liberacion":
        # Docs finalizados (APROBADO)
        items_query = items_query.where(
            Documento.estatus == EstatusDocumento.APROBADO
        )
        count_query = count_query.where(
            Documento.estatus == EstatusDocumento.APROBADO
        )

    # ─── Ejecutar queries ───
    # Para revision/aprobacion: cargamos todos y filtramos en Python.
    # Para elaboracion/liberacion: podemos paginar directo en SQL.
    if tipo in ("revision", "aprobacion"):
        all_rows = (await db.execute(
            items_query.order_by(Documento.codigo.asc(), Documento.version.asc())
        )).all()
        # Filtrar segun user_id
        if tipo == "revision":
            filtered = [r for r in all_rows if user.id in (r.revisor_ids or [])]
        else:
            filtered = [r for r in all_rows if user.id in (r.aprobador_ids or [])]
        total = len(filtered)
        # Paginar en memoria
        start = (page - 1) * page_size
        rows = filtered[start:start + page_size]
    else:
        total = (await db.execute(count_query)).scalar_one() or 0
        rows = (await db.execute(
            items_query
            .order_by(Documento.codigo.asc(), Documento.version.asc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )).all()

    items = [
        BandejaItem(
            documento_id=r.id,
            codigo=r.codigo,
            codigo_completo=f"{r.codigo}/{r.version}",
            version=r.version,
            titulo=r.titulo,
            tipo_codigo=r.tipo_codigo,
            tipo_nombre=r.tipo_nombre,
            gerencia_sigla=r.gerencia_sigla,
            area_sigla=r.area_sigla,
            vigencia=r.vigencia.value if hasattr(r.vigencia, "value") else str(r.vigencia),
            estatus=r.estatus.value if hasattr(r.estatus, "value") else str(r.estatus),
            fecha_solicitud=r.fecha_solicitud,
            elaborador_id=r.elaborador_id,
            requiere_mi_accion=(tipo in ("revision", "aprobacion")),
        )
        for r in rows
    ]

    return BandejaResponse(
        tipo=tipo,
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
