"""
schemas/tipo_documento.py — Schemas Pydantic para TipoDocumento (US-9.03 sub-1).

REFACTOR sesion 13 (2026-06-16):
  - `codigo` ahora es int (1-14), UNIQUE
  - `slug` (str MAYUSCULAS) UNIQUE
  - `nombre` (str) UNIQUE
  - `codigo_doc` se elimina del modelo
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── Inputs ───

class TipoDocumentoBase(BaseModel):
    codigo: int = Field(ge=1, le=99,
                        description="Codigo numerico UNIQUE (1-14). Referencia para nomenclatura CC-5-001 v01.")
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$",
                      description="Slug unico MAYUSCULAS (ej: METODOLOGIA, INSTRUCTIVO).")
    nombre: str = Field(min_length=3, max_length=150)
    periodo_vigencia: Optional[int] = Field(default=None, ge=1, le=99,
                                              description="Vigencia en anos (None si es indefinido)")
    indefinido: bool = False
    max_descargas_dia: Optional[int] = Field(default=None, ge=0, le=9999)
    observacion: Optional[str] = Field(default=None, max_length=500)


class TipoDocumentoCreate(TipoDocumentoBase):
    activo: bool = True


class TipoDocumentoUpdate(BaseModel):
    """PATCH parcial. Todos los campos opcionales."""
    codigo: Optional[int] = Field(default=None, ge=1, le=99)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Z0-9_]+$")
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=150)
    periodo_vigencia: Optional[int] = Field(default=None, ge=1, le=99)
    indefinido: Optional[bool] = None
    max_descargas_dia: Optional[int] = Field(default=None, ge=0, le=9999)
    observacion: Optional[str] = Field(default=None, max_length=500)
    activo: Optional[bool] = None


# ─── Outputs ───

class TipoDocumentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    slug: str
    nombre: str
    periodo_vigencia: Optional[int] = None
    indefinido: bool
    max_descargas_dia: Optional[int] = None
    observacion: Optional[str] = None
    activo: bool
    created_at: datetime
    updated_at: datetime


class TipoDocumentoListResponse(BaseModel):
    total: int
    items: list[TipoDocumentoOut]
