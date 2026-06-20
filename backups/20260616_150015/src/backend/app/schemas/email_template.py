"""
schemas/email_template.py — Schemas Pydantic para EmailTemplate (US-9.04).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.email_template import CodigoPlantilla


# ─── Inputs ───

class EmailTemplateUpdate(BaseModel):
    """PATCH: edicion desde la UI Parametrizacion > Plantillas."""
    nombre: Optional[str] = Field(default=None, min_length=3, max_length=150)
    asunto: Optional[str] = Field(default=None, min_length=3, max_length=500)
    cuerpo_html: Optional[str] = Field(default=None, min_length=1, max_length=50_000)
    variables_json: Optional[list] = None
    activo: Optional[bool] = None


# ─── Outputs ───

class EmailTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: CodigoPlantilla
    nombre: str
    asunto: str
    cuerpo_html: str
    variables_json: Optional[list] = None
    activo: bool
    created_at: datetime
    updated_at: datetime


class EmailTemplateListResponse(BaseModel):
    total: int
    items: list[EmailTemplateOut]


# ─── Preview (US-9.04 boton "Previsualizar") ───

class EmailTemplatePreviewRequest(BaseModel):
    vars: dict = Field(
        default_factory=dict,
        description="Valores de las variables para el render de prueba. "
                    "Vars no provistas quedan vacias.",
    )


class EmailTemplatePreviewResponse(BaseModel):
    codigo: CodigoPlantilla
    asunto_rendered: str
    cuerpo_html_rendered: str
    vars_aplicadas: dict
    vars_faltantes: list[str] = []
