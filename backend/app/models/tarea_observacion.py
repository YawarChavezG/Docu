"""
Modelo: TareaObservacion
R3 Fase 1 - observaciones individuales por tarea (US-3.04).

Por que existe (PROPUESTA-R3-TABLAS.md §2.6):
- US-3.04 exige minimo 10 caracteres en la observacion al rechazar.
- US-3.05 exige correccion DIRIGIDA al revisor que observo (bypass
  directo). Esto requiere tracking de QUE tarea (y por tanto QUE
  usuario) genero la observacion.
- `corregida` + `corregida_at` permite saber cuales observaciones
  siguen pendientes de correccion.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime, Integer, ForeignKey, func,
    Text, Index, CheckConstraint, Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tarea import Tarea
    from app.models.usuario import Usuario


class TareaObservacion(Base):
    """
    Observacion generada por un usuario al atender una tarea
    (normalmente al RECHAZAR). US-3.04.
    """
    __tablename__ = "tarea_observaciones"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    tarea_id: Mapped[int] = mapped_column(
        ForeignKey("tareas.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ─── Contenido ───
    # US-3.04: minimo 10 caracteres. El CHECK en BD es defensivo
    # (la validacion principal esta en el schema Pydantic + service).
    observacion: Mapped[str] = mapped_column(Text, nullable=False)

    # ─── Estado de correccion ───
    corregida: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    corregida_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ─── Auditoria ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ─── Relaciones ───
    tarea: Mapped["Tarea"] = relationship("Tarea")
    usuario: Mapped["Usuario"] = relationship("Usuario")

    # ─── Constraints ───
    __table_args__ = (
        # CHECK: minimo 10 caracteres.
        CheckConstraint(
            "length(observacion) >= 10",
            name="ck_observacion_min_10_chars",
        ),
        # ─── Indices ───
        # Observaciones de una tarea.
        Index("ix_obs_tarea", "tarea_id"),
        # Observaciones pendientes de correccion.
        Index(
            "ix_obs_pendientes",
            "tarea_id", "corregida",
            postgresql_where=Boolean("corregida = FALSE"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TareaObservacion id={self.id} tarea={self.tarea_id} "
            f"corregida={self.corregida}>"
        )
