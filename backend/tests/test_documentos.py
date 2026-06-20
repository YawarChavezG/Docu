"""
Tests de /api/v1/documentos (CORE del SGD).

Endpoints probados:
  GET /api/v1/documentos/buscar?q=...
  GET /api/v1/documentos/preview-codigo?tipo_id=&area_id=&tipo_solicitud=
  GET /api/v1/documentos/{id}
  GET /api/v1/documentos (paginado con filtros)
"""
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.documento import (
    Documento,
    EstatusDocumento,
    VigenciaDocumento,
)
from app.models.documento_flujo import (
    DocumentoFlujo,
    TipoSolicitud,
)
from app.models.tipo_documento import TipoDocumento


# ─── Helpers ───

async def _crear_doc_test(
    db_session,
    seed_catalogos,
    *,
    codigo: str = "CC-3-001",
    version: str = "00",
    titulo: str = "Doc Test",
    estatus: EstatusDocumento = EstatusDocumento.EN_ELABORACION,
    vigencia: VigenciaDocumento = VigenciaDocumento.VIGENTE,
    aprobacion_at=None,
    expira_at=None,
    correlativo: int = 1,
):
    """Inserta un Documento + DocumentoFlujo en la BD de test."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]

    # Crear tipo_documento si no existe (codigo=3)
    tipo_q = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 3)
    )).scalar_one_or_none()
    if not tipo_q:
        tipo_q = TipoDocumento(
            codigo=3, slug="POLITICA", nombre="Politica Test",
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo_q)
        await db_session.flush()
        await db_session.refresh(tipo_q)

    doc = Documento(
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        proceso_id=None,
        tipo_documento_id=tipo_q.id,
        correlativo=correlativo,
        codigo=codigo,
        version=version,
        titulo=titulo,
        aprobacion_at=aprobacion_at,
        expira_at=expira_at,
        vigencia=vigencia,
        estatus=estatus,
        codigo_antiguo=f"LEG-{area.id}-{tipo_q.id}-{correlativo:03d}",
        comentarios_eto="Test",
        activo=True,
        created_by_id=eto.id,
        updated_by_id=eto.id,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # Crear flujo asociado
    flujo = DocumentoFlujo(
        documento_id=doc.id,
        estado_actual_id=1,  # ELABORACION
        tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        tipo_documento_id=tipo_q.id,
        codigo_snapshot=codigo,
        version_snapshot=version,
        titulo=titulo,
        elaborador_id=eto.id,
        cargo_elaborador=eto.cargo,
        fecha_solicitud=aprobacion_at or datetime.now(timezone.utc),
        requiere_evaluacion=False,
        requiere_control_lectura=False,
        alcance_difusion_ids=[area.gerencia_id],
        revisor_ids=[eto.id],
        aprobador_ids=[eto.id],
        firma_usuario_id=eto.id,
        firma_at=aprobacion_at or datetime.now(timezone.utc),
        firma_ip="127.0.0.1",
        firma_user_agent="pytest",
        activo=True,
        created_by_id=eto.id,
    )
    db_session.add(flujo)
    await db_session.commit()
    return doc, flujo


# ════════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_buscar_documentos_sin_auth(client: AsyncClient):
    """GET /documentos/buscar sin auth: 401."""
    r = await client.get("/api/v1/documentos/buscar")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_preview_codigo_sin_auth(client: AsyncClient):
    """GET /documentos/preview-codigo sin auth: 401."""
    r = await client.get("/api/v1/documentos/preview-codigo?tipo_id=1&area_id=1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_documento_sin_auth(client: AsyncClient):
    """GET /documentos/{id} sin auth: 401."""
    r = await client.get("/api/v1/documentos/1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_documentos_sin_auth(client: AsyncClient):
    """GET /documentos sin auth: 401."""
    r = await client.get("/api/v1/documentos")
    assert r.status_code == 401


# ════════════════════════════════════════════════════════════════
#  /buscar  (autocomplete)
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_buscar_documentos_vacio(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """GET /documentos/buscar sin docs: 0 resultados."""
    r = await client.get("/api/v1/documentos/buscar", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_buscar_documentos_match_codigo(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """GET /documentos/buscar?q=CC-3: matchea el prefijo del codigo."""
    doc, _ = await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", titulo="Politica X"
    )
    r = await client.get("/api/v1/documentos/buscar?q=CC-3", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["codigo"] == "CC-3-001" for item in data["items"])


@pytest.mark.asyncio
async def test_buscar_documentos_match_titulo(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """GET /documentos/buscar?q=Procedimiento: matchea el titulo."""
    doc, _ = await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-5-001", titulo="Procedimiento de Calidad"
    )
    r = await client.get("/api/v1/documentos/buscar?q=Procedimiento", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert any(item["titulo"] == "Procedimiento de Calidad" for item in data["items"])


@pytest.mark.asyncio
async def test_buscar_documentos_no_incluye_inactivos(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Documentos con activo=False NO aparecen en /buscar."""
    doc, _ = await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-002", titulo="Doc Inactivo"
    )
    doc.activo = False
    await db_session.commit()

    r = await client.get("/api/v1/documentos/buscar?q=Inactivo", cookies=auth_eto_cookies)
    data = r.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_buscar_documentos_limit(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """GET /documentos/buscar?limit=5: respeta el limite."""
    for i in range(7):
        await _crear_doc_test(
            db_session, seed_catalogos,
            codigo=f"CC-3-{i+10:03d}", titulo=f"Doc {i}", correlativo=i+10,
        )
    r = await client.get(
        "/api/v1/documentos/buscar?q=CC-3&limit=5", cookies=auth_eto_cookies
    )
    data = r.json()
    assert data["total"] == 5


# ════════════════════════════════════════════════════════════════
#  /preview-codigo
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_preview_codigo_creacion(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """GET /documentos/preview-codigo?tipo_id=3&area_id=X&tipo_solicitud=CREACION:"""
    """devuelve codigo con version=00 y correlativo=1 si no hay docs previos."""
    area = seed_catalogos["area"]

    # Crear tipo
    tipo = TipoDocumento(
        codigo=3, slug="POLITICA", nombre="Politica",
        periodo_vigencia=4, indefinido=False, activo=True,
    )
    db_session.add(tipo)
    await db_session.commit()
    await db_session.refresh(tipo)

    r = await client.get(
        f"/api/v1/documentos/preview-codigo?tipo_id={tipo.id}&area_id={area.id}&tipo_solicitud=CREACION",
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["codigo"] == "CC-3-001"
    assert data["codigo_completo"] == "CC-3-001/00"
    assert data["version"] == "00"
    assert data["correlativo_sugerido"] == 1
    assert data["area_sigla"] == "CC"
    assert data["tipo_codigo"] == 3


@pytest.mark.asyncio
async def test_preview_codigo_creacion_con_existente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Preview con docs existentes: correlativo_sugerido = MAX+1."""
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", titulo="Existente 1",
        correlativo=1,
    )
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-002", titulo="Existente 2",
        correlativo=2,
    )

    area = seed_catalogos["area"]
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 3)
    )).scalar_one()

    r = await client.get(
        f"/api/v1/documentos/preview-codigo?tipo_id={tipo.id}&area_id={area.id}&tipo_solicitud=CREACION",
        cookies=auth_eto_cookies,
    )
    data = r.json()
    assert data["codigo"] == "CC-3-003"  # correlativo 3
    assert data["correlativo_sugerido"] == 3


@pytest.mark.asyncio
async def test_preview_codigo_actualizacion(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Preview ACTUALIZACION: version = MAX_VERSION+1, correlativo = MAX."""
    # Crear un doc con version 02 existente
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", version="02", titulo="Doc v02",
        correlativo=1,
    )
    area = seed_catalogos["area"]
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 3)
    )).scalar_one()

    r = await client.get(
        f"/api/v1/documentos/preview-codigo?tipo_id={tipo.id}&area_id={area.id}&tipo_solicitud=ACTUALIZACION",
        cookies=auth_eto_cookies,
    )
    data = r.json()
    assert data["version"] == "03"
    assert data["correlativo_sugerido"] == 1  # mismo correlativo que el v02


@pytest.mark.asyncio
async def test_preview_codigo_tipo_inexistente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Preview con tipo_id inexistente: 404."""
    r = await client.get(
        "/api/v1/documentos/preview-codigo?tipo_id=99999&area_id=1",
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_preview_codigo_validacion_tipo_solicitud(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """tipo_solicitud invalido: 422."""
    r = await client.get(
        "/api/v1/documentos/preview-codigo?tipo_id=1&area_id=1&tipo_solicitud=INVALIDO",
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 422


# ════════════════════════════════════════════════════════════════
#  GET /{id}  (detalle)
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_documento_existente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    doc, _ = await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", titulo="Mi Doc",
    )
    r = await client.get(f"/api/v1/documentos/{doc.id}", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["codigo"] == "CC-3-001"
    assert data["codigo_completo"] == "CC-3-001/00"
    assert data["titulo"] == "Mi Doc"
    assert data["area"]["sigla"] == "CC"
    assert data["gerencia"]["sigla"] == "CAL"
    assert data["tipo"]["codigo"] == 3
    assert len(data["flujos"]) >= 1


@pytest.mark.asyncio
async def test_get_documento_no_existente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    r = await client.get("/api/v1/documentos/99999", cookies=auth_eto_cookies)
    assert r.status_code == 404


# ════════════════════════════════════════════════════════════════
#  GET /  (lista paginada con filtros)
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_documentos_vacio(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    r = await client.get("/api/v1/documentos", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10


@pytest.mark.asyncio
async def test_list_documentos_con_datos(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    for i in range(3):
        await _crear_doc_test(
            db_session, seed_catalogos,
            codigo=f"CC-3-{i+1:03d}", titulo=f"Doc {i}", correlativo=i+1,
        )
    r = await client.get("/api/v1/documentos", cookies=auth_eto_cookies)
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_documentos_filtro_vigencia(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", titulo="Vencido",
        vigencia=VigenciaDocumento.VENCIDO, estatus=EstatusDocumento.APROBADO,
        aprobacion_at=datetime.now(timezone.utc) - timedelta(days=2000),
        expira_at=datetime.now(timezone.utc) - timedelta(days=200),
    )
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-002", titulo="Vigente",
        vigencia=VigenciaDocumento.VIGENTE, estatus=EstatusDocumento.EN_ELABORACION,
        correlativo=2,
    )
    r = await client.get(
        "/api/v1/documentos?vigencia=VENCIDO", cookies=auth_eto_cookies
    )
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "CC-3-001"


@pytest.mark.asyncio
async def test_list_documentos_filtro_estatus_invalido(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    r = await client.get(
        "/api/v1/documentos?estatus=INVALIDO", cookies=auth_eto_cookies
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_documentos_paginacion(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    for i in range(15):
        await _crear_doc_test(
            db_session, seed_catalogos,
            codigo=f"CC-3-{i+1:03d}", titulo=f"Doc {i}", correlativo=i+1,
        )
    r = await client.get(
        "/api/v1/documentos?page=2&page_size=5", cookies=auth_eto_cookies
    )
    data = r.json()
    assert data["total"] == 15
    assert data["page"] == 2
    assert data["page_size"] == 5
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_list_documentos_filtro_q(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", titulo="Procedimiento Especial"
    )
    await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-002", titulo="Manual Generico",
        correlativo=2,
    )
    r = await client.get("/api/v1/documentos?q=Especial", cookies=auth_eto_cookies)
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["titulo"] == "Procedimiento Especial"


@pytest.mark.asyncio
async def test_list_documentos_filtro_inactivo(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    doc, _ = await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-001", titulo="Activo"
    )
    doc2, _ = await _crear_doc_test(
        db_session, seed_catalogos, codigo="CC-3-002", titulo="Inactivo",
        correlativo=2,
    )
    doc2.activo = False
    await db_session.commit()

    # Default: solo activos
    r = await client.get("/api/v1/documentos", cookies=auth_eto_cookies)
    data = r.json()
    assert data["total"] == 1
    # activo=false: incluir inactivos
    r2 = await client.get("/api/v1/documentos?activo=false", cookies=auth_eto_cookies)
    data2 = r2.json()
    assert data2["total"] == 1  # 1 inactivo
