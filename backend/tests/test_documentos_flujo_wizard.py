"""
Tests de /api/v1/documentos/{id}/enviar — Sesión 25 / Issue 11.3.

Verifica que el flujo SÍ persiste los datos del wizard paso 3
(revisores, aprobadores, alcance, justificacion, etc.) al firmar.

Issue 11.3 — El cliente reportó que después de completar los 3 wizards
y firmar, la tabla documento_flujo no tenía los datos. Investigado:
el backend SÍ actualiza (envio_service.py:198-212 con atomic commit
en linea 262). El cliente probablemente miró la tabla antes de firmar
o en un documento creado antes del fix.

Estos tests sirven como cobertura de regresión para futuros cambios.
"""
import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core import database as db_module
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo
from app.models.tipo_documento import TipoDocumento
from app.models.gerencia import Gerencia
from app.models.area import Area


# ─── Helpers ──────────────────────────────────────────────────────

async def _leer_flujo_sql(documento_id: int) -> dict | None:
    """Lee documento_flujo en sesion NUEVA para evitar isolation."""
    async with db_module.AsyncSessionLocal() as s:
        r = await s.execute(
            text("""
                SELECT
                    revisor_ids, aprobador_ids, alcance_difusion_ids,
                    reemplaza_documento_ids, justificacion,
                    requiere_evaluacion, requiere_control_lectura,
                    firma_usuario_id, firma_at
                FROM documento_flujo
                WHERE documento_id = :did AND activo = true
            """),
            {"did": documento_id},
        )
        row = r.fetchone()
        if row is None:
            return None

        def _parse(val):
            """SQLite devuelve JSON como string. Parsear a list/dict."""
            if val is None or val == "":
                return None
            if isinstance(val, (list, dict)):
                return val
            try:
                return json.loads(val)
            except (TypeError, ValueError):
                return val

        return {
            "revisor_ids": _parse(row[0]) or [],
            "aprobador_ids": _parse(row[1]) or [],
            "alcance_difusion_ids": _parse(row[2]) or [],
            "reemplaza_documento_ids": _parse(row[3]),
            "justificacion": row[4],
            "requiere_evaluacion": bool(row[5]),
            "requiere_control_lectura": bool(row[6]),
            "firma_usuario_id": row[7],
            "firma_at": row[8],
        }


# ─── Setup helper ──────────────────────────────────────────────────

async def _crear_documento_test(
    client, eto_cookies, sin_rol_cookies, seed_catalogos, db_session
):
    """Crea un documento via POST, sube archivo y devuelve (doc_id, flujo_id, gerencia_id)."""
    eto = seed_catalogos["eto"]
    ger = seed_catalogos["gerencia"]
    area = seed_catalogos["area"]

    # Crear estado REVISION (Sesion 23 / Bloque B3: codigo REVISION en catalogo)
    from app.models.estado import Estado, ContextoEstado
    estado_rev = Estado(
        codigo="REVISION", nombre="Revision", contexto=ContextoEstado.TAREA,
        descripcion="Documento en revision por revisores", orden=10, activo=True,
    )
    db_session.add(estado_rev)
    await db_session.commit()
    await db_session.refresh(estado_rev)

    # Crear tipo doc
    tipo = TipoDocumento(
        codigo=99, slug="test-11-3", nombre="Test 11.3",
        periodo_vigencia=4, max_descargas_dia=10, activo=True, indefinido=False,
    )
    db_session.add(tipo)
    await db_session.commit()
    await db_session.refresh(tipo)

    # Crear area
    area_test = Area(
        gerencia_id=ger.id, sigla="T113", nombre="Area Test 11.3",
        activo=True, orden=99,
    )
    db_session.add(area_test)
    await db_session.commit()
    await db_session.refresh(area_test)

    # POST documento (el solicitante crea el doc)
    r = await client.post(
        "/api/v1/documentos",
        json={
            "tipo_documento_id": tipo.id,
            "gerencia_id": ger.id,
            "area_id": area_test.id,
            "tipo_solicitud": "CREACION",
            "titulo": "TEST 11.3 wizard flujo",
            "justificacion": "Creado por test pytest",
        },
        cookies=sin_rol_cookies,
    )
    assert r.status_code in (200, 201), f"POST /documentos fallo: {r.status_code} {r.text}"
    body = r.json()
    doc_id = body["documento"]["id"]
    flujo_id = body["flujo_id"]
    return doc_id, flujo_id, ger.id, eto.id


# ─── Issue 11.3 ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_wizard_flujo_persiste_revisores_aprobadores(
    client, auth_eto_cookies, auth_sin_rol_cookies, seed_catalogos, db_session
):
    """
    POST /documentos crea flujo VACIO. POST /enviar con firma 2FA
    debe persistir revisor_ids, aprobador_ids, alcance_difusion_ids,
    justificacion, etc. en documento_flujo.
    """
    # Crear 2 usuarios extra para ser revisor/aprobador
    from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion
    from app.models.rol import Rol, CodigoRol

    eto = seed_catalogos["eto"]
    sin_rol = seed_catalogos["sin_rol"]
    rol_rev = (await db_session.execute(
        select(Rol).where(Rol.codigo == CodigoRol.ELABORADOR_REVISOR)
    )).scalar_one()

    revisor = Usuario(
        username="revisor_t113", email="rev113@x", nombre_completo="Revisor Test 11.3",
        iniciales="RT", cargo="Revisor", area_id=seed_catalogos["area"].id,
        estado=EstadoUsuario.ACTIVO, estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code="99000113",
    )
    revisor.roles.append(rol_rev)
    aprobador = Usuario(
        username="aprobador_t113", email="apr113@x", nombre_completo="Aprobador Test 11.3",
        iniciales="AT", cargo="Aprobador", area_id=seed_catalogos["area"].id,
        estado=EstadoUsuario.ACTIVO, estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code="99000114",
    )
    aprobador.roles.append(rol_rev)
    db_session.add_all([revisor, aprobador])
    await db_session.commit()
    await db_session.refresh(revisor)
    await db_session.refresh(aprobador)

    doc_id, flujo_id, ger_id, _ = await _crear_documento_test(
        client, auth_eto_cookies, auth_sin_rol_cookies, seed_catalogos, db_session
    )

    # Verificar que el flujo INICIAL tiene arrays vacios
    flujo_inicial = await _leer_flujo_sql(doc_id)
    assert flujo_inicial is not None
    assert flujo_inicial["revisor_ids"] in (None, [], "[]"), f"Flujo inicial deberia estar vacio: {flujo_inicial['revisor_ids']}"
    assert flujo_inicial["aprobador_ids"] in (None, [], "[]")
    # NOTA: firma_usuario_id SI se setea al crear el doc (línea 596 de
    # documentos.py: firma_inicial con user.id del creador). Solo se
    # actualiza con el ETO firmante en POST /enviar (envio_service.py:209).

    # POST /enviar con firma 2FA (como ETO)
    r = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json={
            "password": "cofar.2026",
            "revisor_ids": [revisor.id],
            "aprobador_ids": [aprobador.id],
            "requiere_evaluacion": True,
            "requiere_control_lectura": True,
            "alcance_difusion_ids": [ger_id],
            "reemplaza_documento_ids": None,
            "justificacion": "Justificacion completa del wizard paso 3 TEST 11.3",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200, f"POST /enviar fallo: {r.status_code} {r.text}"

    # Verificar que el flujo FINAL tiene TODOS los datos
    flujo_final = await _leer_flujo_sql(doc_id)
    assert flujo_final is not None
    assert revisor.id in flujo_final["revisor_ids"], f"revisor_ids no contiene {revisor.id}: {flujo_final['revisor_ids']}"
    assert aprobador.id in flujo_final["aprobador_ids"], f"aprobador_ids no contiene {aprobador.id}: {flujo_final['aprobador_ids']}"
    assert ger_id in flujo_final["alcance_difusion_ids"], f"alcance_difusion_ids no contiene {ger_id}"
    assert flujo_final["justificacion"] == "Justificacion completa del wizard paso 3 TEST 11.3"
    assert flujo_final["requiere_evaluacion"] is True
    assert flujo_final["requiere_control_lectura"] is True
    assert flujo_final["firma_usuario_id"] is not None
    assert flujo_final["firma_at"] is not None


@pytest.mark.asyncio
async def test_wizard_flujo_persiste_reemplaza_documento_ids(
    client, auth_eto_cookies, auth_sin_rol_cookies, seed_catalogos, db_session
):
    """Verifica que reemplaza_documento_ids (Issue 11.2 fix) tambien persiste."""
    from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion
    from app.models.rol import Rol, CodigoRol

    eto = seed_catalogos["eto"]
    sin_rol = seed_catalogos["sin_rol"]
    rol_rev = (await db_session.execute(
        select(Rol).where(Rol.codigo == CodigoRol.ELABORADOR_REVISOR)
    )).scalar_one()

    revisor = Usuario(
        username="rev2_t113", email="rev2@x", nombre_completo="Revisor 2",
        iniciales="R2", cargo="Revisor", area_id=seed_catalogos["area"].id,
        estado=EstadoUsuario.ACTIVO, estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code="99000115",
    )
    revisor.roles.append(rol_rev)
    db_session.add(revisor)
    await db_session.commit()
    await db_session.refresh(revisor)

    doc_id, flujo_id, ger_id, _ = await _crear_documento_test(
        client, auth_eto_cookies, auth_sin_rol_cookies, seed_catalogos, db_session
    )

    r = await client.post(
        f"/api/v1/documentos/{doc_id}/enviar",
        json={
            "password": "cofar.2026",
            "revisor_ids": [revisor.id],
            "aprobador_ids": [revisor.id],
            "alcance_difusion_ids": [],
            # Sub-bug fix Issue 11.2: enviar chips con codigos (no [])
            "reemplaza_documento_ids": ["CC-3-005/00", "CC-3-006/01"],
            "justificacion": "Reemplaza docs viejos",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200, f"POST /enviar fallo: {r.status_code} {r.text}"

    flujo = await _leer_flujo_sql(doc_id)
    assert flujo["reemplaza_documento_ids"] == ["CC-3-005/00", "CC-3-006/01"], (
        f"BUG 11.2: reemplaza_documento_ids no se persisten: {flujo['reemplaza_documento_ids']}"
    )
