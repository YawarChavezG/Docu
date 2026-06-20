"""
Modelo: MatrizEnrutamientoEto
Asignacion de analistas ETO por gerencia (US-9.03, sub-tarjeta 3).

Logica del flujo Paso 4 (libera ETO):
  El sistema consulta esta tabla para saber QUE analista ETO debe recibir
  la solicitud. Si DISPONIBILIDAD=false, redirige al DELEGADO.

Restricciones:
  - 1 ETO por gerencia (unique en gerencia_id)
  - analista_usuario_id debe tener rol ETO
  - si disponibilidad=false, delegado_usuario_id es recomendado (no obligatorio)
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DisponibilidadEto(str, enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    AUSENTE = "AUSENTE"
    LICENCIA = "LICENCIA"  # vacaciones, etc


class MatrizEnrutamientoEto(Base):
    __tablename__ = "matriz_enrutamiento_eto"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 1 fila por gerencia (unique)
    gerencia_id: Mapped[int] = mapped_column(
        ForeignKey("gerencias.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True,
    )

    # Analista ETO asignado (FK a usuarios)
    analista_usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Disponibilidad: si AUSENTE, redirigir a delegado
    disponibilidad: Mapped[DisponibilidadEto] = mapped_column(
        SAEnum(DisponibilidadEto, name="disponibilidad_eto",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=DisponibilidadEto.DISPONIBLE,
    )

    # Delegado (opcional, recomendado si disponibilidad != DISPONIBLE)
    delegado_usuario_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Auditoria
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    updated_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<MatrizEnrutamientoEto gerencia_id={self.gerencia_id} analista={self.analista_usuario_id}>"
