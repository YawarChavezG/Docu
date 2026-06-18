"""
Modelo: DocumentoFlujo
Instancia del wizard de aprobacion documental ligado a un Documento.

Un Documento puede tener N flujos (1 por cada version). El flujo guarda
el SNAPSHOT del contexto al momento de la firma (area, gerencia, tipo, etc.)
para que el documento historico preserve su contexto aunque las tablas
catalogo cambien despues.

Los arrays JSONB (revisor_ids, aprobador_ids, alcance_difusion_ids,
reemplaza_documento_ids) son temporales para R2. En R3 se migraran a
tablas N:M cuando se necesiten bandejas individuales con timestamps
y estados por tarea.
"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    String, DateTime, Boolean, Integer, ForeignKey, Enum as SAEnum, func,
    Text, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.audit_log import JSONType

if TYPE_CHECKING:
    from app.models.documento import Documento
    from app.models.gerencia import Gerencia
    from app.models.area import Area
    from app.models.tipo_documento import TipoDocumento
    from app.models.estado import Estado
    from app.models.usuario import Usuario


# ─── Enums del modelo ───

class TipoSolicitud(str, enum.Enum):
    """Tipo de solicitud que origina este flujo."""
    CREACION = "CREACION"
    ACTUALIZACION = "ACTUALIZACION"


class DocumentoFlujo(Base):
    """
    Instancia del wizard persistida. Contiene TODOS los datos de los
    3 pasos del wizard (/aprobacion-documento) mas la metadata de firma.
    """
    __tablename__ = "documento_flujo"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones snapshot ───
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estado_actual_id: Mapped[int] = mapped_column(
        ForeignKey("estados.id", ondelete="RESTRICT"),
        nullable=False,
        default=1,  # ELABORACION
        index=True,
    )

    # ─── Paso 1: Datos del documento y carga de archivo ───
    tipo_solicitud: Mapped[TipoSolicitud] = mapped_column(
        SAEnum(TipoSolicitud, name="tipo_solicitud",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    # Snapshots organizacionales (no se actualizan si el area se renombra).
    gerencia_id: Mapped[int] = mapped_column(
        ForeignKey("gerencias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    area_id: Mapped[int] = mapped_column(
        ForeignKey("areas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tipo_documento_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_documento.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Codigo generado al crear el flujo (sin version): "CC-3-005".
    codigo_snapshot: Mapped[str] = mapped_column(String(20), nullable=False)
    # Version al crear el flujo: "00" para creacion, "01"+"NN" para actualizacion.
    version_snapshot: Mapped[str] = mapped_column(String(2), nullable=False, default="00")
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    # Elaborador: quien lleno el wizard (auth.user al firmar).
    elaborador_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Cargo del elaborador al momento de firmar (snapshot).
    cargo_elaborador: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_solicitud: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    justificacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Paso 2: Difusion y evaluacion ───
    # Snapshot del periodo de vigencia del tipo al firmar.
    tiempo_vigencia_anos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requiere_evaluacion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requiere_control_lectura: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Array JSONB de IDs (gerencia_id/area_id) que recibiran el documento.
    alcance_difusion_ids: Mapped[list[int]] = mapped_column(
        JSONType, nullable=False, default=list,
    )

    # ─── Paso 3: Flujo y firmas ───
    # Arrays JSONB de usuario_id. Minimo 1 cada uno (validado en Pydantic).
    revisor_ids: Mapped[list[int]] = mapped_column(
        JSONType, nullable=False, default=list,
    )
    aprobador_ids: Mapped[list[int]] = mapped_column(
        JSONType, nullable=False, default=list,
    )
    # Solo si el usuario marco reemplaza='si'. Array de codigos de documento
    # (ej: ['CC-3-005/00']) a dar de baja. Sesion 25 / Issue 11.2: el cliente
    # ingresa CODIGOS (no IDs) en el wizard paso 3, asi que el modelo es
    # list[str] (JSONB) en vez de list[int].
    reemplaza_documento_ids: Mapped[Optional[list[str]]] = mapped_column(
        JSONType, nullable=True, default=None,
    )

    # ─── Metadata de firma 2FA ───
    firma_usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    firma_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    firma_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    firma_user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ─── Auditoria estandar ───
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True,
    )

    # ─── Relaciones ───
    documento: Mapped["Documento"] = relationship("Documento", back_populates="flujos")
    estado_actual: Mapped["Estado"] = relationship("Estado")
    gerencia: Mapped["Gerencia"] = relationship("Gerencia")
    area: Mapped["Area"] = relationship("Area")
    tipo_documento: Mapped["TipoDocumento"] = relationship("TipoDocumento")
    elaborador: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[elaborador_id],
    )
    firma_usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[firma_usuario_id],
    )
    created_by: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[created_by_id],
    )

    # ─── Indices ───
    __table_args__ = (
        Index("ix_flujo_documento_estado", "documento_id", "estado_actual_id"),
        Index("ix_flujo_tipo_solicitud_fecha", "tipo_solicitud", "fecha_solicitud"),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentoFlujo id={self.id} doc_id={self.documento_id} "
            f"tipo={self.tipo_solicitud.value} estado_id={self.estado_actual_id}>"
        )
