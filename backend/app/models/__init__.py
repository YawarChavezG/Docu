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
    usuario_modulos,
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
    "usuario_modulos",
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
]
