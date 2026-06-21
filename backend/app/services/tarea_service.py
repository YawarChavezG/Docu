"""
Servicio: tarea_service
Core del workflow documental (R3 Fase 2).
Maneja el ciclo de vida de las tareas: crear, completar, rechazar, reasignar.
Y la propagacion entre etapas (todos los revisores OK → aprobacion, etc.).
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Request, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tarea import Tarea
from app.models.tarea_observacion import TareaObservacion
from app.models.usuario import Usuario
from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento
from app.models.documento_flujo import DocumentoFlujo
from app.models.firma_digital import FirmaDigital
from app.models.semaforizacion_tarea import SemaforizacionTarea, TipoTarea
from app.core.audit import write_audit
from app.services.timeline_service import escribir_bitacora

logger = logging.getLogger(__name__)

ESTADOS_VALIDOS = ("PENDIENTE", "COMPLETADO", "RECHAZADO", "REASIGNADO", "VENCIDO", "NO_EJECUTADO")


async def _validar_password(db: AsyncSession, user: Usuario, password: str) -> bool:
    """Valida password del usuario para firma 2FA."""
    from passlib.hash import bcrypt
    if user.password_hash and bcrypt.verify(password, user.password_hash):
        return True
    return False


async def _registrar_firma(db: AsyncSession, request: Request, user: Usuario,
                           accion: str, recurso_id: int, exitoso: bool = True,
                           motivo: Optional[str] = None):
    """Regstra una firma digital en BD."""
    firma = FirmaDigital(
        usuario_id=user.id,
        accion=accion,
        recurso_tipo="tarea",
        recurso_id=recurso_id,
        ip=request.client.host if request.client else "",
        user_agent=(request.headers.get("user-agent", "")[:500] or None),
        resultado_exito=exitoso,
        motivo_fallo=motivo,
    )
    db.add(firma)
    await db.flush()
    return firma


async def crear_tarea(
    db: AsyncSession,
    *,
    documento_flujo_id: int,
    usuario_id: int,
    tipo_tarea: str,
    delegado_origen_id: Optional[int] = None,
    fecha_asignacion: Optional[datetime] = None,
) -> Tarea:
    """
    Crea una tarea y registra timeline: PENDIENTE (ambar).
    NO hace commit (el caller lo hace).
    """
    tarea = Tarea(
        documento_flujo_id=documento_flujo_id,
        usuario_id=usuario_id,
        tipo_tarea=tipo_tarea,
        delegado_origen_id=delegado_origen_id,
        estado="PENDIENTE",
        fecha_asignacion=fecha_asignacion or datetime.now(timezone.utc),
    )
    db.add(tarea)
    await db.flush()

    from app.models.usuario import Usuario
    user_sistema = await db.get(Usuario, usuario_id)
    if user_sistema:
        await escribir_bitacora(
            db=db,
            documento_flujo_id=documento_flujo_id,
            tarea_id=tarea.id,
            usuario=user_sistema,
            accion="PENDIENTE",
            estado_origen=None,
            estado_destino="PENDIENTE",
            observacion=f"Tarea {tipo_tarea} asignada a {user_sistema.nombre_completo}",
        )

    logger.info("Tarea %d creada: flujo=%d usuario=%d tipo=%s",
                tarea.id, documento_flujo_id, usuario_id, tipo_tarea)
    return tarea


async def completar_tarea(
    db: AsyncSession,
    request: Request,
    user: Usuario,
    tarea_id: int,
    firma_password: str,
) -> tuple[Tarea, Optional[str]]:
    """
    Completa una tarea como APROBADO.
    Returns: (tarea, accion_siguiente) donde accion_siguiente puede ser:
             None (aun hay pendientes), 'EN_APROBACION', 'APROBADO', etc.
    """
    tarea = await db.get(Tarea, tarea_id)
    if not tarea or not tarea.activo:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if tarea.usuario_id != user.id:
        raise HTTPException(status_code=403, detail="Esta tarea no te pertenece")
    if tarea.estado != "PENDIENTE":
        raise HTTPException(status_code=409, detail=f"Tarea en estado {tarea.estado}, no se puede completar")

    if firma_password:
        if not await _validar_password(db, user, firma_password):
            await _registrar_firma(db, request, user, "completar_tarea", tarea_id, exitoso=False, motivo="password_invalida")
            raise HTTPException(status_code=401, detail="Password invalida")

    tarea.estado = "COMPLETADO"
    tarea.fecha_completado = datetime.now(timezone.utc)
    await db.flush()

    await _registrar_firma(db, request, user, "completar_tarea", tarea_id)

    await escribir_bitacora(
        db=db, documento_flujo_id=tarea.documento_flujo_id,
        tarea_id=tarea.id, usuario=user, accion="APROBADO",
        estado_origen="PENDIENTE", estado_destino="COMPLETADO",
    )

    await write_audit(db, request, user, accion="COMPLETAR_TAREA",
                      recurso="tarea", recurso_id=tarea.id,
                      descripcion=f"Tarea {tarea.id} completada por {user.username}")

    accion_siguiente = await _verificar_y_avanzar(db, tarea.documento_flujo_id, tarea.tipo_tarea)
    return tarea, accion_siguiente


async def rechazar_tarea(
    db: AsyncSession,
    request: Request,
    user: Usuario,
    tarea_id: int,
    observacion: str,
    firma_password: str,
) -> tuple[Tarea, Optional[str]]:
    """
    Rechaza una tarea con observacion.
    Returns: (tarea, accion_siguiente)
    """
    if len(observacion.strip()) < 10:
        raise HTTPException(status_code=422, detail="La observacion debe tener al menos 10 caracteres")

    tarea = await db.get(Tarea, tarea_id)
    if not tarea or not tarea.activo:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if tarea.usuario_id != user.id:
        raise HTTPException(status_code=403, detail="Esta tarea no te pertenece")
    if tarea.estado != "PENDIENTE":
        raise HTTPException(status_code=409, detail=f"Tarea en estado {tarea.estado}")

    if firma_password:
        if not await _validar_password(db, user, firma_password):
            await _registrar_firma(db, request, user, "rechazar_tarea", tarea_id, exitoso=False, motivo="password_invalida")
            raise HTTPException(status_code=401, detail="Password invalida")

    tarea.estado = "RECHAZADO"
    tarea.fecha_completado = datetime.now(timezone.utc)
    tarea.observacion = observacion.strip()
    await db.flush()

    obs = TareaObservacion(
        tarea_id=tarea.id,
        usuario_id=user.id,
        observacion=observacion.strip(),
    )
    db.add(obs)
    await db.flush()

    await _registrar_firma(db, request, user, "rechazar_tarea", tarea_id)

    await escribir_bitacora(
        db=db, documento_flujo_id=tarea.documento_flujo_id,
        tarea_id=tarea.id, usuario=user, accion="RECHAZADO",
        estado_origen="PENDIENTE", estado_destino="RECHAZADO",
        observacion=observacion.strip(),
    )

    await write_audit(db, request, user, accion="RECHAZAR_TAREA",
                      recurso="tarea", recurso_id=tarea.id,
                      descripcion=f"Tarea {tarea.id} rechazada por {user.username}")

    accion_siguiente = await _verificar_y_avanzar(db, tarea.documento_flujo_id, tarea.tipo_tarea)
    return tarea, accion_siguiente


async def reasignar_tarea(
    db: AsyncSession,
    request: Request,
    user: Usuario,
    tarea_id: int,
    nuevo_usuario_id: int,
    motivo: str,
) -> Tarea:
    """
    Reasigna una tarea a otro usuario.
    Marca la original como REASIGNADA y crea una nueva.
    """
    tarea = await db.get(Tarea, tarea_id)
    if not tarea or not tarea.activo:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if tarea.estado not in ("PENDIENTE",):
        raise HTTPException(status_code=409, detail=f"No se puede reasignar tarea en estado {tarea.estado}")

    tarea.estado = "REASIGNADO"
    tarea.observacion = motivo
    await db.flush()

    nueva_tarea = await crear_tarea(
        db=db,
        documento_flujo_id=tarea.documento_flujo_id,
        usuario_id=nuevo_usuario_id,
        tipo_tarea=tarea.tipo_tarea,
        delegado_origen_id=tarea.usuario_id,
    )

    await escribir_bitacora(
        db=db, documento_flujo_id=tarea.documento_flujo_id,
        tarea_id=tarea.id, usuario=user, accion="REASIGNADO",
        estado_origen="PENDIENTE", estado_destino="REASIGNADO",
        observacion=f"Reasignado {motivo}",
    )

    return nueva_tarea


async def _verificar_y_avanzar(
    db: AsyncSession,
    documento_flujo_id: int,
    tipo_tarea: str,
) -> Optional[str]:
    """
    Verifica si TODAS las tareas de un tipo estan resueltas.
    Si es asi, determina el siguiente paso.
    Returns: None (aun pendientes) o str con la accion (EN_APROBACION, APROBADO, etc.)
    """
    tareas = (await db.execute(
        select(Tarea)
        .where(Tarea.documento_flujo_id == documento_flujo_id)
        .where(Tarea.tipo_tarea == tipo_tarea)
        .where(Tarea.activo == True)
    )).scalars().all()

    pendientes = [t for t in tareas if t.estado == "PENDIENTE"]
    rechazados = [t for t in tareas if t.estado == "RECHAZADO"]

    if pendientes:
        return None

    flujo = await db.get(DocumentoFlujo, documento_flujo_id)
    if not flujo:
        return None

    if rechazados:
        doc = await db.get(Documento, flujo.documento_id)
        if doc:
            doc.estatus = EstatusDocumento.EN_REVISION
        return "EN_CORRECCION"

    if tipo_tarea == TipoTarea.REVISION.value or tipo_tarea == "REVISION":
        doc = await db.get(Documento, flujo.documento_id)
        if doc:
            doc.estatus = EstatusDocumento.APROBADO
        return "EN_APROBACION"

    if tipo_tarea == TipoTarea.APROBACION.value or tipo_tarea == "APROBACION":
        doc = await db.get(Documento, flujo.documento_id)
        if doc:
            doc.estatus = EstatusDocumento.APROBADO
        return "APROBADO"

    return None
