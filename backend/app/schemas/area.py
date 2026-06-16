"""
schemas/area.py — Schemas Pydantic para el recurso Area.

US-9.06 (Parametrizacion > Gerencias y Areas).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Inputs ───

class AreaBase(BaseModel):
    gerencia_id: int = Field(ge=1, description="FK a gerencias.id (debe existir)")
    sigla: str = Field(min_length=2, max_length=10, pattern=r"^[A-Z0-9_-]+$",
                        description="Sigla unica POR GERENCIA (mayusculas). Puede repetirse entre gerencias distintas.")
    nombre: str = Field(min_length=3, max_length=150)
    orden: int = Field(default=0, ge=0, le=999)
    jefe_id: Optional[int] = Field(default=None, ge=1,
                                     description="FK opcional a usuarios.id (jefe de area)")


class AreaCreate(AreaBase):
    """Schema para crear un area. activo=True por default."""
    activo: bool = True


class AreaUpdate(BaseModel):
    """Schema para PATCH parcial. Todos los campos opcionales."""
    gerencia_id: Optional[int] = Field(default=None, ge=1)
    sigla: Optional[str] = Field(default=None, min_length=2, max_length=10,
                                  pattern=r"^[A-Z0-9_-]+$")
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=150)
    orden: Optional[int] = Field(default=None, ge=0, le=999)
    jefe_id: Optional[int] = Field(default=None, ge=1)
    activo: Optional[bool] = None


# ─── Inputs para operaciones jerarquicas (Sesion B - tarea #9d) ───

class AreaMoverRequest(BaseModel):
    """Body para POST /areas/{id}/mover."""
    gerencia_id_destino: int = Field(ge=1, description="FK a gerencias.id destino")


class AreaPromoverRequest(BaseModel):
    """Body para POST /areas/{id}/promover-a-gerencia.
    Convierte esta area en la primera area de una nueva gerencia."""
    sigla_gerencia: str = Field(min_length=2, max_length=10, pattern=r"^[A-Z0-9]+$",
                                 description="Sigla de la nueva gerencia (unica global)")
    nombre_gerencia: str = Field(min_length=3, max_length=150)


# ─── Outputs ───

class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gerencia_id: int
    gerencia_sigla: Optional[str] = None
    gerencia_nombre: Optional[str] = None
    sigla: str
    nombre: str
    activo: bool
    orden: int
    jefe_id: Optional[int] = None
    usuarios_count: int = 0
    created_at: datetime
    updated_at: datetime


class AreaListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AreaOut]
