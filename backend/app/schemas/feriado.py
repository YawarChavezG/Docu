"""
schemas/feriado.py — Schemas Pydantic para el recurso Feriado.

US-9.01: calendario de feriados Bolivia para calculo de plazos en dias habiles.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.feriado import TipoFeriado


# ─── Inputs ───

class FeriadoBase(BaseModel):
    fecha: date = Field(description="Fecha del feriado (YYYY-MM-DD). UNIQUE global.")
    nombre: str = Field(min_length=3, max_length=150)
    tipo: TipoFeriado
    departamento: Optional[str] = Field(default=None, max_length=50,
                                          description="Requerido si tipo=DEPARTAMENTAL")


class FeriadoCreate(FeriadoBase):
    activo: bool = True


class FeriadoUpdate(BaseModel):
    """PATCH parcial. Todos los campos opcionales."""
    fecha: Optional[date] = None
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=150)
    tipo: Optional[TipoFeriado] = None
    departamento: Optional[str] = Field(default=None, max_length=50)
    activo: Optional[bool] = None


# ─── Outputs ───

class FeriadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    nombre: str
    tipo: TipoFeriado
    departamento: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime


class FeriadoListResponse(BaseModel):
    total: int
    items: list[FeriadoOut]
