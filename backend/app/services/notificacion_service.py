"""
Servicio: notificacion_service
Cola de notificaciones para el workflow documental (R3 Fase 2).
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notificacion import Notificacion

logger = logging.getLogger(__name__)

TIPOS_VALIDOS = (
    "ASIGNACION_TAREA", "REASIGNACION", "VENCIMIENTO",
    "DEVOLUCION", "CORRECCION", "PUBLICACION",
    "CONTROL_LECTURA", "EVALUACION", "SISTEMA",
)


async def crear_notificacion(
    db: AsyncSession,
    *,
    usuario_destino_id: int,
    titulo: str,
    mensaje: str,
    tipo_notificacion: str,
    usuario_origen_id: Optional[int] = None,
    documento_flujo_id: Optional[int] = None,
    tarea_id: Optional[int] = None,
) -> Notificacion:
    """Crea una notificacion persistente. NO hace commit (caller lo hace)."""
    if tipo_notificacion not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo de notificacion invalido: {tipo_notificacion}")

    notif = Notificacion(
        usuario_destino_id=usuario_destino_id,
        usuario_origen_id=usuario_origen_id,
        documento_flujo_id=documento_flujo_id,
        tarea_id=tarea_id,
        titulo=titulo,
        mensaje=mensaje,
        tipo_notificacion=tipo_notificacion,
    )
    db.add(notif)
    await db.flush()
    return notif


async def marcar_leida(
    db: AsyncSession,
    notificacion_id: int,
    ip: Optional[str] = None,
) -> Optional[Notificacion]:
    """Marca una notificacion como leida."""
    notif = await db.get(Notificacion, notificacion_id)
    if not notif:
        return None
    notif.leida = True
    notif.fecha_lectura = datetime.now(timezone.utc)
    notif.leida_en = ip
    await db.flush()
    return notif


async def contar_no_leidas(
    db: AsyncSession,
    usuario_destino_id: int,
) -> int:
    """Cuantas notificaciones no leidas tiene un usuario."""
    result = await db.execute(
        select(func.count(Notificacion.id))
        .where(Notificacion.usuario_destino_id == usuario_destino_id)
        .where(Notificacion.leida == False)
    )
    return result.scalar_one() or 0


async def listar_notificaciones(
    db: AsyncSession,
    usuario_destino_id: int,
    solo_no_leidas: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notificacion], int]:
    """Lista notificaciones de un usuario, ordenadas por fecha DESC."""
    query = select(Notificacion).where(
        Notificacion.usuario_destino_id == usuario_destino_id
    )
    count_query = select(func.count(Notificacion.id)).where(
        Notificacion.usuario_destino_id == usuario_destino_id
    )

    if solo_no_leidas:
        query = query.where(Notificacion.leida == False)
        count_query = count_query.where(Notificacion.leida == False)

    total = (await db.execute(count_query)).scalar_one() or 0

    rows = (await db.execute(
        query.order_by(Notificacion.created_at.desc())
        .limit(limit).offset(offset)
    )).scalars().all()

    return list(rows), total
