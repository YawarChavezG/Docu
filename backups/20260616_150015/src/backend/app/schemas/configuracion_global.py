"""
schemas/configuracion_global.py — Schemas Pydantic para configuracion clave-valor.

US-9.01 (Tiempos y SLAs) + US-9.02 (Restricciones).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.configuracion_global import TipoConfiguracion, CategoriaConfiguracion


# ─── Inputs ───

class ConfiguracionGlobalBase(BaseModel):
    clave: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9_]+$",
                        description="Identificador unico en snake_case (ej: max_archivos_por_solicitud)")
    valor: str = Field(min_length=1, max_length=10_000,
                        description="Valor como string. Parsear segun `tipo` en el cliente.")
    tipo: TipoConfiguracion
    categoria: CategoriaConfiguracion
    descripcion: Optional[str] = Field(default=None, max_length=500)


class ConfiguracionGlobalCreate(ConfiguracionGlobalBase):
    """Schema para crear/actualizar (upsert) una clave."""
    pass


class ConfiguracionGlobalUpdate(BaseModel):
    """Schema para PATCH. Solo el valor (y opcionalmente descripcion)."""
    valor: str = Field(min_length=1, max_length=10_000)
    descripcion: Optional[str] = Field(default=None, max_length=500)


# ─── Outputs ───

class ConfiguracionGlobalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clave: str
    valor: str
    tipo: TipoConfiguracion
    categoria: CategoriaConfiguracion
    descripcion: Optional[str]
    activo: bool
    updated_at: datetime
    created_at: datetime
    updated_by_id: Optional[int] = None


class ConfiguracionGlobalListResponse(BaseModel):
    total: int
    items: list[ConfiguracionGlobalOut]


# ─── Bulk (US-9.01 sub-tarjeta "Guardar Vigencia y Flujo" como 1 accion) ───

class ConfiguracionBulkItem(BaseModel):
    clave: str = Field(min_length=3, max_length=100, pattern=r"^[a-z0-9_]+$")
    valor: str = Field(min_length=1, max_length=10_000)


class ConfiguracionBulkRequest(BaseModel):
    items: list[ConfiguracionBulkItem] = Field(min_length=1, max_length=50)
    categoria: CategoriaConfiguracion


class ConfiguracionBulkResponse(BaseModel):
    actualizadas: int
    creadas: int
    claves: list[str]
