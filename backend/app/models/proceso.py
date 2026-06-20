"""
Modelo: Proceso
R3 Fase 1 - catalogo de procesos del SGD.

Por que existe (PROPUESTA-R3-TABLAS.md §1.5.6):
- El modelo `Documento` ya tiene `proceso_id: Mapped[Optional[int]]`
  (columna sin FK). La UI Lista Maestra muestra una columna "Proceso".
- Esta tabla completa el catalogo. Seed minimo con 10 procesos
  genericos; el operador puede renombrar/ajustar despues.
- FK opcional: la columna se conserva nullable para no romper docs
  pre-existentes con proceso_id apuntando a un ID borrado.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, DateTime, Boolean, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Proceso(Base):
    """Catalogo de procesos documentales."""
    __tablename__ = "procesos"

    # ─── Identidad ───
    id: Mapped[int] = mapped_column(primary_key=True)

    # ─── Datos ───
    # ─── Codigo numerico de 4 digitos (visible en UI, ej: 0001) ───
    codigo: Mapped[str] = mapped_column(
        String(4), unique=True, nullable=False,
    )
    # UNIQUE global: dos procesos no pueden tener el mismo nombre.
    nombre: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
    )
    descripcion: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
    )

    # ─── Estado ───
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Auditoria ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Proceso id={self.id} {self.nombre!r}>"
