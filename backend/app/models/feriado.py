"""
Modelo: Feriado
Calendario de feriados de Bolivia 2026+ (US-9.01 - calculo de plazos en dias habiles).

Tipos:
  - NACIONAL: feriado de todo el pais
  - DEPARTAMENTAL: solo un departamento especifico (campo 'departamento')
  - EMPRESARIAL: dia no laborable definido por COFAR (casos especiales)

Usado por:
  - Calculo de plazos de revision/aprobacion (10 habiles o 15 calendario, lo primero)
  - Semaforo de bandejas (excluir feriados del conteo de "dias habiles")
  - Notificaciones (no enviar el dia del feriado)

Datos: ver backend/scripts/seed_feriados.py (16 feriados oficiales Bolivia 2026).
"""
import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Date, DateTime, Boolean, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoFeriado(str, enum.Enum):
    NACIONAL = "NACIONAL"
    DEPARTAMENTAL = "DEPARTAMENTAL"
    EMPRESARIAL = "EMPRESARIAL"


class Feriado(Base):
    __tablename__ = "feriados"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[TipoFeriado] = mapped_column(
        SAEnum(TipoFeriado, name="tipo_feriado",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    # Solo se usa cuando tipo=DEPARTAMENTAL (ej: "LA PAZ", "SANTA CRUZ")
    departamento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Feriado {self.fecha} {self.nombre!r} ({self.tipo.value})>"
