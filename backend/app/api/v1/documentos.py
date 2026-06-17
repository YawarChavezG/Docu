"""
API v1: Documentos (CORE del SGD)
Sesion 21 R2 - Fase 1: endpoints de LECTURA.
Sesion 22 R2 - Fase 2: agrega POST, PATCH, /archivos, /enviar.

Endpoints (todos requieren autenticacion):
  GET  /api/v1/documentos/buscar?q=texto
  GET  /api/v1/documentos/preview-codigo?tipo_id=X&area_id=Y&tipo_solicitud=Z
  GET  /api/v1/documentos/{id}
  GET  /api/v1/documentos?gerencia_id=&area_id=&vigencia=&estatus=&page=
  POST /api/v1/documentos              (Sesion 22)
  PATCH /api/v1/documentos/{id}        (Sesion 22)
  POST /api/v1/documentos/{id}/archivos (Sesion 22)
  POST /api/v1/documentos/{id}/enviar  (Sesion 22, firma 2FA)
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import write_audit
from app.core.database import get_db
from app.core.permissions import require_authenticated, require_eto_or_admin
from app.models.archivo_adjunto import ArchivoAdjunto, StorageBackend as StorageBackendAdjunto, TipoAdjunto
from app.models.area import Area
from app.models.configuracion_global import ConfiguracionGlobal
from app.models.documento import (
    Documento,
    EstatusDocumento,
    VigenciaDocumento,
)
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.estado import Estado
from app.models.gerencia import Gerencia
from app.models.tipo_documento import TipoDocumento
from app.models.usuario import Usuario
from app.schemas.documento import (
    ArchivoAdjuntoOut,
    ArchivoUploadResponse,
    DocumentoAreaRef,
    DocumentoBuscarItem,
    DocumentoBuscarResponse,
    DocumentoCreate,
    DocumentoCreateResponse,
    DocumentoFlujoBasico,
    DocumentoGerenciaRef,
    DocumentoListItem,
    DocumentoListResponse,
    DocumentoOut,
    DocumentoTipoRef,
    DocumentoUpdate,
    EnviarRequest,
    EnviarResponse,
    PreviewCodigoRequest,
    PreviewCodigoResponse,
)
from app.services.correlativo_service import (
    formatear_codigo,
    formatear_codigo_completo,
    siguiente_correlativo_advisory,
)
from app.services.envio_service import enviar_a_liberacion
from app.services.storage import get_storage

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


# ════════════════════════════════════════════════════════════════
#  POST /documentos  (crea documento + flujo inicial)
#  Sesion 22 R2 - FASE 2
# ════════════════════════════════════════════════════════════════

@router.post("", response_model=DocumentoCreateResponse, status_code=201,
             summary="Crea un nuevo documento + su flujo inicial")
async def crear_documento(
    body: DocumentoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un Documento (estatus=EN_ELABORACION) y su DocumentoFlujo
    inicial (estado_actual_id=1 = ELABORACION).

    Auth: cualquier usuario autenticado EXCEPTO VISUALIZADOR.
    Genera el correlativo de forma atomica via advisory lock.
    """
    user = await require_authenticated(request, db)

    # RBAC: VISUALIZADOR no puede crear
    from app.models.rol import CodigoRol
    if user.roles and all(r.codigo == CodigoRol.VISUALIZADOR_CL_EVAL for r in user.roles):
        raise HTTPException(
            status_code=403,
            detail="Los visualizadores no pueden crear documentos.",
        )

    # 1. Validar que gerencia existe
    ger = await db.get(Gerencia, body.gerencia_id)
    if not ger or not ger.activo:
        raise HTTPException(status_code=404, detail=f"Gerencia {body.gerencia_id} no existe o no esta activa")

    # 2. Validar que area existe y pertenece a la gerencia
    area = await db.get(Area, body.area_id)
    if not area or not area.activo:
        raise HTTPException(status_code=404, detail=f"Area {body.area_id} no existe o no esta activa")
    if area.gerencia_id != body.gerencia_id:
        raise HTTPException(
            status_code=422,
            detail=f"El area {body.area_id} no pertenece a la gerencia {body.gerencia_id}",
        )

    # 3. Validar que tipo_documento existe y esta activo
    tipo = await db.get(TipoDocumento, body.tipo_documento_id)
    if not tipo or not tipo.activo:
        raise HTTPException(
            status_code=404,
            detail=f"Tipo de documento {body.tipo_documento_id} no existe o no esta activo",
        )

    # 4. Validar estado ELABORACION existe
    estado_elab = (await db.execute(
        select(Estado).where(Estado.codigo == "ELABORACION")
    )).scalar_one_or_none()
    if not estado_elab:
        raise HTTPException(status_code=500, detail="Estado ELABORACION no encontrado en catalogo")

    # 5. Calcular correlativo + version (atómico via advisory lock)
    correlativo = await siguiente_correlativo_advisory(db, body.area_id, body.tipo_documento_id)
    codigo = formatear_codigo(area.sigla, tipo.codigo, correlativo)

    if body.tipo_solicitud == "CREACION":
        version = "00"
        documento_anterior_id = None
    else:
        # ACTUALIZACION: si no nos pasan documento_anterior_id, calculamos el ultimo
        if body.documento_anterior_id:
            doc_ant = await db.get(Documento, body.documento_anterior_id)
            if not doc_ant or not doc_ant.activo:
                raise HTTPException(
                    status_code=404,
                    detail=f"Documento anterior {body.documento_anterior_id} no existe o no esta activo",
                )
            if doc_ant.area_id != body.area_id or doc_ant.tipo_documento_id != body.tipo_documento_id:
                raise HTTPException(
                    status_code=422,
                    detail="El documento anterior no corresponde al mismo (area, tipo)",
                )
            try:
                nueva_v = int(doc_ant.version) + 1
                version = f"{nueva_v:02d}"
            except (ValueError, TypeError):
                version = "01"
            # Para ACTUALIZACION reusamos el mismo correlativo
            correlativo = doc_ant.correlativo
            codigo = doc_ant.codigo
            documento_anterior_id = body.documento_anterior_id
        else:
            # Fallback: usar el ultimo de (area, tipo)
            last = (await db.execute(
                select(Documento)
                .where(Documento.area_id == body.area_id)
                .where(Documento.tipo_documento_id == body.tipo_documento_id)
                .where(Documento.activo == True)
                .order_by(Documento.correlativo.desc(), Documento.version.desc())
                .limit(1)
            )).scalar_one_or_none()
            if last is None:
                version = "00"
            else:
                correlativo = last.correlativo
                codigo = last.codigo
                try:
                    version = f"{int(last.version) + 1:02d}"
                except (ValueError, TypeError):
                    version = "01"
                documento_anterior_id = last.id

    # 6. Crear el Documento
    doc = Documento(
        gerencia_id=body.gerencia_id,
        area_id=body.area_id,
        proceso_id=None,
        tipo_documento_id=body.tipo_documento_id,
        correlativo=correlativo,
        codigo=codigo,
        version=version,
        titulo=body.titulo,
        vigencia=VigenciaDocumento.VIGENTE,
        estatus=EstatusDocumento.EN_ELABORACION,
        codigo_antiguo=body.codigo_antiguo,
        comentarios_eto=body.comentarios_eto,
        activo=True,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(doc)
    await db.flush()  # Para obtener doc.id

    # 7. Crear el DocumentoFlujo inicial
    flujo = DocumentoFlujo(
        documento_id=doc.id,
        estado_actual_id=estado_elab.id,
        tipo_solicitud=TipoSolicitud(body.tipo_solicitud),
        gerencia_id=body.gerencia_id,
        area_id=body.area_id,
        tipo_documento_id=body.tipo_documento_id,
        codigo_snapshot=codigo,
        version_snapshot=version,
        titulo=body.titulo,
        elaborador_id=user.id,
        cargo_elaborador=user.cargo,
        fecha_solicitud=datetime.now(timezone.utc),
        requiere_evaluacion=False,
        requiere_control_lectura=False,
        alcance_difusion_ids=[],
        revisor_ids=[],
        aprobador_ids=[],
        firma_usuario_id=user.id,
        firma_at=datetime.now(timezone.utc),
        firma_ip=request.client.host if request.client else None,
        firma_user_agent=(request.headers.get("user-agent", "")[:500] or None),
        activo=True,
        created_by_id=user.id,
    )
    db.add(flujo)
    await db.flush()

    # 8. Audit + commit (atomico: si falla, rollback total)
    await write_audit(
        db, request, user,
        accion="CREATE",
        recurso="documento",
        recurso_id=doc.id,
        descripcion=f"Documento {codigo}/{version} creado (titulo='{body.titulo[:50]}')",
        detalles={
            "codigo_completo": f"{codigo}/{version}",
            "tipo_solicitud": body.tipo_solicitud,
            "documento_anterior_id": documento_anterior_id,
        },
    )
    await db.commit()
    await db.refresh(doc)

    # 9. Recargar con joins para el response
    doc_full = (await db.execute(
        select(Documento)
        .where(Documento.id == doc.id)
        .options(
            selectinload(Documento.gerencia),
            selectinload(Documento.area),
            selectinload(Documento.tipo_documento),
        )
    )).scalar_one()

    return DocumentoCreateResponse(
        documento=DocumentoOut(
            id=doc_full.id,
            gerencia=DocumentoGerenciaRef(id=doc_full.gerencia.id, sigla=doc_full.gerencia.sigla, nombre=doc_full.gerencia.nombre),
            area=DocumentoAreaRef(id=doc_full.area.id, sigla=doc_full.area.sigla, nombre=doc_full.area.nombre, gerencia_id=doc_full.area.gerencia_id),
            proceso_id=doc_full.proceso_id,
            tipo=DocumentoTipoRef(
                id=doc_full.tipo_documento.id, codigo=doc_full.tipo_documento.codigo,
                slug=doc_full.tipo_documento.slug, nombre=doc_full.tipo_documento.nombre,
                periodo_vigencia=doc_full.tipo_documento.periodo_vigencia,
                indefinido=doc_full.tipo_documento.indefinido,
                max_descargas_dia=doc_full.tipo_documento.max_descargas_dia,
            ),
            correlativo=doc_full.correlativo,
            codigo=doc_full.codigo,
            codigo_completo=doc_full.codigo_completo,
            version=doc_full.version,
            titulo=doc_full.titulo,
            aprobacion_at=doc_full.aprobacion_at,
            expira_at=doc_full.expira_at,
            vigencia=doc_full.vigencia.value,
            estatus=doc_full.estatus.value,
            codigo_antiguo=doc_full.codigo_antiguo,
            comentarios_eto=doc_full.comentarios_eto,
            activo=doc_full.activo,
            created_at=doc_full.created_at,
            updated_at=doc_full.updated_at,
            flujos=[],
        ),
        flujo_id=flujo.id,
    )


# ════════════════════════════════════════════════════════════════
#  PATCH /documentos/{id}  (edicion antes de firmar)
#  Sesion 22 R2 - FASE 2
# ════════════════════════════════════════════════════════════════

@router.patch("/{documento_id}", response_model=DocumentoOut,
              summary="Edita campos de un documento en elaboracion")
async def update_documento(
    documento_id: int,
    body: DocumentoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Edita titulo, codigo_antiguo, comentarios_eto o estatus de un documento.
    - Cualquier campo: solo permitido si estatus=EN_ELABORACION y eres el elaborador/ETO/ADMIN.
    - Cambio de estatus: solo ETO/ADMIN pueden.
    """
    user = await require_authenticated(request, db)

    doc = (await db.execute(
        select(Documento)
        .where(Documento.id == documento_id)
        .options(
            selectinload(Documento.gerencia),
            selectinload(Documento.area),
            selectinload(Documento.tipo_documento),
            selectinload(Documento.flujos),
        )
    )).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail=f"Documento {documento_id} no encontrado")

    if not doc.activo:
        raise HTTPException(status_code=409, detail="Documento eliminado (borrado logico)")

    # Solo se puede editar en ELABORACION
    if doc.estatus != EstatusDocumento.EN_ELABORACION:
        raise HTTPException(
            status_code=409,
            detail=f"Solo se pueden editar documentos en EN_ELABORACION (actual: {doc.estatus.value})",
        )

    from app.models.rol import CodigoRol
    is_eto_or_admin = user.roles and any(
        r.codigo in (CodigoRol.ETO, CodigoRol.ADMIN) for r in user.roles
    )

    # Cambio de estatus: solo ETO/ADMIN
    if body.estatus is not None and body.estatus != doc.estatus.value:
        if not is_eto_or_admin:
            raise HTTPException(
                status_code=403,
                detail="Solo ETO o ADMIN pueden cambiar el estatus del documento",
            )
        try:
            doc.estatus = EstatusDocumento(body.estatus)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"estatus invalido: {body.estatus}")

    # Edicion de campos basicos
    cambios = {}
    if body.titulo is not None and body.titulo != doc.titulo:
        cambios["titulo"] = {"old": doc.titulo, "new": body.titulo}
        doc.titulo = body.titulo
    if body.codigo_antiguo is not None and body.codigo_antiguo != doc.codigo_antiguo:
        cambios["codigo_antiguo"] = {"old": doc.codigo_antiguo, "new": body.codigo_antiguo}
        doc.codigo_antiguo = body.codigo_antiguo
    if body.comentarios_eto is not None and body.comentarios_eto != doc.comentarios_eto:
        cambios["comentarios_eto"] = {"old": doc.comentarios_eto, "new": body.comentarios_eto}
        doc.comentarios_eto = body.comentarios_eto

    doc.updated_by_id = user.id
    doc.updated_at = datetime.now(timezone.utc)

    # Audit
    await write_audit(
        db, request, user,
        accion="UPDATE",
        recurso="documento",
        recurso_id=doc.id,
        descripcion=f"Documento {doc.codigo_completo} editado",
        detalles={"cambios": cambios} if cambios else None,
    )
    await db.commit()
    await db.refresh(doc)

    return DocumentoOut(
        id=doc.id,
        gerencia=DocumentoGerenciaRef(id=doc.gerencia.id, sigla=doc.gerencia.sigla, nombre=doc.gerencia.nombre),
        area=DocumentoAreaRef(id=doc.area.id, sigla=doc.area.sigla, nombre=doc.area.nombre, gerencia_id=doc.area.gerencia_id),
        proceso_id=doc.proceso_id,
        tipo=DocumentoTipoRef(
            id=doc.tipo_documento.id, codigo=doc.tipo_documento.codigo,
            slug=doc.tipo_documento.slug, nombre=doc.tipo_documento.nombre,
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
        vigencia=doc.vigencia.value,
        estatus=doc.estatus.value,
        codigo_antiguo=doc.codigo_antiguo,
        comentarios_eto=doc.comentarios_eto,
        activo=doc.activo,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        flujos=[
            DocumentoFlujoBasico(
                id=f.id,
                tipo_solicitud=f.tipo_solicitud.value,
                fecha_solicitud=f.fecha_solicitud,
                estado_actual_id=f.estado_actual_id,
                elaborador_id=f.elaborador_id,
            )
            for f in (doc.flujos or [])
        ],
    )


# ════════════════════════════════════════════════════════════════
#  POST /documentos/{id}/archivos  (upload con validacion MIME/tamano)
#  Sesion 22 R2 - FASE 2
# ════════════════════════════════════════════════════════════════

# Whitelist de MIME types permitidos (alineado con R2-PLAN-EJECUCION.md § 3.3)
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
    "application/msword",  # .doc
    "image/png",
    "image/jpeg",
}


@router.post("/{documento_id}/archivos", response_model=ArchivoUploadResponse,
             status_code=201, summary="Sube un archivo adjunto al documento")
async def upload_archivo(
    documento_id: int,
    request: Request,
    archivo: UploadFile = File(..., description="Archivo a subir"),
    tipo_adjunto: str = Form(default="FORMULARIO"),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube un archivo adjunto al documento. Validaciones:
    - Documento existe y activo
    - count(archivos) <= max_archivos_por_solicitud
    - tamano <= max_tamano_archivo_mb * 1024 * 1024
    - mime_type in whitelist
    """
    user = await require_authenticated(request, db)

    # 1. Validar tipo_adjunto
    try:
        tipo_adjunto_enum = TipoAdjunto(tipo_adjunto)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"tipo_adjunto invalido. Valores: {[t.value for t in TipoAdjunto]}",
        )

    # 2. Validar documento existe y activo
    doc = await db.get(Documento, documento_id)
    if not doc or not doc.activo:
        raise HTTPException(
            status_code=404,
            detail=f"Documento {documento_id} no encontrado o no esta activo",
        )

    # 3. Validar MIME type
    mime = (archivo.content_type or "").lower()
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Tipo MIME no permitido: {mime!r}. "
                f"Permitidos: {sorted(ALLOWED_MIME_TYPES)}"
            ),
        )

    # 4. Leer bytes y validar tamano
    file_bytes = await archivo.read()
    tamano = len(file_bytes)

    # Leer max_tamano_archivo_mb de configuracion_global (default 20MB)
    max_mb_row = (await db.execute(
        select(ConfiguracionGlobal).where(
            ConfiguracionGlobal.clave == "max_tamano_archivo_mb"
        )
    )).scalar_one_or_none()
    max_mb = int(max_mb_row.valor) if max_mb_row and max_mb_row.valor else 20
    max_bytes = max_mb * 1024 * 1024
    if tamano > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo excede el maximo permitido ({max_mb} MB). Tamano: {tamano / 1024 / 1024:.2f} MB",
        )

    # 5. Validar count de archivos <= max_archivos_por_solicitud
    max_count_row = (await db.execute(
        select(ConfiguracionGlobal).where(
            ConfiguracionGlobal.clave == "max_archivos_por_solicitud"
        )
    )).scalar_one_or_none()
    max_count = int(max_count_row.valor) if max_count_row and max_count_row.valor else 20
    current_count = (await db.execute(
        select(func.count(ArchivoAdjunto.id)).where(
            ArchivoAdjunto.documento_id == documento_id,
        )
    )).scalar_one() or 0
    if current_count >= max_count:
        raise HTTPException(
            status_code=409,
            detail=f"Limite de archivos alcanzado ({max_count} por documento)",
        )

    # 6. Persistir via storage backend
    storage = get_storage()
    storage_path = storage.save(file_bytes, archivo.filename or "archivo.bin")

    # Determinar backend usado
    from app.services.storage import LocalStorage, SharePointStorage
    storage_backend_enum = (
        StorageBackendAdjunto.SHAREPOINT
        if isinstance(storage, SharePointStorage)
        else StorageBackendAdjunto.LOCAL
    )

    # 7. Crear ArchivoAdjunto
    adj = ArchivoAdjunto(
        documento_id=documento_id,
        usuario_id=user.id,
        nombre_original=archivo.filename or "archivo.bin",
        nombre_storage=Path(storage_path).name,
        mime_type=mime,
        tamano_bytes=tamano,
        tipo_adjunto=tipo_adjunto_enum,
        storage_backend=storage_backend_enum,
        storage_path=storage_path,
    )
    db.add(adj)
    await db.flush()

    # 8. Audit + commit
    await write_audit(
        db, request, user,
        accion="UPLOAD",
        recurso="archivo_adjunto",
        recurso_id=adj.id,
        descripcion=f"Archivo {adj.nombre_original} ({tamano} bytes) subido al doc {doc.codigo_completo}",
        detalles={
            "documento_id": documento_id,
            "mime_type": mime,
            "tamano_bytes": tamano,
            "tipo_adjunto": tipo_adjunto,
            "storage_backend": storage_backend_enum.value,
        },
    )
    await db.commit()
    await db.refresh(adj)

    return ArchivoUploadResponse(
        archivo=ArchivoAdjuntoOut(
            id=adj.id,
            documento_id=adj.documento_id,
            nombre_original=adj.nombre_original,
            nombre_storage=adj.nombre_storage,
            mime_type=adj.mime_type,
            tamano_bytes=adj.tamano_bytes,
            tipo_adjunto=adj.tipo_adjunto.value,
            storage_backend=adj.storage_backend.value,
            storage_path=adj.storage_path,
            created_at=adj.created_at,
        ),
    )


# ════════════════════════════════════════════════════════════════
#  POST /documentos/{id}/enviar  (FIRMA 2FA atomica)
#  Sesion 22 R2 - FASE 2  ← TAREA MAS CRITICA
# ════════════════════════════════════════════════════════════════

@router.post("/{documento_id}/enviar", response_model=EnviarResponse,
             summary="Firma digital 2FA + envio a liberacion (transicion EN_ELABORACION -> EN_REVISION)")
async def enviar_documento_a_liberacion(
    documento_id: int,
    body: EnviarRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Envia un documento a liberacion.

    Flujo atomico (SESION-22-HANDOFF.md § 5 R1):
    1. Validar password (2FA) -> si falla, 401 y NADA se persiste
    2. Re-leer doc con FOR UPDATE
    3. Validar que esta en EN_ELABORACION -> si no, 409
    4. Actualizar flujo + transicionar documento
    5. write_audit + commit (un solo commit atomico)

    Riesgo: si la BD falla despues de validar el password, se hace
    rollback total (no queda como firmado).
    """
    user = await require_authenticated(request, db)

    doc, flujo = await enviar_a_liberacion(
        db=db,
        request=request,
        user=user,
        documento_id=documento_id,
        password=body.password,
        revisor_ids=body.revisor_ids,
        aprobador_ids=body.aprobador_ids,
        requiere_evaluacion=body.requiere_evaluacion,
        requiere_control_lectura=body.requiere_control_lectura,
        alcance_difusion_ids=body.alcance_difusion_ids,
        reemplaza_documento_ids=body.reemplaza_documento_ids,
        justificacion=body.justificacion,
    )

    return EnviarResponse(
        ok=True,
        documento_id=doc.id,
        flujo_id=flujo.id,
        estatus=doc.estatus.value,
    )
