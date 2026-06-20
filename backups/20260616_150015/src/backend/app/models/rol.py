"""
Modelo: Rol
Catálogo de los 5 roles del sistema (definidos en USUARIOS EXISTENTES A ABRIL).
"""
import enum
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodigoRol(str, enum.Enum):
    """Códigos exactos de los 5 roles que existen en COFAR (sesión 2)."""
    ADMIN = "ADMIN"
    ETO = "ETO"
    ELABORADOR_REVISOR = "ELABORADOR - REVISOR"
    ELABORADOR_REVISOR_APROBADOR = "ELABORADOR - REVISOR - APROBADOR"
    VISUALIZADOR_CL_EVAL = "VISUALIZADOR (CL-EVAL)"


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Código exacto del rol (ver CodigoRol enum)
    codigo: Mapped[str] = mapped_column(
        SAEnum(CodigoRol, name="codigo_rol", values_callable=lambda x: [e.value for e in x]),
        unique=True,
        nullable=False,
    )

    # Etiqueta legible en UI (en español)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    # Descripción del rol
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Si requiere delegado obligatorio
    requiere_delegado: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Auditoría
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
        return f"<Rol {self.codigo}>"
