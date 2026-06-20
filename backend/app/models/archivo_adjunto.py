"""
Modelo: ArchivoAdjunto
Archivos subidos al SGD como parte de un Documento.

En Fase 1 (R2 sesion 21) el endpoint /archivos solo persiste el path
ficticio (storage stub). En R3 se reemplaza con upload real a
LocalStorage o SharePointStorage.
"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String, DateTime, Boolean, Integer, ForeignKey, Enum as SAEnum, func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento import Documento
    from app.models.usuario import Usuario


class TipoAdjunto(str, enum.Enum):
    """Clasificacion del archivo adjunto al documento."""
    PRINCIPAL = "PRINCIPAL"   # Documento principal (.docx, max 1)
    FORMULARIO = "FORMULARIO"  # Formularios/anexos (multiples, hasta max_archivos_por_solicitud)


class StorageBackend(str, enum.Enum):
    """Backend de storage donde vive el archivo."""
    LOCAL = "LOCAL"          # DES: /app/storage/uploads/{uuid}.{ext}
    SHAREPOINT = "SHAREPOINT"  # QAS/PROD: Microsoft Graph API


class ArchivoAdjunto(Base):
    """
    Archivo fisico (o referencia a el) asociado a un Documento.
    Pertenece al Documento directamente (no al flujo) para que las
    versiones del mismo documento compartan archivos si corresponde.
    """
    __tablename__ = "archivos_adjuntos"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Metadata del archivo ───
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    # Nombre interno (UUID + extension) para evitar colisiones y path traversal.
    nombre_storage: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # ─── Clasificacion ───
    tipo_adjunto: Mapped[TipoAdjunto] = mapped_column(
        SAEnum(TipoAdjunto, name="tipo_adjunto",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=TipoAdjunto.FORMULARIO,
    )
    storage_backend: Mapped[StorageBackend] = mapped_column(
        SAEnum(StorageBackend, name="storage_backend_adjunto",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=StorageBackend.LOCAL,
    )
    # Ruta interna del archivo. Para LOCAL: /app/storage/uploads/{uuid}.{ext}.
    # Para SHAREPOINT: Graph API driveItem ID o path.
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # ─── Auditoria ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ─── Relaciones ───
    documento: Mapped["Documento"] = relationship(
        "Documento", back_populates="archivos",
    )
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario")

    # ─── Indices ───
    __table_args__ = (
        Index("ix_archivo_documento_tipo", "documento_id", "tipo_adjunto"),
    )

    def __repr__(self) -> str:
        return (
            f"<ArchivoAdjunto id={self.id} nombre={self.nombre_original!r} "
            f"tipo={self.tipo_adjunto.value} {self.tamano_bytes}B>"
        )
