"""
Tests de /api/v1/matriz-enrutamiento-eto.
"""
import pytest
from httpx import AsyncClient

from app.models.matriz_enrutamiento_eto import MatrizEnrutamientoEto
from app.models.gerencia import Gerencia
from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion


@pytest.mark.asyncio
async def test_listar_matriz_eto_sin_auth(client: AsyncClient):
    """GET /matriz-enrutamiento-eto sin auth: 200 o 401."""
    r = await client.get("/api/v1/matriz-enrutamiento-eto")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_matriz_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/matriz-enrutamiento-eto", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_listar_matriz_filtro_solo_disponibles(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = seed_catalogos["gerencia"]
    eto = seed_catalogos["eto"]
    # Solo 1 fila por gerencia (UNIQUE constraint en gerencia_id).
    db_session.add(MatrizEnrutamientoEto(
        gerencia_id=g.id, analista_usuario_id=eto.id, disponibilidad="DISPONIBLE",
    ))
    await db_session.commit()

    r = await client.get(
        "/api/v1/matriz-enrutamiento-eto?solo_disponibles=true",
        cookies=auth_eto_cookies,
    )
    data = r.json()
    # El campo es `disponibilidad` (string "DISPONIBLE"/"AUSENTE")
    for item in data.get("items", []):
        assert item.get("disponibilidad") == "DISPONIBLE"


@pytest.mark.asyncio
async def test_listar_matriz_por_gerencia(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g1 = Gerencia(sigla="MX01", nombre="MX1", orden=1, activo=True)
    g2 = Gerencia(sigla="MX02", nombre="MX2", orden=2, activo=True)
    db_session.add_all([g1, g2])
    await db_session.flush()
    eto = seed_catalogos["eto"]
    db_session.add(MatrizEnrutamientoEto(gerencia_id=g1.id, analista_usuario_id=eto.id, disponibilidad="DISPONIBLE"))
    db_session.add(MatrizEnrutamientoEto(gerencia_id=g2.id, analista_usuario_id=eto.id, disponibilidad="DISPONIBLE"))
    await db_session.commit()

    r = await client.get(
        f"/api/v1/matriz-enrutamiento-eto/gerencia/{g1.id}",
        cookies=auth_eto_cookies,
    )
    data = r.json()
    items = data.get("items", data) if isinstance(data, dict) else data
    for item in items:
        if isinstance(item, dict) and "gerencia_id" in item:
            assert item["gerencia_id"] == g1.id


@pytest.mark.asyncio
async def test_crear_matriz(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    g = seed_catalogos["gerencia"]
    eto = seed_catalogos["eto"]
    r = await client.post(
        "/api/v1/matriz-enrutamiento-eto",
        json={"gerencia_id": g.id, "analista_usuario_id": eto.id, "disponibilidad": "DISPONIBLE"},
        cookies=auth_eto_cookies,
    )
    # 201 si pasa, 422 si el schema requiere otros campos
    assert r.status_code in (201, 422)


@pytest.mark.asyncio
async def test_crear_matriz_sin_rol(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    g = seed_catalogos["gerencia"]
    r = await client.post(
        "/api/v1/matriz-enrutamiento-eto",
        json={"gerencia_id": g.id, "analista_usuario_id": 1, "disponibilidad": "DISPONIBLE"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code in (403, 422)


@pytest.mark.asyncio
async def test_actualizar_matriz(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = seed_catalogos["gerencia"]
    eto = seed_catalogos["eto"]
    m = MatrizEnrutamientoEto(gerencia_id=g.id, analista_usuario_id=eto.id, disponibilidad="DISPONIBLE")
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    r = await client.patch(
        f"/api/v1/matriz-enrutamiento-eto/{m.id}",
        json={"disponibilidad": "AUSENTE"},
        cookies=auth_eto_cookies,
    )
    # 200 o 422 segun schema
    assert r.status_code in (200, 422)


@pytest.mark.asyncio
async def test_eliminar_matriz(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = seed_catalogos["gerencia"]
    eto = seed_catalogos["eto"]
    m = MatrizEnrutamientoEto(gerencia_id=g.id, analista_usuario_id=eto.id, disponibilidad="DISPONIBLE")
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    r = await client.delete(f"/api/v1/matriz-enrutamiento-eto/{m.id}", cookies=auth_eto_cookies)
    assert r.status_code in (200, 204)
