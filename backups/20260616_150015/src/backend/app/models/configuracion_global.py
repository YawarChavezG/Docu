"""
Modelo: ConfiguracionGlobal
Catalogo clave-valor de parametros globales del sistema (US-9.01 + 9.02).

Cubre:
  - VIGENCIA: tiempo_vigencia_anios, plazo_revision_aprobacion_dias,
              espera_auto_delegacion_dias, plazo_control_lectura_dias
  - SEMAFORO: semaforo_verde_dias, semaforo_amarillo_dias
  - ARCHIVOS: max_archivos_por_solicitud, max_tamano_archivo_mb
  - DESCARGAS: max_descargas_editables_dia, paginacion_mi_bandeja,
               tipos_excluidos_limite_descarga
  - GENERAL: cualquier param futuro
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Enum as SAEnum, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TipoConfiguracion(str, enum.Enum):
    """Tipo del valor almacenado (para parsing coherente en el cliente)."""
    INT = "INT"
    FLOAT = "FLOAT"
    BOOL = "BOOL"
    STR = "STR"
    JSON = "JSON"  # listas/objets serializados como JSON


class CategoriaConfiguracion(str, enum.Enum):
    """Agrupa parametros en la UI (tabs US-9.01 + 9.02)."""
    VIGENCIA = "VIGENCIA"
    FLUJO = "FLUJO"
    SEMAFORO = "SEMAFORO"
    ARCHIVOS = "ARCHIVOS"
    DESCARGAS = "DESCARGAS"
    GENERAL = "GENERAL"


class ConfiguracionGlobal(Base):
    __tablename__ = "configuracion_global"

    # Clave como PK (snatural key, legible)
    clave: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Valor siempre como texto. El cliente parsea segun `tipo`.
    valor: Mapped[str] = mapped_column(Text, nullable=False)

    tipo: Mapped[TipoConfiguracion] = mapped_column(
        SAEnum(TipoConfiguracion, name="tipo_configuracion",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    categoria: Mapped[CategoriaConfiguracion] = mapped_column(
        SAEnum(CategoriaConfiguracion, name="categoria_configuracion",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    descripcion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Auditoria
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ConfiguracionGlobal {self.clave}={self.valor!r}>"
