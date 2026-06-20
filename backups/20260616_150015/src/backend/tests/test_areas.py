"""
Tests de /api/v1/areas (US-9.06 + Sesion B - #9d).
CRUD basico + operaciones jerarquicas (mover, promover) + fix B1 (UNIQUE compound).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.area import Area
from app.models.gerencia import Gerencia


# ─── Helpers ─────────────────────────────────────────────────────────
async def _ger(db, sigla: str, nombre: str = None) -> Gerencia:
    g = Gerencia(sigla=sigla, nombre=nombre or f"G-{sigla}", orden=99, activo=True)
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return g


async def _area(db, gerencia_id: int, sigla: str, nombre: str = None) -> Area:
    a = Area(
        gerencia_id=gerencia_id, sigla=sigla,
        nombre=nombre or f"A-{sigla}", activo=True, orden=1
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


# ─── Tests: listado ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_listar_areas_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """GET /areas con ETO: 200 (catalogo publico)."""
    g = seed_catalogos["gerencia"]
    await _area(db_session, g.id, "AR01", "Area Listado")

    r = await client.get("/api/v1/areas", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    # incluye el area del seed_catalogos + la nuestra
    sigs = [a["sigla"] for a in data["items"]]
    assert "AR01" in sigs
    assert "CC" in sigs  # del seed


@pytest.mark.asyncio
async def test_listar_areas_filtro_gerencia_id(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?gerencia_id=X."""
    g1 = await _ger(db_session, "GF01")
    g2 = await _ger(db_session, "GF02")
    await _area(db_session, g1.id, "GA01")
    await _area(db_session, g2.id, "GA02")

    r = await client.get(f"/api/v1/areas?gerencia_id={g1.id}", cookies=auth_eto_cookies)
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["sigla"] == "GA01"


@pytest.mark.asyncio
async def test_listar_areas_filtro_q(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """Filtro ?q= busca en sigla/nombre."""
    g = seed_catalogos["gerencia"]
    await _area(db_session, g.id, "QA01", "Auditoria Calibracion")
    await _area(db_session, g.id, "QA02", "Marketing Digital")

    r = await client.get("/api/v1/areas?q=aud", cookies=auth_eto_cookies)
    data = r.json()
    sigs = [a["sigla"] for a in data["items"]]
    assert "QA01" in sigs
    assert "QA02" not in sigs


# ─── Tests: creacion ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_crear_area_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = seed_catalogos["gerencia"]
    r = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": g.id, "sigla": "CR01", "nombre": "Creada Test"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["sigla"] == "CR01"


@pytest.mark.asyncio
async def test_crear_area_sin_rol_403(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos, db_session):
    g = seed_catalogos["gerencia"]
    r = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": g.id, "sigla": "NP01", "nombre": "No Perm"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_crear_area_gerencia_inexistente_404_o_422(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    r = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": 99999, "sigla": "BG01", "nombre": "Gerencia inexistente"},
        cookies=auth_eto_cookies,
    )
    # Puede ser 404 (FK violation) o 422 (validacion Pydantic)
    assert r.status_code in (404, 422)


# ─── Tests: SIGLA DUPLICADA — fix B1 ───────────────────────────────
@pytest.mark.asyncio
async def test_crear_area_sigla_duplicada_en_misma_gerencia_409(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Sigla duplicada en la MISMA gerencia: 409 (UNIQUE compound)."""
    g = seed_catalogos["gerencia"]
    # El seed ya creo CC en g. Intentar crear CC de nuevo.
    r = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": g.id, "sigla": "CC", "nombre": "Duplicado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_crear_area_misma_sigla_en_otra_gerencia_ok(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Sigla IGUAL en DIFERENTE gerencia: 201 (fix B1, UNIQUE compound)."""
    g1 = await _ger(db_session, "FG1")
    g2 = await _ger(db_session, "FG2")
    r1 = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": g1.id, "sigla": "MISMA", "nombre": "Area en G1"},
        cookies=auth_eto_cookies,
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": g2.id, "sigla": "MISMA", "nombre": "Area en G2"},
        cookies=auth_eto_cookies,
    )
    assert r2.status_code == 201  # fix B1 funciona


# ─── Tests: PATCH /{id} ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_actualizar_area_nombre(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    g = seed_catalogos["gerencia"]
    a = await _area(db_session, g.id, "AU01")
    r = await client.patch(
        f"/api/v1/areas/{a.id}",
        json={"nombre": "Nombre Actualizado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == "Nombre Actualizado"
    assert data["sigla"] == "AU01"


# ─── Tests: DELETE ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_eliminar_area_logico(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """DELETE default: borrado logico."""
    g = seed_catalogos["gerencia"]
    a = await _area(db_session, g.id, "DEL1")
    r = await client.delete(f"/api/v1/areas/{a.id}", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["activo"] is False


@pytest.mark.asyncio
async def test_eliminar_area_fisico(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """DELETE ?fisico=true: borrado FISICO (retorna 204 No Content)."""
    from sqlalchemy import select
    g = seed_catalogos["gerencia"]
    a = await _area(db_session, g.id, "DEL2")
    aid = a.id

    r = await client.delete(f"/api/v1/areas/{a.id}?fisico=true", cookies=auth_eto_cookies)
    assert r.status_code == 204

    # Verificar que ya no existe en BD
    res = await db_session.execute(select(Area).where(Area.id == aid))
    assert res.scalar_one_or_none() is None


# ─── Tests: /mover (jerarquica) ────────────────────────────────────
@pytest.mark.asyncio
async def test_mover_area_entre_gerencias(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """POST /areas/{id}/mover cambia gerencia_id."""
    g1 = await _ger(db_session, "MV01")
    g2 = await _ger(db_session, "MV02")
    a = await _area(db_session, g1.id, "MV_A")

    r = await client.post(
        f"/api/v1/areas/{a.id}/mover",
        json={"gerencia_id_destino": g2.id},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["gerencia_id"] == g2.id

    # Verificar en BD
    await db_session.refresh(a)
    assert a.gerencia_id == g2.id


@pytest.mark.asyncio
async def test_mover_area_a_gerencia_inexistente_404_o_422(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    g = seed_catalogos["gerencia"]
    a = await _area(db_session, g.id, "MV03")
    r = await client.post(
        f"/api/v1/areas/{a.id}/mover",
        json={"gerencia_id_destino": 99999},
        cookies=auth_eto_cookies,
    )
    assert r.status_code in (404, 422)


# ─── Tests: /promover-a-gerencia ──────────────────────────────────
@pytest.mark.asyncio
async def test_promover_area_a_gerencia(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    """POST /areas/{id}/promover-a-gerencia crea una nueva gerencia y desvincula el area."""
    g = seed_catalogos["gerencia"]
    a = await _area(db_session, g.id, "PROM")

    r = await client.post(
        f"/api/v1/areas/{a.id}/promover-a-gerencia",
        json={"sigla_gerencia": "PROMGER", "nombre_gerencia": "Gerencia Promovida Test"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200

    # Verificar en BD: nueva gerencia existe, area ahora pertenece a ella
    res = await db_session.execute(select(Gerencia).where(Gerencia.sigla == "PROMGER"))
    nueva_ger = res.scalar_one_or_none()
    assert nueva_ger is not None

    await db_session.refresh(a)
    assert a.gerencia_id == nueva_ger.id


@pytest.mark.asyncio
async def test_promover_area_sigla_duplicada_409(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    """Promover con sigla que ya existe: 409."""
    g_existente = await _ger(db_session, "EXIST")
    a = await _area(db_session, seed_catalogos["gerencia"].id, "PROM2")

    r = await client.post(
        f"/api/v1/areas/{a.id}/promover-a-gerencia",
        json={"sigla_gerencia": "EXIST", "nombre_gerencia": "Duplicada"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 409


# ─── Test integracion: audit en operaciones ────────────────────────
@pytest.mark.asyncio
async def test_crear_area_genera_audit_log(
    client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session
):
    from app.models.audit_log import AuditLog
    from sqlalchemy import select, func

    g = seed_catalogos["gerencia"]
    r = await client.post(
        "/api/v1/areas",
        json={"gerencia_id": g.id, "sigla": "AUD1", "nombre": "Audit Test"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 201

    stmt = select(func.count(AuditLog.id)).where(
        AuditLog.recurso == "area",
        AuditLog.accion == "CREATE",
    )
    res = await db_session.execute(stmt)
    total = res.scalar_one()
    assert total >= 1


from sqlalchemy import select  # late import para evitar circular
