"""
Modelo: Tarea
R3 Fase 1 - pieza central del workflow documental.

Por que existe (PROPUESTA-R3-TABLAS.md §2.1):
- Reemplaza los JSONB `revisor_ids` / `aprobador_ids` de DocumentoFlujo
  por una TABLA N:M que guarda ESTADO INDIVIDUAL por revisor/aprobador
  y SLAs individuales.
- Permite: bandeja por usuario (no por documento), SLA por tarea,
  reasignacion trazable, correccion dirigida al revisor que observo.

Cada Tarea es una unidad de trabajo asignada a UN usuario sobre UN
documento_flujo. Tipos posibles: REVISION, APROBACION, LIBERACION,
CORRECCION, CONTROL_LECTURA, EVALUACION (ver TipoTarea en
semaforizacion_tarea.py).
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String, DateTime, Boolean, Integer, ForeignKey, func,
    Text, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.documento_flujo import DocumentoFlujo
    from app.models.usuario import Usuario
    from app.models.firma_digital import FirmaDigital
    from app.models.semaforizacion_tarea import SemaforizacionTarea


class Tarea(Base):
    """
    Unidad de trabajo del workflow documental. R3 Fase 1.

    Reglas:
    - Una Tarea pertenece a UN usuario y UN documento_flujo.
    - El estado individual permite saber QUE usuarios ya completaron
      y CUALES siguen pendientes (a diferencia del JSONB que era
      opaco dentro del documento).
    - `delegado_origen_id` != NULL => esta tarea fue reasignada por el
      cron o por un ETO; el usuario original era `delegado_origen_id`
      y el actual es `usuario_id`.
    - `intento_reasignacion` maximo 3 (Fase 3 cron reasignacion).
    """
    __tablename__ = "tareas"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Relaciones ───
    documento_flujo_id: Mapped[int] = mapped_column(
        ForeignKey("documento_flujo.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Quien era el usuario ORIGINAL si la tarea fue reasignada.
    # NULL = asignacion original.
    delegado_origen_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    # FK al catalogo de semaforizacion (PK = tipo_tarea).
    tipo_tarea: Mapped[str] = mapped_column(
        ForeignKey("semaforizacion_tarea.tipo_tarea", ondelete="RESTRICT"),
        nullable=False,
    )
    # Firma 2FA que registro la accion sobre esta tarea.
    firma_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("firmas_digitales.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Estado individual ───
    # PENDIENTE: creada, sin accion del usuario.
    # COMPLETADO: el usuario aprobo/firmo.
    # RECHAZADO: el usuario rechazo (con observacion obligatoria).
    # REASIGNADO: reasignada al delegado o jefe (queda historica).
    # VENCIDO: supero plazo_maximo_dias (lo setea el cron de Fase 3).
    # NO_EJECUTADO: control de lectura o evaluacion no completada en plazo.
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDIENTE",
    )

    # ─── Timelines individuales (cada tarea tiene su propio SLA) ───
    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    # Calculado: fecha_asignacion + semaforizacion_tarea.plazo_maximo_dias
    # (en dias naturales o habiles segun semaforizacion_tarea.usa_dias_habiles).
    fecha_vencimiento: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    # NULL hasta que se complete.
    fecha_completado: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    # Para controles de lectura / evaluaciones (US-6).
    fecha_limite_eval: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # ─── Reasignacion ───
    intento_reasignacion: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )

    # ─── Observacion (obligatoria en RECHAZADO, validada en servicio) ───
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Auditoria estandar ───
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
    usuario: Mapped["Usuario"] = relationship(
        "Usuario", foreign_keys=[usuario_id],
    )
    delegado_origen: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[delegado_origen_id],
    )
    firma: Mapped[Optional["FirmaDigital"]] = relationship("FirmaDigital")

    # ─── Constraints ───
    __table_args__ = (
        # CHECK: estado pertenece al set valido.
        CheckConstraint(
            "estado IN ('PENDIENTE', 'COMPLETADO', 'RECHAZADO', "
            "'REASIGNADO', 'VENCIDO', 'NO_EJECUTADO')",
            name="ck_tarea_estado_valido",
        ),
        # CHECK: intento_reasignacion no negativo.
        CheckConstraint(
            "intento_reasignacion >= 0 AND intento_reasignacion <= 3",
            name="ck_tarea_intento_rango",
        ),
        # UNIQUE: una persona no puede tener 2 tareas iguales para el mismo flujo.
        UniqueConstraint(
            "documento_flujo_id", "usuario_id", "tipo_tarea",
            "fecha_asignacion",
            name="uq_tarea_flujo_usuario_tipo_fecha",
        ),
        # ─── Indices criticos ───
        # Bandeja: WHERE usuario_id = X AND estado = 'PENDIENTE'.
        Index("ix_tareas_usuario_estado", "usuario_id", "estado",
              postgresql_where=Boolean("activo = TRUE")),
        # Verificar avance de una etapa: WHERE documento_flujo_id = X AND tipo_tarea = Y.
        Index("ix_tareas_flujo_tipo", "documento_flujo_id", "tipo_tarea"),
        # Cron reasignacion: WHERE estado = 'PENDIENTE' AND fecha_vencimiento < NOW().
        Index("ix_tareas_vencimiento", "fecha_vencimiento",
              postgresql_where=Boolean("estado = 'PENDIENTE'")),
        # Calculo SLA: WHERE estado = 'PENDIENTE'.
        Index("ix_tareas_asignacion", "fecha_asignacion",
              postgresql_where=Boolean("estado = 'PENDIENTE'")),
    )

    def __repr__(self) -> str:
        return (
            f"<Tarea id={self.id} flujo={self.documento_flujo_id} "
            f"usuario={self.usuario_id} tipo={self.tipo_tarea} estado={self.estado}>"
        )
