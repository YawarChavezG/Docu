"""
Tests de /api/v1/tipos-documento.
"""
import pytest
from httpx import AsyncClient

from app.models.tipo_documento import TipoDocumento


@pytest.mark.asyncio
async def test_listar_tipos_doc_sin_auth(client: AsyncClient):
    """GET /tipos-documento sin auth: 200 o 401."""
    r = await client.get("/api/v1/tipos-documento")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_tipos_doc_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/tipos-documento", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_listar_tipos_doc_filtro_q(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(TipoDocumento(
        codigo="TST1", nombre="Procedimiento Test", codigo_doc=99,
        periodo_vigencia=4, indefinido=False, activo=True,
    ))
    db_session.add(TipoDocumento(
        codigo="TST2", nombre="Manual de Prueba", codigo_doc=100,
        periodo_vigencia=3, indefinido=False, activo=True,
    ))
    await db_session.commit()

    r = await client.get("/api/v1/tipos-documento?q=proced", cookies=auth_eto_cookies)
    data = r.json()
    codigos = [t["codigo"] for t in data["items"]]
    assert "TST1" in codigos
    assert "TST2" not in codigos


@pytest.mark.asyncio
async def test_crear_tipo_doc(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.post(
        "/api/v1/tipos-documento",
        json={
            "codigo": "TSTCR",
            "nombre": "Tipo Test Crear",
            "codigo_doc": 50,
            "periodo_vigencia": 3,
            "indefinido": False,
            "activo": True,
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["codigo"] == "TSTCR"


@pytest.mark.asyncio
async def test_crear_tipo_doc_sin_rol(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """POST /tipos-documento sin rol: 403 o 422."""
    r = await client.post(
        "/api/v1/tipos-documento",
        json={"codigo": "X", "nombre": "X", "codigo_doc": 50, "periodo_vigencia": 1, "indefinido": False},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code in (403, 422)


@pytest.mark.asyncio
async def test_actualizar_tipo_doc(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    t = TipoDocumento(
        codigo="TSTUP", nombre="Orig", codigo_doc=300,
        periodo_vigencia=3, indefinido=False, activo=True,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)

    r = await client.patch(
        f"/api/v1/tipos-documento/{t.id}",
        json={"nombre": "Modificado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Modificado"


@pytest.mark.asyncio
async def test_eliminar_tipo_doc(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    t = TipoDocumento(
        codigo="TSTDEL", nombre="Borrar", codigo_doc=400,
        periodo_vigencia=3, indefinido=False, activo=True,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)

    r = await client.delete(f"/api/v1/tipos-documento/{t.id}", cookies=auth_eto_cookies)
    assert r.status_code in (200, 204)
