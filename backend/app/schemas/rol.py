"""schemas/rol.py — Schemas Pydantic para Rol."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RolOut(BaseModel):
    """Salida de un Rol (catalogo)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    requiere_delegado: bool
    created_at: datetime
    updated_at: datetime


class RolListResponse(BaseModel):
    total: int
    items: list[RolOut]
