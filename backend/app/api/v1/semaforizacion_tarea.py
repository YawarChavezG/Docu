"""
api/v1/semaforizacion_tarea.py — CRUD de la configuracion del semaforo por
tipo de tarea (EPICA 9, sesion 13).

Antes: 2 claves globales en `configuracion_global` (semaforo_verde_dias,
semaforo_amarillo_dias) que aplicaban a TODAS las tareas.

Ahora: 1 fila por tipo de tarea en `semaforizacion_tarea` (4 tipos:
REVISION, APROBACION, CONTROL_LECTURA, EVALUACION). Cada una con sus
propios dias_verde, dias_amarillo, dias_rojo.

Endpoints (todos bajo prefix /api/v1/semaforizacion-tarea):
  GET    /                        lista las 4 reglas
  GET    /{tipo_tarea}            detalle de 1 regla
  PATCH  /{tipo_tarea}            update de una regla
  POST   /calcular                 dado (tipo_tarea, dias_transcurridos) devuelve el color

GETs no requieren auth. Mutaciones requieren ETO o ADMIN.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_eto_or_admin
from app.core.audit import write_audit
from app.models.semaforizacion_tarea import SemaforizacionTarea, TipoTarea
from app.schemas.semaforizacion_tarea import (
    SemaforizacionTareaListResponse,
    SemaforizacionTareaOut,
    SemaforizacionTareaUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/semaforizacion-tarea", tags=["Semaforizacion"])


def _calcular_color(cfg: SemaforizacionTarea, dias_transcurridos: int) -> str:
    """Devuelve 'VERDE' | 'AMARILLO' | 'ROJO' segun la regla."""
    if dias_transcurridos <= cfg.dias_verde:
        return "VERDE"
    if dias_transcurridos <= cfg.dias_amarillo:
        return "AMARILLO"
    return "ROJO"


# ─── Endpoints ───

@router.get("", response_model=SemaforizacionTareaListResponse)
async def list_semaforizacion(
    db: AsyncSession = Depends(get_db),
):
    """Lista las 4 reglas. No requiere auth (catalogo publico)."""
    rows = (await db.execute(
        select(SemaforizacionTarea).order_by(SemaforizacionTarea.tipo_tarea)
    )).scalars().all()
    return SemaforizacionTareaListResponse(
        total=len(rows),
        items=[SemaforizacionTareaOut.model_validate(r) for r in rows],
    )


@router.get("/{tipo_tarea}", response_model=SemaforizacionTareaOut)
async def get_semaforizacion(
    tipo_tarea: TipoTarea,
    db: AsyncSession = Depends(get_db),
):
    """Detalle. No requiere auth."""
    s = (await db.execute(
        select(SemaforizacionTarea).where(SemaforizacionTarea.tipo_tarea == tipo_tarea)
    )).scalar_one_or_none()
    if s is None:
        raise HTTPException(404, f"No existe regla de semaforo para {tipo_tarea.value}")
    return SemaforizacionTareaOut.model_validate(s)


@router.patch("/{tipo_tarea}", response_model=SemaforizacionTareaOut)
async def update_semaforizacion(
    tipo_tarea: TipoTarea,
    payload: SemaforizacionTareaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza una regla. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    s = (await db.execute(
        select(SemaforizacionTarea).where(SemaforizacionTarea.tipo_tarea == tipo_tarea)
    )).scalar_one_or_none()
    if s is None:
        raise HTTPException(404, f"No existe regla de semaforo para {tipo_tarea.value}")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return SemaforizacionTareaOut.model_validate(s)

    # Validacion: dias_verde < dias_amarillo < dias_rojo <= plazo_maximo
    new_v = data.get("dias_verde", s.dias_verde)
    new_a = data.get("dias_amarillo", s.dias_amarillo)
    new_r = data.get("dias_rojo", s.dias_rojo)
    new_p = data.get("plazo_maximo_dias", s.plazo_maximo_dias)
    if not (new_v < new_a < new_r <= new_p):
        raise HTTPException(
            422,
            f"Regla invalida: dias_verde({new_v}) < dias_amarillo({new_a}) < dias_rojo({new_r}) <= plazo_maximo({new_p})",
        )

    antes = {
        "dias_verde": s.dias_verde, "dias_amarillo": s.dias_amarillo, "dias_rojo": s.dias_rojo,
        "plazo_maximo_dias": s.plazo_maximo_dias, "activo": s.activo,
    }
    for field, value in data.items():
        setattr(s, field, value)
    await db.commit()
    await db.refresh(s)
    despues = {
        "dias_verde": s.dias_verde, "dias_amarillo": s.dias_amarillo, "dias_rojo": s.dias_rojo,
        "plazo_maximo_dias": s.plazo_maximo_dias, "activo": s.activo,
    }
    await write_audit(
        db, request, user,
        accion="UPDATE", recurso="semaforizacion_tarea", recurso_id=None,
        descripcion=f"Semaforo {tipo_tarea.value} actualizado",
        detalles={"antes": antes, "despues": despues, "campos": list(data.keys()), "tipo_tarea": tipo_tarea.value},
    )
    await db.commit()
    logger.info(f"Semaforo {tipo_tarea.value} actualizado: {despues}")
    return SemaforizacionTareaOut.model_validate(s)


# ─── Endpoint util: dado (tipo_tarea, dias) devuelve el color ───

class ColorRequest(BaseModel):
    tipo_tarea: TipoTarea
    dias_transcurridos: int = Field(ge=0, le=365)


class ColorResponse(BaseModel):
    tipo_tarea: TipoTarea
    dias_transcurridos: int
    dias_verde: int
    dias_amarillo: int
    dias_rojo: int
    plazo_maximo_dias: int
    color: str  # "VERDE" | "AMARILLO" | "ROJO" | "VENCIDA"
    dias_restantes: int


@router.post("/calcular", response_model=ColorResponse)
async def calcular_color(
    payload: ColorRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Dado un tipo de tarea y los dias transcurridos desde la asignacion,
    devuelve el color del semaforo segun la regla configurada.

    Tambien devuelve `dias_restantes` (puede ser negativo si esta vencida).
    No requiere auth (consulta deterministica).
    """
    s = (await db.execute(
        select(SemaforizacionTarea).where(SemaforizacionTarea.tipo_tarea == payload.tipo_tarea)
    )).scalar_one_or_none()
    if s is None:
        raise HTTPException(404, f"No existe regla de semaforo para {payload.tipo_tarea.value}")
    color = _calcular_color(s, payload.dias_transcurridos)
    return ColorResponse(
        tipo_tarea=payload.tipo_tarea,
        dias_transcurridos=payload.dias_transcurridos,
        dias_verde=s.dias_verde,
        dias_amarillo=s.dias_amarillo,
        dias_rojo=s.dias_rojo,
        plazo_maximo_dias=s.plazo_maximo_dias,
        color="VENCIDA" if payload.dias_transcurridos > s.plazo_maximo_dias else color,
        dias_restantes=s.plazo_maximo_dias - payload.dias_transcurridos,
    )
