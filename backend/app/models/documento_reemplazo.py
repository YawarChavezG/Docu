"""
Modelo: DocumentoReemplazo
R3 Fase 1 - tabla N:M para reemplazos documentales (US-1.07, US-5.01).

Por que existe (PROPUESTA-R3-TABLAS.md §2.4):
- Reemplaza el JSONB `reemplaza_documento_ids` de DocumentoFlujo.
- Cada codigo ingresado en el wizard paso 3 es una fila.
- Cuando el documento se publica, un trigger / servicio (Fase 5) cambia
  los documentos viejos a OBSOLETO.
- `codigo_documento_viejo` se guarda como STRING (no ID) porque al
  momento de carga del wizard el doc viejo podria no existir en BD
  (legacy, dado de baja, etc.).
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String, DateTime, Integer, ForeignKey, func,
    Boolean, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.documento import Documento


class DocumentoReemplazo(Base):
    """
    Un codigo de documento a dar de baja cuando se publique el nuevo.
    """
    __tablename__ = "documento_reemplazos"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    # El documento NUEVO que reemplaza (via flujo).
    documento_flujo_id: Mapped[int] = mapped_column(
        ForeignKey("documento_flujo.id", ondelete="CASCADE"),
        nullable=False,
    )
    # El documento VIEJO (si existe en BD). Puede ser NULL si el
    # usuario ingreso un codigo que no existe en BD todavia
    # (migracion legacy, codigo antiguo sin documentar, etc.).
    documento_viejo_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documentos.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Codigo del documento a reemplazar ───
    # String, no FK. Formato: "CC-3-005/01" o "CC-3-005" sin version.
    codigo_documento_viejo: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )

    # ─── Estado del reemplazo ───
    # FALSE hasta que el documento nuevo se publique (US-5.01).
    ejecutado: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    ejecutado_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ─── Auditoria ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ─── Relaciones ───
    documento_flujo: Mapped["DocumentoFlujo"] = relationship("DocumentoFlujo")
    documento_viejo: Mapped[Optional["Documento"]] = relationship(
        "Documento", foreign_keys=[documento_viejo_id],
    )

    # ─── Indices ───
    __table_args__ = (
        # Listar reemplazos del documento nuevo.
        Index("ix_reemplazos_flujo", "documento_flujo_id"),
        # Buscar por codigo (reportes de obsolescencia, etc.).
        Index("ix_reemplazos_codigo", "codigo_documento_viejo"),
        # Trigger: WHERE ejecutado = FALSE AND documento_viejo_id IS NOT NULL.
        Index(
            "ix_reemplazos_pendientes",
            "documento_viejo_id",
            postgresql_where=Boolean("ejecutado = FALSE AND documento_viejo_id IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentoReemplazo id={self.id} flujo={self.documento_flujo_id} "
            f"viejo={self.codigo_documento_viejo!r} ejecutado={self.ejecutado}>"
        )
