"""
schemas/semaforizacion_tarea.py — Schemas Pydantic.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.semaforizacion_tarea import TipoTarea


# ─── Inputs ───

class SemaforizacionTareaBase(BaseModel):
    dias_verde: int = Field(ge=1, le=30, description="Ultimo dia (inclusive) en VERDE")
    dias_amarillo: int = Field(ge=1, le=30, description="Ultimo dia (inclusive) en AMARILLO")
    dias_rojo: int = Field(ge=1, le=30, description="Ultimo dia (inclusive) en ROJO")
    plazo_maximo_dias: int = Field(ge=1, le=30, default=15)
    descripcion: Optional[str] = Field(default=None, max_length=500)


class SemaforizacionTareaUpdate(BaseModel):
    """PATCH parcial. Todos los campos opcionales."""
    dias_verde: Optional[int] = Field(default=None, ge=1, le=30)
    dias_amarillo: Optional[int] = Field(default=None, ge=1, le=30)
    dias_rojo: Optional[int] = Field(default=None, ge=1, le=30)
    plazo_maximo_dias: Optional[int] = Field(default=None, ge=1, le=30)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    activo: Optional[bool] = None


# ─── Outputs ───

class SemaforizacionTareaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo_tarea: TipoTarea
    dias_verde: int
    dias_amarillo: int
    dias_rojo: int
    plazo_maximo_dias: int
    descripcion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime


class SemaforizacionTareaListResponse(BaseModel):
    total: int
    items: list[SemaforizacionTareaOut]
