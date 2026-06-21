"""
Servicio: timeline_service
Registra cada evento del flujo documental en bitacora_timeline (append-only).

La bitácora es INMUTABLE: nunca se UPDATE ni DELETE. Solo INSERT.
Cada evento tiene un color_nodo según la acción (US-8.01):
  - Azul:   CREADO, CORREGIDO, ENVIADO
  - Verde:  LIBERADO_ETO, APROBADO, PUBLICADO
  - Rojo:   RECHAZADO, ELIMINADO, OBSOLETO, VENCIDO
  - Ámbar:  PENDIENTE, EN_REVISION, EN_CORRECCION
  - Gris:   REASIGNADO
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bitacora_timeline import BitacoraTimeline
from app.models.usuario import Usuario

COLOR_MAP = {
    "CREADO": "azul",
    "ENVIADO": "azul",
    "CORREGIDO": "azul",
    "LIBERADO_ETO": "verde",
    "APROBADO": "verde",
    "PUBLICADO": "verde",
    "RECHAZADO": "rojo",
    "ELIMINADO": "rojo",
    "OBSOLETO": "rojo",
    "VENCIDO": "rojo",
    "DEVUELTO": "rojo",
    "PENDIENTE": "ambar",
    "EN_REVISION": "ambar",
    "EN_CORRECCION": "ambar",
    "EN_APROBACION": "ambar",
    "REASIGNADO": "gris",
    "REASIGNADO_AUTO": "gris",
    "REASIGNADO_ETO": "gris",
}


async def escribir_bitacora(
    db: AsyncSession,
    *,
    documento_flujo_id: int,
    tarea_id: Optional[int] = None,
    usuario: Usuario,
    accion: str,
    estado_origen: Optional[str] = None,
    estado_destino: Optional[str] = None,
    observacion: Optional[str] = None,
    adjunto_url: Optional[str] = None,
) -> BitacoraTimeline:
    """
    Escribe un nodo en la bitácora del documento.

    Args:
        db: sesión de BD
        documento_flujo_id: ID del flujo documental
        tarea_id: ID de la tarea (opcional)
        usuario: usuario que ejecuta la acción
        accion: código de la acción
        estado_origen: estado anterior (opcional)
        estado_destino: estado nuevo (opcional)
        observacion: texto libre (obligatorio en RECHAZADO)
        adjunto_url: URL a evidencia (opcional)

    Returns:
        BitacoraTimeline creada
    """
    color = COLOR_MAP.get(accion, "azul")

    entry = BitacoraTimeline(
        documento_flujo_id=documento_flujo_id,
        tarea_id=tarea_id,
        usuario_id=usuario.id,
        accion=accion,
        estado_origen=estado_origen,
        estado_destino=estado_destino,
        color_nodo=color,
        observacion=observacion,
        adjunto_url=adjunto_url,
    )
    db.add(entry)
    await db.flush()
    return entry
