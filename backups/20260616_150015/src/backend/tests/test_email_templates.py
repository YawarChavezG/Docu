"""
Tests de /api/v1/email-templates.
"""
import pytest
from httpx import AsyncClient

from app.models.email_template import EmailTemplate, CodigoPlantilla


@pytest.mark.asyncio
async def test_listar_email_templates_sin_auth(client: AsyncClient):
    """GET /email-templates sin auth: 200 (catalogo publico) o 401."""
    r = await client.get("/api/v1/email-templates")
    assert r.status_code in (200, 401)


@pytest.mark.asyncio
async def test_listar_email_templates_eto(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/email-templates", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_get_email_template(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    t = EmailTemplate(
        codigo=CodigoPlantilla.NUEVA_TAREA,
        nombre="Test Plantilla",
        asunto="Asunto Test",
        cuerpo_html="<p>Hola {{CODIGO}}</p>",
        variables_json=["CODIGO"],
        activo=True,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)

    r = await client.get(f"/api/v1/email-templates/{t.codigo.value}", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["asunto"] == "Asunto Test"


@pytest.mark.asyncio
async def test_get_email_template_no_existe_404(client: AsyncClient, auth_eto_cookies, seed_catalogos):
    r = await client.get("/api/v1/email-templates/NO_EXISTE", cookies=auth_eto_cookies)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_actualizar_email_template(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    t = EmailTemplate(
        codigo=CodigoPlantilla.NUEVA_TAREA,
        nombre="Test",
        asunto="Original",
        cuerpo_html="<p>orig</p>",
        activo=True,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)

    r = await client.patch(
        f"/api/v1/email-templates/{t.codigo.value}",
        json={"asunto": "Modificado"},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    assert r.json()["asunto"] == "Modificado"


@pytest.mark.asyncio
async def test_preview_email_template_con_variables(client: AsyncClient, auth_eto_cookies, seed_catalogos, db_session):
    t = EmailTemplate(
        codigo=CodigoPlantilla.NUEVA_TAREA,
        nombre="Test Preview",
        asunto="[{{CODIGO}}] {{TITULO}}",
        cuerpo_html="<p>Hola {{USUARIO}}</p>",
        variables_json=["CODIGO", "TITULO", "USUARIO"],
        activo=True,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)

    r = await client.post(
        f"/api/v1/email-templates/{t.codigo.value}/preview",
        json={"vars": {"CODIGO": "PRO-001", "TITULO": "Test", "USUARIO": "aromero"}},
        cookies=auth_eto_cookies,
    )
    assert r.status_code == 200
    data = r.json()
    assert "asunto_rendered" in data
    assert "PRO-001" in data["asunto_rendered"]


@pytest.mark.asyncio
async def test_email_template_sin_rol(client: AsyncClient, auth_sin_rol_cookies, seed_catalogos):
    """PATCH email-template sin rol: 403, 404 o 422."""
    r = await client.patch(
        "/api/v1/email-templates/NUEVA_TAREA",
        json={"asunto": "x"},
        cookies=auth_sin_rol_cookies,
    )
    assert r.status_code in (403, 404, 422)
