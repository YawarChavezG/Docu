"""
Modelo: Ausencia
Programación de vacaciones/licencias. Cuando está activa, el sistema redirige
las tareas del usuario a su delegado.
"""
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Ausencia(Base):
    __tablename__ = "ausencias"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fecha_desde: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_hasta: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Motivo
    motivo: Mapped[str] = mapped_column(String(50), nullable=False)  # vacaciones, licencia, capacitacion

    # Si está activa (false = cancelada por el usuario)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Notas
    notas: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Auditoría
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relación
    usuario = relationship("Usuario", back_populates="ausencias")

    def __repr__(self) -> str:
        return f"<Ausencia {self.usuario_id} {self.fecha_desde}→{self.fecha_hasta}>"

    @property
    def esta_vigente(self) -> bool:
        """True si la ausencia está activa y la fecha actual está en el rango."""
        if not self.activo:
            return False
        hoy = date.today()
        return self.fecha_desde <= hoy <= self.fecha_hasta
