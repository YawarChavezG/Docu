"""
schemas/gerencia.py — Schemas Pydantic para el recurso Gerencia.

US-9.06 (Parametrizacion > Gerencias y Areas).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Inputs ───

class GerenciaBase(BaseModel):
    sigla: str = Field(min_length=2, max_length=10, pattern=r"^[A-Z0-9_-]+$",
                        description="Sigla unica mayuscula (ej: CAL, PLA, RRH)")
    nombre: str = Field(min_length=3, max_length=150,
                         description="Nombre completo de la gerencia")
    orden: int = Field(default=0, ge=0, le=999,
                       description="Orden de visualizacion en UI (menor = primero)")


class GerenciaCreate(GerenciaBase):
    """Schema para crear una gerencia. activo=True por default."""
    activo: bool = True


class GerenciaUpdate(BaseModel):
    """Schema para PATCH parcial. Todos los campos opcionales."""
    sigla: Optional[str] = Field(default=None, min_length=2, max_length=10,
                                  pattern=r"^[A-Z0-9_-]+$")
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=150)
    orden: Optional[int] = Field(default=None, ge=0, le=999)
    activo: Optional[bool] = None


# ─── Outputs ───

class GerenciaOut(BaseModel):
    """Schema de respuesta. Inlude conteo de areas."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sigla: str
    nombre: str
    activo: bool
    orden: int
    areas_count: int = 0
    created_at: datetime
    updated_at: datetime


class GerenciaListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GerenciaOut]
