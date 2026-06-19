"""
Tests de /api/v1/usuarios (Sesion B - #9e).
List paginado + filtros + PATCH override + export XLSX/CSV.
"""
import pytest
from httpx import AsyncClient

from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion
from app.models.rol import CodigoRol, Rol
from app.models.modulo import CodigoModulo, Modulo


# ─── Helpers ─────────────────────────────────────────────────────────
async def _crear_usuario(
    db, *,
    username: str,
    email: str = None,
    nombre: str = "Test User",
    ad_postal_code: str = "99999999",
    estado=EstadoUsuario.ACTIVO,
    roles: list = None,
    modulos: list = None,
):
    """Crea un usuario adicional (no de seed)."""
    from app.models.area import Area
    u = Usuario(
        username=username,
        email=email or f"{username}@cofar.local",
        nombre_completo=nombre,
        iniciales="".join([p[0] for p in nombre.split()[:2]]).upper() or "?",
        cargo="Tester",
        area_id=None,
        estado=estado,
        estado_delegacion=EstadoDelegacion.NA,
        ad_postal_code=ad_postal_code,
    )
    if roles:
        for r in roles:
            u.roles.append(r)
    if modulos:
        for m in modulos:
            u.modulos.append(m)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


# ─── Tests: listar (solo ADMIN) ─────────────────────────────────────
@pytest.mark.asyncio
async def test_listar_usuarios_sin_auth_401(client: AsyncClient):
    """GET /usuarios sin auth: 401."""
    r = await client.get("/api/v1/usuarios")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_listar_usuarios_admin(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """GET /usuarios con ADMIN: 200 + KPIs."""
    r = await client.get("/api/v1/usuarios", cookies=auth_admin_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "kpis" in data
    # incluye los 3 del seed (admin, aromero, solicitante)
    assert data["total"] >= 3
    # kpis tiene total/activos/ausentes
    kpis = data["kpis"]
    assert "total" in kpis
    assert "activos" in kpis
    assert "ausentes" in kpis


@pytest.mark.asyncio
async def test_listar_usuarios_eto_200(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """GET /usuarios con ETO: 200 (sesion 9 relajo a ETO/ADMIN/roles-delegables)."""
    r = await client.get("/api/v1/usuarios", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "kpis" in data


@pytest.mark.asyncio
async def test_listar_usuarios_paginacion(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """GET /usuarios con page y page_size."""
    r = await client.get(
        "/api/v1/usuarios?page=1&page_size=2",
        cookies=auth_admin_cookies,
    )
    data = r.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total"] >= 3


@pytest.mark.asyncio
async def test_listar_usuarios_filtro_q(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """Filtro ?q= busca en username/nombre/email."""
    await _crear_usuario(db_session, username="zyxw", nombre="Maria Rodriguez")
    r = await client.get("/api/v1/usuarios?q=rodriguez", cookies=auth_admin_cookies)
    data = r.json()
    sigs = [u["username"] for u in data["items"]]
    assert "zyxw" in sigs


@pytest.mark.asyncio
async def test_listar_usuarios_filtro_estado(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """Filtro ?estado=inactivo retorna solo inactivos."""
    await _crear_usuario(db_session, username="ina1", estado=EstadoUsuario.INACTIVO)
    r = await client.get("/api/v1/usuarios?estado=inactivo", cookies=auth_admin_cookies)
    data = r.json()
    usernames = [u["username"] for u in data["items"]]
    assert "ina1" in usernames
    for u in data["items"]:
        assert u["estado"] == "inactivo"


@pytest.mark.asyncio
async def test_listar_usuarios_filtro_fuente_ad(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """Filtro ?fuente=ad retorna solo usuarios con azure_oid."""
    await _crear_usuario(db_session, username="local1", ad_postal_code=None)
    r = await client.get("/api/v1/usuarios?fuente=local", cookies=auth_admin_cookies)
    data = r.json()
    usernames = [u["username"] for u in data["items"]]
    assert "local1" in usernames


@pytest.mark.asyncio
async def test_listar_usuarios_filtro_rol(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """Filtro ?rol=ETO retorna solo usuarios con rol ETO."""
    r = await client.get("/api/v1/usuarios?rol=ETO", cookies=auth_admin_cookies)
    data = r.json()
    assert data["total"] >= 1
    for u in data["items"]:
        assert "ETO" in u["roles"]


# ─── Tests: GET /{id} ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_usuario_admin(client: AsyncClient, auth_admin_cookies, seed_catalogos):
    r = await client.get(f"/api/v1/usuarios/{seed_catalogos['eto'].id}", cookies=auth_admin_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "aromero"


@pytest.mark.asyncio
async def test_get_usuario_no_existente_404(client: AsyncClient, auth_admin_cookies, seed_catalogos):
    r = await client.get("/api/v1/usuarios/99999", cookies=auth_admin_cookies)
    assert r.status_code == 404


# ─── Tests: PATCH /{id} override ────────────────────────────────────
@pytest.mark.asyncio
async def test_override_usuario_cambiar_estado(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """ETO/ADMIN puede override estado/ausente (US-9.05). No puede cambiarse a si mismo."""
    target = seed_catalogos["sin_rol"]
    r = await client.patch(
        f"/api/v1/usuarios/{target.id}",
        json={"estado": "inactivo", "observaciones": "Suspendido test"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["estado"] == "inactivo"


@pytest.mark.asyncio
async def test_override_usuario_ausente(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Marcar ausente=True (vacaciones)."""
    target = seed_catalogos["eto"]
    r = await client.patch(
        f"/api/v1/usuarios/{target.id}",
        json={"ausente": True},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["ausente"] is True


@pytest.mark.asyncio
async def test_override_usuario_sin_perm_403(
    client: AsyncClient, auth_sin_rol_cookies, seed_catalogos
):
    target = seed_catalogos["eto"]
    r = await client.patch(
        f"/api/v1/usuarios/{target.id}",
        json={"ausente": True},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_override_usuario_no_existente_404(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    r = await client.patch(
        "/api/v1/usuarios/99999",
        json={"ausente": True},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_override_genera_audit(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Override de usuario debe generar entrada en audit_log con accion OVERRIDE."""
    from app.models.audit_log import AuditLog
    from sqlalchemy import select, func

    target = seed_catalogos["sin_rol"]
    await client.patch(
        f"/api/v1/usuarios/{target.id}",
        json={"estado": "activo", "observaciones": "Test audit"},
        cookies=auth_eto_cookies,
    )

    stmt = select(func.count(AuditLog.id)).where(
        AuditLog.recurso == "usuario",
        AuditLog.accion == "OVERRIDE",
        AuditLog.recurso_id == target.id,
    )
    res = await db_session.execute(stmt)
    assert res.scalar_one() >= 1


# ─── Tests: export ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_export_usuarios_xlsx_eto_o_admin(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    """Export a XLSX (default). Solo ETO/ADMIN."""
    r = await client.get("/api/v1/usuarios/export?formato=xlsx", cookies=auth_eto_cookies)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert r.headers["content-disposition"].startswith("attachment;")


@pytest.mark.asyncio
async def test_export_usuarios_csv(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    r = await client.get("/api/v1/usuarios/export?formato=csv", cookies=auth_eto_cookies)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")


@pytest.mark.asyncio
async def test_export_usuarios_sin_perm_403(
    client: AsyncClient, auth_sin_rol_cookies, seed_catalogos
):
    r = await client.get("/api/v1/usuarios/export", cookies=auth_sin_rol_cookies)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_export_usuarios_formato_invalido_422(
    client: AsyncClient, auth_eto_cookies, seed_catalogos
):
    r = await client.get("/api/v1/usuarios/export?formato=pdf", cookies=auth_eto_cookies)
    assert r.status_code == 422  # pattern ^(xlsx|csv)$


# ─── Tests: sync-ad ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_sync_ad_sin_ldap_503(
    client: AsyncClient, auth_admin_cookies, seed_catalogos
):
    """POST /usuarios/sync-ad sin LDAP_ENABLED: 503."""
    # LDAP_ENABLED=false en .env
    r = await client.post("/api/v1/usuarios/sync-ad", cookies=auth_admin_cookies)
    assert r.status_code == 503


# ─── Tests: sync-status ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_sync_status_admin(client: AsyncClient, auth_admin_cookies, seed_catalogos):
    r = await client.get("/api/v1/usuarios/sync-status", cookies=auth_admin_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "total_usuarios" in data
    assert "usuarios_del_ad" in data
    assert "usuarios_locales" in data
    assert data["total_usuarios"] >= 3
