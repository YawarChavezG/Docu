"""
schemas/plantilla_documental.py — Schemas Pydantic para plantillas documentales.

Sesion 24 / Bloque E: las plantillas son archivos estaticos (.docx) servidos
desde /app/storage/plantillas/. El listado se genera a partir del contenido
del directorio (no hay tabla en BD para esto: son assets).

PlantillaDocumentalOut:
  - nombre_archivo: nombre interno del archivo en disco (e.g. "procedimiento.docx")
  - nombre_display: nombre legible para UI (e.g. "Procedimiento")
  - categoria: word|excel|ppt|otro (derivado de la extension)
  - tamano_bytes: tamano del archivo en disco
  - version: version logica (default "v1" hasta que el cliente pida algo distinto)

PlantillaDownloadOut:
  - url: URL relativa para descargar el archivo (via /api/v1/plantillas-documentales/{nombre}/download)
"""
from typing import Literal

from pydantic import BaseModel, Field

CategoriaPlantilla = Literal["word", "excel", "ppt", "otro"]


class PlantillaDocumentalOut(BaseModel):
    """Metadata de una plantilla documental para mostrar en cards/listas."""

    nombre_archivo: str = Field(..., description="Nombre interno del archivo en disco")
    nombre_display: str = Field(..., description="Nombre legible para UI")
    descripcion: str = Field("", description="Descripcion breve de la plantilla")
    categoria: CategoriaPlantilla = Field(..., description="Tipo derivado de la extension")
    tamano_bytes: int = Field(..., ge=0, description="Tamano del archivo en bytes")
    version: str = Field("v1", description="Version logica de la plantilla")
    url_descarga: str = Field(..., description="URL relativa para descargar (auth required)")
    activo: bool = Field(True, description="Si la plantilla esta visible o fue eliminada")


class PlantillaListResponse(BaseModel):
    """Respuesta de GET /api/v1/plantillas-documentales."""

    total: int
    items: list[PlantillaDocumentalOut]
