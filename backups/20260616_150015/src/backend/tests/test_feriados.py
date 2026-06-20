"""
Tests de /api/v1/feriados.
"""
import pytest
from httpx import AsyncClient
from datetime import date

from app.models.feriado import Feriado


@pytest.mark.asyncio
async def test_listar_feriados_sin_auth(client: AsyncClient):
    """GET /feriados sin auth: 200 o 401 (catalogo publico)."""
    r = await client.get("/api/v1/feriados")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_feriados_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/feriados", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_listar_feriados_filtro_anio(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(Feriado(fecha=date(2027, 1, 1), nombre="Ano Nuevo 2027", tipo="NACIONAL"))
    db_session.add(Feriado(fecha=date(2026, 1, 1), nombre="Ano Nuevo 2026", tipo="NACIONAL"))
    await db_session.commit()

    r = await client.get("/api/v1/feriados?anio=2027", cookies=auth_eto_cookies)
    data = r.json()
    nombres = [f["nombre"] for f in data["items"]]
    assert "Ano Nuevo 2027" in nombres
    assert "Ano Nuevo 2026" not in nombres


@pytest.mark.asyncio
async def test_crear_feriado(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    r = await client.post(
        "/api/v1/feriados",
        json={"fecha": "2030-05-15", "nombre": "Feriado Test", "tipo": "NACIONAL", "activo": True},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Feriado Test"


@pytest.mark.asyncio
async def test_crear_feriado_sin_rol(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """POST /feriados sin rol: 403 o 422."""
    r = await client.post(
        "/api/v1/feriados",
        json={"fecha": "2030-05-15", "nombre": "X", "tipo": "NACIONAL"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code in (403, 422)


@pytest.mark.asyncio
async def test_crear_feriado_duplicado_409(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(Feriado(fecha=date(2030, 1, 1), nombre="Orig", tipo="NACIONAL"))
    await db_session.commit()

    r = await client.post(
        "/api/v1/feriados",
        json={"fecha": "2030-01-01", "nombre": "Dup", "tipo": "NACIONAL"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_actualizar_feriado(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    f = Feriado(fecha=date(2030, 6, 1), nombre="Orig", tipo="NACIONAL")
    db_session.add(f)
    await db_session.commit()
    await db_session.refresh(f)

    r = await client.patch(
        f"/api/v1/feriados/{f.id}",
        json={"nombre": "Modificado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Modificado"


@pytest.mark.asyncio
async def test_eliminar_feriado(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    f = Feriado(fecha=date(2030, 7, 1), nombre="Borrar", tipo="NACIONAL")
    db_session.add(f)
    await db_session.commit()
    await db_session.refresh(f)

    r = await client.delete(f"/api/v1/feriados/{f.id}", cookies=auth_eto_cookies)
    assert r.status_code in (200, 204)
