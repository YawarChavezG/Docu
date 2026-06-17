"""
API v1: Documentos (CORE del SGD)
Sesion 21 R2 - Fase 1: solo endpoints de LECTURA.

Endpoints (todos requieren autenticacion):
  GET /api/v1/documentos/buscar?q=texto
      Autocomplete para /version-editable. Top 10 matches.
  GET /api/v1/documentos/preview-codigo?tipo_id=X&area_id=Y&tipo_solicitud=Z
      Calcula el codigo SIN persistir. Usado por el wizard paso 1.
  GET /api/v1/documentos/{id}
      Detalle completo con joins.
  GET /api/v1/documentos?gerencia_id=&area_id=&vigencia=&estatus=&page=
      Lista paginada con filtros (para ListaMaestra y bandejas).

En Fase 2 se agregan: POST /documentos, PATCH, /archivos, /enviar.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.permissions import require_authenticated
from app.models.archivo_adjunto import ArchivoAdjunto
from app.models.area import Area
from app.models.documento import (
    Documento,
    EstatusDocumento,
    VigenciaDocumento,
)
from app.models.documento_flujo import DocumentoFlujo
from app.models.gerencia import Gerencia
from app.models.tipo_documento import TipoDocumento
from app.schemas.documento import (
    DocumentoAreaRef,
    DocumentoBuscarItem,
    DocumentoBuscarResponse,
    DocumentoFlujoBasico,
    DocumentoGerenciaRef,
    DocumentoListItem,
    DocumentoListResponse,
    DocumentoOut,
    DocumentoTipoRef,
    PreviewCodigoRequest,
    PreviewCodigoResponse,
)
from app.services.correlativo_service import (
    formatear_codigo,
    formatear_codigo_completo,
    siguiente_correlativo_advisory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documentos", tags=["documentos"])


# ════════════════════════════════════════════════════════════════
#  GET /documentos/buscar?q=...  (autocomplete)
# ════════════════════════════════════════════════════════════════

@router.get("/buscar", response_model=DocumentoBuscarResponse, summary="Autocomplete de documentos")
async def buscar_documentos(
    request: Request,
    q: str = Query("", description="Texto a buscar (codigo o titulo). Vacio = listado completo limitado."),
    limit: int = Query(10, ge=1, le=50, description="Maximo de resultados"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca documentos por coincidencia en codigo o titulo.
    - Si q empieza con letra(s) + guion: match exacto en prefijo del codigo (CC-3-...).
    - Si no: match parcial en titulo.
    Solo retorna documentos activos.
    """
    await require_authenticated(request, db)

    stmt = (
        select(Documento)
        .where(Documento.activo == True)
        .options(
            selectinload(Documento.tipo_documento),
            selectinload(Documento.area),
            selectinload(Documento.gerencia),
        )
    )

    if q.strip():
        like = f"%{q.strip()}%"
        # Priorizar match exacto de prefijo en codigo, luego match en titulo.
        stmt = stmt.where(
            or_(
                Documento.codigo.ilike(like),
                Documento.titulo.ilike(like),
            )
        )
        # Orden: primero los que EMPIEZAN con q en codigo, luego el resto.
        stmt = stmt.order_by(
            # TRUE (1) si el codigo empieza con q, FALSE (0) si no
            (Documento.codigo.ilike(f"{q.strip()}%")).desc(),
            Documento.codigo.asc(),
        )
    else:
        stmt = stmt.order_by(Documento.codigo.asc())

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    docs = result.scalars().all()

    items = [
        DocumentoBuscarItem(
            id=d.id,
            codigo=d.codigo,
            codigo_completo=d.codigo_completo,
            version=d.version,
            titulo=d.titulo,
            tipo=DocumentoTipoRef(
                id=d.tipo_documento.id,
                codigo=d.tipo_documento.codigo,
                slug=d.tipo_documento.slug,
                nombre=d.tipo_documento.nombre,
                periodo_vigencia=d.tipo_documento.periodo_vigencia,
                indefinido=d.tipo_documento.indefinido,
                max_descargas_dia=d.tipo_documento.max_descargas_dia,
            ),
            area=DocumentoAreaRef(
                id=d.area.id,
                sigla=d.area.sigla,
                nombre=d.area.nombre,
                gerencia_id=d.area.gerencia_id,
            ),
            gerencia=DocumentoGerenciaRef(
                id=d.gerencia.id,
                sigla=d.gerencia.sigla,
                nombre=d.gerencia.nombre,
            ),
            vigencia=d.vigencia.value if hasattr(d.vigencia, "value") else str(d.vigencia),
            estatus=d.estatus.value if hasattr(d.estatus, "value") else str(d.estatus),
        )
        for d in docs
    ]

    return DocumentoBuscarResponse(total=len(items), items=items)


# ════════════════════════════════════════════════════════════════
#  GET /documentos/preview-codigo  (no persiste)
# ════════════════════════════════════════════════════════════════

@router.get("/preview-codigo", response_model=PreviewCodigoResponse, summary="Preview del codigo sin persistir")
async def preview_codigo(
    request: Request,
    tipo_id: int = Query(..., gt=0, description="ID del tipo_documento"),
    area_id: int = Query(..., gt=0, description="ID del area"),
    tipo_solicitud: str = Query("CREACION", pattern=r"^(CREACION|ACTUALIZACION)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Calcula el codigo que se ASIGNARIA al siguiente documento de (area, tipo).
    NO persiste nada. Usado por el campo 'Codigo (automatico)' del wizard.

    Logica:
    - CREACION: version = "00", correlativo = MAX + 1 dentro de (area, tipo)
    - ACTUALIZACION: correlativo = uno existente, version = MAX(version) + 1
      (si no hay docs previos en (area, tipo), version = "00" como fallback)
    """
    await require_authenticated(request, db)

    # 1. Validar que tipo y area existan
    tipo = await db.get(TipoDocumento, tipo_id)
    if not tipo or not tipo.activo:
        raise HTTPException(status_code=404, detail=f"Tipo de documento {tipo_id} no existe o no esta activo")

    area = await db.get(Area, area_id)
    if not area or not area.activo:
        raise HTTPException(status_code=404, detail=f"Area {area_id} no existe o no esta activa")

    # 2. Calcular correlativo
    #    Para CREACION: nuevo correlativo (MAX + 1)
    #    Para ACTUALIZACION: usamos el ultimo existente + 1 version
    if tipo_solicitud == "CREACION":
        # Necesitamos un lock para que el preview sea consistente.
        # Como NO vamos a persistir, usamos el read-only (sin lock) — es
        # solo informativo para el usuario.
        result = await db.execute(
            select(func.coalesce(func.max(Documento.correlativo), 0))
            .where(Documento.area_id == area_id)
            .where(Documento.tipo_documento_id == tipo_id)
            .where(Documento.activo == True)
        )
        max_corr = result.scalar_one() or 0
        correlativo_sugerido = max_corr + 1
        version = "00"
    else:
        # ACTUALIZACION: el usuario quiere actualizar un documento EXISTENTE.
        # Como Fase 1 no tiene UI para elegir cual, devolvemos el ultimo + version nueva.
        result = await db.execute(
            select(Documento.correlativo, Documento.version)
            .where(Documento.area_id == area_id)
            .where(Documento.tipo_documento_id == tipo_id)
            .where(Documento.activo == True)
            .order_by(Documento.correlativo.desc(), Documento.version.desc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            # No hay docs previos de este (area, tipo) → fallback a CREACION v00
            correlativo_sugerido = 1
            version = "00"
        else:
            correlativo_sugerido = row[0]
            # Incrementar version (con zero-pad a 2 digitos)
            try:
                nueva_v = int(row[1]) + 1
                version = f"{nueva_v:02d}"
            except (ValueError, TypeError):
                version = "01"

    codigo = formatear_codigo(area.sigla, tipo.codigo, correlativo_sugerido)
    codigo_completo = formatear_codigo_completo(codigo, version)

    return PreviewCodigoResponse(
        codigo=codigo,
        codigo_completo=codigo_completo,
        version=version,
        correlativo_sugerido=correlativo_sugerido,
        area_sigla=area.sigla,
        tipo_codigo=tipo.codigo,
    )


# ════════════════════════════════════════════════════════════════
#  GET /documentos/{id}  (detalle completo)
# ════════════════════════════════════════════════════════════════

@router.get("/{documento_id}", response_model=DocumentoOut, summary="Detalle de un documento")
async def get_documento(
    request: Request,
    documento_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el documento con todos los joins (gerencia, area, tipo, flujos)."""
    await require_authenticated(request, db)

    stmt = (
        select(Documento)
        .where(Documento.id == documento_id)
        .options(
            selectinload(Documento.gerencia),
            selectinload(Documento.area),
            selectinload(Documento.tipo_documento),
            selectinload(Documento.flujos),
        )
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail=f"Documento {documento_id} no encontrado")

    return DocumentoOut(
        id=doc.id,
        gerencia=DocumentoGerenciaRef(
            id=doc.gerencia.id, sigla=doc.gerencia.sigla, nombre=doc.gerencia.nombre,
        ),
        area=DocumentoAreaRef(
            id=doc.area.id, sigla=doc.area.sigla, nombre=doc.area.nombre,
            gerencia_id=doc.area.gerencia_id,
        ),
        proceso_id=doc.proceso_id,
        tipo=DocumentoTipoRef(
            id=doc.tipo_documento.id,
            codigo=doc.tipo_documento.codigo,
            slug=doc.tipo_documento.slug,
            nombre=doc.tipo_documento.nombre,
            periodo_vigencia=doc.tipo_documento.periodo_vigencia,
            indefinido=doc.tipo_documento.indefinido,
            max_descargas_dia=doc.tipo_documento.max_descargas_dia,
        ),
        correlativo=doc.correlativo,
        codigo=doc.codigo,
        codigo_completo=doc.codigo_completo,
        version=doc.version,
        titulo=doc.titulo,
        aprobacion_at=doc.aprobacion_at,
        expira_at=doc.expira_at,
        vigencia=doc.vigencia.value if hasattr(doc.vigencia, "value") else str(doc.vigencia),
        estatus=doc.estatus.value if hasattr(doc.estatus, "value") else str(doc.estatus),
        codigo_antiguo=doc.codigo_antiguo,
        comentarios_eto=doc.comentarios_eto,
        activo=doc.activo,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        flujos=[
            DocumentoFlujoBasico(
                id=f.id,
                tipo_solicitud=f.tipo_solicitud.value if hasattr(f.tipo_solicitud, "value") else str(f.tipo_solicitud),
                fecha_solicitud=f.fecha_solicitud,
                estado_actual_id=f.estado_actual_id,
                elaborador_id=f.elaborador_id,
            )
            for f in (doc.flujos or [])
        ],
    )


# ════════════════════════════════════════════════════════════════
#  GET /documentos  (lista paginada con filtros)
# ════════════════════════════════════════════════════════════════

@router.get("", response_model=DocumentoListResponse, summary="Lista paginada de documentos")
async def list_documentos(
    request: Request,
    gerencia_id: Optional[int] = Query(None, gt=0),
    area_id: Optional[int] = Query(None, gt=0),
    tipo_documento_id: Optional[int] = Query(None, gt=0),
    vigencia: Optional[str] = Query(None, description="VIGENTE | POR_VENCER | VENCIDO | OBSOLETO"),
    estatus: Optional[str] = Query(None, description="EN_ELABORACION | EN_REVISION | APROBADO | OBSOLETO"),
    activo: Optional[bool] = Query(True, description="Filtrar por borrado logico (default: solo activos)"),
    q: Optional[str] = Query(None, description="Busqueda libre en codigo o titulo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista documentos con filtros y paginacion. Usado por ListaMaestra y bandejas."""
    await require_authenticated(request, db)

    # ─── Validar enums si se proporcionaron ───
    if vigencia is not None:
        try:
            VigenciaDocumento(vigencia)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"vigencia invalida. Valores: {[v.value for v in VigenciaDocumento]}",
            )
    if estatus is not None:
        try:
            EstatusDocumento(estatus)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"estatus invalido. Valores: {[e.value for e in EstatusDocumento]}",
            )

    # ─── Construir WHERE ───
    conditions = []
    if gerencia_id is not None:
        conditions.append(Documento.gerencia_id == gerencia_id)
    if area_id is not None:
        conditions.append(Documento.area_id == area_id)
    if tipo_documento_id is not None:
        conditions.append(Documento.tipo_documento_id == tipo_documento_id)
    if vigencia is not None:
        conditions.append(Documento.vigencia == VigenciaDocumento(vigencia))
    if estatus is not None:
        conditions.append(Documento.estatus == EstatusDocumento(estatus))
    if activo is not None:
        conditions.append(Documento.activo == activo)
    if q:
        like = f"%{q.strip()}%"
        conditions.append(
            or_(
                Documento.codigo.ilike(like),
                Documento.titulo.ilike(like),
            )
        )

    # ─── Count total ───
    count_stmt = select(func.count(Documento.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = (await db.execute(count_stmt)).scalar_one() or 0

    # ─── List page ───
    stmt = (
        select(
            Documento.id,
            Documento.codigo,
            Documento.version,
            Documento.titulo,
            TipoDocumento.codigo.label("tipo_codigo"),
            TipoDocumento.nombre.label("tipo_nombre"),
            Gerencia.sigla.label("gerencia_sigla"),
            Area.sigla.label("area_sigla"),
            Documento.vigencia,
            Documento.estatus,
            Documento.aprobacion_at,
            Documento.expira_at,
            Documento.activo,
        )
        .join(TipoDocumento, TipoDocumento.id == Documento.tipo_documento_id)
        .join(Area, Area.id == Documento.area_id)
        .join(Gerencia, Gerencia.id == Documento.gerencia_id)
        .order_by(Documento.codigo.asc(), Documento.version.asc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))

    result = await db.execute(stmt)
    rows = result.all()

    items = [
        DocumentoListItem(
            id=r.id,
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
            aprobacion_at=r.aprobacion_at,
            expira_at=r.expira_at,
            activo=r.activo,
        )
        for r in rows
    ]

    return DocumentoListResponse(
        total=total, page=page, page_size=page_size, items=items,
    )
