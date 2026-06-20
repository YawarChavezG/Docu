"""
Schemas para el catalogo de procesos.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProcesoOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProcesoListResponse(BaseModel):
    total: int
    items: list[ProcesoOut]
