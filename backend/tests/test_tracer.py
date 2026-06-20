"""
Tracer bullet: validar que el setup de tests funciona end-to-end.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient):
    """El endpoint /health retorna 200 (vía nginx health) o el equivalente."""
    # Health via /api/v1/health (registrado en app.main con prefix /api/v1)
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("ok", "healthy")


@pytest.mark.asyncio
async def test_login_local_ok(client: AsyncClient, seed_catalogos):
    """El login contra BD local funciona con el password dummy."""
    r = await client.post(
        "/api/v1/login",
        json={"username": "admin", "password": "cofar.2026", "auth_source": "local"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["username"] == "admin"
    assert "ADMIN" in data["user"]["roles"]


@pytest.mark.asyncio
async def test_login_local_user_no_existe(client: AsyncClient):
    """Login falla con 401 si el usuario no existe en BD."""
    r = await client.post(
        "/api/v1/login",
        json={"username": "fantasma", "password": "cofar.2026", "auth_source": "local"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_local_password_incorrecto(client: AsyncClient, seed_catalogos):
    """Login falla con 401 si el password no es el dummy."""
    r = await client.post(
        "/api/v1/login",
        json={"username": "admin", "password": "WRONG", "auth_source": "local"},
    )
    assert r.status_code == 401
