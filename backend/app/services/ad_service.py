"""
Servicio de Active Directory (AD).

Funciones:
- `ldap_bind(username, password)`: autentica contra AD. Retorna True/False.
- `ldap_search_users(query, page, page_size)`: lista usuarios de COFAR (filtrados).
- `ldap_get_user_by_samaccountname(sam)`: busca un usuario por sAMAccountName.
- `ldap_sync_all()`: bulk sync (no usado en impersonate, solo en el job de las 00:05).

Filtros aplicados al listado (basados en el script JS de n8n):
- Excluir OU=especiales, OU=pruebas
- Excluir userAccountControl = 514 (deshabilitado) o 66050 (deshabilitado + password expira)
- Excluir sAMAccountName = dlanchipa, ozegarra
- Excluir CNs en la lista `LDAP_EXCLUDED_CNS` del .env (17 defaults)
- Warning si `postalCode` vacÃ­o (no excluye, solo alerta)

Si `LDAP_ENABLED=false` (DES sin AD), el servicio retorna None en todas las funciones
y los endpoints que dependen de Ã©l caen en fallback.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from ldap3 import Connection, Server, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException

from app.core.config import settings

logger = logging.getLogger(__name__)


# â”€â”€â”€ Defaults para CNs excluidos â”€â”€â”€
DEFAULT_EXCLUDED_CNS = [
    "Mollinedo, Luis Elvin",  # mal categorizado
    "Licencias Cofar",  # buzÃ³n
    "Capacitacion Cochabamba",
    "Capacitacion El Alto",
    "Capacitacion La Paz",
    "Capacitacion Oruro",
    "CapacitaciÃ³n PotosÃ­",
    "CapacitaciÃ³n Quillacollo",
    "CapacitaciÃ³n Sucre",
    "CapacitaciÃ³n Tarija",
    "CapacitaciÃ³n Trinidad",
    "Almacen Potosi",
    "Almacen El Alto",
    "Contador Particulas",  # buzÃ³n
    "Choque Mena, Fabiola Jhazmin",  # persona mal ubicada
    "Datec",  # buzÃ³n
]

# â”€â”€â”€ Defaults para sAMAccountName excluidos â”€â”€â”€
DEFAULT_EXCLUDED_SAMACCOUNTNAMES = ["dlanchipa", "ozegarra"]


def _get_excluded_cns() -> List[str]:
    """Lee LDAP_EXCLUDED_CNS del .env. Si estÃ¡ vacÃ­o, usa los defaults."""
    if not settings.ldap_excluded_cns:
        return DEFAULT_EXCLUDED_CNS
    # Separar por coma
    return [c.strip() for c in settings.ldap_excluded_cns.split(",") if c.strip()]


def _get_excluded_samaccountnames() -> List[str]:
    if not settings.ldap_excluded_samaccountnames:
        return DEFAULT_EXCLUDED_SAMACCOUNTNAMES
    return [s.strip().lower() for s in settings.ldap_excluded_samaccountnames.split(",") if s.strip()]


def build_server() -> Server:
    """Construye un Server ldap3 a partir de la config del .env."""
    if settings.ldap_use_ssl:
        return Server(
            host=settings.ldap_server,
            port=settings.ldap_port or 636,
            use_ssl=True,
            tls=Tls(validate=0),  # En DES no validamos cert
            get_info=ALL,
        )
    return Server(
        host=settings.ldap_server,
        port=settings.ldap_port or 389,
        use_ssl=False,
        get_info=ALL,
    )


def _build_user_dn(username: str) -> str:
    """
    Construye el DN del usuario para bind.

    Si LDAP_BIND_USER_DN estÃ¡ configurado, se usa el filtro
    `LDAP_USER_SEARCH_FILTER` con base `LDAP_USER_SEARCH_BASE` para
    encontrar el DN dinÃ¡micamente. Si no, se construye como:
    `sAMAccountName={username}@{DOMAIN}` o el formato del config.
    """
    # Si el username ya es un DN completo, devolverlo tal cual
    if username.startswith("CN=") or username.startswith("cn="):
        return username

    # Si LDAP_BIND_USER_DN estÃ¡ vacÃ­o, intentar construir desde username
    if hasattr(settings, "ldap_bind_user_dn") and settings.ldap_bind_user_dn:
        # Si el bind user DN tiene placeholder, reemplazar
        return settings.ldap_bind_user_dn.replace("{username}", username)

    # Default: UPN format (username@domain)
    domain = settings.ldap_domain or "cofar.com"
    return f"{username}@{domain}"


# â”€â”€â”€ Bind operations â”€â”€â”€

def ldap_bind(username: str, password: str) -> Tuple[bool, str]:
    """
    Intenta hacer bind contra el AD con las credenciales del usuario.
    Retorna (success, mensaje_error).
    """
    if not settings.ldap_enabled:
        return False, "LDAP deshabilitado en configuraciÃ³n"

    if not username or not password:
        return False, "Usuario o contraseÃ±a vacÃ­os"

    try:
        server = build_server()
        user_dn = _build_user_dn(username)

        conn = Connection(
            server,
            user=user_dn,
            password=password,
            auto_bind=True,
            read_only=True,
            receive_timeout=10,
        )
        bound = conn.bound
        conn.unbind()
        if bound:
            logger.info(f"LDAP bind exitoso para {username}")
            return True, ""
        return False, "Bind no completado (credenciales invÃ¡lidas o cuenta deshabilitada)"
    except LDAPException as e:
        logger.warning(f"LDAP bind fallÃ³ para {username}: {e}")
        return False, f"Error LDAP: {str(e)[:200]}"
    except Exception as e:
        logger.exception(f"Error inesperado en LDAP bind para {username}")
        return False, f"Error interno: {str(e)[:200]}"


def ldap_bind_service_account() -> Optional[Connection]:
    """
    Hace bind con el service account (configurado en LDAP_BIND_USER y
    LDAP_BIND_PASSWORD). Retorna la conexiÃ³n activa o None si falla.
    """
    if not settings.ldap_enabled:
        return None

    if not settings.ldap_bind_user or not settings.ldap_bind_password:
        return None

    try:
        server = build_server()
        conn = Connection(
            server,
            user=settings.ldap_bind_user,
            password=settings.ldap_bind_password,
            auto_bind=True,
            read_only=True,
            receive_timeout=10,
        )
        if conn.bound:
            logger.info(f"Service account bind OK: {settings.ldap_bind_user}")
            return conn
        conn.unbind()
        return None
    except LDAPException as e:
        logger.error(f"Service account bind fallÃ³: {e}")
        return None
    except Exception as e:
        logger.exception("Error inesperado en service account bind")
        return None


# â”€â”€â”€ Search operations â”€â”€â”€

# Atributos que traemos de cada usuario de AD
#
# NOTA HISTORICA: "dn" no es un atributo LDAP valido para pedir (es el
# DN del entry, no un atributo). ldap3 lo rechaza con
# "invalid attribute type dn". distinguishedName si es valido.
#
# 2026-06-15: quitamos "info" porque lanzo "attribute type not present"
# contra el AD de COFAR. "info" es de OpenLDAP (RFC 4524), en AD el campo
# analogo es "description" (que a veces se llama "Info" en la consola
# GUI pero el LDAP attribute name es "description"). Si hace falta,
# agregar "description" como reemplazo.
#
# Atributos NO pedidos intencionalmente (causan errores en algunos AD):
#   - "info"            -> OpenLDAP only
#   - "physicalDeliveryOfficeName" -> a veces no existe en el schema
#   - "company"         -> a veces no retornable
#   - "memberOf"        -> muy grande, no lo necesitamos para sync
USER_ATTRIBUTES = [
    "sAMAccountName",
    "sn",
    "givenName",
    "displayName",
    "mail",
    "title",
    "department",
    "postalCode",
    "telephoneNumber",
    "mobile",
    "userAccountControl",
    "objectClass",     # para filtrar solo user/person (saca equipos/grupos)
    "sAMAccountType",  # 805306368 = SAM_NORMAL_USER_ACCOUNT (filtro de n8n)
    "objectGUID",      # ID unico del objeto en AD, lo usamos como azure_oid
]


def _es_usuario_real_cofar(entry_attrs: dict, excluded_cns: List[str], excluded_sams: List[str]) -> bool:
    """
    Aplica los filtros del script JS de n8n + la lista de CNs excluidos del .env.
    Retorna True si el usuario debe mostrarse.

    NOTA 2026-06-15: ldap3 devuelve los atributos como LISTAS, no como
    strings. Por eso usamos _primero() para aplanar antes de cualquier
    .lower() / .strip() / comparacion.

    OUs excluidas (las mismas que el script JS de n8n + extras del AD de COFAR):
      - ou=especiales     (cuentas de buzon, licencias, etc)
      - ou=pruebas        (usuarios de testing)
      - ou=capacitacion   (buzones de capacitacion, no son personas)
      - ou=quintanilla    (empresa externa, no son empleados COFAR)
    """
    # IMPORTANTE: aplanar TODOS los valores con _primero() porque
    # ldap3 devuelve listas para casi todos los atributos.
    dn = _primero(entry_attrs.get("dn") or entry_attrs.get("distinguishedName") or "").lower()

    # Filtro 1: OUs que NO son personas reales de COFAR
    ous_excluidas = [
        "ou=especiales",
        "ou=pruebas",
        "ou=capacitacion",  # plural
        "ou=capacitaciones",  # alternativa
        "ou=quintanilla",
    ]
    for ou in ous_excluidas:
        if ou in dn:
            return False

    # Filtro 2: userAccountControl deshabilitado
    # IMPORTANTE: usar bit-mask (int(uac) & 2) != 0 para detectar
    # ACCOUNTDISABLE. NO comparar contra valores literales ("514", "66050")
    # porque en el AD de COFAR hay cuentas deshabilitadas con uAC 4098,
    # 8194, 32774, etc. que pasan el filtro de literales.
    # Ref: scripts/sync_ad_oficial.py:_es_cuenta_deshabilitada
    uac = _primero(entry_attrs.get("userAccountControl"))
    if uac:
        try:
            if (int(uac) & 2) != 0:
                return False
        except (ValueError, TypeError):
            pass  # uAC no parseable â†’ no excluimos por esto

    # Filtro 3: sAMAccountName en lista excluida
    sam = _primero(entry_attrs.get("sAMAccountName")).lower()
    if sam in excluded_sams:
        return False

    # Filtro 4: CN en lista excluida
    cn = _primero(entry_attrs.get("cn") or entry_attrs.get("sn") or "")
    if cn in excluded_cns:
        return False

    # Si el DN contiene un CN que estÃ¡ en la lista excluida
    for excluded_cn in excluded_cns:
        if excluded_cn and f"cn={excluded_cn.lower()}" in dn:
            return False

    return True


def _primero(valor) -> str:
    """ldap3 devuelve los atributos como listas. Extrae el primer valor como str."""
    if valor is None:
        return ""
    if isinstance(valor, list):
        return str(valor[0]) if valor else ""
    return str(valor)


def _normalizar_usuario_ad(attrs: dict) -> dict:
    """
    Toma los atributos crudos de AD y devuelve un dict normalizado.
    Solo incluye los campos que nos interesan.

    NOTA: ldap3 devuelve cada atributo como **lista** de strings (incluso
    si tiene un solo valor). Por eso usamos _primero() para aplanar.
    """
    given = _primero(attrs.get("givenName"))
    sn = _primero(attrs.get("sn"))
    # Para displayName preferimos el que viene del AD, sino construimos
    display = _primero(attrs.get("displayName")) or f"{given} {sn}".strip()
    postal = _primero(attrs.get("postalCode"))
    return {
        # El "dn" lo guardamos tal cual lo devuelve ldap3 (entry_dn) en el caller.
        # NO pedimos "distinguishedName" porque puede ser >100 chars y romper
        # la BD. Usamos objectGUID (binario) convertido a hex (32 chars) que
        # es el identificador unico de AD para ese objeto.
        "sAMAccountName": _primero(attrs.get("sAMAccountName")),
        "givenName": given,
        "sn": sn,
        "displayName": display,
        "nombre_completo": display,
        "mail": _primero(attrs.get("mail")),
        "title": _primero(attrs.get("title")),  # cargo
        "department": _primero(attrs.get("department")),
        "physicalDeliveryOfficeName": _primero(attrs.get("physicalDeliveryOfficeName")),
        "telephoneNumber": _primero(attrs.get("telephoneNumber")),
        "mobile": _primero(attrs.get("mobile")),
        "postalCode": postal,
        "userAccountControl": _primero(attrs.get("userAccountControl")),
        # objectGUID es unico por objeto en AD, lo pedimos aparte del DN
        # porque el DN puede ser >100 chars y romper la BD. Aqui lo
        # guardamos como bytes para que el caller lo serialice a hex.
        "objectGUID_raw": attrs.get("objectGUID"),
        # objectClass y sAMAccountType los pasamos crudos (como listas) para
        # que el caller (sync_ad) pueda filtrar por ellos.
        "objectClass": attrs.get("objectClass"),
        "sAMAccountType": attrs.get("sAMAccountType"),
        "tiene_codigo_sap": bool(postal),  # warning si False
    }


def _guid_a_hex(guid_raw) -> str:
    """
    Convierte el objectGUID de AD (bytes) a un string hex de 32 chars.
    AD lo almacena en formato little-endian, ldap3 a veces lo expone
    como bytes raw o como lista. Lo normalizamos a hex uppercase.
    """
    if not guid_raw:
        return ""
    if isinstance(guid_raw, list):
        guid_raw = guid_raw[0] if guid_raw else b""
    if isinstance(guid_raw, str):
        # ldap3 a veces lo devuelve como string hex ya formateado
        return guid_raw.replace("-", "").replace("{", "").replace("}", "").strip()
    if isinstance(guid_raw, (bytes, bytearray)):
        return guid_raw.hex().upper()
    return ""


def _poblar_cn_desde_dn(attrs: dict) -> None:
    """
    ldap3 a veces no devuelve el campo `cn` automÃ¡ticamente. Lo extrae del DN.
    """
    if "cn" not in attrs and "distinguishedName" in attrs:
        dn = attrs["distinguishedName"]
        if isinstance(dn, list):
            dn = dn[0] if dn else ""
        if isinstance(dn, str) and dn.upper().startswith("CN="):
            # "CN=Apellido, Nombre,OU=..." â†’ "Apellido, Nombre"
            cn_part = dn[3:].split(",", 1)[0]
            attrs["cn"] = [cn_part]  # guardamos como lista por consistencia


def ldap_search_users(
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Busca usuarios reales de COFAR en AD.

    IMPORTANTE 2026-06-15: logica REEMPLAZADA para coincidir EXACTAMENTE con
    scripts/sync_ad_oficial.py (fuente de verdad validada por el cliente).
    Antes tenia filtros extra (capacitacion, quintanilla, 17 CNs) que hacian
    que el sync trajera solo 586 usuarios en lugar de los 753 esperados.

    Logica actual (replica del script validado):
      1. Search: (&(objectClass=user)(sAMAccountType=805306368)) en
         ou=Oficina Central,dc=cofar,dc=com, size_limit=5000.
      2. Filtros post-search:
         - OU=especiales o OU=pruebas (en el DN)
         - userAccountControl con bit 1 (ACCOUNTDISABLE)
         - sAMAccountName en {dlanchipa, ozegarra}
         - postalCode vacio (sin codigo SAP)
    """
    if not settings.ldap_enabled:
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
            "warnings": ["LDAP deshabilitado en este ambiente"],
        }

    conn = ldap_bind_service_account()
    if conn is None:
        detalle = []
        if not settings.ldap_enabled:
            detalle.append("LDAP_ENABLED=false en .env")
        if not settings.ldap_server:
            detalle.append("LDAP_SERVER vacio")
        if not settings.ldap_bind_user:
            detalle.append("LDAP_BIND_USER vacio")
        if not settings.ldap_bind_password:
            detalle.append("LDAP_BIND_PASSWORD vacio")
        msg = "No se pudo conectar al servidor LDAP con el service account"
        if detalle:
            msg += " (" + "; ".join(detalle) + ")"
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
            "warnings": [msg],
        }

    # Atributos pedidos: mismos que scripts/sync_ad_oficial.py
    SEARCH_ATTRIBUTES = [
        "sn", "title", "physicalDeliveryOfficeName", "telephoneNumber",
        "givenName", "department", "sAMAccountName", "mobile", "postalCode",
        "mail", "company", "info", "userAccountControl",
    ]

    try:
        # Search base y filter EXACTOS del script validado
        search_base = "ou=Oficina Central,dc=cofar,dc=com"
        search_filter = "(&(objectClass=user)(sAMAccountType=805306368))"

        logger.info(
            f"LDAP search (sync_ad_oficial logic): base={search_base} "
            f"filter={search_filter}"
        )

        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=SEARCH_ATTRIBUTES,
            size_limit=5000,
        )

        all_users = []
        excl_contadores = {
            "ou_especiales": 0,
            "ou_pruebas": 0,
            "uac_deshabilitado": 0,
            "sam_excluido": 0,
            "sam_vacio": 0,
            "sin_postal": 0,
        }

        for entry in conn.entries:
            attrs = {k: v for k, v in entry.entry_attributes_as_dict.items() if v is not None}
            attrs["dn"] = entry.entry_dn

            sam = _primero(attrs.get("sAMAccountName"))
            if not sam:
                excl_contadores["sam_vacio"] += 1
                continue

            # Filtro 1: OU=especiales o OU=pruebas (en el DN)
            dn_lower = str(attrs["dn"]).lower()
            if "ou=especiales" in dn_lower:
                excl_contadores["ou_especiales"] += 1
                continue
            if "ou=pruebas" in dn_lower:
                excl_contadores["ou_pruebas"] += 1
                continue

            # Filtro 2: cuenta deshabilitada (bit 1 = ACCOUNTDISABLE)
            uac_raw = attrs.get("userAccountControl")
            uac_flat = _primero(uac_raw)
            deshabilitada = False
            if uac_flat:
                try:
                    deshabilitada = (int(uac_flat) & 2) != 0
                except (ValueError, TypeError):
                    pass
            if deshabilitada:
                excl_contadores["uac_deshabilitado"] += 1
                continue

            # Filtro 3: sAMAccountName en lista excluida
            if sam.lower() in ("dlanchipa", "ozegarra"):
                excl_contadores["sam_excluido"] += 1
                continue

            # Filtro 4: codigo SAP (postalCode) no vacio
            postal = _primero(attrs.get("postalCode"))
            if not postal:
                excl_contadores["sin_postal"] += 1
                continue

            # Pasa todos los filtros
            user = _normalizar_usuario_ad(attrs)
            all_users.append(user)

        total_entries = len(conn.entries)
        logger.info(
            f"LDAP search result: {total_entries} entries -> "
            f"{len(all_users)} aceptados, "
            + ", ".join(f"{v} por {k}" for k, v in excl_contadores.items() if v > 0)
        )

        all_users.sort(key=lambda u: u["nombre_completo"].lower())

        total = len(all_users)
        start = (page - 1) * page_size
        end = start + page_size
        items = all_users[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
            "warnings": [],
        }
    except LDAPException as e:
        logger.exception("LDAP search fallo")
        err = str(e)
        if "attribute type not present" in err.lower():
            hint = " Algun atributo no existe en este AD."
        elif "invalid attribute type" in err.lower():
            hint = " Algun atributo esta mal escrito."
        elif "no such object" in err.lower():
            hint = " El search_base no existe en el AD."
        elif "size limit" in err.lower():
            hint = " El AD rechazo por size_limit."
        else:
            hint = ""
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
            "warnings": [f"Error en busqueda LDAP: {err[:200]}{hint}"],
        }
    finally:
        try:
            conn.unbind()
        except Exception:
            pass


def ldap_get_user_by_samaccountname(sam: str) -> Optional[dict]:
    """
    Busca un usuario especÃ­fico por sAMAccountName.
    Retorna dict normalizado o None si no existe.
    """
    if not settings.ldap_enabled:
        return None

    conn = ldap_bind_service_account()
    if conn is None:
        return None

    try:
        # Si LDAP_USER_SEARCH_BASE esta vacio o parece mal armado,
        # caemos al default del dominio.
        search_base = settings.ldap_user_search_base
        if not search_base or "DC=" not in search_base.upper():
            # Armar desde LDAP_BASE_DN (ej: OU=Oficina Central,DC=cofar,DC=com -> DC=cofar,DC=com)
            base_dn = settings.ldap_base_dn or "DC=cofar,DC=com"
            # Tomar solo la parte DC=...
            parts = [p for p in base_dn.split(",") if p.strip().upper().startswith("DC=")]
            search_base = ",".join(parts) if parts else "DC=cofar,DC=com"
        logger.debug(f"ldap_get_user_by_samaccountname('{sam}'): base={search_base}")

        conn.search(
            search_base=search_base,
            search_filter=f"(sAMAccountName={sam})",
            search_scope=SUBTREE,
            attributes=USER_ATTRIBUTES,
        )

        if not conn.entries:
            return None

        entry = conn.entries[0]
        attrs = {k: v for k, v in entry.entry_attributes_as_dict.items() if v is not None}
        _poblar_cn_desde_dn(attrs)
        user = _normalizar_usuario_ad(attrs)
        if not user["tiene_codigo_sap"]:
            # Sesion 25 / Issue 4.2: usuario sin codigo SAP no se retorna.
            # El sync_ad ya filtra por postalCode no vacio (linea 495-497).
            # El login on-demand antes NO filtraba, lo que permitia crear
            # usuarios en BD sin SAP. Ahora se alinea con sync_ad: retorna
            # None para que el caller rechace con 401/403.
            logger.warning(
                f"ldap_get_user_by_samaccountname('{sam}'): sin postalCode, rechazado"
            )
            return None
        return user
    except LDAPException:
        logger.exception(f"LDAP get_user_by_samaccountname fallÃ³ para {sam}")
        return None
    finally:
        try:
            conn.unbind()
        except Exception:
            pass


def obtener_atributos_usuario_ad(sam: str) -> Optional[dict]:
    """
    Alias / wrapper de ldap_get_user_by_samaccountname para uso
    desde auth.py en el flujo de login (sync on-demand de atributos).
    Retorna dict normalizado o None.
    """
    return ldap_get_user_by_samaccountname(sam)
