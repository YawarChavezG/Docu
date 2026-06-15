"""
Endpoints de impersonate (solo para rol ADMIN).

Flujo:
1. Admin hace login normal (con su cuenta real, sea del AD o stub en DES).
2. Admin accede a `GET /api/v1/admin/impersonate/list?query=...` y ve los usuarios
   reales de COFAR (filtrados por los 17 CNs excluidos + el resto de filtros).
3. Admin hace `POST /api/v1/admin/impersonate/start` con el sAMAccountName elegido.
4. El backend crea una cookie `impersonated_user` y mantiene la cookie `user_id`
   apuntando al ADMIN.
5. Todas las requests siguientes del frontend incluyen esta cookie; el backend
   sabe que debe "ser" el usuario impersonado.
6. Admin hace `POST /api/v1/admin/impersonate/stop` para volver a su sesión.

El usuario impersonado es un dict "virtual" (no se persiste en BD). Solo
existe durante la sesión con la cookie activa.
"""
import logging

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.usuario import Usuario
from app.models.rol import CodigoRol
from app.models.area import Area
from app.models.gerencia import Gerencia
from app.services.impersonate_service import (
    buscar_usuarios_ad,
    obtener_usuario_ad,
    construir_usuario_virtual_para_impersonate,
    validar_que_es_admin,
    UserNotFoundError,
    NoEsAdminError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/impersonate", tags=["Impersonate"])


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
    Solo accesible para rol ADMIN.
    """
    current = await _get_current_user_from_cookie(request, db)
    if current is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not any(r.codigo == CodigoRol.ADMIN for r in current.roles):
        raise HTTPException(status_code=403, detail="Solo ADMIN puede listar usuarios de AD")

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
    Inicia impersonate del sAMAccountName dado. Solo ADMIN.
    Setea cookie `impersonated_user` (no-HttpOnly para que el frontend la lea).
    """
    current = await _get_current_user_from_cookie(request, db)
    if current is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    if not any(r.codigo == CodigoRol.ADMIN for r in current.roles):
        raise HTTPException(status_code=403, detail="Solo ADMIN puede impersonar")

    sam = payload.sAMAccountName.strip()
    if not sam:
        raise HTTPException(status_code=400, detail="sAMAccountName es obligatorio")

    ad_user = None

    # Modo QAS/PRD: AD real
    if settings.ldap_enabled:
        try:
            ad_user = obtener_usuario_ad(sam)
        except UserNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        # Modo DES: fallback al usuario en BD (los 4 stub seeded)
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
                detail=f"Usuario '{sam}' no encontrado en BD ni en AD (modo DES usa BD)",
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

    return ImpersonateStartResponse(
        message=f"Impersonando a {ad_user['nombre_completo']} ({sam})",
        user=ImpersonateUserOut(**virtual),
        impersonated_by=current.username,
    )


@router.post("/stop")
async def stop_impersonate(response: Response):
    """Sale del modo impersonate. Borra la cookie."""
    response.delete_cookie("impersonated_user", path="/")
    return {"message": "Impersonate finalizado. Volvió a su sesión original."}
