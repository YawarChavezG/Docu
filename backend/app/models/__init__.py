"""
Modelos SQLAlchemy del SGD COFAR.

Importar este módulo garantiza que todos los modelos están registrados
en `Base.metadata` para que Alembic los detecte.
"""
from app.core.database import Base

# ─── Catálogos ───
from app.models.rol import Rol, CodigoRol  # noqa: F401
from app.models.gerencia import Gerencia  # noqa: F401
from app.models.area import Area  # noqa: F401
from app.models.modulo import Modulo, CodigoModulo  # noqa: F401

# ─── Usuario + asociaciones ───
from app.models.usuario import (  # noqa: F401
    Usuario,
    usuario_roles,
    EstadoUsuario,
    EstadoDelegacion,
)

# ─── Soporte R1 ───
from app.models.delegacion import Delegacion  # noqa: F401
from app.models.ausencia import Ausencia  # noqa: F401
from app.models.firma_digital import FirmaDigital  # noqa: F401
from app.models.log_sync_ad import LogSyncAd, TipoSync, ResultadoSync  # noqa: F401

# ─── Parametrizacion R1 ───
from app.models.configuracion_global import (  # noqa: F401
    ConfiguracionGlobal,
    TipoConfiguracion,
    CategoriaConfiguracion,
)
from app.models.feriado import Feriado, TipoFeriado  # noqa: F401
from app.models.email_template import EmailTemplate, CodigoPlantilla  # noqa: F401
from app.models.matriz_enrutamiento_eto import (  # noqa: F401
    MatrizEnrutamientoEto,
    DisponibilidadEto,
)
from app.models.tipo_documento import TipoDocumento  # noqa: F401
from app.models.estado import Estado, ContextoEstado  # noqa: F401
from app.models.semaforizacion_tarea import SemaforizacionTarea, TipoTarea  # noqa: F401

# ─── Auditoria (EPICA 9) ───
from app.models.audit_log import AuditLog  # noqa: F401

# ─── R2: Documentos y workflow (sesion 21) ───
from app.models.documento import (  # noqa: F401
    Documento,
    VigenciaDocumento,
    EstatusDocumento,
)
from app.models.documento_flujo import (  # noqa: F401
    DocumentoFlujo,
    TipoSolicitud,
)
from app.models.archivo_adjunto import (  # noqa: F401
    ArchivoAdjunto,
    TipoAdjunto,
    StorageBackend,
)
from app.models.documento_formulario import (  # noqa: F401
    DocumentoFormulario,
)
from app.models.plantilla import Plantilla  # noqa: F401

# ─── R3 Fase 1: Workflow de revision y aprobacion (sesion 37) ───
# Catalogo: Proceso (PROPUESTA-R3-TABLAS.md §1.5.6).
from app.models.proceso import Proceso  # noqa: F401
# Core: Tarea, BitacoraTimeline, Notificacion.
from app.models.tarea import Tarea  # noqa: F401
from app.models.bitacora_timeline import BitacoraTimeline  # noqa: F401
from app.models.notificacion import Notificacion  # noqa: F401
# Tablas N:M que reemplazan JSONB en documento_flujo.
from app.models.documento_reemplazo import DocumentoReemplazo  # noqa: F401
from app.models.documento_alcance_difusion import DocumentoAlcanceDifusion  # noqa: F401
# Sub-tabla: observaciones por tarea.
from app.models.tarea_observacion import TareaObservacion  # noqa: F401


__all__ = [
    "Base",
    "Rol",
    "CodigoRol",
    "Gerencia",
    "Area",
    "Modulo",
    "CodigoModulo",
    "Usuario",
    "usuario_roles",
    "EstadoUsuario",
    "EstadoDelegacion",
    "Delegacion",
    "Ausencia",
    "FirmaDigital",
    "LogSyncAd",
    "TipoSync",
    "ResultadoSync",
    "ConfiguracionGlobal",
    "TipoConfiguracion",
    "CategoriaConfiguracion",
    "Feriado",
    "TipoFeriado",
    "EmailTemplate",
    "CodigoPlantilla",
    "MatrizEnrutamientoEto",
    "DisponibilidadEto",
    "TipoDocumento",
    "Estado",
    "ContextoEstado",
    "SemaforizacionTarea",
    "TipoTarea",
    "AuditLog",
    "Documento",
    "VigenciaDocumento",
    "EstatusDocumento",
    "DocumentoFlujo",
    "TipoSolicitud",
    "ArchivoAdjunto",
    "TipoAdjunto",
    "StorageBackend",
    "DocumentoFormulario",
    # R3 Fase 1
    "Proceso",
    "Tarea",
    "BitacoraTimeline",
    "Notificacion",
    "DocumentoReemplazo",
    "DocumentoAlcanceDifusion",
    "TareaObservacion",
    "Plantilla",
]
