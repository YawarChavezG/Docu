"""
Modelo: Area
Sub-unidades dentro de una gerencia. 25+ áreas con sigla única.
Datos del Excel GERENCIAS, AREAS Y SIGLAS.
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.gerencia import Gerencia
    from app.models.usuario import Usuario


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True)

    gerencia_id: Mapped[int] = mapped_column(
        ForeignKey("gerencias.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Sigla del area (ej: "CC", "DT", "PRO").
    # UNIQUE(gerencia_id, sigla): la sigla es unica DENTRO de cada gerencia, no global.
    # Antes (Sesion 5) era UNIQUE global, lo que impedia "revivir" un area con la
    # misma sigla despues de borrado logico si la sigla ya existia en otra gerencia.
    # Fix B1 (Sesion 6).
    sigla: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Nombre completo
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    # Si está activa (borrado lógico)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Si requiere un jefe_id (futuro - para fallback chain de reasignación)
    # NOTA: NO lleva ForeignKey porque crea un ciclo con usuarios.area_id -> areas.id
    # que SQLAlchemy no puede ordenar en SQLite (tests). Cuando se implemente la
    # funcionalidad, agregar FK con use_alter=True en el constraint.
    jefe_id: Mapped[int | None] = mapped_column(nullable=True)

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

    # Relaciones
    gerencia: Mapped["Gerencia"] = relationship("Gerencia", back_populates="areas")
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="area", foreign_keys="Usuario.area_id"
    )

    __table_args__ = (
        UniqueConstraint("gerencia_id", "sigla", name="uq_areas_gerencia_sigla"),
    )

    def __repr__(self) -> str:
        return f"<Area {self.sigla} - {self.nombre}>"
