"""
Modelo: BitacoraTimeline
R3 Fase 1 - timeline inmutable del documento (US-8.01).

Por que existe (PROPUESTA-R3-TABLAS.md §2.2):
- Append-only. NUNCA se UPDATE ni DELETE una fila. Solo INSERT.
- Reemplaza el uso de audit_log para acciones del workflow
  (audit_log sigue para acciones administrativas; bitacora_timeline
  es especificamente para la VISTA de timeline del usuario).
- color_nodo se define en backend segun la accion (reglas de US-8.01):
    * azul   = CREADO, CORREGIDO
    * verde  = LIBERADO_ETO, APROBADO, PUBLICADO
    * rojo   = RECHAZADO, ELIMINADO, OBSOLETO, VENCIDO
    * ambar  = PENDIENTE (cuando se crea una tarea)
    * gris   = REASIGNADO (automatico o manual)
- Las acciones automaticas (cron) se registran con usuario_id del
  usuario SISTEMA (id=0 o un usuario especial; ver Fase 3).
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String, DateTime, Integer, ForeignKey, func,
    Text, Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.tarea import Tarea
    from app.models.usuario import Usuario


class BitacoraTimeline(Base):
    """
    Nodo del timeline del documento. Append-only.

    No se exponen setters ni update desde el ORM: el service
    `timeline_service.py` (Fase 2) sera el unico que INSERT aqui.
    """
    __tablename__ = "bitacora_timeline"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    documento_flujo_id: Mapped[int] = mapped_column(
        ForeignKey("documento_flujo.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Opcional: si este nodo pertenece a una tarea especifica.
    tarea_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tareas.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Quien ejecuto la accion (o el SISTEMA para acciones automaticas).
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # ─── Accion ejecutada ───
    # CREADO | LIBERADO_ETO | APROBADO | RECHAZADO | CORREGIDO |
    # REASIGNADO_AUTO | REASIGNADO_ETO | VENCIDO | PUBLICADO |
    # OBSOLETO | ELIMINADO | TAREA_CREADA.
    accion: Mapped[str] = mapped_column(String(50), nullable=False)

    # ─── Trazabilidad de transicion ───
    estado_origen: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estado_destino: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ─── Color del nodo en la UI (calculado en backend, CHECK en BD) ───
    color_nodo: Mapped[str] = mapped_column(
        String(10), nullable=False, default="azul",
    )

    # ─── Contenido ───
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adjunto_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ─── Inmutable (created_at es el unico timestamp) ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # ─── Relaciones ───
    documento_flujo: Mapped["DocumentoFlujo"] = relationship("DocumentoFlujo")
    tarea: Mapped[Optional["Tarea"]] = relationship("Tarea")
    usuario: Mapped["Usuario"] = relationship("Usuario")

    # ─── Constraints ───
    __table_args__ = (
        # CHECK: color_nodo pertenece al set valido de US-8.01.
        CheckConstraint(
            "color_nodo IN ('azul', 'verde', 'rojo', 'ambar', 'gris')",
            name="ck_bitacora_color_valido",
        ),
        # ─── Indices ───
        # Timeline del documento: WHERE documento_flujo_id = X ORDER BY created_at.
        Index("ix_bitacora_flujo", "documento_flujo_id", "created_at"),
        # Actividad del usuario: WHERE usuario_id = X.
        Index("ix_bitacora_usuario", "usuario_id"),
        # Filtro por tipo de accion en rango de fechas (reportes).
        Index("ix_bitacora_accion_fecha", "accion", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<BitacoraTimeline id={self.id} flujo={self.documento_flujo_id} "
            f"accion={self.accion!r} color={self.color_nodo}>"
        )
