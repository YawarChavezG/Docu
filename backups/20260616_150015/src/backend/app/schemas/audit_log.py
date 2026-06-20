"""
Schemas Pydantic v2 para AuditLog.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuditLogOut(BaseModel):
    """Una entrada de audit-log para listar en la UI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: Optional[int] = None
    usuario_username: Optional[str] = None
    usuario_nombre: Optional[str] = None
    accion: str
    recurso: str
    recurso_id: Optional[int] = None
    descripcion: Optional[str] = None
    detalles: Optional[dict[str, Any]] = None
    ip: Optional[str] = None
    exitoso: bool
    error_msg: Optional[str] = None
    created_at: datetime


class AuditLogPaginado(BaseModel):
    """Respuesta paginada del listado."""
    total: int
    limit: int
    offset: int
    items: list[AuditLogOut]
