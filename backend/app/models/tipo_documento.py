"""
Modelo: TipoDocumento
Catalogo de tipos de documento del SGD (US-9.03 sub-tarjeta 1).

Datos del Excel 'TIPOS DE DOCUMENTO, CÓDIGO Y VIGENCIA.xlsx':
  13 tipos, 2 comparten codigo_doc=6 (INSTRUCTIVO e INSTRUCTIVO TECNICO).
  `codigo_doc` es campo LOGICO (no unique) — la PK es el `codigo` (string).

US-9.02: cada tipo puede tener un max_descargas_dia distinto.
US-9.04 (codigo de documento en plantilla): la sigla del tipo va en
el codigo del documento (ej: CC-5-001 v01, donde 5=PROCEDIMIENTO).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoDocumento(Base):
    __tablename__ = "tipos_documento"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Codigo string, unico (slug). Ej: "METODOLOGIA", "INSTRUCTIVO", "INSTRUCTIVO_TECNICO"
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Nombre humano del tipo. Ej: "Manual de Funciones"
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)

    # Codigo LOGICO del documento (1-14, NO unique porque INSTRUCTIVO y
    # INSTRUCTIVO TECNICO comparten el 6).
    codigo_doc: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

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
        return f"<TipoDocumento {self.codigo} (cod_doc={self.codigo_doc})>"
