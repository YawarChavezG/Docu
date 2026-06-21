"""
Schemas para Tareas del workflow documental (R3 Fase 2).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TareaOut(BaseModel):
    id: int
    documento_flujo_id: int
    usuario_id: int
    tipo_tarea: str
    estado: str
    fecha_asignacion: datetime
    fecha_vencimiento: Optional[datetime] = None
    fecha_completado: Optional[datetime] = None
    codigo_completo: str = ""
    titulo_documento: str = ""

    model_config = {"from_attributes": True}


class TareaListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TareaOut]
