"""
audit.py — Helper para escribir entradas de AuditLog desde los routers.

Uso tipico en un endpoint POST/PATCH/DELETE:

    from app.core.audit import write_audit
    from app.core.dependencies import get_db

    @router.post("/gerencias")
    async def crear_gerencia(
        body: GerenciaCreate,
        request: Request,
        user: Usuario = Depends(require_eto_or_admin),
        db: AsyncSession = Depends(get_db),
    ):
        nueva = Gerencia(...)
        db.add(nueva)
        await db.commit()
        await db.refresh(nueva)

        await write_audit(
            db, request, user,
            accion="CREATE",
            recurso="gerencia",
            recurso_id=nueva.id,
            descripcion=f"Gerencia {nueva.sigla} creada",
            detalles={"despues": {"sigla": nueva.sigla, "nombre": nueva.nombre}},
        )
        return nueva
"""
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)


def _client_ip(request: Optional[Request]) -> Optional[str]:
    """Extrae la IP del cliente. Prioriza X-Forwarded-For (Nginx/proxy) y fallback a client.host."""
    if request is None or request.client is None:
        return None
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Primer IP de la lista = cliente original
        return xff.split(",")[0].strip()
    return request.client.host


def _user_agent(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    return request.headers.get("user-agent")


async def write_audit(
    db: AsyncSession,
    request: Optional[Request],
    user: Optional[Usuario],
    *,
    accion: str,
    recurso: str,
    recurso_id: Optional[int] = None,
    descripcion: Optional[str] = None,
    detalles: Optional[dict[str, Any]] = None,
    exitoso: bool = True,
    error_msg: Optional[str] = None,
) -> AuditLog:
    """
    Crea una entrada de AuditLog. NO hace commit: el caller debe hacer
    commit de su propia transaccion (asi el audit es atomico con la accion).

    Si la insercion falla, solo loggea WARNING y NO propaga la excepcion
    (para no enmascarar el resultado real de la operacion).

    Sesion 23 / Bloque D1: si el request tiene cookie `impersonated_user` y
    el `user` que llega es ESE usuario (no el admin original), se agrega
    `impersonated_by: <username_admin>` al campo `detalles` para preservar
    la trazabilidad de quien REALMENTE realizo la accion.
    """
    # Detectar impersonate activo (Sesion 23 / Bloque D1)
    if request is not None and user is not None:
        impersonated_cookie = request.cookies.get("impersonated_user")
        if impersonated_cookie and user.username == impersonated_cookie:
            user_id_raw = request.cookies.get("user_id")
            if user_id_raw:
                try:
                    admin_id = int(user_id_raw)
                    admin = (await db.execute(
                        select(Usuario).where(Usuario.id == admin_id)
                    )).scalar_one_or_none()
                    if admin is not None and admin.id != user.id:
                        # Agregar trazabilidad al campo detalles
                        detalles = dict(detalles or {})
                        detalles["impersonated_by"] = admin.username
                        detalles["impersonated_by_id"] = admin.id
                except (ValueError, TypeError):
                    pass

    entry = AuditLog(
        usuario_id=user.id if user else None,
        usuario_username=user.username if user else None,
        usuario_nombre=user.nombre_completo if user else None,
        accion=accion.upper() if accion else "UNKNOWN",
        recurso=recurso,
        recurso_id=recurso_id,
        descripcion=descripcion,
        detalles=detalles,
        ip=_client_ip(request),
        user_agent=_user_agent(request),
        exitoso=exitoso,
        error_msg=error_msg,
    )
    try:
        db.add(entry)
        await db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo escribir entrada de audit (%s %s): %s", accion, recurso, exc)
        await db.rollback()
    return entry
