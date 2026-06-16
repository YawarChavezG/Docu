"""schemas/estado.py — Schemas Pydantic."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.estado import ContextoEstado


class EstadoBase(BaseModel):
    codigo: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    nombre: str = Field(min_length=3, max_length=150)
    contexto: ContextoEstado = ContextoEstado.AMBOS
    orden: int = Field(default=0, ge=0, le=999)
    descripcion: Optional[str] = Field(default=None, max_length=500)


class EstadoCreate(EstadoBase):
    activo: bool = True


class EstadoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=150)
    contexto: Optional[ContextoEstado] = None
    orden: Optional[int] = Field(default=None, ge=0, le=999)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    activo: Optional[bool] = None


class EstadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    contexto: ContextoEstado
    orden: int
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime


class EstadoListResponse(BaseModel):
    total: int
    items: list[EstadoOut]
