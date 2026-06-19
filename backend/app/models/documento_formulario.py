"""
Modelo: DocumentoFormulario
R3 item 0.4: codigo de formularios -F01, -F02, etc.

Un documento tiene N formularios con codigo correlativo propio.
A diferencia de archivos_adjuntos (que es generico), esta tabla es
especifica para formularios y guarda su correlativo + codigo completo
usado como nombre del archivo y para busqueda en bandejas.

Segun PROPUESTA-R3-TABLAS.md §1.5.3:

    | Tipo              | Codigo             |
    |-------------------|--------------------|
    | Documento         | CC-6-032           |
    | Formulario 1      | CC-6-032-F01       |
    | Formulario 2      | CC-6-032-F02       |
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String, DateTime, Boolean, Integer, ForeignKey, func,
    Index, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento import Documento
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.usuario import Usuario


class DocumentoFormulario(Base):
    """
    Formulario asociado a un DocumentoFlujo (NO al Documento directamente).

    Por que documento_flujo_id y no documento_id?
    - En una actualizacion, se crea un nuevo flujo. Los formularios
      pertenecen al flujo, no al documento (un mismo documento puede
      tener varios flujos, uno por version, cada uno con sus formularios).
    - Esto permite tambien que en el futuro se pueda subir formularios
      a un flujo sin afectar a otros flujos del mismo documento.

    El codigo_formulario se calcula como:
        {documento.codigo}-F{correlativo_formulario:02d}
    Ej: "CC-6-032-F01"
    """
    __tablename__ = "documento_formularios"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    documento_flujo_id: Mapped[int] = mapped_column(
        ForeignKey("documento_flujo.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Codigo y correlativo (R3 item 0.4) ───
    # Correlativo 1, 2, 3... dentro del flujo. UNIQUE por flujo.
    correlativo_formulario: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    # Codigo completo calculado: "CC-6-032-F01". UNIQUE global.
    codigo_formulario: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True,
    )

    # ─── Metadata del archivo (mismos campos que archivos_adjuntos) ───
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_storage: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_backend: Mapped[str] = mapped_column(
        String(50), nullable=False, default="LOCAL",
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Auditoria ───
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ─── Relaciones ───
    documento_flujo: Mapped["DocumentoFlujo"] = relationship("DocumentoFlujo")
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario")

    # ─── Indices ───
    __table_args__ = (
        # UNIQUE: un mismo flujo no puede tener 2 formularios con el mismo
        # correlativo. Ya hay un UNIQUE global en codigo_formulario.
        Index("ix_formulario_flujo_corr", "documento_flujo_id", "correlativo_formulario", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentoFormulario id={self.id} {self.codigo_formulario!r} "
            f"flujo={self.documento_flujo_id} {self.tamano_bytes}B>"
        )
