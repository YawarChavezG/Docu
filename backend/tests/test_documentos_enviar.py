"""
Tests CRITICOS para POST /documentos/{id}/enviar (Sesion 22 R2 FASE 2 - Tarea 2.4).

Riesgo principal: atomicidad de la firma 2FA. Si la BD falla despues de
validar el password, NO debe quedar como firmado.

Cobertura:
- test_enviar_password_correcta_200: flujo feliz
- test_enviar_password_incorrecta_401: rechazo + NADA persistido
- test_enviar_sin_revisores_422: validacion wizard
- test_enviar_sin_aprobadores_422: validacion wizard
- test_enviar_doc_ya_enviado_409: re-envio
- test_enviar_captura_ip_y_user_agent: metadata de firma
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento
from app.models.documento_flujo import DocumentoFlujo
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


async def _crear_doc_en_elaboracion(client, cookies, area, tipo):
    """Crea un documento via POST en estatus EN_ELABORACION."""
    r = await client.post("/api/v1/documentos", json={
        "gerencia_id": area.gerencia_id, "area_id": area.id,
        "tipo_documento_id": tipo.id, "titulo": "Doc para enviar",
        "tipo_solicitud": "CREACION",
    }, cookies=cookies)
    assert r.status_code == 201
    return r.json()["documento"]["id"]


def _payload_enviar(doc_id: int, password: str = "cofar.2026", **overrides):
    """Genera un body valido para POST /enviar."""
    payload = {
        "password": password,
        "revisor_ids": [1, 2],
        "aprobador_ids": [3],
        "requiere_evaluacion": True,
        "requiere_control_lectura": True,
        "alcance_difusion_ids": [1, 2],
    }
    payload.update(overrides)
    return payload


# ════════════════════════════════════════════════════════════════
#  POST /documentos/{id}/enviar — los 6 tests mas importantes
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_enviar_password_correcta_200(client, seed_catalogos, db_session):
    """Password correcta: 200 + doc transiciona a LIBERACION_ETO (R3 item 0.6) + flujo con revisores."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id), cookies=cookies,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert data["documento_id"] == doc_id
    # R3 item 0.6: ahora va a LIBERACION_ETO (no directo a EN_REVISION).
    # ETO debe liberar el documento para que pase a EN_REVISION (ver test_liberar_200).
    assert data["estatus"] == "LIBERACION_ETO"

    # Verificar persistencia
    doc = await db_session.get(Documento, doc_id)
    assert doc.estatus == EstatusDocumento.LIBERACION_ETO

    # Verificar que el flujo tiene los revisores (se usaran cuando ETO libere)
    flujo = (await db_session.execute(
        select(DocumentoFlujo)
        .where(DocumentoFlujo.documento_id == doc_id)
        .where(DocumentoFlujo.activo == True)
    )).scalar_one()
    assert flujo.revisor_ids == [1, 2]
    assert flujo.aprobador_ids == [3]
    assert flujo.requiere_evaluacion is True
    assert flujo.requiere_control_lectura is True


@pytest.mark.asyncio
async def test_enviar_password_incorrecta_401(client, seed_catalogos, db_session):
    """Password incorrecta: 401 + NADA se persiste (rollback)."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)

    # Contar flujos antes
    flujos_antes = (await db_session.execute(
        select(DocumentoFlujo).where(DocumentoFlujo.documento_id == doc_id)
    )).scalars().all()

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id, password="WRONG_PASSWORD"), cookies=cookies,
    )
    assert resp.status_code == 401, resp.text
    assert "invalida" in resp.json()["detail"].lower()

    # Verificar que el doc SIGUE en EN_ELABORACION (rollback)
    doc = await db_session.get(Documento, doc_id)
    assert doc.estatus == EstatusDocumento.EN_ELABORACION

    # Verificar que el flujo NO se modifico (revisores vacios originales)
    flujo = (await db_session.execute(
        select(DocumentoFlujo)
        .where(DocumentoFlujo.documento_id == doc_id)
        .where(DocumentoFlujo.activo == True)
    )).scalar_one()
    assert flujo.revisor_ids == []  # vacio del POST inicial
    assert flujo.aprobador_ids == []


@pytest.mark.asyncio
async def test_enviar_sin_revisores_422(client, seed_catalogos, db_session):
    """Wizard sin revisores: 422."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id, revisor_ids=[]), cookies=cookies,
    )
    # 422 puede ser Pydantic (lista) o HTTPException (dict)
    assert resp.status_code == 422
    body = resp.json()
    if isinstance(body, dict) and "detail" in body:
        # HTTPException
        assert "revisor" in str(body["detail"]).lower()
    else:
        # Pydantic ValidationError (lista de errores)
        text = str(body).lower()
        assert "revisor" in text or "min_length" in text or "min_items" in text

    # El doc sigue en EN_ELABORACION
    doc = await db_session.get(Documento, doc_id)
    assert doc.estatus == EstatusDocumento.EN_ELABORACION


@pytest.mark.asyncio
async def test_enviar_sin_aprobadores_422(client, seed_catalogos, db_session):
    """Wizard sin aprobadores: 422."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id, aprobador_ids=[]), cookies=cookies,
    )
    assert resp.status_code == 422
    body = resp.json()
    if isinstance(body, dict) and "detail" in body:
        assert "aprobador" in str(body["detail"]).lower()
    else:
        text = str(body).lower()
        assert "aprobador" in text or "min_length" in text or "min_items" in text


@pytest.mark.asyncio
async def test_enviar_doc_ya_enviado_409(client, seed_catalogos, db_session):
    """Re-enviar un doc ya en EN_REVISION: 409."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)

    # Primer envio: OK
    r1 = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id), cookies=cookies,
    )
    assert r1.status_code == 200

    # Segundo envio: 409
    r2 = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id), cookies=cookies,
    )
    assert r2.status_code == 409
    assert "EN_REVISION" in r2.json()["detail"] or "elaboracion" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enviar_captura_ip_y_user_agent(client, seed_catalogos, db_session):
    """Firma captura IP y user-agent en el flujo."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id),
        cookies=cookies,
        headers={"user-agent": "Test-UA/1.0"},
    )
    assert resp.status_code == 200

    # Verificar metadata de firma
    flujo = (await db_session.execute(
        select(DocumentoFlujo)
        .where(DocumentoFlujo.documento_id == doc_id)
        .where(DocumentoFlujo.activo == True)
    )).scalar_one()
    assert flujo.firma_usuario_id == eto.id
    assert flujo.firma_at is not None
    assert flujo.firma_user_agent == "Test-UA/1.0"


# ════════════════════════════════════════════════════════════════
#  R3 item 0.6: flujo post-wizard va a ETO primero (LIBERACION_ETO)
#  + nuevo endpoint POST /documentos/{id}/liberar
#  Sesion 36 R3 - FASE 0
# ════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_liberar_200_transiciona_a_en_revision(client, seed_catalogos, db_session):
    """ETO llama /liberar despues de /enviar: el doc pasa de LIBERACION_ETO -> EN_REVISION."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    r1 = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id), cookies=cookies,
    )
    assert r1.status_code == 200
    assert r1.json()["estatus"] == "LIBERACION_ETO"

    r2 = await client.post(
        f"/api/v1/documentos/{doc_id}/liberar",
        json={"password": "cofar.2026"}, cookies=cookies,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["estatus"] == "EN_REVISION"

    doc = await db_session.get(Documento, doc_id)
    assert doc.estatus == EstatusDocumento.EN_REVISION


@pytest.mark.asyncio
async def test_liberar_sin_liberacion_eto_409(client, seed_catalogos, db_session):
    """Llamar /liberar en un doc que NO esta en LIBERACION_ETO devuelve 409."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    # NO llamamos /enviar, el doc sigue en EN_ELABORACION.
    r = await client.post(
        f"/api/v1/documentos/{doc_id}/liberar",
        json={"password": "cofar.2026"}, cookies=cookies,
    )
    assert r.status_code == 409
    assert "LIBERACION_ETO" in r.json()["detail"]


@pytest.mark.asyncio
async def test_liberar_password_incorrecta_401(client, seed_catalogos, db_session):
    """Password incorrecta: 401 + NADA se persiste."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id), cookies=cookies,
    )

    r = await client.post(
        f"/api/v1/documentos/{doc_id}/liberar",
        json={"password": "WRONG"}, cookies=cookies,
    )
    assert r.status_code == 401

    doc = await db_session.get(Documento, doc_id)
    assert doc.estatus == EstatusDocumento.LIBERACION_ETO
    # IP puede ser None en test (ASGITransport), pero al menos NO debe ser None tras un commit
    # (en produccion viene de request.client.host)


@pytest.mark.asyncio
async def test_liberar_documento_inexistente_404(client, seed_catalogos, db_session):
    """Llamar /liberar con un doc_id que no existe: 404."""
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    r = await client.post(
        "/api/v1/documentos/99999/liberar",
        json={"password": "cofar.2026"}, cookies=cookies,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_liberar_documento_sin_estado_revision_catalogo_500(client, seed_catalogos, db_session):
    """Si el catalogo de estados no tiene REVISION/EN_REVISION -> 500."""
    from app.models.estado import Estado
    # Eliminar el estado REVISION del catalogo
    await db_session.execute(
        __import__("sqlalchemy").delete(Estado).where(
            Estado.codigo.in_(["REVISION", "EN_REVISION"])
        )
    )
    await db_session.commit()

    tipo = await _crear_tipo(db_session, codigo=55, slug="LIB55", nombre="Liberar Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    # Enviar a LIBERACION_ETO
    r1 = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=_payload_enviar(doc_id), cookies=cookies,
    )
    assert r1.status_code == 200

    # Liberar (falla porque no hay estado REVISION en catalogo)
    r2 = await client.post(
        f"/api/v1/documentos/{doc_id}/liberar",
        json={"password": "cofar.2026"}, cookies=cookies,
    )
    assert r2.status_code == 500
    assert "REVISION" in r2.json()["detail"]


# ════════════════════════════════════════════════════════════════
#  R3 item 0.2: Actualizacion documental
#  Sesion 36 R3 - FASE 0
# ════════════════════════════════════════════════════════════════


async def _crear_doc_aprobado(client, cookies, area, tipo, correlativo=1, version="00", titulo="Doc Original"):
    """Helper: crea un documento y lo transiciona a APROBADO via /enviar + flujo fake."""
    # 1) Crear
    res = await client.post(
        "/api/v1/documentos",
        json={
            "gerencia_id": area.gerencia_id,
            "area_id": area.id,
            "tipo_documento_id": tipo.id,
            "titulo": titulo,
            "tipo_solicitud": "CREACION",
        },
        cookies=cookies,
    )
    assert res.status_code == 201, res.text
    return res.json()["documento"]["id"]


@pytest.mark.asyncio
async def test_list_actualizables_filtra_por_area_y_tipo(client, seed_catalogos, db_session):
    """GET /documentos/actualizables filtra por (area_id, tipo_documento_id)."""
    from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento

    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    # Crear 2 docs APROBADOS
    doc1 = await _crear_doc_aprobado(client, cookies, area, tipo, titulo="Doc 1")
    doc2 = await _crear_doc_aprobado(client, cookies, area, tipo, titulo="Doc 2")

    # Marcar como APROBADO directamente
    for doc_id in [doc1, doc2]:
        doc = await db_session.get(Documento, doc_id)
        doc.estatus = EstatusDocumento.APROBADO
        doc.vigencia = VigenciaDocumento.VIGENTE
    await db_session.commit()

    r = await client.get(
        f"/api/v1/documentos/actualizables?area_id={area.id}&tipo_documento_id={tipo.id}",
        cookies=cookies,
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert {x["id"] for x in items} == {doc1, doc2}
    # Verificar que el campo nombre_completo esta presente
    for item in items:
        assert "nombre_completo" in item
        assert "V00" in item["nombre_completo"]


@pytest.mark.asyncio
async def test_enviar_con_documento_actualizado_id_persiste_en_flujo(client, seed_catalogos, db_session):
    """R3 item 0.2: enviar con documento_actualizado_id lo persiste en flujo.documento_actualizado_id."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    # Crear doc original (simulado como APROBADO)
    doc_original_id = await _crear_doc_aprobado(client, cookies, area, tipo, titulo="Doc Original")
    doc_original = await db_session.get(Documento, doc_original_id)
    doc_original.estatus = EstatusDocumento.APROBADO
    doc_original.vigencia = VigenciaDocumento.VIGENTE
    await db_session.commit()

    # Crear doc NUEVO y enviar como actualizacion
    doc_nuevo_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    payload = _payload_enviar(doc_nuevo_id)
    payload["documento_actualizado_id"] = doc_original_id
    payload["justificacion"] = "Actualizacion de prueba"

    r = await client.post(
        f"/api/v1/documentos/{doc_nuevo_id}/enviar",
        json=payload, cookies=cookies,
    )
    assert r.status_code == 200, r.text

    # Verificar que el flujo tiene documento_actualizado_id
    flujo = (await db_session.execute(
        select(DocumentoFlujo)
        .where(DocumentoFlujo.documento_id == doc_nuevo_id)
        .where(DocumentoFlujo.activo == True)
    )).scalar_one()
    assert flujo.documento_actualizado_id == doc_original_id
    assert flujo.tipo_solicitud.value == "CREACION"  # el flujo guarda tipo_solicitud del create


@pytest.mark.asyncio
async def test_enviar_documento_actualizado_id_invalido_422(client, seed_catalogos, db_session):
    """Si documento_actualizado_id es el mismo que el nuevo doc, devuelve 422."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    payload = _payload_enviar(doc_id)
    payload["documento_actualizado_id"] = doc_id  # Mismo id

    r = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=payload, cookies=cookies,
    )
    assert r.status_code == 422
    assert "mismo" in r.json()["detail"].lower() or "no puede" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enviar_documento_actualizado_id_inexistente_404(client, seed_catalogos, db_session):
    """Si documento_actualizado_id no existe, devuelve 404."""
    tipo = await _crear_tipo(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}

    doc_id = await _crear_doc_en_elaboracion(client, cookies, area, tipo)
    payload = _payload_enviar(doc_id)
    payload["documento_actualizado_id"] = 99999  # No existe

    r = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json=payload, cookies=cookies,
    )
    assert r.status_code == 404
    assert "99999" in r.json()["detail"]
