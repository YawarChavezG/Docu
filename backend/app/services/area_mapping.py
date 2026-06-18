"""
services/area_mapping.py — Sesion 25 / Issue 4.4.

Match automatico de usuarios AD a areas de la BD basandose en el campo
`ad_info` (department del Active Directory). Lo que manda es el AD: si
en el AD se actualiza el department, en el proximo sync (masivo o
on-demand) se reintenta el match y se actualiza el area_id.

Estrategia (en orden):
1. Match EXACTO case-insensitive contra `area.nombre`
2. Match por SIGLA case-insensitive (campo `area.sigla`)
3. Match por CONTENIDO: si el department del AD contiene una sigla
   conocida o viceversa
4. Si no hay match: retorna None + warning en log

El matching es 100% automatico (sin intervencion manual de ETO). El
cliente quiere que "lo que manda es el AD" - entonces cualquier cambio
en el department del AD se refleja en area_id en la proxima corrida.
"""
import logging
import re
import unicodedata
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.area import Area

logger = logging.getLogger(__name__)


def _normalizar(texto: Optional[str]) -> str:
    """
    Normaliza string para matching:
    - lowercase
    - sin acentos (NFD + remove combining)
    - sin caracteres especiales (solo alfanumericos + espacios)
    - colapsa espacios
    """
    if not texto:
        return ""
    # NFD descompone acentos (Tecnologia -> Tecnologia)
    nfkd = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    # Solo letras, numeros y espacios
    limpio = re.sub(r"[^a-z0-9\s]", " ", sin_acentos.lower())
    # Colapsar espacios
    return re.sub(r"\s+", " ", limpio).strip()


def _contiene_palabra(texto: str, palabra: str) -> bool:
    """
    True si `palabra` aparece como PALABRA COMPLETA en `texto`.
    "rrhh" en "direccion rrhh bolivia" = True.
    "cc" en "direccion rrhh bolivia" = False (no es palabra, es subsecuencia).
    """
    if not palabra or not texto:
        return False
    palabras = texto.split()
    return palabra in palabras


def _area_match_score(dept_norm: str, area: Area) -> int:
    """
    Retorna un score de matching entre un department normalizado y un area.
    Mayor score = mejor match. 0 = sin match.

    Pesos:
    - 100: match exacto contra area.nombre
    - 80:  match exacto contra area.sigla
    - 50:  department contiene sigla como PALABRA COMPLETA (o viceversa)
    - 30:  match parcial por nombre (palabra completa)
    """
    if not dept_norm:
        return 0

    nombre_norm = _normalizar(area.nombre)
    sigla_norm = _normalizar(area.sigla)

    if dept_norm == nombre_norm:
        return 100
    if dept_norm == sigla_norm:
        return 80
    # Match por palabra completa (evita "cc" en "direccion" = false positive)
    if sigla_norm and (_contiene_palabra(dept_norm, sigla_norm) or _contiene_palabra(sigla_norm, dept_norm)):
        return 50
    if nombre_norm and (_contiene_palabra(dept_norm, nombre_norm) or _contiene_palabra(nombre_norm, dept_norm)):
        return 30
    return 0


async def match_area_por_ad_info(
    db: AsyncSession, ad_info: Optional[str]
) -> Optional[int]:
    """
    Busca el area_id que mejor matchea con el ad_info (department del AD).

    Args:
        db: sesion de BD async
        ad_info: department del AD (ej: "Tecnologia", "RRHH", "Comercial")

    Returns:
        area_id del mejor match, o None si no se encontro match.
    """
    if not ad_info or not ad_info.strip():
        return None

    # ad_info viene como "department | office" del backend
    # Tomamos solo la primera parte (department)
    dept = ad_info.split("|")[0].strip()
    if not dept:
        return None

    dept_norm = _normalizar(dept)
    if not dept_norm:
        return None

    # Traer TODAS las areas (son ~50, no es problema)
    areas = (await db.execute(
        select(Area).where(Area.activo == True)
    )).scalars().all()

    if not areas:
        return None

    # Calcular score para cada area
    best_area = None
    best_score = 0
    for area in areas:
        score = _area_match_score(dept_norm, area)
        if score > best_score:
            best_score = score
            best_area = area

    # Solo aceptar match con score >= 50 (sigla contiene / nombre contiene)
    # Score 30 (match parcial por nombre) es muy laxo, lo descartamos
    if best_score >= 50 and best_area is not None:
        logger.info(
            f"area_mapping: '{dept}' -> area_id={best_area.id} "
            f"({best_area.sigla} - {best_area.nombre}) score={best_score}"
        )
        return best_area.id

    logger.debug(
        f"area_mapping: '{dept}' sin match (mejor score={best_score})"
    )
    return None
