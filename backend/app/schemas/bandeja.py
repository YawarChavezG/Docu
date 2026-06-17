"""
schemas/bandeja.py — Schemas para los endpoints de bandejas.
Sesion 22 R2 FASE 2 - Tarea 2.5.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BandejaItem(BaseModel):
    """Item individual de una bandeja. Resumen del documento con metadata relevante."""
    documento_id: int
    codigo: str
    codigo_completo: str
    version: str
    titulo: str
    tipo_codigo: int
    tipo_nombre: str
    gerencia_sigla: str
    area_sigla: str
    vigencia: str
    estatus: str
    fecha_solicitud: Optional[datetime] = None
    elaborador_id: Optional[int] = None
    elaborador_username: Optional[str] = None
    # Acciones disponibles (segun el tipo de bandeja)
    requiere_mi_accion: bool = False


class BandejaResponse(BaseModel):
    """Respuesta del endpoint /bandeja."""
    tipo: str  # elaboracion | revision | aprobacion | liberacion
    total: int
    page: int
    page_size: int
    items: List[BandejaItem]
