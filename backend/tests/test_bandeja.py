"""
Tests para GET /api/v1/bandeja (Sesion 22 R2 FASE 2 - Tarea 2.5).
8 tests = 4 endpoints x 2 escenarios (con docs, sin docs).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento


# ─── Helpers ───

async def _crear_tipo(db_session, codigo: int, slug: str, nombre: str):
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == codigo)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=codigo, slug=slug, nombre=nombre,
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)
    return tipo


async def _crear_doc(db_session, seed_catalogos, codigo: str, version: str,
                     estatus: EstatusDocumento, created_by_id: int,
                     revisor_ids=None, aprobador_ids=None, correlativo: int = None):
    """Inserta Documento + DocumentoFlujo en la BD de test."""
    area = seed_catalogos["area"]
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")

    # Si no se pasa correlativo, derivar del codigo (ultimos 3 digitos)
    if correlativo is None:
        try:
            correlativo = int(codigo.split("-")[-1])
        except (ValueError, IndexError):
            correlativo = 99

    doc = Documento(
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        tipo_documento_id=tipo.id,
        correlativo=correlativo,
        codigo=codigo,
        version=version,
        titulo=f"Doc {codigo}",
        vigencia="VIGENTE",
        estatus=estatus,
        activo=True,
        created_by_id=created_by_id,
        updated_by_id=created_by_id,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    flujo = DocumentoFlujo(
        documento_id=doc.id,
        estado_actual_id=2 if estatus == EstatusDocumento.EN_REVISION else 1,
        tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        tipo_documento_id=tipo.id,
        codigo_snapshot=codigo,
        version_snapshot=version,
        titulo=f"Doc {codigo}",
        elaborador_id=created_by_id,
        cargo_elaborador="Test",
        fecha_solicitud=doc.created_at,
        requiere_evaluacion=False,
        requiere_control_lectura=False,
        alcance_difusion_ids=[],
        revisor_ids=revisor_ids or [],
        aprobador_ids=aprobador_ids or [],
        firma_usuario_id=created_by_id,
        firma_at=doc.created_at,
        activo=True,
        created_by_id=created_by_id,
    )
    db_session.add(flujo)
    await db_session.commit()
    return doc


# ════════════════════════════════════════════════════════════════
#  GET /bandeja?tipo=elaboracion
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_bandeja_elaboracion_sin_docs(client, seed_catalogos):
    """Sin docs en elaboracion: total=0."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    r = await client.get("/api/v1/bandeja?tipo=elaboracion", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["tipo"] == "elaboracion"
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_bandeja_elaboracion_con_docs(client, seed_catalogos, db_session):
    """Con docs en elaboracion del usuario: aparecen en la bandeja."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    await _crear_doc(db_session, seed_catalogos, "CC-3-100", "00", EstatusDocumento.EN_ELABORACION, eto.id)
    await _crear_doc(db_session, seed_catalogos, "CC-3-101", "00", EstatusDocumento.EN_ELABORACION, eto.id)

    r = await client.get("/api/v1/bandeja?tipo=elaboracion", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert {i["codigo"] for i in data["items"]} == {"CC-3-100", "CC-3-101"}


# ════════════════════════════════════════════════════════════════
#  GET /bandeja?tipo=revision
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_bandeja_revision_sin_docs(client, seed_catalogos):
    """Sin docs donde soy revisor: total=0."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    r = await client.get("/api/v1/bandeja?tipo=revision", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_bandeja_revision_con_docs(client, seed_catalogos, db_session):
    """Con docs donde soy revisor: aparecen en la bandeja."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    # Crear doc en EN_REVISION donde eto es revisor
    await _crear_doc(db_session, seed_catalogos, "CC-3-200", "00",
                     EstatusDocumento.EN_REVISION, eto.id,
                     revisor_ids=[eto.id], aprobador_ids=[1])
    # Crear doc en EN_REVISION donde eto NO es revisor
    await _crear_doc(db_session, seed_catalogos, "CC-3-201", "00",
                     EstatusDocumento.EN_REVISION, eto.id,
                     revisor_ids=[999], aprobador_ids=[1])

    r = await client.get("/api/v1/bandeja?tipo=revision", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "CC-3-200"
    assert data["items"][0]["requiere_mi_accion"] is True


# ════════════════════════════════════════════════════════════════
#  GET /bandeja?tipo=aprobacion
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_bandeja_aprobacion_sin_docs(client, seed_catalogos):
    """Sin docs donde soy aprobador: total=0."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    r = await client.get("/api/v1/bandeja?tipo=aprobacion", cookies=cookies)
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_bandeja_aprobacion_con_docs(client, seed_catalogos, db_session):
    """Con docs donde soy aprobador: aparecen en la bandeja."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    await _crear_doc(db_session, seed_catalogos, "CC-3-300", "00",
                     EstatusDocumento.EN_REVISION, eto.id,
                     revisor_ids=[1], aprobador_ids=[eto.id])

    r = await client.get("/api/v1/bandeja?tipo=aprobacion", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "CC-3-300"
    assert data["items"][0]["requiere_mi_accion"] is True


# ════════════════════════════════════════════════════════════════
#  GET /bandeja?tipo=liberacion
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_bandeja_liberacion_sin_docs(client, seed_catalogos):
    """ETO sin docs finalizados: total=0."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    r = await client.get("/api/v1/bandeja?tipo=liberacion", cookies=cookies)
    assert r.status_code == 200
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_bandeja_liberacion_con_docs(client, seed_catalogos, db_session):
    """ETO con docs finalizados: aparecen en la bandeja."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    await _crear_doc(db_session, seed_catalogos, "CC-3-400", "00",
                     EstatusDocumento.APROBADO, eto.id,
                     revisor_ids=[eto.id], aprobador_ids=[eto.id])

    r = await client.get("/api/v1/bandeja?tipo=liberacion", cookies=cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "CC-3-400"
    assert data["items"][0]["estatus"] == "APROBADO"
