"""
Modelo: Modulo
Catálogo de los 10 módulos del sistema (USUARIOS EXISTENTES A ABRIL columna
"MODULOS HABILITADOS"). Se asignan por usuario (N:M).
"""
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodigoModulo(str, enum.Enum):
    """Códigos de los 10 módulos del sistema."""
    BANDEJA_TAREAS = "BANDEJA_TAREAS"
    MI_BANDEJA = "MI_BANDEJA"
    LISTA_MAESTRA = "LISTA_MAESTRA"
    CONSULTAR_DOCUMENTOS = "CONSULTAR_DOCUMENTOS"
    MIS_EVALUACIONES = "MIS_EVALUACIONES"
    ASISTENTE_IA = "ASISTENTE_IA"
    NUEVA_SOLICITUD = "NUEVA_SOLICITUD"
    PLANTILLAS_DOCUMENTALES = "PLANTILLAS_DOCUMENTALES"
    PARAMETRIZACION = "PARAMETRIZACION"
    REPORTES = "REPORTES"
    TODOS = "TODOS"  # Bypass: si el usuario tiene este módulo, no se valida por otros


class Modulo(Base):
    __tablename__ = "modulos"

    id: Mapped[int] = mapped_column(primary_key=True)

    codigo: Mapped[str] = mapped_column(
        SAEnum(CodigoModulo, name="codigo_modulo", values_callable=lambda x: [e.value for e in x]),
        unique=True,
        nullable=False,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ruta_ui: Mapped[str | None] = mapped_column(String(200), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    orden: Mapped[int] = mapped_column(default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Modulo {self.codigo}>"
