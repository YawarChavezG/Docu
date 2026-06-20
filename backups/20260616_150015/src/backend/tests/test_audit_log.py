"""
Tests de /api/v1/audit-log (Sesion B - tarea #9).

El audit-log es append-only: solo lectura desde la API.
Escritura la hace `app.core.audit.write_audit()` instrumentado en 8 routers.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit
from app.core.database import Base
from app.models.audit_log import AuditLog
from app.models.gerencia import Gerencia


# ─── Helpers ─────────────────────────────────────────────────────────
async def _crear_audit_directo(
    db: AsyncSession,
    usuario,
    *,
    accion: str = "CREATE",
    recurso: str = "gerencia",
    recurso_id: int = 1,
    descripcion: str = "Test audit",
    exitoso: bool = True,
):
    """Inserta una entrada de audit_log directamente (sin pasar por la API)."""
    entry = AuditLog(
        usuario_id=usuario.id if usuario else None,
        usuario_username=usuario.username if usuario else None,
        usuario_nombre=usuario.nombre_completo if usuario else None,
        accion=accion,
        recurso=recurso,
        recurso_id=recurso_id,
        descripcion=descripcion,
        detalles={"test": True},
        exitoso=exitoso,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# ─── Tests: acceso ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_log_sin_auth_retorna_403(client: AsyncClient):
    """Sin cookies de auth, requiere ETO/ADMIN. 401 (no hay sesion)."""
    r = await client.get("/api/v1/audit-log")
    # Sin cookies: require_eto_or_admin retorna 401
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_audit_log_eto_accede(client: AsyncClient, auth_eto_cookies):
    """ETO ve el audit log (200)."""
    r = await client.get("/api/v1/audit-log", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_audit_log_admin_accede(client: AsyncClient, auth_admin_cookies):
    """ADMIN ve el audit log (200)."""
    r = await client.get("/api/v1/audit-log", cookies=auth_admin_cookies)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_audit_log_usuario_sin_rol_rechazado(client: AsyncClient, auth_sin_rol_cookies):
    """Usuario sin rol ETO/ADMIN es rechazado (403)."""
    r = await client.get("/api/v1/audit-log", cookies=auth_sin_rol_cookies)
    assert r.status_code == 403


# ─── Tests: filtros ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_log_lista_vacia_al_principio(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """Sin entradas, retorna 0 items y total 0."""
    r = await client.get("/api/v1/audit-log", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_audit_log_filtro_por_accion(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?accion=CREATE retorna solo CREATE."""
    eto = seed_catalogos["eto"]
    await _crear_audit_directo(db_session, eto, accion="CREATE", recurso="gerencia", recurso_id=1)
    await _crear_audit_directo(db_session, eto, accion="UPDATE", recurso="gerencia", recurso_id=1)
    await _crear_audit_directo(db_session, eto, accion="DELETE", recurso="gerencia", recurso_id=1)

    r = await client.get("/api/v1/audit-log?accion=CREATE", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["accion"] == "CREATE"


@pytest.mark.asyncio
async def test_audit_log_filtro_por_recurso(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?recurso=area retorna solo entradas de area."""
    eto = seed_catalogos["eto"]
    await _crear_audit_directo(db_session, eto, recurso="gerencia", recurso_id=1)
    await _crear_audit_directo(db_session, eto, recurso="area", recurso_id=1)
    await _crear_audit_directo(db_session, eto, recurso="area", recurso_id=2)

    r = await client.get("/api/v1/audit-log?recurso=area", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    for it in data["items"]:
        assert it["recurso"] == "area"


@pytest.mark.asyncio
async def test_audit_log_filtro_por_usuario_id(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?usuario_id=X retorna solo entradas de ese usuario."""
    eto = seed_catalogos["eto"]
    admin = seed_catalogos["admin"]
    await _crear_audit_directo(db_session, eto, accion="CREATE")
    await _crear_audit_directo(db_session, eto, accion="UPDATE")
    await _crear_audit_directo(db_session, admin, accion="DELETE")

    r = await client.get(f"/api/v1/audit-log?usuario_id={admin.id}", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["usuario_username"] == "admin"


@pytest.mark.asyncio
async def test_audit_log_filtro_por_usuario_username(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?usuario_username=X (exacto)."""
    eto = seed_catalogos["eto"]
    admin = seed_catalogos["admin"]
    await _crear_audit_directo(db_session, eto, accion="CREATE")
    await _crear_audit_directo(db_session, admin, accion="DELETE")

    r = await client.get("/api/v1/audit-log?usuario_username=aromero", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["usuario_username"] == "aromero"


@pytest.mark.asyncio
async def test_audit_log_filtro_por_exitoso(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?exitoso=false retorna solo entradas con error."""
    eto = seed_catalogos["eto"]
    await _crear_audit_directo(db_session, eto, accion="CREATE", exitoso=True)
    await _crear_audit_directo(db_session, eto, accion="DELETE", exitoso=False, descripcion="FAIL test")

    r = await client.get("/api/v1/audit-log?exitoso=false", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["exitoso"] is False


@pytest.mark.asyncio
async def test_audit_log_paginacion(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Paginacion con limit y offset."""
    eto = seed_catalogos["eto"]
    for i in range(5):
        await _crear_audit_directo(db_session, eto, accion="CREATE", recurso_id=i)

    r1 = await client.get("/api/v1/audit-log?limit=2&offset=0", cookies=auth_eto_cookies)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["total"] == 5
    assert data1["limit"] == 2
    assert data1["offset"] == 0
    assert len(data1["items"]) == 2

    r2 = await client.get("/api/v1/audit-log?limit=2&offset=4", cookies=auth_eto_cookies)
    data2 = r2.json()
    assert len(data2["items"]) == 1  # solo queda 1


@pytest.mark.asyncio
async def test_audit_log_limit_max_200(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """Pide limit > 200 debe ser rechazado (Query validation)."""
    r = await client.get("/api/v1/audit-log?limit=500", cookies=auth_eto_cookies)
    assert r.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_audit_log_ordenado_desc_por_fecha(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Las entradas vienen ordenadas por created_at DESC (mas reciente primero)."""
    import asyncio
    eto = seed_catalogos["eto"]
    e1 = await _crear_audit_directo(db_session, eto, accion="CREATE", descripcion="primera")
    await asyncio.sleep(0.05)  # asegurar diferencia temporal
    e2 = await _crear_audit_directo(db_session, eto, accion="UPDATE", descripcion="segunda")
    await asyncio.sleep(0.05)
    e3 = await _crear_audit_directo(db_session, eto, accion="DELETE", descripcion="tercera")

    r = await client.get("/api/v1/audit-log", cookies=auth_eto_cookies)
    data = r.json()
    assert data["total"] == 3
    # La primera (en orden) es la mas reciente = e3
    assert data["items"][0]["id"] == e3.id
    assert data["items"][2]["id"] == e1.id
