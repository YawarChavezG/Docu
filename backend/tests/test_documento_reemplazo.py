"""
Tests para DocumentoReemplazo (R3 Fase 1 - sesion 37).
Tabla N:M para reemplazos documentales (US-1.07, US-5.01).
"""
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.documento_reemplazo import DocumentoReemplazo
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento
from sqlalchemy import text


async def _crear_flujo_y_doc_viejo(db_session, seed_catalogos, codigo_viejo="CC-7-099"):
    area = seed_catalogos["area"]
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 7)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=7, slug="REGLAMENTO", nombre="Reglamento",
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)

    # Doc viejo (que sera reemplazado)
    doc_viejo = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=99, codigo=codigo_viejo, version="00", titulo="Viejo",
        estatus=EstatusDocumento.APROBADO, activo=True,
    )
    db_session.add(doc_viejo)
    await db_session.commit()
    await db_session.refresh(doc_viejo)

    # Doc nuevo + flujo
    doc_nuevo = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=100, codigo="CC-7-100", version="00", titulo="Nuevo",
        estatus=EstatusDocumento.EN_REVISION, activo=True,
    )
    db_session.add(doc_nuevo)
    await db_session.commit()
    await db_session.refresh(doc_nuevo)

    estado_id = (await db_session.execute(text("SELECT id FROM estados WHERE codigo='EN_REVISION'"))).scalar_one()
    flujo = DocumentoFlujo(
        documento_id=doc_nuevo.id, estado_actual_id=estado_id,
        tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot="CC-7-100", version_snapshot="00", titulo="Nuevo",
        elaborador_id=seed_catalogos["eto"].id, fecha_solicitud=doc_nuevo.created_at,
        alcance_difusion_ids=[], revisor_ids=[], aprobador_ids=[],
        activo=True, created_by_id=seed_catalogos["eto"].id,
    )
    db_session.add(flujo)
    await db_session.commit()
    await db_session.refresh(flujo)
    return flujo, doc_viejo


# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_crear_reemplazo_basico(db_session, seed_catalogos):
    """Crear reemplazo con defaults: ejecutado=False, sin FK a doc viejo."""
    flujo, _ = await _crear_flujo_y_doc_viejo(db_session, seed_catalogos)
    r = DocumentoReemplazo(
        documento_flujo_id=flujo.id,
        codigo_documento_viejo="CC-7-099/00",  # sin FK (puede no existir en BD)
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    assert r.id is not None
    assert r.ejecutado is False
    assert r.ejecutado_at is None
    assert r.documento_viejo_id is None
    assert r.codigo_documento_viejo == "CC-7-099/00"


@pytest.mark.asyncio
async def test_reemplazo_con_fk_doc_viejo(db_session, seed_catalogos):
    """FK documento_viejo_id: vincula al documento que se va a obsoletar."""
    flujo, doc_viejo = await _crear_flujo_y_doc_viejo(db_session, seed_catalogos)
    r = DocumentoReemplazo(
        documento_flujo_id=flujo.id,
        documento_viejo_id=doc_viejo.id,
        codigo_documento_viejo=doc_viejo.codigo,
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    assert r.documento_viejo_id == doc_viejo.id


@pytest.mark.asyncio
async def test_marcar_ejecutado(db_session, seed_catalogos):
    """Marcar ejecutado: cambia el flag + setea ejecutado_at."""
    from datetime import datetime
    flujo, _ = await _crear_flujo_y_doc_viejo(db_session, seed_catalogos)
    r = DocumentoReemplazo(
        documento_flujo_id=flujo.id,
        codigo_documento_viejo="CC-7-099/00",
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)

    r.ejecutado = True
    r.ejecutado_at = datetime.now()
    await db_session.commit()
    await db_session.refresh(r)
    assert r.ejecutado is True
    assert r.ejecutado_at is not None


@pytest.mark.asyncio
async def test_indice_pendientes(db_session, seed_catalogos):
    """Indice ix_reemplazos_pendientes: WHERE ejecutado=FALSE AND documento_viejo_id NOT NULL."""
    flujo, doc_viejo = await _crear_flujo_y_doc_viejo(db_session, seed_catalogos)

    # 1 pendiente, 1 ejecutado, 1 sin FK (no entra en el partial index)
    r1 = DocumentoReemplazo(documento_flujo_id=flujo.id, documento_viejo_id=doc_viejo.id,
                             codigo_documento_viejo=doc_viejo.codigo, ejecutado=False)
    r2 = DocumentoReemplazo(documento_flujo_id=flujo.id, documento_viejo_id=doc_viejo.id,
                             codigo_documento_viejo=doc_viejo.codigo, ejecutado=True)
    r3 = DocumentoReemplazo(documento_flujo_id=flujo.id, codigo_documento_viejo="OTRO/00")
    db_session.add_all([r1, r2, r3])
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(DocumentoReemplazo.id))
        .where(DocumentoReemplazo.ejecutado == False)
        .where(DocumentoReemplazo.documento_viejo_id.is_not(None))
    )
    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_fk_flujo_invalido(db_session, seed_catalogos):
    """FK documento_flujo_id: inexistente => IntegrityError."""
    r = DocumentoReemplazo(
        documento_flujo_id=999999, codigo_documento_viejo="CC-7-099/00",
    )
    db_session.add(r)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_codigo_sin_doc_existente_es_valido(db_session, seed_catalogos):
    """codigo_documento_viejo puede ser cualquier string (no es FK)."""
    flujo, _ = await _crear_flujo_y_doc_viejo(db_session, seed_catalogos)
    r = DocumentoReemplazo(
        documento_flujo_id=flujo.id,
        codigo_documento_viejo="LEGACY-99/00",  # no existe en BD
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    assert r.codigo_documento_viejo == "LEGACY-99/00"


@pytest.mark.asyncio
async def test_repr(db_session, seed_catalogos):
    flujo, _ = await _crear_flujo_y_doc_viejo(db_session, seed_catalogos)
    r = DocumentoReemplazo(
        documento_flujo_id=flujo.id, codigo_documento_viejo="CC-7-099/00",
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    rv = repr(r)
    assert "DocumentoReemplazo" in rv
    assert "CC-7-099/00" in rv
