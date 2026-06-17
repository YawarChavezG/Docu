"""
schemas/documento.py — Schemas Pydantic v2 para Documento, DocumentoFlujo y ArchivoAdjunto.

Sesion 21 (R2 - Fase 1). Solo schemas de LECTURA en esta fase.
Los schemas de CREACION/EDICION (DocumentoCreate, DocumentoUpdate, ArchivoUpload)
se agregan en Fase 2 (sesion 22) cuando se implemente el wizard POST.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


# ─── Enums (re-exportados para que Pydantic los pueda usar) ───

# Los enums reales viven en los modelos. Pydantic v2 los acepta directamente.


# ════════════════════════════════════════════════════════════════
#  Documento (CORE)
# ════════════════════════════════════════════════════════════════


class DocumentoTipoRef(BaseModel):
    """Subset de TipoDocumento para no exponer el modelo completo."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    slug: str
    nombre: str
    periodo_vigencia: Optional[int] = None
    indefinido: bool = False
    max_descargas_dia: Optional[int] = None


class DocumentoGerenciaRef(BaseModel):
    """Subset de Gerencia para inclusion en respuestas."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sigla: str
    nombre: str


class DocumentoAreaRef(BaseModel):
    """Subset de Area para inclusion en respuestas."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sigla: str
    nombre: str
    gerencia_id: int


# ─── Output basico (autocomplete) ───

class DocumentoBuscarItem(BaseModel):
    """Item del endpoint /documentos/buscar (autocomplete)."""
    id: int
    codigo: str              # "CC-3-005" (sin version)
    codigo_completo: str     # "CC-3-005/00" (con version)
    version: str
    titulo: str
    tipo: DocumentoTipoRef
    area: DocumentoAreaRef
    gerencia: DocumentoGerenciaRef
    vigencia: str            # "VIGENTE" | "POR_VENCER" | "VENCIDO" | "OBSOLETO"
    estatus: str             # "EN_ELABORACION" | "EN_REVISION" | "APROBADO" | "OBSOLETO"


class DocumentoBuscarResponse(BaseModel):
    """Respuesta del endpoint de busqueda/autocomplete."""
    total: int
    items: List[DocumentoBuscarItem]


# ─── Output completo ───

class DocumentoFlujoBasico(BaseModel):
    """Subset de DocumentoFlujo para inclusion en DocumentoOut."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_solicitud: str
    fecha_solicitud: datetime
    estado_actual_id: int
    elaborador_id: Optional[int] = None


class DocumentoOut(BaseModel):
    """Detalle completo de un documento, con joins a tablas relacionadas."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    gerencia: DocumentoGerenciaRef
    area: DocumentoAreaRef
    proceso_id: Optional[int] = None
    tipo: DocumentoTipoRef
    correlativo: int
    codigo: str
    codigo_completo: str
    version: str
    titulo: str
    aprobacion_at: Optional[datetime] = None
    expira_at: Optional[datetime] = None
    vigencia: str
    estatus: str
    codigo_antiguo: Optional[str] = None
    comentarios_eto: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
    flujos: List[DocumentoFlujoBasico] = []


# ─── List paginado ───

class DocumentoListItem(BaseModel):
    """Item de la lista paginada de documentos (sin joins pesados)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    codigo_completo: str
    version: str
    titulo: str
    tipo_codigo: int
    tipo_nombre: str
    gerencia_sigla: str
    area_sigla: str
    vigencia: str
    estatus: str
    aprobacion_at: Optional[datetime] = None
    expira_at: Optional[datetime] = None
    activo: bool


class DocumentoListResponse(BaseModel):
    """Respuesta paginada de /documentos con filtros."""
    total: int
    page: int
    page_size: int
    items: List[DocumentoListItem]


# ─── Preview codigo (sin persistir) ───

class PreviewCodigoRequest(BaseModel):
    """Body del endpoint /documentos/preview-codigo."""
    tipo_id: int = Field(..., gt=0, description="ID del tipo_documento (tipos_documento.id)")
    area_id: int = Field(..., gt=0, description="ID del area (areas.id)")
    tipo_solicitud: str = Field(
        default="CREACION",
        pattern=r"^(CREACION|ACTUALIZACION)$",
        description="CREACION o ACTUALIZACION",
    )


class PreviewCodigoResponse(BaseModel):
    """Respuesta del endpoint /documentos/preview-codigo."""
    codigo: str                # "CC-3-005" (sin version)
    codigo_completo: str       # "CC-3-005/00" (con version para CREACION)
    version: str               # "00" para CREACION, "01"+"NN" para ACTUALIZACION
    correlativo_sugerido: int  # siguiente correlativo disponible
    area_sigla: str            # "CC" — para debugging del front
    tipo_codigo: int           # 3 — para debugging del front


# ════════════════════════════════════════════════════════════════
#  Input schemas (POST / PATCH) — Sesion 22 R2 FASE 2
# ════════════════════════════════════════════════════════════════

class DocumentoCreate(BaseModel):
    """Body para POST /documentos. Crea el Documento + DocumentoFlujo inicial."""
    gerencia_id: int = Field(..., gt=0, description="ID de la gerencia responsable")
    area_id: int = Field(..., gt=0, description="ID del area responsable")
    tipo_documento_id: int = Field(..., gt=0, description="ID del tipo de documento")
    titulo: str = Field(..., min_length=3, max_length=200, description="Titulo del documento")
    codigo_antiguo: Optional[str] = Field(None, max_length=50, description="Codigo del sistema legacy")
    comentarios_eto: Optional[str] = Field(None, max_length=50, description="Comentarios para ETO (max 50 chars)")
    tipo_solicitud: str = Field(
        default="CREACION",
        pattern=r"^(CREACION|ACTUALIZACION)$",
        description="CREACION o ACTUALIZACION",
    )
    # Para ACTUALIZACION: id del documento a actualizar (correlativo destino)
    documento_anterior_id: Optional[int] = Field(None, gt=0)


class DocumentoUpdate(BaseModel):
    """Body para PATCH /documentos/{id}. Solo permite editar campos no-firma."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    codigo_antiguo: Optional[str] = Field(None, max_length=50)
    comentarios_eto: Optional[str] = Field(None, max_length=50)
    # Cambiar estatus solo lo pueden hacer ETO/ADMIN. Se valida en el endpoint.
    estatus: Optional[str] = Field(
        None,
        pattern=r"^(EN_ELABORACION|EN_REVISION|APROBADO|OBSOLETO)$",
    )


class DocumentoCreateResponse(BaseModel):
    """Respuesta del POST /documentos. Devuelve el doc creado + el flujo inicial."""
    documento: DocumentoOut
    flujo_id: int
    message: str = "Documento creado exitosamente"


class EnviarRequest(BaseModel):
    """Body para POST /documentos/{id}/enviar (firma 2FA + transicion a EN_REVISION)."""
    password: str = Field(..., min_length=1, description="Password del usuario para 2FA")
    # Snapshot del wizard paso 3 (se persisten en documento_flujo)
    revisor_ids: list[int] = Field(..., min_length=1, description="Minimo 1 revisor")
    aprobador_ids: list[int] = Field(..., min_length=1, description="Minimo 1 aprobador")
    requiere_evaluacion: bool = False
    requiere_control_lectura: bool = False
    alcance_difusion_ids: list[int] = Field(default_factory=list)
    reemplaza_documento_ids: Optional[list[int]] = None
    justificacion: Optional[str] = Field(None, max_length=1000)


class EnviarResponse(BaseModel):
    """Respuesta del POST /documentos/{id}/enviar."""
    ok: bool
    documento_id: int
    flujo_id: int
    estatus: str
    message: str = "Solicitud enviada a liberacion"


# ════════════════════════════════════════════════════════════════
#  Archivo adjunto (output) — Sesion 22 R2 FASE 2
# ════════════════════════════════════════════════════════════════

class ArchivoAdjuntoOut(BaseModel):
    """Respuesta de POST /documentos/{id}/archivos."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    documento_id: int
    nombre_original: str
    nombre_storage: str
    mime_type: str
    tamano_bytes: int
    tipo_adjunto: str
    storage_backend: str
    storage_path: str
    created_at: datetime


class ArchivoUploadResponse(BaseModel):
    """Respuesta del upload con metadata completa."""
    archivo: ArchivoAdjuntoOut
    message: str = "Archivo subido exitosamente"
