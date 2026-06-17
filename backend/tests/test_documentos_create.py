"""
Tests para POST /documentos y PATCH /documentos/{id} (Sesion 22 R2 FASE 2).

Estrategia: usar el seed_catalogos (1 gerencia CAL, 1 area CC, 1 admin, 1 ETO aromero,
1 sin_rol solicitante) + crear tipos_documento adicionales.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento


# ─── Helpers ───

async def _crear_tipo_test(db_session, codigo: int, slug: str, nombre: str):
    """Inserta un TipoDocumento de test si no existe."""
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


# ════════════════════════════════════════════════════════════════
#  POST /documentos
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_crear_documento_eto_201(client: AsyncClient, seed_catalogos, db_session):
    """ETO puede crear un documento. Devuelve 201 con codigo autogenerado."""
    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]

    payload = {
        "gerencia_id": area.gerencia_id,
        "area_id": area.id,
        "tipo_documento_id": tipo.id,
        "titulo": "Procedimiento de Control de Documentos v1",
        "codigo_antiguo": "LEG-1-3-001",
        "comentarios_eto": "OK primera version",
        "tipo_solicitud": "CREACION",
    }

    resp = await client.post("/api/v1/documentos", json=payload, cookies={"user_id": str(eto.id), "session": "x", "csrf_token": "x"})
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert "documento" in data
    assert "flujo_id" in data
    doc = data["documento"]
    assert doc["codigo"] == f"CC-3-001"  # sigla area + tipo + correlativo 001
    assert doc["version"] == "00"
    assert doc["codigo_completo"] == "CC-3-001/00"
    assert doc["titulo"] == payload["titulo"]
    assert doc["estatus"] == "EN_ELABORACION"
    assert doc["vigencia"] == "VIGENTE"


@pytest.mark.asyncio
async def test_crear_documento_sin_titulo_422(client: AsyncClient, seed_catalogos, db_session):
    """Titulo < 3 chars: 422 (validacion Pydantic)."""
    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]

    payload = {
        "gerencia_id": area.gerencia_id,
        "area_id": area.id,
        "tipo_documento_id": tipo.id,
        "titulo": "AB",  # muy corto
        "tipo_solicitud": "CREACION",
    }
    resp = await client.post("/api/v1/documentos", json=payload, cookies={"user_id": str(eto.id), "session": "x"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_crear_documento_sin_auth_401(client: AsyncClient, seed_catalogos, db_session):
    """Sin auth: 401."""
    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    payload = {
        "gerencia_id": area.gerencia_id,
        "area_id": area.id,
        "tipo_documento_id": tipo.id,
        "titulo": "Doc sin auth",
        "tipo_solicitud": "CREACION",
    }
    resp = await client.post("/api/v1/documentos", json=payload)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_crear_documento_codigo_autogenerado_unico(client: AsyncClient, seed_catalogos, db_session):
    """2 docs en misma (area, tipo) → correlativos distintos (001, 002)."""
    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    # Primer doc
    r1 = await client.post("/api/v1/documentos", json={
        "gerencia_id": area.gerencia_id, "area_id": area.id,
        "tipo_documento_id": tipo.id, "titulo": "Doc 1", "tipo_solicitud": "CREACION",
    }, cookies=cookies)
    assert r1.status_code == 201
    assert r1.json()["documento"]["codigo"] == "CC-3-001"

    # Segundo doc
    r2 = await client.post("/api/v1/documentos", json={
        "gerencia_id": area.gerencia_id, "area_id": area.id,
        "tipo_documento_id": tipo.id, "titulo": "Doc 2", "tipo_solicitud": "CREACION",
    }, cookies=cookies)
    assert r2.status_code == 201
    assert r2.json()["documento"]["codigo"] == "CC-3-002"

    # Codigos distintos
    assert r1.json()["documento"]["codigo"] != r2.json()["documento"]["codigo"]


@pytest.mark.asyncio
async def test_crear_documento_area_no_pertenece_gerencia_422(client: AsyncClient, seed_catalogos, db_session):
    """Area de otra gerencia: 422."""
    from app.models.gerencia import Gerencia
    from app.models.area import Area

    # Crear otra gerencia + area
    g2 = Gerencia(sigla="OTR", nombre="OTRA GERENCIA", orden=99, activo=True)
    db_session.add(g2)
    await db_session.commit()
    await db_session.refresh(g2)
    a2 = Area(gerencia_id=g2.id, sigla="OT", nombre="OTRA AREA", activo=True, orden=1)
    db_session.add(a2)
    await db_session.commit()
    await db_session.refresh(a2)

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area_real = seed_catalogos["area"]
    eto = seed_catalogos["eto"]

    # Mando gerencia=1 pero area=g2 (inconsistente)
    resp = await client.post("/api/v1/documentos", json={
        "gerencia_id": area_real.gerencia_id,
        "area_id": a2.id,  # pertenece a g2
        "tipo_documento_id": tipo.id,
        "titulo": "Doc con inconsistencia",
        "tipo_solicitud": "CREACION",
    }, cookies={"user_id": str(eto.id), "session": "x"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_crear_documento_crea_flujo_inicial(client: AsyncClient, seed_catalogos, db_session):
    """El POST crea automaticamente un DocumentoFlujo en estado ELABORACION."""
    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]

    resp = await client.post("/api/v1/documentos", json={
        "gerencia_id": area.gerencia_id, "area_id": area.id,
        "tipo_documento_id": tipo.id, "titulo": "Test flujo",
        "tipo_solicitud": "CREACION",
    }, cookies={"user_id": str(eto.id), "session": "x"})
    assert resp.status_code == 201
    flujo_id = resp.json()["flujo_id"]

    # Verificar en BD
    flujo = await db_session.get(DocumentoFlujo, flujo_id)
    assert flujo is not None
    assert flujo.tipo_solicitud == TipoSolicitud.CREACION
    assert flujo.codigo_snapshot == "CC-3-001"
    assert flujo.version_snapshot == "00"
    assert flujo.titulo == "Test flujo"
    assert flujo.elaborador_id == eto.id


# ════════════════════════════════════════════════════════════════
#  PATCH /documentos/{id}
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_patch_documento_edita_titulo_200(client: AsyncClient, seed_catalogos, db_session):
    """PATCH de un doc en EN_ELABORACION: actualiza titulo."""
    # Crear doc de prueba
    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]

    r = await client.post("/api/v1/documentos", json={
        "gerencia_id": area.gerencia_id, "area_id": area.id,
        "tipo_documento_id": tipo.id, "titulo": "Titulo Original",
        "tipo_solicitud": "CREACION",
    }, cookies={"user_id": str(eto.id), "session": "x"})
    doc_id = r.json()["documento"]["id"]

    # Patch
    r2 = await client.patch(f"/api/v1/documentos/{doc_id}", json={
        "titulo": "Titulo Editado",
    }, cookies={"user_id": str(eto.id), "session": "x"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["titulo"] == "Titulo Editado"
    assert r2.json()["codigo"] == "CC-3-001"  # el codigo no cambia


@pytest.mark.asyncio
async def test_patch_documento_inexistente_404(client: AsyncClient, seed_catalogos):
    """PATCH a un doc que no existe: 404."""
    eto = seed_catalogos["eto"]
    r = await client.patch("/api/v1/documentos/99999", json={"titulo": "Doc valido largo"}, cookies={"user_id": str(eto.id), "session": "x"})
    assert r.status_code == 404
