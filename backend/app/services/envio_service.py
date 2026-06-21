"""
Servicio: envio_service
Logica atomica para "firmar y enviar a liberacion" un documento (US-2.06 / 3.03).

Atomicidad (riesgo R1 del SESION-22-HANDOFF.md § 5):
- Si la BD falla DESPUES de validar el password, NO debe quedar como firmado.
- Patron: una sola transaccion con write_audit + commit al final.
- Si cualquier paso lanza excepcion, el context manager hace rollback total.

El servicio NO maneja auth: el caller (router) ya autentico al usuario
y obtiene su `password` del request body. La validacion del password
se hace contra la BD local (o LDAP si LDAP_ENABLED=true).
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import write_audit
from app.core.config import settings
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo
from app.models.estado import Estado
from app.models.firma_digital import FirmaDigital
from app.models.usuario import Usuario
from app.services import ad_service

logger = logging.getLogger(__name__)


async def validar_password_usuario(
    db: AsyncSession, usuario: Usuario, password: str
) -> bool:
    """
    Valida la password del usuario.

    Logica dual (igual que auth.py):
    - Si la password es "cofar.2026" o "admin.2026" (stubs de DES), aceptar
      inmediatamente. Esto es para que los usuarios sembrados localmente
      (aromero, cecEspinoza, admin, etc.) puedan firmar 2FA en DES aunque
      LDAP_ENABLED=true.
    - Si no, si LDAP_ENABLED=true: intentar bind real contra AD.
    - Si no: rechazar.

    Sesion 23 / Bloque B5: bug preexistente. Antes, validar_password_usuario
    iba directo a LDAP si LDAP_ENABLED=true, lo que rompia la firma 2FA
    en DES para usuarios locales (porque su password real no es la del AD).

    Returns True si la password es valida, False en caso contrario.
    NO lanza excepcion (para que el caller decida como responder).
    """
    # 1) Stubs locales (mismas passwords dummy que auth.py)
    LOCAL_PASSWORDS = ("cofar.2026", "admin.2026")
    if password in LOCAL_PASSWORDS:
        return True
    # 2) Si LDAP esta habilitado, intentar bind real
    if settings.ldap_enabled:
        ok, _ = ad_service.ldap_bind(usuario.username, password)
        return ok
    # 3) LDAP deshabilitado y password no es dummy -> rechazar
    return False


async def enviar_a_liberacion(
    db: AsyncSession,
    request: Request,
    user: Usuario,
    documento_id: int,
    *,
    password: str,
    revisor_ids: list[int],
    aprobador_ids: list[int],
    requiere_evaluacion: bool = False,
    requiere_control_lectura: bool = False,
    alcance_difusion_ids: Optional[list[int]] = None,
    reemplaza_documento_ids: Optional[list[int]] = None,
    justificacion: Optional[str] = None,
    documento_actualizado_id: Optional[int] = None,
) -> tuple[Documento, DocumentoFlujo]:
    """
    Envia un documento a la cola de ETO (estatus EN_ELABORACION -> LIBERACION_ETO).

    R3 item 0.6: tras firmar el wizard, el documento NO va directo a EN_REVISION
    (revisores). Va a LIBERACION_ETO, donde espera que el ETO asignado segun
    la matriz_enrutamiento_eto lo libere. Solo cuando ETO libera (futuro
    endpoint POST /documentos/{id}/liberar, R3 Fase 1) el documento pasa a
    EN_REVISION y se crean las tareas para los revisores.

    Flujo atomico:
    1. Validar password (2FA) - si falla, raise 401, NO persiste nada
    2. Re-leer documento con FOR UPDATE
    3. Validar que esta en EN_ELABORACION
    4. Actualizar DocumentoFlujo con revisores/aprobadores/difusion
    5. Transicionar Documento.estatus a LIBERACION_ETO
    6. Setear metadata de firma (firma_at, firma_ip, firma_user_agent)
    7. write_audit
    8. Commit - si algo falla despues del password, rollback total

    Returns: (documento_actualizado, flujo_actualizado)
    Raises:
        HTTPException 401 si password invalida
        HTTPException 404 si documento no existe
        HTTPException 409 si documento no esta en EN_ELABORACION
    """
    # ─── 1. Validar password PRIMERO (antes de tocar BD) ───
    if not await validar_password_usuario(db, user, password):
        # Loggear el intento fallido en firmas_digitales (auditoria forense)
        try:
            firma_fallida = FirmaDigital(
                usuario_id=user.id,
                accion="enviar_liberacion",
                recurso_tipo="documento",
                recurso_id=documento_id,
                ip=request.client.host if request.client else "",
                user_agent=(request.headers.get("user-agent", "")[:500] or None),
                resultado_exito=False,
                motivo_fallo="password_invalida",
            )
            db.add(firma_fallida)
            await db.commit()
        except Exception as e:
            logger.warning(f"No se pudo registrar firma fallida: {e}")
        # Loggear el intento fallido
        logger.warning(
            "Intento de firma con password invalida: user=%s documento=%s",
            user.username, documento_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password invalida. La firma 2FA no se realizo.",
        )

    # ─── 2. Re-leer documento con SELECT FOR UPDATE (lock pesimista) ───
    # Esto evita que 2 requests paralelos puedan firmar el mismo doc.
    doc_q = (
        select(Documento)
        .where(Documento.id == documento_id)
        .with_for_update()
    )
    doc = (await db.execute(doc_q)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} no encontrado",
        )
    if not doc.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Documento eliminado (borrado logico)",
        )

    # ─── 3. Validar estatus ───
    if doc.estatus != EstatusDocumento.EN_ELABORACION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Solo se pueden enviar documentos en EN_ELABORACION "
                f"(actual: {doc.estatus.value})"
            ),
        )

    # ─── 4. Validar listas (revisores y aprobadores no vacios) ───
    if not revisor_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe especificar al menos 1 revisor",
        )
    if not aprobador_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe especificar al menos 1 aprobador",
        )

    # ─── 5. Buscar estado LIBERACION_ETO (R3 item 0.6) ───
    # En R2 este paso buscaba REVISION/EN_REVISION directamente. Ahora
    # vamos a LIBERACION_ETO primero, y ETO nos lleva a REVISION.
    estado_lib = (await db.execute(
        select(Estado).where(Estado.codigo == "LIBERACION_ETO")
    )).scalars().first()
    if not estado_lib:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Estado LIBERACION_ETO no encontrado en catalogo (ejecutar seed_estados.py?)",
        )

    # ─── 6. Cargar el DocumentoFlujo mas reciente del documento ───
    flujo_q = (
        select(DocumentoFlujo)
        .where(DocumentoFlujo.documento_id == documento_id)
        .where(DocumentoFlujo.activo == True)
        .order_by(DocumentoFlujo.id.desc())
        .limit(1)
    )
    flujo = (await db.execute(flujo_q)).scalar_one_or_none()
    if flujo is None:
        # Esto NO deberia pasar (siempre se crea con el doc), pero por las dudas
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se encontro flujo activo para el documento {documento_id}",
        )

    # ─── 7. Actualizar el flujo con los datos del wizard ───
    flujo.estado_actual_id = estado_lib.id
    flujo.revisor_ids = list(revisor_ids)
    flujo.aprobador_ids = list(aprobador_ids)
    flujo.requiere_evaluacion = requiere_evaluacion
    flujo.requiere_control_lectura = requiere_control_lectura
    flujo.alcance_difusion_ids = list(alcance_difusion_ids or [])
    flujo.reemplaza_documento_ids = list(reemplaza_documento_ids) if reemplaza_documento_ids else None
    flujo.justificacion = justificacion
    # R3 item 0.2: registrar el documento original cuando es actualizacion.
    # Validamos que el doc actualizado exista (si viene) y que sea distinto del nuevo.
    if documento_actualizado_id is not None:
        if documento_actualizado_id == documento_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="documento_actualizado_id no puede ser el mismo que el documento nuevo",
            )
        doc_anterior = await db.get(Documento, documento_actualizado_id)
        if not doc_anterior:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento a actualizar {documento_actualizado_id} no existe",
            )
        flujo.documento_actualizado_id = documento_actualizado_id
    # Metadata de firma (sobreescribimos la firma inicial del POST /documentos
    # con la firma "real" del wizard)
    flujo.firma_usuario_id = user.id
    flujo.firma_at = datetime.now(timezone.utc)
    flujo.firma_ip = request.client.host if request.client else None
    flujo.firma_user_agent = (request.headers.get("user-agent", "")[:500] or None)

    # ─── 8. Transicionar estatus del Documento ───
    # R3 item 0.6: el documento va a LIBERACION_ETO (no a EN_REVISION todavia).
    # El ETO tiene una cola de "Liberaciones Pendientes" en su bandeja.
    # Solo cuando ETO libere (futuro endpoint R3 Fase 1), pasara a EN_REVISION
    # y se crearan las tareas para los revisores.
    doc.estatus = EstatusDocumento.LIBERACION_ETO
    doc.updated_by_id = user.id
    doc.updated_at = datetime.now(timezone.utc)

    # ─── 9. write_audit (no commit, se hara junto con el resto) ───
    await write_audit(
        db, request, user,
        accion="ENVIAR_LIBERACION",
        recurso="documento",
        recurso_id=doc.id,
        descripcion=(
            f"Documento {doc.codigo_completo} enviado a cola de Liberacion ETO "
            f"(revisores={len(revisor_ids)}, aprobadores={len(aprobador_ids)})"
        ),
        detalles={
            "flujo_id": flujo.id,
            "revisor_ids": revisor_ids,
            "aprobador_ids": aprobador_ids,
            "requiere_evaluacion": requiere_evaluacion,
            "requiere_control_lectura": requiere_control_lectura,
            "alcance_difusion_count": len(alcance_difusion_ids or []),
            "estatus_anterior": "EN_ELABORACION",
            "estatus_nuevo": "LIBERACION_ETO",
        },
    )

    # ─── 9b. Registrar firma digital exitosa (Sesion 23 / Bloque B4-B5) ───
    # El modelo firma_digital ya existia pero nunca se usaba. Ahora SI se
    # crea una fila inmutable por cada firma 2FA exitosa.
    firma_ok = FirmaDigital(
        usuario_id=user.id,
        accion="enviar_liberacion",
        recurso_tipo="documento",
        recurso_id=doc.id,
        ip=request.client.host if request.client else "",
        user_agent=(request.headers.get("user-agent", "")[:500] or None),
        resultado_exito=True,
        motivo_fallo=None,
    )
    db.add(firma_ok)

    # ─── 9b. Registrar nodo en timeline (Fase 4) ───
    from app.services.timeline_service import escribir_bitacora
    await escribir_bitacora(
        db=db,
        documento_flujo_id=flujo.id,
        usuario=user,
        accion="CREADO",
        estado_origen="EN_ELABORACION",
        estado_destino="LIBERACION_ETO",
        observacion=f"Documento {doc.codigo_completo} creado por {user.nombre_completo}",
    )

    # ─── 10. Commit atomico (un solo commit para todo) ───
    # Si algo falla despues, SQLAlchemy hace rollback automatico al salir
    # del context manager o al lanzar una excepcion.
    await db.commit()
    await db.refresh(doc)
    await db.refresh(flujo)

    logger.info(
        "Documento %s enviado a cola de Liberacion ETO por user=%s (flujo_id=%s)",
        doc.codigo_completo, user.username, flujo.id,
    )
    return doc, flujo


async def liberar_documento(
    db: AsyncSession,
    request: Request,
    user: Usuario,
    documento_id: int,
    *,
    password: str,
) -> Documento:
    """
    R3 item 0.6 (stub Fase 0): transiciona LIBERACION_ETO -> EN_REVISION.
    ETO llama este endpoint desde su bandeja cuando esta conforme con la
    documentacion. En R3 Fase 1 este servicio ademas creara las tareas
    para los revisores (tabla `tareas` que se crea en Fase 1).

    Por ahora (Fase 0) solo transiciona el estatus y registra audit/firma.
    Las tareas para revisores se crearan en el paso de R3 Fase 1.

    Args:
        password: password del ETO para firma 2FA (auditoria forense).

    Returns:
        Documento actualizado.

    Raises:
        HTTPException 401 si password invalida.
        HTTPException 404 si documento no existe.
        HTTPException 409 si documento no esta en LIBERACION_ETO.
    """
    if not await validar_password_usuario(db, user, password):
        try:
            firma_fallida = FirmaDigital(
                usuario_id=user.id,
                accion="liberar_documento",
                recurso_tipo="documento",
                recurso_id=documento_id,
                ip=request.client.host if request.client else "",
                user_agent=(request.headers.get("user-agent", "")[:500] or None),
                resultado_exito=False,
                motivo_fallo="password_invalida",
            )
            db.add(firma_fallida)
            await db.commit()
        except Exception as e:
            logger.warning(f"No se pudo registrar firma fallida: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password invalida. La firma 2FA no se realizo.",
        )

    doc_q = (
        select(Documento)
        .where(Documento.id == documento_id)
        .with_for_update()
    )
    doc = (await db.execute(doc_q)).scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} no encontrado",
        )
    if doc.estatus != EstatusDocumento.LIBERACION_ETO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Solo se pueden liberar documentos en LIBERACION_ETO "
                f"(actual: {doc.estatus.value})"
            ),
        )

    # Buscar estado REVISION (catalog, no enum del modelo)
    estado_rev = (await db.execute(
        select(Estado).where(Estado.codigo.in_(["REVISION", "EN_REVISION"]))
    )).scalars().first()
    if not estado_rev:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Estado REVISION no encontrado en catalogo",
        )

    # Actualizar DocumentoFlujo.estado_actual_id al estado REVISION
    flujo_q = (
        select(DocumentoFlujo)
        .where(DocumentoFlujo.documento_id == documento_id)
        .where(DocumentoFlujo.activo == True)
        .order_by(DocumentoFlujo.id.desc())
        .limit(1)
    )
    flujo = (await db.execute(flujo_q)).scalar_one_or_none()
    if flujo is not None:
        flujo.estado_actual_id = estado_rev.id

    doc.estatus = EstatusDocumento.EN_REVISION
    doc.updated_by_id = user.id
    doc.updated_at = datetime.now(timezone.utc)

    await write_audit(
        db, request, user,
        accion="LIBERAR_DOCUMENTO",
        recurso="documento",
        recurso_id=doc.id,
        descripcion=f"Documento {doc.codigo_completo} liberado por ETO (pasa a revision)",
        detalles={
            "flujo_id": flujo.id if flujo else None,
            "estatus_anterior": "LIBERACION_ETO",
            "estatus_nuevo": "EN_REVISION",
            "revisor_ids_pendientes_crear_tarea": flujo.revisor_ids if flujo else None,
        },
    )

    firma_ok = FirmaDigital(
        usuario_id=user.id,
        accion="liberar_documento",
        recurso_tipo="documento",
        recurso_id=doc.id,
        ip=request.client.host if request.client else "",
        user_agent=(request.headers.get("user-agent", "")[:500] or None),
        resultado_exito=True,
        motivo_fallo=None,
    )
    db.add(firma_ok)

    # Timeline: ETO libera el documento (Fase 4)
    from app.services.timeline_service import escribir_bitacora
    await escribir_bitacora(
        db=db,
        documento_flujo_id=flujo.id if flujo else 0,
        usuario=user,
        accion="LIBERADO_ETO",
        estado_origen="LIBERACION_ETO",
        estado_destino="EN_REVISION",
        observacion=f"Documento {doc.codigo_completo} liberado por ETO {user.nombre_completo}",
    )

    # Fan-out: crear tareas REVISION por cada revisor (R3 Fase 2)
    from app.services.tarea_service import crear_tarea
    revisores_ids_para_tareas = []
    if flujo and flujo.revisor_ids:
        revisores_ids_para_tareas = flujo.revisor_ids
    for rid in revisores_ids_para_tareas:
        await crear_tarea(
            db=db,
            documento_flujo_id=flujo.id,
            usuario_id=rid,
            tipo_tarea="REVISION",
        )

    await db.commit()
    await db.refresh(doc)

    logger.info(
        "Documento %s liberado por ETO user=%s (estatus=%s)",
        doc.codigo_completo, user.username, doc.estatus.value,
    )
    return doc
