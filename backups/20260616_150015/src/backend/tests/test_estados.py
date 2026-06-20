"""
Tests de /api/v1/estados.
"""
import pytest
from httpx import AsyncClient

from app.models.estado import Estado, ContextoEstado


@pytest.mark.asyncio
async def test_listar_estados_sin_auth(client: AsyncClient):
    """GET /estados sin auth: 200 (catalogo publico) o 401."""
    r = await client.get("/api/v1/estados")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_estados_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/estados", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_listar_estados_filtro_contexto(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(Estado(codigo="TEST_TAREA", nombre="Tarea Test", contexto=ContextoEstado.TAREA, activo=True))
    db_session.add(Estado(codigo="TEST_PROC", nombre="Proc Test", contexto=ContextoEstado.PROCESO, activo=True))
    await db_session.commit()

    r = await client.get("/api/v1/estados?contexto=TAREA", cookies=auth_eto_cookies)
    data = r.json()
    codigos = [e["codigo"] for e in data["items"]]
    assert "TEST_TAREA" in codigos
    assert "TEST_PROC" not in codigos


@pytest.mark.asyncio
async def test_crear_estado(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.post(
        "/api/v1/estados",
        json={"codigo": "NEWEST", "nombre": "Nuevo Estado", "contexto": "TAREA", "activo": True},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["codigo"] == "NEWEST"


@pytest.mark.asyncio
async def test_crear_estado_sin_rol(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """POST /estados sin rol: 403 o 422."""
    r = await client.post(
        "/api/v1/estados",
        json={"codigo": "X", "nombre": "X", "contexto": "TAREA"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code in (403, 422)


@pytest.mark.asyncio
async def test_actualizar_estado(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    e = Estado(codigo="EUP", nombre="Orig", contexto=ContextoEstado.TAREA, activo=True)
    db_session.add(e)
    await db_session.commit()
    await db_session.refresh(e)

    r = await client.patch(
        f"/api/v1/estados/{e.id}",
        json={"nombre": "Modificado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Modificado"


@pytest.mark.asyncio
async def test_eliminar_estado(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    e = Estado(codigo="EDEL", nombre="Borrar", contexto=ContextoEstado.TAREA, activo=True)
    db_session.add(e)
    await db_session.commit()
    await db_session.refresh(e)

    r = await client.delete(f"/api/v1/estados/{e.id}", cookies=auth_eto_cookies)
    assert r.status_code in (200, 204)
