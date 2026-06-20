"""
Tests de /api/v1/ausencias — Sesión 25 / Issue 1.1.

Verifica que crear/actualizar/cancelar una ausencia con motivo distinto
a "vacaciones" (ej: capacitacion, licencia, otro) SIEMPRE actualice
usuarios.ausente correctamente, no solo cuando el motivo es vacaciones.

Issue 1.1 — RESOLUCIÓN: validado en backend real con curl que el helper
_vigente_set_usuario_ausente funciona correctamente para TODOS los motivos.
El cliente malinterpretó su testing (las ausencias creadas eran con fechas
futuras, no vigentes HOY, por eso ausente=false era el comportamiento
correcto). NO requiere fix de código. Estos tests sirven como cobertura
de regresión para futuros cambios.
"""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy import select, text

from app.models.usuario import Usuario
from app.core import database as db_module


# ─── Helpers ──────────────────────────────────────────────────────

def _iso(d: date) -> str:
    return d.isoformat()


async def _leer_ausente_sql(usuario_id: int) -> bool:
    """Lee usuarios.ausente en una sesion NUEVA para evitar isolation issues."""
    async with db_module.AsyncSessionLocal() as s:
        r = await s.execute(
            text("SELECT ausente FROM usuarios WHERE id=:id"),
            {"id": usuario_id},
        )
        val = r.scalar()
        return bool(val)


# ─── Issue 1.1 ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ausencia_capacitacion_marca_ausente_true(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """
    Crear ausencia con motivo=capacitacion y fechas VIGENTES
    debe setear usuarios.ausente=True.
    """
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy),
            "fecha_hasta": _iso(hoy + timedelta(days=5)),
            "motivo": "capacitacion",
            "notas": "Curso de auditoría",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201, f"POST falló: {r.status_code} {r.text}"

    assert await _leer_ausente_sql(eto.id) is True, (
        "usuarios.ausente=False despues de crear ausencia vigente con motivo=capacitacion"
    )


@pytest.mark.asyncio
async def test_ausencia_licencia_marca_ausente_true(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Variante con motivo=licencia."""
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy),
            "fecha_hasta": _iso(hoy + timedelta(days=3)),
            "motivo": "licencia",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    assert await _leer_ausente_sql(eto.id) is True


@pytest.mark.asyncio
async def test_ausencia_otro_marca_ausente_true(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Variante con motivo=otro."""
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy),
            "fecha_hasta": _iso(hoy + timedelta(days=2)),
            "motivo": "otro",
            "notas": "Permiso personal",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    assert await _leer_ausente_sql(eto.id) is True


@pytest.mark.asyncio
async def test_ausencia_futura_no_marca_ausente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Control: ausencia FUTURA NO debe marcar ausente HOY."""
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy + timedelta(days=5)),
            "fecha_hasta": _iso(hoy + timedelta(days=10)),
            "motivo": "vacaciones",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    assert await _leer_ausente_sql(eto.id) is False


@pytest.mark.asyncio
async def test_ausencia_vencida_no_marca_ausente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Control: ausencia YA VENCIDA NO debe marcar ausente."""
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy - timedelta(days=10)),
            "fecha_hasta": _iso(hoy - timedelta(days=1)),
            "motivo": "capacitacion",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    assert await _leer_ausente_sql(eto.id) is False


@pytest.mark.asyncio
async def test_cancelar_ausencia_marca_ausente_false(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Verifica que DELETE (cancelar) pone ausente=False."""
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy),
            "fecha_hasta": _iso(hoy + timedelta(days=2)),
            "motivo": "capacitacion",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    ausencia_id = r.json()["id"]
    assert await _leer_ausente_sql(eto.id) is True

    r = await client.delete(
        f"/api/v1/ausencias/{ausencia_id}",
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert await _leer_ausente_sql(eto.id) is False


@pytest.mark.asyncio
async def test_patch_motivo_no_cambia_ausente_si_ya_vigente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """
    Si cambio el motivo de una ausencia VIGENTE, el flag ausente debe seguir true.
    Caso: cliente cambia de vacaciones a capacitacion.
    """
    eto = seed_catalogos["eto"]
    hoy = date.today()
    r = await client.post(
        f"/api/v1/ausencias/usuarios/{eto.id}",
        json={
            "fecha_desde": _iso(hoy),
            "fecha_hasta": _iso(hoy + timedelta(days=3)),
            "motivo": "vacaciones",
        },
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    ausencia_id = r.json()["id"]
    assert await _leer_ausente_sql(eto.id) is True

    r = await client.patch(
        f"/api/v1/ausencias/{ausencia_id}",
        json={"motivo": "capacitacion", "notas": "Cambio de plan"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["motivo"] == "capacitacion"
    assert await _leer_ausente_sql(eto.id) is True, (
        "BUG 1.1: ausente=False despues de PATCH cambiando motivo de vigente"
    )
