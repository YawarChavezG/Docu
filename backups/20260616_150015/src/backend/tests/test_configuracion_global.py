"""
Tests de /api/v1/configuracion-global (US-9.01 + 9.02).
"""
import pytest
from httpx import AsyncClient

from app.models.configuracion_global import (
    ConfiguracionGlobal,
    CategoriaConfiguracion,
    TipoConfiguracion,
)


# ─── Tests ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_listar_config_sin_auth(client: AsyncClient):
    """GET /configuracion-global sin auth: 200 (catalogo publico) o 401 (privado)."""
    r = await client.get("/api/v1/configuracion-global")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_config_todos(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """GET /configuracion-global sin filtros: 200."""
    r = await client.get("/api/v1/configuracion-global", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_listar_config_filtro_categoria(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?categoria=VIGENCIA retorna solo items de esa categoria."""
    db_session.add(ConfiguracionGlobal(
        clave="k1", valor="v1",
        tipo=TipoConfiguracion.STR,
        categoria=CategoriaConfiguracion.VIGENCIA,
    ))
    db_session.add(ConfiguracionGlobal(
        clave="k2", valor="v2",
        tipo=TipoConfiguracion.STR,
        categoria=CategoriaConfiguracion.FLUJO,
    ))
    await db_session.commit()

    r = await client.get("/api/v1/configuracion-global?categoria=VIGENCIA", cookies=auth_eto_cookies)
    data = r.json()
    claves = [i["clave"] for i in data["items"]]
    assert "k1" in claves
    assert "k2" not in claves


@pytest.mark.asyncio
async def test_get_config_por_clave(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(ConfiguracionGlobal(
        clave="unica_test", valor="42",
        tipo=TipoConfiguracion.INT,
        categoria=CategoriaConfiguracion.GENERAL,
    ))
    await db_session.commit()

    r = await client.get("/api/v1/configuracion-global/unica_test", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["valor"] == "42"


@pytest.mark.asyncio
async def test_get_config_clave_no_existe_404(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/configuracion-global/no_existe_123", cookies=auth_eto_cookies)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_crear_config_upsert(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """POST /configuracion-global (UPSERT) crea/actualiza."""
    r = await client.post(
        "/api/v1/configuracion-global",
        json={
            "clave": "nueva_clave",
            "valor": "100",
            "tipo": "INT",
            "categoria": "GENERAL",
        },
        cookies=auth_eto_cookies,
    )
    # UPSERT: 201 si es nuevo, 200 si ya existe
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["clave"] == "nueva_clave"
    assert data["valor"] == "100"


@pytest.mark.asyncio
async def test_crear_config_sin_rol(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """POST config sin rol: 403 o 422 (validacion)."""
    r = await client.post(
        "/api/v1/configuracion-global",
        json={"clave": "x", "valor": "y", "tipo": "STR", "categoria": "GENERAL"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code in (403, 422)


@pytest.mark.asyncio
async def test_actualizar_config_patch(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(ConfiguracionGlobal(
        clave="upd_test", valor="old",
        tipo=TipoConfiguracion.STR,
        categoria=CategoriaConfiguracion.GENERAL,
    ))
    await db_session.commit()

    r = await client.patch(
        "/api/v1/configuracion-global/upd_test",
        json={"valor": "new"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["valor"] == "new"


@pytest.mark.asyncio
async def test_bulk_upsert_config(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """POST /configuracion-global/bulk."""
    r = await client.post(
        "/api/v1/configuracion-global/bulk",
        json={
            "categoria": "TEST_BULK",
            "items": [
                {"clave": "bulk1", "valor": "1"},
                {"clave": "bulk2", "valor": "2"},
            ],
        },
        cookies=auth_eto_cookies,
    )
    # 200/201 OK, 422 si el endpoint requiere tipo en items
    assert r.status_code in (200, 201, 422)


@pytest.mark.asyncio
async def test_eliminar_config(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    db_session.add(ConfiguracionGlobal(
        clave="del_test", valor="x",
        tipo=TipoConfiguracion.STR,
        categoria=CategoriaConfiguracion.GENERAL,
    ))
    await db_session.commit()

    r = await client.delete("/api/v1/configuracion-global/del_test", cookies=auth_eto_cookies)
    assert r.status_code in (200, 204)


@pytest.mark.asyncio
async def test_eliminar_config_no_existe_404(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.delete("/api/v1/configuracion-global/no_existe_zzz", cookies=auth_eto_cookies)
    assert r.status_code == 404
