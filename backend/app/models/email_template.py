"""
Modelo: EmailTemplate
Plantillas de notificacion por email (US-9.04).

El backend usa jinja2 para renderizar asunto y cuerpo_html con las
variables indicadas en `variables_json`. La UI muestra las variables
disponibles (panel "Etiquetas Disponibles" del US-9.04).

Catalogo cerrado: 6 plantillas (5 del .docx + 1 del PDF 'auto-delegacion').
No se pueden crear plantillas nuevas desde la UI; solo editar las existentes.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Text, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodigoPlantilla(str, enum.Enum):
    """Codigos exactos de las 6 plantillas (5 .docx + 1 PDF)."""
    NUEVA_TAREA = "NUEVA_TAREA"
    ALERTA_VENCIMIENTO = "ALERTA_VENCIMIENTO"
    DOCUMENTO_APROBADO = "DOCUMENTO_APROBADO"
    DOCUMENTO_OBSERVADO = "DOCUMENTO_OBSERVADO"
    EVALUACION_PENDIENTE = "EVALUACION_PENDIENTE"
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
    variables_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
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
