"""
Modelo: AuditLog
Registro inmutable de acciones administrativas (EPICA 9 - US-9.05).

Caracteristicas:
- Append-only (no UPDATE/DELETE desde la API)
- Captura IP y User-Agent del request
- detalles en JSONB para extensibilidad sin migraciones
- Indice en (recurso, recurso_id) y (created_at desc) para los filtros
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import String, DateTime, Integer, Boolean, Text, Index, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Tipo portable: JSONB en PostgreSQL, JSON en SQLite (tests)
JSONType = JSON().with_variant(JSONB(), "postgresql")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Quien ejecuto la accion (puede ser None para acciones del sistema)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    usuario_username: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    usuario_nombre: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Que accion (CREATE, UPDATE, DELETE, LOGIN, EXPORT, SYNC, etc.)
    accion: Mapped[str] = mapped_column(String(40), nullable=False, index=True)

    # Sobre que recurso (gerencia, area, configuracion_global, usuario, etc.)
    recurso: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    recurso_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Descripcion legible
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSONB flexible: {"antes": {...}, "despues": {...}, "diff": {...}}
    detalles: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONType,
        nullable=True,
    )

    # Contexto del request
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 max 45 chars
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Resultado
    exitoso: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Indice compuesto para queries tipicas: (recurso, created_at desc)
    __table_args__ = (
        Index("ix_audit_log_recurso_created", "recurso", "created_at"),
        Index("ix_audit_log_usuario_created", "usuario_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} {self.accion} {self.recurso}/{self.recurso_id} by={self.usuario_username}>"
