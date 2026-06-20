"""
Servicio de sincronizacion de usuarios desde Active Directory (AD).

Sesion 33 (deploy v1.1.0-qas): extrae la logica del endpoint
POST /api/v1/usuarios/sync-ad para que pueda reutilizarse desde
la Celery task `app.workers.tasks.sincronizar_ad` (cron cada 6h).

Modulo DRY: el endpoint y la Celery task llaman a `sincronizar_ad_async()`.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.area import Area
from app.models.usuario import EstadoUsuario, Usuario
from app.services import ad_service
from app.services.area_mapping import match_area_por_ad_info

logger = logging.getLogger(__name__)


# Limites REALES del modelo Usuario (ver app/models/usuario.py).
# Si el AD trae algo mas largo, se trunca a estos limites.
_LIMITS = {
    "username": 50,
    "azure_oid": 100,
    "email": 150,
    "nombre_completo": 200,
    "iniciales": 5,
    "cargo": 100,
    "ad_info": 2000,
    "ad_postal_code": 50,
}


def _truncar(s, max_len: int) -> Optional[str]:
    """Truncar string a max_len chars, cuidando None."""
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    if len(s) > max_len:
        logger.warning(f"Truncando campo de {len(s)} a {max_len} chars: {s[:60]}...")
        return s[:max_len]
    return s


async def sincronizar_ad_async(
    db: AsyncSession,
    max_results: int = 5000,
    write_audit_callback=None,
) -> dict:
    """
    Sincroniza usuarios desde el AD real de COFAR a la BD local.

    Args:
        db: sesion async de SQLAlchemy
        max_results: tamano maximo de pagina LDAP (default 5000, igual que
            el endpoint /sync-ad)
        write_audit_callback: opcional, funcion async (db, accion, recurso,
            recurso_id, detalles) para registrar en audit_log. Si None, no
            se audita (util para el cron automatico).

    Returns:
        dict con metricas: total_ad, creados, actualizados, sin_cambios,
        excluidos, errores, desvinculados, duracion_seg, warnings.

    Raises:
        RuntimeError: si LDAP_ENABLED=false. El caller decide si
            continua con warning o aborta.
    """
    if not settings.ldap_enabled:
        raise RuntimeError("LDAP deshabilitado en configuracion")

    # Importacion local para evitar import circular
    from app.api.v1.auth import _calcular_iniciales

    t0 = datetime.utcnow()
    result = ad_service.ldap_search_users(query=None, page=1, page_size=max_results)
    ad_users = result["items"]
    excluded_count = max_results - len(ad_users)
    warnings = result.get("warnings", [])

    # Set de sAMAccountNames que SI estan en el AD (despues de filtros de n8n)
    sams_en_ad = set()
    for ad_user in ad_users:
        sam = ad_user.get("sAMAccountName")
        if sam and not sam.endswith("$"):
            sams_en_ad.add(sam.lower())

    creados = 0
    actualizados = 0
    sin_cambios = 0
    errores = 0
    excluidos_por_filtro = 0
    for ad_user in ad_users:
        try:
            sam = ad_user.get("sAMAccountName")
            if not sam:
                errores += 1
                continue

            # ─── Filtros adicionales (los de n8n) ───
            # 1) Saltar cuentas de equipo (terminan en $)
            if sam.endswith("$"):
                excluidos_por_filtro += 1
                continue
            # 2) Saltar cuentas con objectClass sin 'user' (equipos, grupos, etc.)
            oc = ad_user.get("objectClass")
            if oc:
                if isinstance(oc, list):
                    oc = " ".join(oc).lower()
                else:
                    oc = str(oc).lower()
                if "user" not in oc or "person" not in oc:
                    excluidos_por_filtro += 1
                    continue
            # 3) sAMAccountType: solo SAM_NORMAL_USER_ACCOUNT (805306368 = 0x30000000)
            sam_type = ad_user.get("sAMAccountType")
            if sam_type is not None:
                if isinstance(sam_type, list):
                    sam_type = sam_type[0] if sam_type else None
                if str(sam_type) != "805306368":
                    excluidos_por_filtro += 1
                    continue

            existing = (await db.execute(
                select(Usuario).where(Usuario.username == sam)
            )).scalar_one_or_none()

            # Truncar campos al limite REAL del modelo (varchar(N))
            nc = _truncar(ad_user.get("nombre_completo") or sam.title(), _LIMITS["nombre_completo"])
            cargo = _truncar(ad_user.get("title") or "(sin cargo)", _LIMITS["cargo"])
            email = _truncar(ad_user.get("mail") or f"{sam}@cofar.com", _LIMITS["email"])
            ad_info = _truncar(ad_user.get("department"), _LIMITS["ad_info"])
            postal = _truncar(ad_user.get("postalCode"), _LIMITS["ad_postal_code"])
            given = ad_user.get("givenName") or ""
            sn = ad_user.get("sn") or ""
            iniciales = _truncar(_calcular_iniciales(given, sn), _LIMITS["iniciales"])
            sam_trunc = _truncar(sam, _LIMITS["username"])

            if existing is None:
                # Issue 4.4: si el AD trae department, intentar mapear a area_id
                area_id_mapeado = None
                if ad_info:
                    try:
                        area_id_mapeado = await match_area_por_ad_info(db, ad_info)
                    except Exception as e_map:
                        logger.warning(f"area_mapping fallo para {sam}: {e_map}")

                user = Usuario(
                    username=sam_trunc,
                    email=email,
                    nombre_completo=nc or sam_trunc,
                    iniciales=iniciales or "?",
                    cargo=cargo or "(sin cargo)",
                    azure_oid=None,
                    ad_info=ad_info,
                    ad_postal_code=postal,
                    ad_last_synced_at=datetime.utcnow(),
                    area_id=area_id_mapeado,
                    estado=EstadoUsuario.ACTIVO,
                    # No seteamos estado_delegacion aqui: el seed lo hace
                    # con el rol real (rol_codigo). Para stubs sin rol, NA.
                    es_usuario_ad=True,
                )
                db.add(user)
                creados += 1
            else:
                # Sesion 23 / Bloque C1: si el usuario estaba DESVINCULADO
                # y vuelve a aparecer en el AD, reactivarlo.
                if existing.estado == EstadoUsuario.DESVINCULADO:
                    existing.estado = EstadoUsuario.ACTIVO
                changed = False
                if email and existing.email != email:
                    existing.email = email; changed = True
                if nc and existing.nombre_completo != nc:
                    existing.nombre_completo = nc; changed = True
                if cargo and existing.cargo != cargo:
                    existing.cargo = cargo; changed = True
                if iniciales and existing.iniciales != iniciales:
                    existing.iniciales = iniciales; changed = True
                if postal and existing.ad_postal_code != postal:
                    existing.ad_postal_code = postal; changed = True
                if ad_info and existing.ad_info != ad_info:
                    existing.ad_info = ad_info; changed = True
                    # Issue 4.4: si el department del AD cambio,
                    # reintentar el mapping a area_id.
                    try:
                        nueva_area = await match_area_por_ad_info(db, ad_info)
                        if nueva_area and nueva_area != existing.area_id:
                            existing.area_id = nueva_area
                            changed = True
                            logger.info(
                                f"area_id actualizado por cambio de department: "
                                f"{sam} {existing.area_id} -> {nueva_area}"
                            )
                    except Exception as e_map:
                        logger.warning(f"area_mapping fallo para {sam}: {e_map}")
                if changed:
                    existing.ad_last_synced_at = datetime.utcnow()
                    actualizados += 1
                else:
                    sin_cambios += 1

            # Flush por usuario: si uno falla por longitud/unique/etc,
            # hace rollback SOLO de ese y sigue con el siguiente.
            try:
                await db.flush()
            except Exception as e_flush:
                await db.rollback()
                logger.warning(
                    f"Error insertando/actualizando {sam}: {str(e_flush)[:200]}. "
                    f"Continuando con el siguiente."
                )
                errores += 1
                if existing is None:
                    creados -= 1
                elif changed:
                    actualizados -= 1
                else:
                    sin_cambios -= 1
                continue
        except Exception as e:
            sam_log = ad_user.get("sAMAccountName", "?")
            logger.warning(f"Error procesando usuario AD {sam_log}: {e}")
            errores += 1
            await db.rollback()

    # ─── Sesion 23 / Bloque C1: marcar como desvinculados a los que NO
    # aparecen en el AD pero SI estaban en la BD con codigo SAP.
    desvinculados = 0
    bd_con_sap = (await db.execute(
        select(Usuario).where(
            Usuario.ad_postal_code.isnot(None),
            Usuario.estado.in_([EstadoUsuario.ACTIVO, EstadoUsuario.INACTIVO]),
        )
    )).scalars().all()
    for u in bd_con_sap:
        if u.username.lower() not in sams_en_ad:
            u.estado = EstadoUsuario.DESVINCULADO
            u.ad_last_synced_at = datetime.utcnow()
            desvinculados += 1
            logger.info(
                f"Sync AD: usuario {u.username} (id={u.id}, SAP={u.ad_postal_code}) "
                f"marcado como DESVINCULADO (no aparece en AD actual)"
            )

    await db.commit()
    duracion = (datetime.utcnow() - t0).total_seconds()
    logger.info(
        f"Sync AD: {len(ad_users)} del AD, {creados} creados, {actualizados} actualizados, "
        f"{sin_cambios} sin cambios, {excluidos_por_filtro} excluidos por filtro, "
        f"{errores} errores, {desvinculados} desvinculados, {duracion:.1f}s"
    )

    # Audit log opcional (solo lo usa el endpoint, no el cron automatico)
    if write_audit_callback is not None:
        try:
            await write_audit_callback(
                accion="SYNC_AD",
                recurso="usuarios",
                detalles={
                    "total_ad": len(ad_users),
                    "creados": creados,
                    "actualizados": actualizados,
                    "sin_cambios": sin_cambios,
                    "excluidos_por_filtro": excluidos_por_filtro,
                    "errores": errores,
                    "desvinculados": desvinculados,
                    "duracion_seg": round(duracion, 1),
                },
            )
        except Exception as e_audit:
            logger.warning(f"audit_log fallo: {e_audit}")

    return {
        "total_ad": len(ad_users),
        "creados": creados,
        "actualizados": actualizados,
        "sin_cambios": sin_cambios,
        "excluidos": excluded_count,
        "errores": errores,
        "desvinculados": desvinculados,
        "duracion_seg": duracion,
        "warnings": warnings,
    }
