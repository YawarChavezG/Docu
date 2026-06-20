"""
Modelo: TipoDocumento
Catalogo de tipos de documento del SGD (US-9.03 sub-tarjeta 1).

REFACTOR sesion 13 (2026-06-16):
  Antes:
    - `codigo` (str slug, ej: 'PROCEDIMIENTO')  -- unico
    - `codigo_doc` (int, 1-14)                  -- NO unico (INSTRUCTIVO
                                                   e INSTRUCTIVO_TECNICO
                                                   comparten 6)
    - `nombre` (str)

  Despues:
    - `codigo` (int, 1-14)   -- UNIQUE, es el codigo logico del tipo
                                (usado en nomenclatura CC-5-001 v01
                                donde 5 = PROCEDIMIENTO)
    - `slug` (str)           -- UNIQUE, slug humano en MAYUSCULAS
                                (METODOLOGIA, INSTRUCTIVO, etc.)
    - `nombre` (str)         -- UNIQUE, nombre legible
    - DROP `codigo_doc` (redundante con `codigo`)

Datos del Excel 'TIPOS DE DOCUMENTO, CODIGO Y VIGENCIA.xlsx' (13 tipos,
2 comparten codigo_doc=6: INSTRUCTIVO e INSTRUCTIVO_TECNICO; en el nuevo
modelo ambos tienen codigo=6 pero slug y nombre distintos).

US-9.02: cada tipo puede tener un max_descargas_dia distinto.
US-9.04 (codigo de documento en plantilla): el `codigo` (int) es el que
aparece en la nomenclatura del documento (ej: CC-5-001 v01, donde
5=PROCEDIMIENTO).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoDocumento(Base):
    __tablename__ = "tipos_documento"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Codigo numerico (1-14). UNIQUE, sera el campo de referencia para
    # otras tablas (correlativos, nomenclatura CC-5-001 v01, etc).
    codigo: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)

    # Slug humano en MAYUSCULAS (METODOLOGIA, INSTRUCTIVO, etc). UNIQUE.
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Nombre legible (Metodologia, Instructivo, etc). UNIQUE.
    nombre: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    # Vigencia en anos (None si es indefinido)
    periodo_vigencia: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Si es indefinido (no vence)
    indefinido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Limite de descargas por dia (US-9.02). None = sin limite.
    max_descargas_dia: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Observacion opcional (ej: "SOLO APLICA PARA MANTENIMIENTO")
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        return f"<TipoDocumento codigo={self.codigo} slug={self.slug!r}>"
