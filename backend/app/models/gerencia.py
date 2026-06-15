"""
Modelo: Gerencia
Catálogo de las 8-10 gerencias de 1er nivel de COFAR.
Datos del Excel GERENCIAS, AREAS Y SIGLAS + ASIGNACION AUTOMATICA ANALISTAS ETO.
"""
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Gerencia(Base):
    __tablename__ = "gerencias"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Sigla corta (ej: "CAL", "PLA", "RRH")
    sigla: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)

    # Nombre completo (ej: "CALIDAD", "PLANTA", "RECURSOS HUMANOS")
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    # Si está activa (borrado lógico)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Orden para mostrar en UI
    orden: Mapped[int] = mapped_column(default=0, nullable=False)

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

    # Relación: una gerencia tiene muchas áreas
    areas: Mapped[list["Area"]] = relationship(  # noqa: F821
        "Area",
        back_populates="gerencia",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Gerencia {self.sigla}>"
