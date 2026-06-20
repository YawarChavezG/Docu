"""
Tests para DocumentoAlcanceDifusion (R3 Fase 1 - sesion 37).
Tabla N:M para el arbol de difusion (US-1.06).
"""
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.documento_alcance_difusion import DocumentoAlcanceDifusion
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento
from sqlalchemy import text


async def _crear_flujo(db_session, seed_catalogos, codigo="CC-7-200"):
    area = seed_catalogos["area"]
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 9)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=9, slug="GUIA", nombre="Guia",
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)

    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=200, codigo=codigo, version="00", titulo="Test",
        estatus=EstatusDocumento.EN_REVISION, activo=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    estado_id = (await db_session.execute(text("SELECT id FROM estados WHERE codigo='EN_REVISION'"))).scalar_one()
    flujo = DocumentoFlujo(
        documento_id=doc.id, estado_actual_id=estado_id,
        tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot=codigo, version_snapshot="00", titulo="Test",
        elaborador_id=seed_catalogos["eto"].id, fecha_solicitud=doc.created_at,
        alcance_difusion_ids=[], revisor_ids=[], aprobador_ids=[],
        activo=True, created_by_id=seed_catalogos["eto"].id,
    )
    db_session.add(flujo)
    await db_session.commit()
    await db_session.refresh(flujo)
    return flujo


# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_crear_alcance_gerencia(db_session, seed_catalogos):
    """Crear alcance para una gerencia (area NULL)."""
    flujo = await _crear_flujo(db_session, seed_catalogos)
    ger = seed_catalogos["gerencia"]
    a = DocumentoAlcanceDifusion(
        documento_flujo_id=flujo.id, gerencia_id=ger.id,
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    assert a.id is not None
    assert a.gerencia_id == ger.id
    assert a.area_id is None


@pytest.mark.asyncio
async def test_crear_alcance_area(db_session, seed_catalogos):
    """Crear alcance para un area (gerencia NULL)."""
    flujo = await _crear_flujo(db_session, seed_catalogos)
    area = seed_catalogos["area"]
    a = DocumentoAlcanceDifusion(
        documento_flujo_id=flujo.id, area_id=area.id,
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    assert a.area_id == area.id
    assert a.gerencia_id is None


@pytest.mark.asyncio
async def test_check_exactly_one_definido():
    """CHECK ck_alcance_exactly_one: el modelo declara la constraint XOR."""
    table_args = DocumentoAlcanceDifusion.__table_args__
    found = any(
        getattr(c, "name", None) == "ck_alcance_exactly_one" and
        "IS NOT NULL" in c.sqltext.text and "IS NULL" in c.sqltext.text
        for c in table_args if hasattr(c, "sqltext")
    )
    assert found, "CHECK constraint ck_alcance_exactly_one debe estar definido (gerencia XOR area)"


@pytest.mark.asyncio
async def test_indice_alcance_flujo(db_session, seed_catalogos):
    """Indice ix_alcance_flujo: WHERE documento_flujo_id=X."""
    flujo = await _crear_flujo(db_session, seed_catalogos)
    ger = seed_catalogos["gerencia"]
    area = seed_catalogos["area"]

    db_session.add_all([
        DocumentoAlcanceDifusion(documento_flujo_id=flujo.id, gerencia_id=ger.id),
        DocumentoAlcanceDifusion(documento_flujo_id=flujo.id, area_id=area.id),
    ])
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(DocumentoAlcanceDifusion.id))
        .where(DocumentoAlcanceDifusion.documento_flujo_id == flujo.id)
    )
    assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_fk_flujo_invalido(db_session, seed_catalogos):
    """FK documento_flujo_id: inexistente => IntegrityError."""
    ger = seed_catalogos["gerencia"]
    a = DocumentoAlcanceDifusion(documento_flujo_id=999999, gerencia_id=ger.id)
    db_session.add(a)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_repr_muestra_target(db_session, seed_catalogos):
    flujo = await _crear_flujo(db_session, seed_catalogos)
    ger = seed_catalogos["gerencia"]
    a = DocumentoAlcanceDifusion(
        documento_flujo_id=flujo.id, gerencia_id=ger.id,
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    rv = repr(a)
    assert "DocumentoAlcanceDifusion" in rv
    assert f"gerencia={ger.id}" in rv
