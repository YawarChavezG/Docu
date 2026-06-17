"""
Modelo: EmailTemplate
Plantillas de notificacion por email (US-9.04).

El backend usa jinja2 para renderizar asunto y cuerpo_html con las
variables indicadas en `variables_json`. La UI muestra las variables
disponibles (panel "Etiquetas Disponibles" del US-9.04).

Catalogo cerrado: 10 plantillas (sesion 13 - basadas en
docs/PR/PLANTILLAS DE NOTIFICACION.md):
   1. ASIGNACION DE REVISION
   2. ASIGNACION DE APROBACION
   3. SOLICITUD DE CORRECCION
   4. CONTROL DE LECTURA ASIGNADO
   5. EVALUACION ASIGNADA
   6. LIBERACION DE DOCUMENTO
   7. DOCUMENTO APROBADO
   8. REASIGNACION POR INCUMPLIMIENTO
   9. REASIGNACION MANUAL
  10. TAREA PROXIMA A VENCER (sustituye a ALERTA_VENCIMIENTO + cron diario)
  +  AUTO DELEGACION (mantenido del PDF original)

No se pueden crear plantillas nuevas desde la UI; solo editar las existentes.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Text, JSON, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodigoPlantilla(str, enum.Enum):
    """Codigos exactos de las 10 plantillas (sesion 13)."""
    # Nuevas del documento PLANTILLAS DE NOTIFICACION.md
    ASIG_REVISION = "ASIG_REVISION"             # 1
    ASIG_APROBACION = "ASIG_APROBACION"         # 2
    SOLICITUD_CORRECCION = "SOLICITUD_CORRECCION"  # 3
    CONTROL_LECTURA = "CONTROL_LECTURA"         # 4
    EVALUACION_ASIGNADA = "EVALUACION_ASIGNADA"  # 5
    LIBERACION_DOCUMENTO = "LIBERACION_DOCUMENTO"  # 6
    DOCUMENTO_APROBADO = "DOCUMENTO_APROBADO"   # 7
    REASIG_INCUMPLIMIENTO = "REASIG_INCUMPLIMIENTO"  # 8
    REASIG_MANUAL = "REASIG_MANUAL"             # 9
    TAREA_PROXIMA_VENCER = "TAREA_PROXIMA_VENCER"  # 10
    # Mantenida del PDF original
    AUTO_DELEGACION_ACTIVADA = "AUTO_DELEGACION_ACTIVADA"


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[CodigoPlantilla] = mapped_column(
        SAEnum(CodigoPlantilla, name="codigo_plantilla",
               values_callable=lambda x: [e.value for e in x]),
        unique=True, nullable=False, index=True,
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    asunto: Mapped[str] = mapped_column(String(500), nullable=False)
    cuerpo_html: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EmailTemplate {self.codigo.value}>"
