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
- Warning si `postalCode` vacío (no excluye, solo alerta)

Si `LDAP_ENABLED=false` (DES sin AD), el servicio retorna None en todas las funciones
y los endpoints que dependen de él caen en fallback.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from ldap3 import Connection, Server, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException

from app.core.config import settings

logger = logging.getLogger(__name__)


# ─── Defaults para CNs excluidos ───
DEFAULT_EXCLUDED_CNS = [
    "Mollinedo, Luis Elvin",  # mal categorizado
    "Licencias Cofar",  # buzón
    "Capacitacion Cochabamba",
    "Capacitacion El Alto",
    "Capacitacion La Paz",
    "Capacitacion Oruro",
    "Capacitación Potosí",
    "Capacitación Quillacollo",
    "Capacitación Sucre",
    "Capacitación Tarija",
    "Capacitación Trinidad",
    "Almacen Potosi",
    "Almacen El Alto",
    "Contador Particulas",  # buzón
    "Choque Mena, Fabiola Jhazmin",  # persona mal ubicada
    "Datec",  # buzón
]

# ─── Defaults para sAMAccountName excluidos ───
DEFAULT_EXCLUDED_SAMACCOUNTNAMES = ["dlanchipa", "ozegarra"]


def _get_excluded_cns() -> List[str]:
    """Lee LDAP_EXCLUDED_CNS del .env. Si está vacío, usa los defaults."""
    if not settings.ldap_excluded_cns:
        return DEFAULT_EXCLUDED_CNS
    # Separar por coma
    return [c.strip() for c in settings.ldap_excluded_cns.split(",") if c.strip()]


def _get_excluded_samaccountnames() -> List[str]:
    if not settings.ldap_excluded_samaccountnames:
        return DEFAULT_EXCLUDED_SAMACCOUNTNAMES
    return [s.strip().lower() for s in settings.ldap_excluded_samaccountnames.split(",") if s.strip()]


def _build_server() -> Server:
    """Construye un Server ldap3 a partir de la config."""
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

    Si LDAP_BIND_USER_DN está configurado, se usa el filtro
    `LDAP_USER_SEARCH_FILTER` con base `LDAP_USER_SEARCH_BASE` para
    encontrar el DN dinámicamente. Si no, se construye como:
    `sAMAccountName={username}@{DOMAIN}` o el formato del config.
    """
    # Si el username ya es un DN completo, devolverlo tal cual
    if username.startswith("CN=") or username.startswith("cn="):
        return username

    # Si LDAP_BIND_USER_DN está vacío, intentar construir desde username
    if hasattr(settings, "ldap_bind_user_dn") and settings.ldap_bind_user_dn:
        # Si el bind user DN tiene placeholder, reemplazar
        return settings.ldap_bind_user_dn.replace("{username}", username)

    # Default: UPN format (username@domain)
    domain = settings.ldap_domain or "cofar.com"
    return f"{username}@{domain}"


# ─── Bind operations ───

def ldap_bind(username: str, password: str) -> Tuple[bool, str]:
    """
    Intenta hacer bind contra el AD con las credenciales del usuario.
    Retorna (success, mensaje_error).
    """
    if not settings.ldap_enabled:
        return False, "LDAP deshabilitado en configuración"

    if not username or not password:
        return False, "Usuario o contraseña vacíos"

    try:
        server = _build_server()
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
        return False, "Bind no completado (credenciales inválidas o cuenta deshabilitada)"
    except LDAPException as e:
        logger.warning(f"LDAP bind falló para {username}: {e}")
        return False, f"Error LDAP: {str(e)[:200]}"
    except Exception as e:
        logger.exception(f"Error inesperado en LDAP bind para {username}")
        return False, f"Error interno: {str(e)[:200]}"


def ldap_bind_service_account() -> Optional[Connection]:
    """
    Hace bind con el service account (configurado en LDAP_BIND_USER y
    LDAP_BIND_PASSWORD). Retorna la conexión activa o None si falla.
    """
    if not settings.ldap_enabled:
        return None

    if not settings.ldap_bind_user or not settings.ldap_bind_password:
        return None

    try:
        server = _build_server()
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
        logger.error(f"Service account bind falló: {e}")
        return None
    except Exception as e:
        logger.exception("Error inesperado en service account bind")
        return None


# ─── Search operations ───

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
            pass  # uAC no parseable → no excluimos por esto

    # Filtro 3: sAMAccountName en lista excluida
    sam = _primero(entry_attrs.get("sAMAccountName")).lower()
    if sam in excluded_sams:
        return False

    # Filtro 4: CN en lista excluida
    cn = _primero(entry_attrs.get("cn") or entry_attrs.get("sn") or "")
    if cn in excluded_cns:
        return False

    # Si el DN contiene un CN que está en la lista excluida
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
    ldap3 a veces no devuelve el campo `cn` automáticamente. Lo extrae del DN.
    """
    if "cn" not in attrs and "distinguishedName" in attrs:
        dn = attrs["distinguishedName"]
        if isinstance(dn, list):
            dn = dn[0] if dn else ""
        if isinstance(dn, str) and dn.upper().startswith("CN="):
            # "CN=Apellido, Nombre,OU=..." → "Apellido, Nombre"
            cn_part = dn[3:].split(",", 1)[0]
            attrs["cn"] = [cn_part]  # guardamos como lista por consistencia


def ldap_search_users(
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Busca usuarios reales de COFAR en AD.
    - query: filtro de búsqueda (opcional, busca en cn, givenName, sn, sAMAccountName, mail)
    - page, page_size: paginación
    Retorna: {"total": N, "page": X, "page_size": Y, "items": [usuarios], "warnings": [warnings]}
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
        # Diagnostico: por que fallo el bind?
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

    try:
        # Construir el filtro de búsqueda
        if query:
            q = query.replace("(", "").replace(")", "").replace("*", "")  # sanitizar
            search_filter = (
                f"(|(cn=*{q}*)(givenName=*{q}*)(sn=*{q}*)"
                f"(sAMAccountName=*{q}*)(mail=*{q}*)(title=*{q}*))"
            )
        else:
            # Sin query: traer todos los usuarios con sAMAccountName (no service accounts)
            search_filter = "(sAMAccountName=*)"

        search_base = settings.ldap_user_search_base or "OU=Usuarios,DC=cofar,DC=com"
        # Defensive: si por algun motivo el search_base quedo malformado
        # (ej: bug del .bat que parte en '='), reconstruir un DN valido
        # desde el ldap_base_dn. Si tampoco eso anda, usar el default duro.
        if not search_base or "DC=" not in search_base.upper() or "=" not in search_base.split(",")[0]:
            base_dn = settings.ldap_base_dn or "DC=cofar,DC=com"
            logger.warning(
                f"ldap_user_search_base malformado ('{search_base}'), "
                f"reconstruyendo desde ldap_base_dn ('{base_dn}')"
            )
            search_base = f"OU=Usuarios,{base_dn}"

        logger.info(f"LDAP search: base={search_base} filter={search_filter} page_size={page_size}")

        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=USER_ATTRIBUTES,
            size_limit=5000,  # 2026-06-15: subido de 2000 a 5000 para
                              # no truncar el sync. En COFAR hay ~750
                              # usuarios reales; con 2000 nos quedaban
                              # cortos. 5000 es seguro (el size_limit solo
                              # limita, no trae "basura").
        )

        excluded_cns = _get_excluded_cns()
        excluded_sams = _get_excluded_samaccountnames()

        all_users = []
        warnings = []
        # Contadores por razon de exclusion (para debug)
        excl_contadores = {
            "sam_vacio": 0,
            "termina_en_$": 0,
            "ou_especiales": 0,
            "ou_pruebas": 0,
            "ou_capacitacion": 0,
            "ou_quintanilla": 0,
            "uac_deshabilitado": 0,
            "cn_excluido": 0,
        }

        for entry in conn.entries:
            # ldap3 devuelve los valores como listas. Mantenemos la lista
            # intacta; _normalizar_usuario_ad() se encarga de aplanar.
            attrs = {k: v for k, v in entry.entry_attributes_as_dict.items() if v is not None}
            # Agregamos el "dn" del entry (NO confundir con distinguishedName
            # que puede ser >100 chars). entry.entry_dn es el DN real del
            # objeto y se necesita para los filtros de OU.
            attrs["dn"] = entry.entry_dn
            _poblar_cn_desde_dn(attrs)

            sam_check = _primero(attrs.get("sAMAccountName"))
            if not sam_check:
                excl_contadores["sam_vacio"] += 1
                continue
            if sam_check.endswith("$"):
                excl_contadores["termina_en_$"] += 1
                continue

            dn_check = attrs["dn"].lower()
            if "ou=especiales" in dn_check:
                excl_contadores["ou_especiales"] += 1
                continue
            if "ou=pruebas" in dn_check:
                excl_contadores["ou_pruebas"] += 1
                continue
            if "ou=capacitacion" in dn_check or "ou=capacitaciones" in dn_check:
                excl_contadores["ou_capacitacion"] += 1
                continue
            if "ou=quintanilla" in dn_check:
                excl_contadores["ou_quintanilla"] += 1
                continue

            uac_check = _primero(attrs.get("userAccountControl"))
            # IMPORTANTE: bit-mask para detectar ACCOUNTDISABLE (bit 1 = valor 2).
            # NO comparar contra valores literales ("514", "66050") porque el
            # AD de COFAR tiene cuentas deshabilitadas con uAC 4098, 8194,
            # 32774, etc. que pasarian el filtro de literales.
            # Ref: scripts/sync_ad_oficial.py:_es_cuenta_deshabilitada
            cuenta_deshabilitada = False
            if uac_check:
                try:
                    cuenta_deshabilitada = (int(uac_check) & 2) != 0
                except (ValueError, TypeError):
                    pass
            if cuenta_deshabilitada:
                excl_contadores["uac_deshabilitado"] += 1
                continue

            cn_check = _primero(attrs.get("cn") or attrs.get("sn") or "")
            if cn_check in excluded_cns:
                excl_contadores["cn_excluido"] += 1
                continue

            # Si llego aca, pasa los filtros de OU/uAC/CN.
            # Filtro adicional: usuarios SIN codigo SAP (postalCode vacio)
            # se EXCLUYEN del listado, igual que en scripts/sync_ad_oficial.py
            # (no se importan a la BD porque no son empleados activos
            # codificables en SAP).
            user = _normalizar_usuario_ad(attrs)
            if not user["tiene_codigo_sap"]:
                # Warning visible en la respuesta (para debug), pero NO se
                # incluye en all_users → se excluye del sync.
                user["warning"] = "⚠️ Sin código SAP (postalCode vacío en AD)"
                excl_contadores["postal_vacio"] = excl_contadores.get("postal_vacio", 0) + 1
                continue

            all_users.append(user)

        # Loguear contadores de exclusion (para debug)
        total_entries = len(conn.entries)
        logger.info(
            f"LDAP search result: {total_entries} entries -> "
            f"{len(all_users)} aceptados, "
            + ", ".join(f"{v} por {k}" for k, v in excl_contadores.items() if v > 0)
        )

        # Ordenar alfabéticamente por nombre completo
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
            "warnings": warnings,
        }
    except LDAPException as e:
        logger.exception("LDAP search falló")
        err = str(e)
        # Errores comunes:
        # - "attribute type not present" -> algun attr de USER_ATTRIBUTES no
        #   existe en el schema del AD. Sacarlo de USER_ATTRIBUTES.
        # - "invalid attribute type"     -> el attr no es valido para search/return
        # - "no such object"             -> el search_base no existe
        if "attribute type not present" in err.lower():
            hint = (" Algún atributo de USER_ATTRIBUTES no existe en este AD. "
                    "Revisar ad_service.py y quitarlo (sospechosos: info, company, "
                    "physicalDeliveryOfficeName, memberOf).")
        elif "invalid attribute type" in err.lower():
            hint = (" Algún atributo de USER_ATTRIBUTES está mal escrito.")
        elif "no such object" in err.lower():
            hint = f" El search_base '{settings.ldap_user_search_base}' no existe en el AD."
        elif "size limit" in err.lower():
            hint = " El AD rechazó por size_limit, hay que filtrar mejor."
        else:
            hint = ""
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "items": [],
            "warnings": [f"Error en búsqueda LDAP: {err[:200]}{hint}"],
        }
    finally:
        try:
            conn.unbind()
        except Exception:
            pass


def ldap_get_user_by_samaccountname(sam: str) -> Optional[dict]:
    """
    Busca un usuario específico por sAMAccountName.
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
            user["warning"] = "⚠️ Sin código SAP (postalCode vacío en AD)"
        return user
    except LDAPException:
        logger.exception(f"LDAP get_user_by_samaccountname falló para {sam}")
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
