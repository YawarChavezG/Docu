"""
Modelo: DocumentoAlcanceDifusion
R3 Fase 1 - tabla N:M para el arbol de difusion (US-1.06).

Por que existe (PROPUESTA-R3-TABLAS.md §2.5):
- Reemplaza el JSONB `alcance_difusion_ids` de DocumentoFlujo.
- Cada nodo del arbol de difusion (gerencia o area) es una fila.
- Un registro puede apuntar a una gerencia O a un area (no ambos).
  Esto preserva la estructura: si se selecciona un area especifica,
  la gerencia no se duplica.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime, Integer, ForeignKey, func,
    Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.gerencia import Gerencia
    from app.models.area import Area


class DocumentoAlcanceDifusion(Base):
    """
    Nodo del arbol de difusion del documento. Apunta a una gerencia
    o a un area (no ambos a la vez).
    """
    __tablename__ = "documento_alcance_difusion"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    documento_flujo_id: Mapped[int] = mapped_column(
        ForeignKey("documento_flujo.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Exactamente UNO de los dos: gerencia o area.
    gerencia_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gerencias.id", ondelete="CASCADE"),
        nullable=True,
    )
    area_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("areas.id", ondelete="CASCADE"),
        nullable=True,
    )

    # ─── Auditoria ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ─── Relaciones ───
    documento_flujo: Mapped["DocumentoFlujo"] = relationship("DocumentoFlujo")
    gerencia: Mapped[Optional["Gerencia"]] = relationship("Gerencia")
    area: Mapped[Optional["Area"]] = relationship("Area")

    # ─── Constraints ───
    __table_args__ = (
        # CHECK: al menos uno (gerencia o area) debe ser no NULL.
        # Tambien: NO ambos (pertenecer a area ya implica a su gerencia).
        CheckConstraint(
            "(gerencia_id IS NOT NULL AND area_id IS NULL) OR "
            "(gerencia_id IS NULL AND area_id IS NOT NULL)",
            name="ck_alcance_exactly_one",
        ),
        # ─── Indices ───
        Index("ix_alcance_flujo", "documento_flujo_id"),
    )

    def __repr__(self) -> str:
        target = (
            f"gerencia={self.gerencia_id}" if self.gerencia_id
            else f"area={self.area_id}"
        )
        return (
            f"<DocumentoAlcanceDifusion id={self.id} flujo={self.documento_flujo_id} "
            f"{target}>"
        )
