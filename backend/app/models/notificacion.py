"""
Modelo: Notificacion
R3 Fase 1 - cola de notificaciones con tracking de lectura.

Por que existe (PROPUESTA-R3-TABLAS.md §2.3):
- Reemplaza el polling del store `notificaciones.js` (frontend, 143 lineas)
  por una tabla persistente servida via API REST (Fase 4).
- Tracking de lectura para el badge de la campana y el dropdown
  (Fase 6 frontend).
- `email_enviado` se setea cuando el SMTP real (QAS) envie el correo;
  en DES queda false porque SMTP_ENABLED=false.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String, DateTime, Integer, ForeignKey, func,
    Text, Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.tarea import Tarea


class Notificacion(Base):
    """
    Notificacion persistida para un usuario. Reemplaza el polling del
    store frontend (sesion 36).
    """
    __tablename__ = "notificaciones"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    # Quien debe ver la notificacion.
    usuario_destino_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Quien la genero (NULL si es del sistema, ej: cron reasignacion).
    usuario_origen_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    # NULL si la notificacion no es sobre un documento especifico.
    documento_flujo_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documento_flujo.id", ondelete="CASCADE"),
        nullable=True,
    )
    # NULL si la notificacion no esta ligada a una tarea especifica.
    tarea_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tareas.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Contenido ───
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    # ASIGNACION_TAREA | REASIGNACION | VENCIMIENTO | DEVOLUCION |
    # CORRECCION | PUBLICACION | CONTROL_LECTURA | EVALUACION | SISTEMA.
    tipo_notificacion: Mapped[str] = mapped_column(String(30), nullable=False)

    # ─── Tracking de lectura ───
    leida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_lectura: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    # IP desde donde se leyo (forense opcional).
    leida_en: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # ─── Tracking de envio email (QAS SMTP real) ───
    email_enviado: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    email_enviado_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ─── Inmutable (no se UPDATE la fila; solo se marca leida) ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ─── Relaciones ───
    usuario_destino: Mapped["Usuario"] = relationship(
        "Usuario", foreign_keys=[usuario_destino_id],
    )
    usuario_origen: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[usuario_origen_id],
    )
    documento_flujo: Mapped[Optional["DocumentoFlujo"]] = relationship(
        "DocumentoFlujo",
    )
    tarea: Mapped[Optional["Tarea"]] = relationship("Tarea")

    # ─── Constraints ───
    __table_args__ = (
        # CHECK: tipo_notificacion pertenece al set valido.
        CheckConstraint(
            "tipo_notificacion IN ("
            "'ASIGNACION_TAREA', 'REASIGNACION', 'VENCIMIENTO', "
            "'DEVOLUCION', 'CORRECCION', 'PUBLICACION', "
            "'CONTROL_LECTURA', 'EVALUACION', 'SISTEMA'"
            ")",
            name="ck_notif_tipo_valido",
        ),
        # ─── Indices ───
        # Badge campana: WHERE usuario_destino_id = X AND leida = FALSE.
        Index(
            "ix_notif_usuario_no_leidas",
            "usuario_destino_id", "leida",
            postgresql_where=Boolean("leida = FALSE"),
        ),
        # Listado cronologico: WHERE usuario_destino_id = X ORDER BY created_at DESC.
        Index("ix_notif_usuario_fecha", "usuario_destino_id", "created_at"),
        # Por documento: WHERE documento_flujo_id = X.
        Index("ix_notif_flujo", "documento_flujo_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Notificacion id={self.id} destino={self.usuario_destino_id} "
            f"tipo={self.tipo_notificacion!r} leida={self.leida}>"
        )
