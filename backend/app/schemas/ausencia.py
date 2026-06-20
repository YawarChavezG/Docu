"""
Schemas Pydantic v2 para ausencias (Sesion 23 / Bloque B1).
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AusenciaBase(BaseModel):
    fecha_desde: date
    fecha_hasta: date
    motivo: str = Field(..., description="vacaciones | licencia | capacitacion | otro")
    notas: Optional[str] = None

    @field_validator("fecha_hasta")
    @classmethod
    def _check_fecha_hasta(cls, v: date, info) -> date:
        f_desde = info.data.get("fecha_desde")
        if f_desde and v < f_desde:
            raise ValueError("fecha_hasta no puede ser anterior a fecha_desde")
        return v


class AusenciaCreate(AusenciaBase):
    pass


class AusenciaUpdate(BaseModel):
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    motivo: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class AusenciaOut(BaseModel):
    id: int
    usuario_id: int
    fecha_desde: date
    fecha_hasta: date
    motivo: str
    notas: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime
    esta_vigente: bool

    class Config:
        from_attributes = True


class AusenciaListResponse(BaseModel):
    total: int
    items: list[AusenciaOut]
