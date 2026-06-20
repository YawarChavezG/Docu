"""
Servicio de impersonate.

Permite a un ADMIN logueado "ser" otro usuario de AD para hacer pruebas.
NO modifica el AD ni la sesión LDAP real. Solo crea un override
en la sesión del SGD.
"""
import logging
from typing import Optional, Tuple

from app.services import ad_service
from app.models.rol import CodigoRol

logger = logging.getLogger(__name__)


# ─── Errores custom ───

class ImpersonateError(Exception):
    """Error genérico de impersonate."""
    pass


class UserNotFoundError(ImpersonateError):
    """El usuario de AD no existe o no pasó los filtros."""
    pass


class NoEsAdminError(ImpersonateError):
    """El usuario autenticado no es ADMIN."""
    pass


# ─── Lógica ───

def buscar_usuarios_ad(
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Wrapper sobre ad_service.ldap_search_users con manejo de errores.
    """
    return ad_service.ldap_search_users(query=query, page=page, page_size=page_size)


def obtener_usuario_ad(sam: str) -> dict:
    """
    Wrapper sobre ad_service.ldap_get_user_by_samaccountname.
    Lanza UserNotFoundError si no existe.
    """
    user = ad_service.ldap_get_user_by_samaccountname(sam)
    if user is None:
        raise UserNotFoundError(f"Usuario '{sam}' no encontrado en AD o excluido por filtros")
    return user


def construir_usuario_virtual_para_impersonate(ad_user: dict) -> dict:
    """
    Convierte un dict de usuario AD en un dict "usuario virtual"
    que el sistema SGD puede usar para impersonate.

    NO se persiste en la BD. Solo se devuelve al frontend.
    """
    return {
        # Identidad
        "username": ad_user["sAMAccountName"],
        "email": ad_user["mail"],
        "nombre_completo": ad_user["nombre_completo"],
        "iniciales": _calcular_iniciales(ad_user["nombre_completo"]),
        "cargo": ad_user["title"],
        "azure_oid": None,  # No se persiste; no tiene guid real
        "area_id": None,
        "estado": "activo",
        "ausente": False,
        "delegado_id": None,
        "estado_delegacion": "na",
        "requiere_delegado": False,
        "visualiza_reportes": False,
        # Por defecto, el usuario impersonado NO tiene módulos.
        # Solo porque la US-2.06 dice que los módulos son exclusivos de SGD.
        # Si en el futuro queremos inferirlos, se hara aqui.
        "modulos": [],
        "roles": [],
        # Metadata de impersonate
        "es_impersonado": True,
        "ad_dn": ad_user.get("dn", ""),
        "ad_info": ad_user.get("info", ""),
        "ad_postal_code": ad_user.get("postalCode", ""),
        "ad_tiene_codigo_sap": ad_user.get("tiene_codigo_sap", False),
        "ad_warning": ad_user.get("warning", ""),
    }


def _calcular_iniciales(nombre_completo: str) -> str:
    """De 'Juan Carlos Perez Vargas' → 'JPV'."""
    if not nombre_completo:
        return "??"
    partes = nombre_completo.split()
    if len(partes) >= 2:
        # Primera letra del primer nombre + primera letra del primer apellido
        return (partes[0][0] + partes[-2][0]).upper()
    elif len(partes) == 1:
        return partes[0][:2].upper()
    return "??"


def validar_que_es_admin(roles: list) -> None:
    """
    Valida que el usuario autenticado tenga rol ADMIN.
    Lanza NoEsAdminError si no.
    """
    if CodigoRol.ADMIN not in roles:
        raise NoEsAdminError("Solo usuarios con rol ADMIN pueden hacer impersonate")
