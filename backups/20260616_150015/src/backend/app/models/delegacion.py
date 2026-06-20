"""
Modelo: Delegacion
Un usuario (principal) puede tener un delegado (suplente) configurado.
La US-1.03 dice que un usuario NO puede delegarse a sí mismo.
"""
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Delegacion(Base):
    __tablename__ = "delegaciones"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_principal_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    delegado_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Si está activa o no
    activo: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    # Notas del usuario principal (ej: "solo en proyectos de validación")
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

    # Relaciones
    usuario_principal = relationship(
        "Usuario", foreign_keys=[usuario_principal_id], back_populates="delegaciones_como_principal"
    )
    delegado = relationship(
        "Usuario", foreign_keys=[delegado_id], back_populates="delegaciones_como_suplente"
    )

    __table_args__ = (
        # Un usuario solo puede tener UN delegado activo
        UniqueConstraint("usuario_principal_id", "activo", name="uq_principal_activo"),
    )

    def __repr__(self) -> str:
        return f"<Delegacion {self.usuario_principal_id} → {self.delegado_id}>"
