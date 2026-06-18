"""
Tests de area_mapping — Sesion 25 / Issue 4.4.

Verifica que el mapping automatico ad_info (department del AD)
a area_id funciona correctamente.
"""
import pytest
from sqlalchemy import select

from app.models.area import Area
from app.services.area_mapping import (
    match_area_por_ad_info,
    _normalizar,
    _area_match_score,
)


# ─── Tests de _normalizar ──────────────────────────────────────────

def test_normalizar_acentos():
    """Normalizar NFD quita acentos."""
    assert _normalizar("Tecnología") == "tecnologia"
    assert _normalizar("Gestión") == "gestion"
    assert _normalizar("Área de Calidad") == "area de calidad"


def test_normalizar_lowercase_y_espacios():
    """Lowercase + colapsa espacios."""
    assert _normalizar("RRHH  RRHH") == "rrhh rrhh"
    assert _normalizar("  COMERCIAL  ") == "comercial"


def test_normalizar_none_y_vacio():
    """None y string vacio retornan string vacio."""
    assert _normalizar(None) == ""
    assert _normalizar("") == ""
    assert _normalizar("   ") == ""


def test_normalizar_caracteres_especiales():
    """Caracteres especiales son removidos."""
    assert _normalizar("Dpto. RR-HH!") == "dpto rr hh"


# ─── Tests de _area_match_score ────────────────────────────────────

def test_score_match_exacto_nombre():
    """Match exacto contra nombre retorna 100."""
    area = Area(sigla="X", nombre="Tecnologia", activo=True, gerencia_id=1)
    assert _area_match_score("tecnologia", area) == 100


def test_score_match_exacto_sigla():
    """Match exacto contra sigla retorna 80."""
    area = Area(sigla="TEC", nombre="Tecnologia", activo=True, gerencia_id=1)
    assert _area_match_score("tec", area) == 80


def test_score_sigla_contenida_en_dept():
    """Si sigla aparece como PALABRA COMPLETA en department, score=50."""
    # Caso real: sigla "TEC" es palabra completa en "Departamento TEC La Paz"
    area = Area(sigla="TEC", nombre="Tecnologia", activo=True, gerencia_id=1)
    assert _area_match_score("departamento tec la paz", area) == 50
    # "tecnologia" como palabra en dept tambien matchea (score 30 por nombre)
    # (no 50 porque "tec" como sigla no es palabra completa en "tecnologia y sistemas")
    assert _area_match_score("tecnologia y sistemas", area) == 30


def test_score_dept_contenido_en_sigla():
    """Si department (palabra completa) matchea como palabra en sigla, score=50."""
    area = Area(sigla="RRHH", nombre="Recursos Humanos", activo=True, gerencia_id=1)
    # "rrhh" == "rrhh" (sigla exacta) = 80, no 50
    assert _area_match_score("rrhh", area) == 80
    # dept "calidad" como palabra en sigla "RRHH" -> 0 (no matchea)
    assert _area_match_score("calidad", area) == 0


def test_score_sin_match():
    """Si no hay match, score=0."""
    area = Area(sigla="TEC", nombre="Tecnologia", activo=True, gerencia_id=1)
    assert _area_match_score("comercial", area) == 0
    assert _area_match_score("", area) == 0
    assert _area_match_score("rrhh", area) == 0


# ─── Tests de match_area_por_ad_info ───────────────────────────────

@pytest.mark.asyncio
async def test_match_area_por_nombre_exacto(db_session, seed_catalogos):
    """Match por nombre exacto."""
    area_test = Area(
        gerencia_id=seed_catalogos["gerencia"].id,
        sigla="TST113", nombre="Area Test 113 Mapping", activo=True, orden=99,
    )
    db_session.add(area_test)
    await db_session.commit()
    await db_session.refresh(area_test)

    result = await match_area_por_ad_info(db_session, "Area Test 113 Mapping")
    assert result == area_test.id


@pytest.mark.asyncio
async def test_match_area_por_sigla_exacta(db_session, seed_catalogos):
    """Match por sigla exacta."""
    area_test = Area(
        gerencia_id=seed_catalogos["gerencia"].id,
        sigla="TECX", nombre="Tecnologia X", activo=True, orden=99,
    )
    db_session.add(area_test)
    await db_session.commit()
    await db_session.refresh(area_test)

    result = await match_area_por_ad_info(db_session, "TECX")
    assert result == area_test.id


@pytest.mark.asyncio
async def test_match_area_sigla_contenida_en_dept(db_session, seed_catalogos):
    """Match cuando sigla esta como PALABRA COMPLETA en el department del AD."""
    area_test = Area(
        gerencia_id=seed_catalogos["gerencia"].id,
        sigla="RRHH", nombre="Recursos Humanos", activo=True, orden=99,
    )
    db_session.add(area_test)
    await db_session.commit()
    await db_session.refresh(area_test)

    result = await match_area_por_ad_info(db_session, "Direccion RRHH Bolivia")
    assert result == area_test.id


@pytest.mark.asyncio
async def test_match_area_con_oficina(db_session, seed_catalogos):
    """ad_info puede venir como 'department | office'."""
    area_test = Area(
        gerencia_id=seed_catalogos["gerencia"].id,
        sigla="COM", nombre="Comercial", activo=True, orden=99,
    )
    db_session.add(area_test)
    await db_session.commit()
    await db_session.refresh(area_test)

    result = await match_area_por_ad_info(db_session, "Comercial | Edificio Central")
    assert result == area_test.id


@pytest.mark.asyncio
async def test_match_area_sin_match_retorna_none(db_session, seed_catalogos):
    """Si no hay match, retorna None (no aborta)."""
    result = await match_area_por_ad_info(db_session, "Departamento Inexistente XYZ")
    assert result is None


@pytest.mark.asyncio
async def test_match_area_ad_info_vacio_retorna_none(db_session, seed_catalogos):
    """ad_info vacio o None retorna None."""
    assert await match_area_por_ad_info(db_session, None) is None
    assert await match_area_por_ad_info(db_session, "") is None
    assert await match_area_por_ad_info(db_session, "   ") is None
    assert await match_area_por_ad_info(db_session, "|") is None
