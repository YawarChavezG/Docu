"""
permissions.py — Helpers de autorización compartidos.

Helpers reusables entre los routers de parametrizacion (gerencias, areas,
config-global, feriados, email-templates, matriz-eto, tipos-doc, estados).
Evita duplicar la lectura de cookie + chequeo de rol en cada router.
"""
import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.usuario import Usuario
from app.models.rol import CodigoRol
from app.models.area import Area

logger = logging.getLogger(__name__)


async def get_current_user_from_cookie(
    request: Request, db: AsyncSession
) -> Optional[Usuario]:
    """
    Lee el user_id de la cookie y devuelve el Usuario con roles + area + gerencia.
    Si hay cookie `impersonated_user` (Sesion 23 / Bloque D1), devuelve
    el usuario IMPERSONADO en vez del admin original, para que las
    bandejas/sidebar/etc reflejen al impersonado.

    Devuelve None si no hay cookie o el usuario no existe.

    NOTA: la auditoria (write_audit) sigue recibiendo al admin original
    a traves de get_current_user_admin() cuando se quiere registrar la
    accion como el admin, no como el impersonado.
    """
    user_id_raw = request.cookies.get("user_id")
    if not user_id_raw:
        return None
    try:
        uid = int(user_id_raw)
    except (ValueError, TypeError):
        return None

    # Sesion 23 / Bloque D1: si hay cookie de impersonate, devolver
    # el usuario impersonado (con sus roles, modulos, area) para que
    # el resto de la UI se comporte como si fuera el.
    impersonated_username = request.cookies.get("impersonated_user")
    if impersonated_username:
        result = await db.execute(
            select(Usuario)
            .where(Usuario.username == impersonated_username)
            .options(
                selectinload(Usuario.roles),
                selectinload(Usuario.area).selectinload(Area.gerencia),
            )
        )
        imp = result.scalar_one_or_none()
        if imp is not None:
            return imp
        # Si el impersonado no existe, caer al admin original

    return (await db.execute(
        select(Usuario)
        .where(Usuario.id == uid)
        .options(
            selectinload(Usuario.roles),
            selectinload(Usuario.area).selectinload(Area.gerencia),
        )
    )).scalar_one_or_none()


def _user_has_any_role(user: Usuario, role_codes: list[str]) -> bool:
    """True si el usuario tiene AL MENOS uno de los role_codes."""
    if not user or not user.roles:
        return False
    user_codes = {r.codigo for r in user.roles}
    return any(rc in user_codes for rc in role_codes)


async def require_authenticated(request: Request, db: AsyncSession) -> Usuario:
    """
    Verifica que haya sesion activa. 401 si no.
    """
    user = await get_current_user_from_cookie(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Inicia sesion.",
        )
    return user


async def require_eto_or_admin(request: Request, db: AsyncSession) -> Usuario:
    """
    Verifica que el usuario este autenticado Y tenga rol ETO o ADMIN.
    ETO es el rol primario de parametrizacion (US-9.0x del PDF oficial).
    401 si no hay sesion, 403 si el rol no es valido.
    """
    user = await require_authenticated(request, db)
    if not _user_has_any_role(user, [CodigoRol.ETO, CodigoRol.ADMIN]):
        codes = ", ".join(r.codigo for r in user.roles) or "ninguno"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Esta operacion requiere rol ETO o ADMIN "
                f"(tu rol: {codes})"
            ),
        )
    return user


async def require_admin(request: Request, db: AsyncSession) -> Usuario:
    """Verifica que el usuario sea ADMIN. 401/403 segun corresponda."""
    user = await require_authenticated(request, db)
    if not _user_has_any_role(user, [CodigoRol.ADMIN]):
        codes = ", ".join(r.codigo for r in user.roles) or "ninguno"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Esta operacion requiere rol ADMIN (tu rol: {codes})",
        )
    return user


async def require_eto_admin_o_rol_delegable(request: Request, db: AsyncSession) -> Usuario:
    """
    Similar a require_eto_or_admin, pero tambien permite usuarios cuyo rol
    tenga requiere_delegado=True (ej: ELABORADOR - REVISOR).
    Necesario para que Elaboradores/Revisores puedan elegir delegado en Mi Perfil.
    """
    user = await require_authenticated(request, db)
    if _user_has_any_role(user, [CodigoRol.ETO, CodigoRol.ADMIN]):
        return user
    for r in user.roles:
        if r.requiere_delegado:
            return user
    codes = ", ".join(r.codigo for r in user.roles) or "ninguno"
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            f"Esta operacion requiere rol ETO, ADMIN o un rol que requiera delegado "
            f"(tu rol: {codes})"
        ),
    )
