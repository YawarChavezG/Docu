"""
Modelo: Estado
Catalogo de estados de proceso y tarea (US-9.03 sub-tarjeta 2).

Cada estado aplica a un 'contexto':
  - PROCESO: ciclo de vida del documento completo (Elaboracion -> Liberacion -> Revision -> Finalizado)
  - TAREA: estado de una tarea individual dentro del workflow
  - ACCION: accion disparada por el sistema o el usuario
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Integer, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContextoEstado(str, enum.Enum):
    PROCESO = "PROCESO"
    TAREA = "TAREA"
    ACCION = "ACCION"


class Estado(Base):
    __tablename__ = "estados"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    contexto: Mapped[ContextoEstado] = mapped_column(
        SAEnum(ContextoEstado, name="contexto_estado",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ContextoEstado.TAREA,
    )
    orden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
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
        return f"<Estado {self.codigo} ({self.contexto.value})>"
