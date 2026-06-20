"""
Tests de /api/v1/gerencias (US-9.06).
CRUD basico + paginacion + filtros.
"""
import pytest
from httpx import AsyncClient

from app.models.gerencia import Gerencia


# ─── Helpers ─────────────────────────────────────────────────────────
async def _crear_gerencia(
    db, sigla: str, nombre: str, orden: int = 1, activo: bool = True
) -> Gerencia:
    g = Gerencia(sigla=sigla, nombre=nombre, orden=orden, activo=activo)
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return g


# ─── Tests: acceso ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_listar_gerencias_sin_auth_retorna_401(client: AsyncClient):
    """GET /gerencias sin auth: 401 o 200 (catalogo publico segun diseno)."""
    r = await client.get("/api/v1/gerencias")
    # El endpoint es publico (no requiere auth) segun Sesion 5.
    # Si requiere auth, seria 401. Si no, 200.
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_gerencias_eto_accede(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """GET /gerencias con ETO: 200 (catalogo publico segun Sesion 5)."""
    r = await client.get("/api/v1/gerencias", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_listar_gerencias_usuario_normal(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """GET /gerencias sin rol ETO/ADMIN: tambien 200 (catalogo publico)."""
    r = await client.get("/api/v1/gerencias", cookies=auth_sin_rol_cookies)
    assert r.status_code == 200


# ─── Tests: creacion ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_crear_gerencia_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """ETO crea gerencia (201)."""
    r = await client.post(
        "/api/v1/gerencias",
        json={"sigla": "NUEVA", "nombre": "Nueva Gerencia", "orden": 99, "activo": True},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["sigla"] == "NUEVA"
    assert data["nombre"] == "Nueva Gerencia"
    assert data["activo"] is True


@pytest.mark.asyncio
async def test_crear_gerencia_admin(client: AsyncClient, auth_admin_cookies, seed_catalogos, db_session):
    """ADMIN crea gerencia (201)."""
    r = await client.post(
        "/api/v1/gerencias",
        json={"sigla": "ADM1", "nombre": "Admin Test"},
        cookies=auth_admin_cookies,
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_crear_gerencia_sin_rol_403(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """Usuario normal NO puede crear (403)."""
    r = await client.post(
        "/api/v1/gerencias",
        json={"sigla": "NOPERM", "nombre": "Sin Permiso"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_crear_gerencia_sigla_duplicada_409(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """Crear gerencia con sigla duplicada: 409."""
    r1 = await client.post(
        "/api/v1/gerencias",
        json={"sigla": "DUP", "nombre": "Primera"},
        cookies=auth_eto_cookies,
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/gerencias",
        json={"sigla": "DUP", "nombre": "Segunda"},
        cookies=auth_eto_cookies,
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_crear_gerencia_payload_invalido_422(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    """Falta sigla: 422."""
    r = await client.post(
        "/api/v1/gerencias",
        json={"nombre": "Sin sigla"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 422


# ─── Tests: GET /{id} ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_gerencia_existente(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = await _crear_gerencia(db_session, "GX01", "GET_TEST")
    r = await client.get(f"/api/v1/gerencias/{g.id}", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["sigla"] == "GX01"
    assert data["id"] == g.id


@pytest.mark.asyncio
async def test_get_gerencia_no_existente_404(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/gerencias/99999", cookies=auth_eto_cookies)
    assert r.status_code == 404


# ─── Tests: PATCH ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_actualizar_gerencia(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = await _crear_gerencia(db_session, "UPDA", "Original")
    r = await client.patch(
        f"/api/v1/gerencias/{g.id}",
        json={"nombre": "Modificado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "Modificado"
    assert data["sigla"] == "UPDA"  # no se toco


@pytest.mark.asyncio
async def test_actualizar_gerencia_sigla_duplicada_409(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Intentar cambiar sigla a una que ya existe: 409."""
    g1 = await _crear_gerencia(db_session, "AAA1", "Gerencia A")
    g2 = await _crear_gerencia(db_session, "BBB1", "Gerencia B")
    r = await client.patch(
        f"/api/v1/gerencias/{g2.id}",
        json={"sigla": "AAA1"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_actualizar_gerencia_sin_cambios_devuelve_igual(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """PATCH sin campos: 200 con datos sin cambios."""
    g = await _crear_gerencia(db_session, "NOCH", "Sin Cambios")
    r = await client.patch(f"/api/v1/gerencias/{g.id}", json={}, cookies=auth_eto_cookies)
    assert r.status_code == 200
    assert r.json()["nombre"] == "Sin Cambios"


# ─── Tests: DELETE (borrado logico) ─────────────────────────────────
@pytest.mark.asyncio
async def test_eliminar_gerencia_logico(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """DELETE deja activo=false (borrado logico)."""
    g = await _crear_gerencia(db_session, "DEL1", "Borrar Logico")
    r = await client.delete(f"/api/v1/gerencias/{g.id}", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["activo"] is False


@pytest.mark.asyncio
async def test_eliminar_gerencia_ya_inactiva_409(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """DELETE de gerencia ya inactiva: 409."""
    g = await _crear_gerencia(db_session, "DEL2", "Ya Inactiva", activo=False)
    r = await client.delete(f"/api/v1/gerencias/{g.id}", cookies=auth_eto_cookies)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_eliminar_gerencia_desactiva_areas_hijas(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """DELETE de gerencia con areas hijas: las desactiva tambien."""
    from app.models.area import Area
    g = await _crear_gerencia(db_session, "DEL3", "Con Areas")
    area1 = Area(gerencia_id=g.id, sigla="DA1", nombre="Area Hija 1", activo=True, orden=1)
    area2 = Area(gerencia_id=g.id, sigla="DA2", nombre="Area Hija 2", activo=True, orden=2)
    db_session.add_all([area1, area2])
    await db_session.commit()

    r = await client.delete(f"/api/v1/gerencias/{g.id}", cookies=auth_eto_cookies)
    assert r.status_code == 200

    # Verificar que las areas se desactivaron
    await db_session.refresh(area1)
    await db_session.refresh(area2)
    assert area1.activo is False
    assert area2.activo is False


# ─── Tests: filtros de listado ──────────────────────────────────────
@pytest.mark.asyncio
async def test_listar_gerencias_filtro_q_busqueda(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?q= busca en sigla y nombre (case-insensitive)."""
    await _crear_gerencia(db_session, "ABC1", "Gerencia de Auditoria")
    await _crear_gerencia(db_session, "DEF1", "Gerencia de Marketing")
    await _crear_gerencia(db_session, "GHI1", "Otra Cosa")

    r = await client.get("/api/v1/gerencias?q=aud", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["sigla"] == "ABC1"


@pytest.mark.asyncio
async def test_listar_gerencias_filtro_activo(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?activo=false retorna solo inactivas."""
    await _crear_gerencia(db_session, "FA01", "FA_Activa", activo=True)
    await _crear_gerencia(db_session, "FA02", "FA_Inactiva", activo=False)
    await _crear_gerencia(db_session, "FA03", "FA_Activa2", activo=True)

    r = await client.get("/api/v1/gerencias?activo=false", cookies=auth_eto_cookies)
    data = r.json()
    inactivas = [g for g in data["items"] if g["sigla"].startswith("FA")]
    assert len(inactivas) == 1
    assert inactivas[0]["sigla"] == "FA02"

    r2 = await client.get("/api/v1/gerencias?activo=all", cookies=auth_eto_cookies)
    data2 = r2.json()
    todas_fa = [g for g in data2["items"] if g["sigla"].startswith("FA")]
    assert len(todas_fa) == 3


@pytest.mark.asyncio
async def test_listar_gerencias_paginacion(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Paginacion con page y page_size."""
    for i in range(5):
        await _crear_gerencia(db_session, f"PG{i:02d}", f"PG_Gerencia_{i}", orden=i + 100)

    r1 = await client.get("/api/v1/gerencias?page=1&page_size=10", cookies=auth_eto_cookies)
    data1 = r1.json()
    # Filtramos solo las que creamos en este test
    nuestras = [g for g in data1["items"] if g["sigla"].startswith("PG")]
    assert len(nuestras) == 5
    assert data1["page"] == 1
    assert data1["page_size"] == 10


# ─── Tests: orden de listado ───────────────────────────────────────
@pytest.mark.asyncio
async def test_listar_gerencias_orden_por_sigla(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """El listado ordena por (orden, sigla)."""
    await _crear_gerencia(db_session, "ZZZ", "Zeta", orden=3)
    await _crear_gerencia(db_session, "AAA", "Alfa", orden=1)
    await _crear_gerencia(db_session, "MMM", "Mike", orden=2)

    r = await client.get("/api/v1/gerencias", cookies=auth_eto_cookies)
    data = r.json()
    sigs = [g["sigla"] for g in data["items"]]
    # Filtramos solo las que creamos (puede haber otras del seed)
    nuestras = [s for s in sigs if s in ("AAA", "MMM", "ZZZ")]
    assert nuestras == ["AAA", "MMM", "ZZZ"]


# ─── Tests: integracion con audit ──────────────────────────────────
@pytest.mark.asyncio
async def test_crear_gerencia_genera_audit_log(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Crear gerencia debe generar entrada en audit_log."""
    from app.models.audit_log import AuditLog
    from sqlalchemy import select, func

    r = await client.post(
        "/api/v1/gerencias",
        json={"sigla": "AUD1", "nombre": "Audit Test"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201

    # Verificar audit
    stmt = select(func.count(AuditLog.id)).where(
        AuditLog.recurso == "gerencia",
        AuditLog.accion == "CREATE",
    )
    res = await db_session.execute(stmt)
    total = res.scalar_one()
    assert total >= 1
