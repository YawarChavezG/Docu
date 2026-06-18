"""
Endpoints de autenticación.

Refactorizado (sesión 3) para usar:
- Tabla `usuarios` real (no más dict hardcoded de 4 usuarios)
- LDAP bind real contra Active Directory (cuando LDAP_ENABLED=true)
- Password de DES: `cofar.2026` (validada contra la BD)
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.usuario import Usuario, EstadoUsuario
from app.models.rol import Rol, CodigoRol
# Sesion 26: Modulo/CodigoModulo ya no se usan en auth.py. La tabla
# usuario_modulos y la relacion fueron eliminadas.
from app.models.gerencia import Gerencia
from app.models.area import Area
from app.services import ad_service
from app.services.area_mapping import match_area_por_ad_info

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Schemas ───

class LoginRequest(BaseModel):
    username: str
    password: str
    # Fuente de autenticacion. "cofar" = contra AD real (default).
    # "local" = contra la BD local (usuarios seeded de test).
    # Si no se manda, se respeta settings.ldap_enabled del server.
    auth_source: str | None = None


class UserModuleOut(BaseModel):
    codigo: str
    nombre: str


class UserRoleOut(BaseModel):
    codigo: str
    nombre: str


class LoginUserOut(BaseModel):
    username: str
    nombre_completo: str
    iniciales: str
    email: str
    cargo: str
    area_id: int | None
    gerencia_sigla: str | None
    area_sigla: str | None
    # Datos crudos del AD (útiles cuando no hay match con tabla areas)
    ad_department: str | None = None
    ad_physical_delivery_office: str | None = None
    estado: str
    ausente: bool
    es_impersonado: bool = False
    es_usuario_ad: bool = False  # Sesion 26: para ProfileModal (AD vs local)
    # Sesion 26: modulos eliminado (era codigo muerto, el ACL del frontend
    # usa solo el rol). Si en el futuro se necesita, se puede volver a
    # agregar via un JOIN con tabla rol_modulos o similar.
    roles: list[str] = []  # códigos de rol


class LoginResponse(BaseModel):
    message: str
    user: LoginUserOut
    csrf_token: str | None = None
    impersonated_by: str | None = None  # username del admin que está impersonando


# ─── Helpers ───

async def _cargar_usuario_por_id(db: AsyncSession, usuario_id: int) -> Usuario | None:
    """
    Carga el usuario por ID + roles + area (con gerencia) en una sola query.
    """
    result = await db.execute(
        select(Usuario)
        .where(Usuario.id == usuario_id)
        .options(
            selectinload(Usuario.roles),
            selectinload(Usuario.area).selectinload(Area.gerencia),
        )
    )
    return result.scalar_one_or_none()


async def _cargar_usuario_completo(db: AsyncSession, username: str) -> Usuario | None:
    """
    Carga el usuario por username + roles + area (con gerencia) en una sola query.
    """
    result = await db.execute(
        select(Usuario)
        .where(Usuario.username == username)
        .options(
            selectinload(Usuario.roles),
            selectinload(Usuario.area).selectinload(Area.gerencia),
        )
    )
    return result.scalar_one_or_none()


def _calcular_iniciales(given_name: str, surname: str) -> str:
    """
    Calcula iniciales: primera letra del givenName + primera letra del sn.
    Regla COFAR: 'Yawar Gonzalo' + 'Chavez Gonzales' -> 'YC'.
    Si faltan datos, devuelve '??'.
    """
    g = (given_name or "").strip()
    s = (surname or "").strip()
    if g and s:
        return (g[0] + s[0]).upper()
    if g:
        return g[:2].upper()
    if s:
        return s[:2].upper()
    return "??"


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Login contra SGD.

    Flujo:
    1. Si LDAP_ENABLED=true: bind contra AD con las credenciales.
    2. Crea/actualiza el Usuario en BD (sync on-demand).
    3. Si LDAP_ENABLED=false (DES): busca el usuario en BD, valida password dummy `cofar.2026`.

    El bind LDAP es la fuente de verdad de la identidad. La BD de SGD es solo
    metadata (rol, módulos, area, estado_delegacion).
    """
    username = payload.username.strip().lower()
    password = payload.password

    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuario y contraseña son obligatorios")

    user = await _cargar_usuario_completo(db, username)
    password_valida = False

    # ─── Modo dual: BD local con pass dummy O LDAP real ───
    # Regla:
    #   1) Si el usuario existe en BD Y pass == "cofar.2026" (o el pass
    #      del admin_local = "admin.2026") → login local OK.
    #   2) Si LDAP_ENABLED=true y paso 1 falló → intentar bind contra AD.
    #      Si el bind funciona → sync on-demand a BD y login OK.
    #   3) Si ninguno → 401.

    # Resolver el modo: prioridad a lo que manda el frontend (auth_source).
    # Si no llega, usamos el setting del server.
    # "local"   -> SIEMPRE validar contra BD local (ignora LDAP).
    # "cofar"   -> SIEMPRE validar contra AD (puede ser cofar_enabled=True o
    #              False, en este ultimo caso da 401 directo).
    # None      -> comportamiento legacy: BD local primero, luego LDAP.
    requested = (payload.auth_source or "").strip().lower()
    if requested not in ("local", "cofar"):
        requested = "auto"

    LOCAL_PASSWORDS = ("cofar.2026", "admin.2026")  # en DES solamente
    is_local_user = user is not None
    is_local_pass_ok = password in LOCAL_PASSWORDS

    # ─── Caso 1: el frontend pidio explicitamente "local" ───
    if requested == "local":
        if is_local_user and is_local_pass_ok:
            password_valida = True
            logger.info(f"Login local OK (forzado): {username}")
        else:
            raise HTTPException(
                status_code=401,
                detail="Credenciales locales inválidas. Usa uno de los 5 usuarios de test (pass 'cofar.2026' o 'admin.2026')."
            )
    # ─── Caso 2: el frontend pidio explicitamente "cofar" ───
    elif requested == "cofar":
        if not settings.ldap_enabled:
            raise HTTPException(
                status_code=503,
                detail="LDAP deshabilitado en este ambiente. Selecciona 'BD Local' en el login."
            )
        ok, error_msg = ad_service.ldap_bind(username, password)
        if not ok:
            raise HTTPException(status_code=401, detail=f"Credenciales inválidas ({error_msg})")
        password_valida = True
        logger.info(f"Login AD OK (forzado): {username}")
    # ─── Caso 3: auto (no se mando auth_source) → BD local primero, sino LDAP ───
    elif is_local_user and is_local_pass_ok:
        password_valida = True
        logger.info(f"Login local OK (auto): {username}")
    elif settings.ldap_enabled:
        ok, error_msg = ad_service.ldap_bind(username, password)
        if not ok:
            logger.warning(f"LDAP bind falló para {username}: {error_msg}")
            raise HTTPException(status_code=401, detail=f"Credenciales inválidas ({error_msg})")
        password_valida = True

        # Si el usuario no existe en BD, crearlo on-the-fly con los
        # atributos reales que acabamos de leer del AD.
        if user is None:
            logger.info(f"Usuario {username} existe en AD pero no en SGD, creando...")
            # Traer atributos del AD (cargo, mail, etc.) usando el service account
            attrs = ad_service.obtener_atributos_usuario_ad(username) or {}
            logger.info(
                f"Atributos AD de {username}: "
                f"displayName={attrs.get('nombre_completo')!r} "
                f"title={attrs.get('title')!r} "
                f"department={attrs.get('department')!r} "
                f"mail={attrs.get('mail')!r}"
            )
            # ad_info guarda el department del AD (gerencia aprox).
            # ad_postal_code guarda el postalCode (codigo SAP si existe).
            ad_info_parts = []
            if attrs.get("department"):
                ad_info_parts.append(attrs["department"])
            if attrs.get("physicalDeliveryOfficeName"):
                ad_info_parts.append(attrs["physicalDeliveryOfficeName"])
            ad_info_combined = " | ".join(ad_info_parts) if ad_info_parts else None

            # Issue 4.4: mapear department del AD a area_id (automatico)
            area_id_login = None
            if ad_info_combined:
                try:
                    area_id_login = await match_area_por_ad_info(db, ad_info_combined)
                except Exception as e_map:
                    logger.warning(f"area_mapping fallo en login on-demand: {e_map}")

            user = Usuario(
                username=username,
                email=attrs.get("mail") or f"{username}@cofar.com",
                nombre_completo=attrs.get("nombre_completo") or username.title(),
                iniciales=_calcular_iniciales(attrs.get("givenName"), attrs.get("sn")),
                cargo=attrs.get("title") or "(sin cargo)",
                azure_oid=attrs.get("objectGUID") or attrs.get("dn") or None,
                ad_info=ad_info_combined,
                ad_postal_code=attrs.get("postalCode") or None,
                ad_last_synced_at=datetime.utcnow(),
                area_id=area_id_login,  # Issue 4.4
                estado=EstadoUsuario.ACTIVO,
                es_usuario_ad=True,  # Sesion 23 / Bloque C2
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            user = await _cargar_usuario_completo(db, username)
        else:
            # Usuario ya existe en BD: refrescar desde AD (sync on-demand)
            attrs = ad_service.obtener_atributos_usuario_ad(username)
            if attrs:
                updated = False
                if attrs.get("mail") and attrs["mail"] != user.email:
                    user.email = attrs["mail"]; updated = True
                if attrs.get("nombre_completo") and attrs["nombre_completo"] != user.nombre_completo:
                    user.nombre_completo = attrs["nombre_completo"]; updated = True
                if attrs.get("title") and attrs["title"] != user.cargo:
                    user.cargo = attrs["title"]; updated = True
                if attrs.get("postalCode") and attrs["postalCode"] != user.ad_postal_code:
                    user.ad_postal_code = attrs["postalCode"]; updated = True
                # Issue 4.4: si llego department nuevo, reintentar area_id mapping
                if attrs.get("department") and attrs["department"] != (user.ad_info or "").split("|")[0].strip():
                    # Actualizar ad_info con department + office
                    office = attrs.get("physicalDeliveryOfficeName") or ""
                    user.ad_info = " | ".join(filter(None, [attrs["department"], office])) or None
                    updated = True
                    try:
                        nueva_area = await match_area_por_ad_info(db, user.ad_info)
                        if nueva_area and nueva_area != user.area_id:
                            user.area_id = nueva_area
                            logger.info(
                                f"area_id actualizado por cambio de department (login on-demand): "
                                f"{username} {user.area_id} -> {nueva_area}"
                            )
                    except Exception as e_map:
                        logger.warning(f"area_mapping fallo en login: {e_map}")
                if updated:
                    user.ad_last_synced_at = datetime.utcnow()
                    await db.commit()
                    await db.refresh(user)
                    logger.info(f"Usuario {username} actualizado desde AD (sync on-demand)")
    else:
        # LDAP deshabilitado, no es usuario local → 401
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not password_valida or user is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if user.estado == EstadoUsuario.DESVINCULADO:
        raise HTTPException(status_code=403, detail="Usuario desvinculado. Contacte al administrador.")

    # ─── Setear cookies HttpOnly ───
    csrf_token = f"dev-csrf-{user.username}-{user.id}"
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, samesite="lax", secure=False, path="/")
    response.set_cookie(key="session", value=f"dev-session-{user.id}", httponly=True, samesite="lax", secure=False, path="/")
    response.set_cookie(key="user_id", value=str(user.id), httponly=True, samesite="lax", secure=False, path="/")

    # ─── Devolver usuario con sus roles (Sesion 26: modulos eliminado, era codigo muerto) ───
    roles_codigos = [r.codigo for r in user.roles] if user.roles else []

    return LoginResponse(
        message="Login exitoso",
        user=LoginUserOut(
            username=user.username,
            nombre_completo=user.nombre_completo,
            iniciales=user.iniciales,
            email=user.email,
            cargo=user.cargo,
            area_id=user.area_id,
            gerencia_sigla=user.area.gerencia.sigla if user.area and user.area.gerencia else None,
            area_sigla=user.area.sigla if user.area else None,
            # ad_info = "department | office" del AD (si existe)
            ad_department=user.ad_info,
            ad_physical_delivery_office=None,
            estado=user.estado.value if hasattr(user.estado, "value") else str(user.estado),
            ausente=user.ausente,
            es_impersonado=False,
            es_usuario_ad=user.es_usuario_ad,  # Sesion 26
            roles=roles_codigos,
        ),
        csrf_token=csrf_token,
    )


@router.post("/logout")
async def logout(response: Response):
    """Limpia cookies de sesión."""
    response.delete_cookie("session", path="/")
    response.delete_cookie("csrf_token", path="/")
    response.delete_cookie("user_id", path="/")
    response.delete_cookie("impersonated_user", path="/")
    return {"message": "Logout exitoso"}


@router.get("/me")
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve el usuario actual. Lee la cookie `user_id` y resuelve contra BD.
    Si está impersonando, devuelve el usuario impersonado y el `impersonated_by`.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        return {
            "authenticated": False,
            "user": None,
        }

    try:
        uid = int(user_id)
    except ValueError:
        return {"authenticated": False, "user": None}

    # Si está impersonando
    impersonated_username = request.cookies.get("impersonated_user")
    if impersonated_username:
        # El user_id de la cookie sigue siendo el ADMIN, pero mostramos el impersonado
        admin = await _cargar_usuario_por_id(db, uid)
        if admin is None:
            return {"authenticated": False, "user": None}
        imp = await _cargar_usuario_completo(db, impersonated_username)
        if imp is None:
            return {
                "authenticated": True,
                "user": None,
                "impersonated_by": admin.username,
                "error": "Usuario impersonado no existe",
            }
        return {
            "authenticated": True,
            "impersonated_by": admin.username,
            "user": LoginUserOut(
                username=imp.username,
                nombre_completo=imp.nombre_completo,
                iniciales=imp.iniciales,
                email=imp.email,
                cargo=imp.cargo,
                area_id=imp.area_id,
                gerencia_sigla=imp.area.gerencia.sigla if imp.area and imp.area.gerencia else None,
                area_sigla=imp.area.sigla if imp.area else None,
                # ad_info = "department | office" del AD (si existe)
                ad_department=imp.ad_info,
                ad_physical_delivery_office=None,
                estado=imp.estado.value if hasattr(imp.estado, "value") else str(imp.estado),
                ausente=imp.ausente,
                es_impersonado=True,
                es_usuario_ad=imp.es_usuario_ad,  # Sesion 26
                roles=[r.codigo for r in imp.roles] if imp.roles else [],
            ),
        }

    # No impersonando: flujo normal
    user = await _cargar_usuario_por_id(db, uid)
    if user is None:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": LoginUserOut(
            username=user.username,
            nombre_completo=user.nombre_completo,
            iniciales=user.iniciales,
            email=user.email,
            cargo=user.cargo,
            area_id=user.area_id,
            gerencia_sigla=user.area.gerencia.sigla if user.area and user.area.gerencia else None,
            area_sigla=user.area.sigla if user.area else None,
            # ad_info = "department | office" del AD (si existe)
            ad_department=user.ad_info,
            ad_physical_delivery_office=None,
            estado=user.estado.value if hasattr(user.estado, "value") else str(user.estado),
            ausente=user.ausente,
            es_impersonado=False,
            es_usuario_ad=user.es_usuario_ad,  # Sesion 26
            roles=[r.codigo for r in user.roles] if user.roles else [],
        ),
    }


@router.post("/verify-password")
async def verify_password(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    2FA simple: re-validar usuario + contraseña.
    Usado para firma digital en US-2.06, 3.03, 3.04, 6.03, 7.03, 7.06.
    NO setea cookies ni cambia sesión.
    Retorna {valid: bool, message: str}
    """
    username = payload.username.strip().lower()
    password = payload.password

    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuario y contraseña son obligatorios")

    user = await _cargar_usuario_completo(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if settings.ldap_enabled:
        ok, _ = ad_service.ldap_bind(username, password)
        if not ok:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
    else:
        if password != "cofar.2026":
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {"valid": True, "username": username, "message": "Contraseña verificada"}


# ─── USUARIOS_DEV_STUB eliminado (ahora se leen de BD) ───
