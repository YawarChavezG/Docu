"""
schemas/matriz_enrutamiento_eto.py — Schemas Pydantic.

US-9.03 sub-tarjeta 3 "Matriz de Enrutamiento ETO".
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.matriz_enrutamiento_eto import DisponibilidadEto


# ─── Inputs ───

class MatrizEnrutamientoEtoBase(BaseModel):
    gerencia_id: int = Field(ge=1, description="FK a gerencias.id (UNIQUE)")
    analista_usuario_id: int = Field(ge=1, description="FK a usuarios.id (debe tener rol ETO)")
    disponibilidad: DisponibilidadEto = DisponibilidadEto.DISPONIBLE
    delegado_usuario_id: Optional[int] = Field(default=None, ge=1,
                                                 description="FK opcional a usuarios.id (recomendado si disponibilidad != DISPONIBLE)")


class MatrizEnrutamientoEtoCreate(MatrizEnrutamientoEtoBase):
    pass


class MatrizEnrutamientoEtoUpdate(BaseModel):
    """PATCH parcial."""
    analista_usuario_id: Optional[int] = Field(default=None, ge=1)
    disponibilidad: Optional[DisponibilidadEto] = None
    delegado_usuario_id: Optional[int] = Field(default=None, ge=1)


# ─── Outputs ───

class MatrizEnrutamientoEtoOut(BaseModel):
    """Incluye JOINs a gerencia y usuarios (analista, delegado, updated_by)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    gerencia_id: int
    gerencia_sigla: Optional[str] = None
    gerencia_nombre: Optional[str] = None
    analista_usuario_id: int
    analista_username: Optional[str] = None
    analista_nombre: Optional[str] = None
    disponibilidad: DisponibilidadEto
    delegado_usuario_id: Optional[int] = None
    delegado_username: Optional[str] = None
    delegado_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    updated_by_id: Optional[int] = None


class MatrizEnrutamientoEtoListResponse(BaseModel):
    total: int
    items: list[MatrizEnrutamientoEtoOut]
