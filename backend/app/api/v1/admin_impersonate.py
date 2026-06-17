"""
Endpoints de impersonate (rol ADMIN o ETO).

Flujo:
1. Admin/ETO hace login normal (con su cuenta real, sea del AD o stub en DES).
2. Admin/ETO accede a `GET /api/v1/admin/impersonate/list?query=...` y ve los usuarios
   reales de COFAR (filtrados por los 17 CNs excluidos + el resto de filtros).
3. Admin/ETO hace `POST /api/v1/admin/impersonate/start` con el sAMAccountName elegido.
4. El backend crea una cookie `impersonated_user` y mantiene la cookie `user_id`
   apuntando al ADMIN/ETO.
5. Todas las requests siguientes del frontend incluyen esta cookie; el backend
   sabe que debe "ser" el usuario impersonado.
6. Admin/ETO hace `POST /api/v1/admin/impersonate/stop` para volver a su sesión.

El usuario impersonado es un dict "virtual" (no se persiste en BD). Solo
existe durante la sesión con la cookie activa.

Sesion 17: ademas de ADMIN, ETO puede impersonar. Ambos eventos (start y
stop) se loguean en `audit_log` con `recurso='impersonate'` y
`accion='IMPERSONATE_START'/'IMPERSONATE_STOP'`.
"""
import logging

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.core.audit import write_audit
from app.models.usuario import Usuario
from app.models.rol import CodigoRol
from app.models.area import Area
from app.models.gerencia import Gerencia
from app.services.impersonate_service import (
    buscar_usuarios_ad,
    obtener_usuario_ad,
    construir_usuario_virtual_para_impersonate,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/impersonate", tags=["Impersonate"])


# ─── Roles permitidos ───

ROLES_PERMITIDOS_IMPERSONATE = {CodigoRol.ADMIN, CodigoRol.ETO}


def _user_can_impersonate(user: Usuario) -> bool:
    """True si el user tiene rol ADMIN o ETO (sesion 17: ambos permitidos)."""
    return any(r.codigo in ROLES_PERMITIDOS_IMPERSONATE for r in user.roles)


# ─── Schemas ───

class ImpersonateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[dict]
    warnings: list[str] = []


class ImpersonateStartRequest(BaseModel):
    sAMAccountName: str


class ImpersonateUserOut(BaseModel):
    username: str
    email: str
    nombre_completo: str
    iniciales: str
    cargo: str
    gerencia_sigla: str | None = None
    area_sigla: str | None = None
    es_impersonado: bool = True
    ad_dn: str = ""
    ad_info: str = ""
    ad_postal_code: str = ""
    ad_tiene_codigo_sap: bool = False
    ad_warning: str = ""
    modulos: list[str] = []
    roles: list[str] = []


class ImpersonateStartResponse(BaseModel):
    message: str
    user: ImpersonateUserOut
    impersonated_by: str


# ─── Helpers ───

async def _get_current_user_from_cookie(request: Request, db: AsyncSession) -> Usuario | None:
    """Lee user_id de la cookie y devuelve el Usuario (con roles)."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        uid = int(user_id)
    except ValueError:
        return None
    result = await db.execute(
        select(Usuario)
        .where(Usuario.id == uid)
        .options(selectinload(Usuario.roles), selectinload(Usuario.modulos))
    )
    return result.scalar_one_or_none()


# ─── Endpoints ───

@router.get("/list", response_model=ImpersonateListResponse)
async def list_users(
    request: Request,
    query: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Lista usuarios reales de COFAR desde AD (filtrados).
    Accesible para rol ADMIN o ETO (sesion 17).
    """
    current = await _get_current_user_from_cookie(request, db)
    if current is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not _user_can_impersonate(current):
        raise HTTPException(
            status_code=403,
            detail="Solo ADMIN o ETO pueden listar usuarios de AD",
        )

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 200:
        page_size = 50

    result = buscar_usuarios_ad(query=query, page=page, page_size=page_size)
    return ImpersonateListResponse(**result)


@router.post("/start", response_model=ImpersonateStartResponse)
async def start_impersonate(
    payload: ImpersonateStartRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Inicia impersonate del sAMAccountName dado. ADMIN o ETO.
    Setea cookie `impersonated_user` (no-HttpOnly para que el frontend la lea).
    Loguea el evento en audit_log (recurso='impersonate', accion='IMPERSONATE_START').
    """
    current = await _get_current_user_from_cookie(request, db)
    if current is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not _user_can_impersonate(current):
        raise HTTPException(
            status_code=403,
            detail="Solo ADMIN o ETO pueden impersonar",
        )

    sam = payload.sAMAccountName.strip()
    if not sam:
        raise HTTPException(status_code=400, detail="sAMAccountName es obligatorio")

    # Sesion 17: no se puede impersonar a si mismo
    if sam.lower() == current.username.lower():
        raise HTTPException(
            status_code=422,
            detail="No puede impersonarse a si mismo",
        )

    # Sesion 17: si ya esta impersonando, no puede iniciar otro sin antes
    # terminar el actual (evita confusion sobre quien es "el admin real").
    existing_imp = request.cookies.get("impersonated_user")
    if existing_imp:
        raise HTTPException(
            status_code=409,
            detail=f"Ya esta impersonando a '{existing_imp}'. Termine primero con /stop.",
        )

    ad_user = None

    # Sesion 23 / Bloque D1: buscar primero en AD (si LDAP_ENABLED), y
    # si no se encuentra, hacer fallback a la BD local. Esto permite
    # impersonar a usuarios sembrados como stubs de DES (aromero,
    # cecEspinoza, visualizador, etc.) aunque LDAP_ENABLED=true.
    if settings.ldap_enabled:
        try:
            ad_user = obtener_usuario_ad(sam)
        except UserNotFoundError:
            # Fallback a BD local (Sesion 23)
            ad_user = None

    if ad_user is None:
        # Buscar en BD local (incluye stubs de DES y usuarios creados por sync-ad)
        from app.models.usuario import Usuario
        result = await db.execute(
            select(Usuario)
            .where(Usuario.username == sam)
            .options(selectinload(Usuario.area).selectinload(Area.gerencia))
        )
        bd_user = result.scalar_one_or_none()
        if bd_user is None:
            raise HTTPException(
                status_code=404,
                detail=f"Usuario '{sam}' no encontrado en AD ni en BD local",
            )
        # Convertir el Usuario de BD en un dict "tipo AD" para reutilizar
        # construir_usuario_virtual_para_impersonate.
        ad_user = {
            "dn": f"CN={bd_user.nombre_completo},OU=Usuarios,DC=cofar,DC=com",
            "sAMAccountName": bd_user.username,
            "givenName": bd_user.nombre_completo.split()[0] if bd_user.nombre_completo else bd_user.username,
            "sn": " ".join(bd_user.nombre_completo.split()[1:]) if bd_user.nombre_completo else "",
            "nombre_completo": bd_user.nombre_completo,
            "mail": bd_user.email,
            "title": bd_user.cargo,
            "department": bd_user.area.gerencia.nombre if bd_user.area and bd_user.area.gerencia else "",
            "physicalDeliveryOfficeName": bd_user.area.nombre if bd_user.area else "",
            "telephoneNumber": "",
            "mobile": "",
            "postalCode": bd_user.ad_postal_code or "",
            "company": "COFAR SRL",
            "info": bd_user.ad_info or "",
            "userAccountControl": "512",  # activo
            "tiene_codigo_sap": bool(bd_user.ad_postal_code),
        }
        if not ad_user["tiene_codigo_sap"]:
            ad_user["warning"] = "⚠️ Usuario de BD sin código SAP (postalCode vacío)"

    virtual = construir_usuario_virtual_para_impersonate(ad_user)

    # Setear cookie de impersonate (NO HttpOnly para que el frontend JS la lea)
    response.set_cookie(
        key="impersonated_user",
        value=sam,
        httponly=False,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 60 * 8,  # 8 horas
    )

    # ─── Audit log (recurso='impersonate', accion='IMPERSONATE_START') ───
    await write_audit(
        db, request, current,
        accion="IMPERSONATE_START",
        recurso="impersonate",
        recurso_id=None,
        descripcion=(
            f"Impersonate iniciado: {current.username} -> {sam} "
            f"({ad_user.get('nombre_completo', sam)})"
        ),
        detalles={
            "impersonado_username": sam,
            "impersonado_nombre": ad_user.get("nombre_completo", sam),
            "admin_username": current.username,
            "admin_roles": [r.codigo for r in current.roles],
            "modo": "AD" if settings.ldap_enabled else "BD",
        },
    )
    await db.commit()

    return ImpersonateStartResponse(
        message=f"Impersonando a {ad_user['nombre_completo']} ({sam})",
        user=ImpersonateUserOut(**virtual),
        impersonated_by=current.username,
    )


@router.post("/stop")
async def stop_impersonate(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Sale del modo impersonate. Borra la cookie.
    Loguea el evento en audit_log (recurso='impersonate', accion='IMPERSONATE_STOP').
    No-op si no hay cookie activa (no loguea para evitar entradas huerfanas).
    """
    current = await _get_current_user_from_cookie(request, db)
    if current is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not _user_can_impersonate(current):
        raise HTTPException(
            status_code=403,
            detail="Solo ADMIN o ETO pueden terminar un impersonate",
        )

    previous = request.cookies.get("impersonated_user")
    response.delete_cookie("impersonated_user", path="/")

    if previous:
        # ─── Audit log (recurso='impersonate', accion='IMPERSONATE_STOP') ───
        await write_audit(
            db, request, current,
            accion="IMPERSONATE_STOP",
            recurso="impersonate",
            recurso_id=None,
            descripcion=(
                f"Impersonate terminado: {current.username} salio de {previous}"
            ),
            detalles={
                "impersonado_username": previous,
                "admin_username": current.username,
                "admin_roles": [r.codigo for r in current.roles],
            },
        )
        await db.commit()
    else:
        logger.info(f"stop_impersonate no-op: {current.username} no estaba impersonando")

    return {
        "message": (
            f"Impersonate finalizado. Volvio a su sesion original como {current.username}."
        ),
        "previous_impersonated": previous,
    }
