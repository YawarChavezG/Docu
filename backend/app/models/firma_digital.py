"""
Modelo: FirmaDigital
Log inmutable de todas las verificaciones 2FA (usuario + password) en el sistema.
Usado por US-2.06, 3.03, 3.04, 6.03, 7.03, 7.06 (todos los flujos que requieren firma).
"""
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FirmaDigital(Base):
    __tablename__ = "firmas_digitales"

    id: Mapped[int] = mapped_column(primary_key=True)

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Acción firmada (ej: "aprobacion_revision", "liberacion_eto", "recepcion_copia")
    accion: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Tipo de recurso firmado (ej: "documento_version", "copia_fisica", "examen")
    recurso_tipo: Mapped[str] = mapped_column(String(50), nullable=False)

    # ID del recurso
    recurso_id: Mapped[int] = mapped_column(nullable=False, index=True)

    # IP desde donde se firmó
    ip: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max 45 chars

    # User agent (opcional, para auditoría forense)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Si la firma fue exitosa (credenciales válidas)
    resultado_exito: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)

    # Si falló, motivo
    motivo_fallo: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Auditoría (inmutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relación
    usuario = relationship("Usuario", back_populates="firmas_digitales")

    def __repr__(self) -> str:
        return f"<FirmaDigital {self.accion} {self.recurso_tipo}#{self.recurso_id} usuario={self.usuario_id}>"
