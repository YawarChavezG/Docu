"""
Tests para el endpoint /api/v1/plantillas-documentales (Sesion 24 / Bloque E).

Estrategia: usar `tmp_path` con archivos .docx dummy, setear PLANTILLAS_STORAGE_PATH
via env var, y verificar:
  - GET / lista los archivos (con metadata)
  - GET /{file}/download sirve el archivo
  - Cada download crea una entrada en audit_log
  - Path traversal y extensiones invalidas son rechazadas
  - Sin auth: 401
"""
import os
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core import database as db_module
from app.models.audit_log import AuditLog


# ─── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
async def plantillas_dir(tmp_path, monkeypatch, db_session):
    """Crea 2 .docx dummy + 1 .exe (ignorado) y setea PLANTILLAS_STORAGE_PATH.
    Ademas inserta en BD para que el endpoint DB-based las encuentre."""
    (tmp_path / "ficha.docx").write_bytes(b"dummy docx content 1")
    (tmp_path / "procedimiento.docx").write_bytes(b"dummy docx content 2")
    (tmp_path / "malware.exe").write_bytes(b"bad")
    monkeypatch.setenv("PLANTILLAS_STORAGE_PATH", str(tmp_path))
    # Sembrar en BD (el endpoint ahora lee de BD, no del disco directamente)
    from app.services.plantilla_manager_service import seed_plantillas_desde_disco
    await seed_plantillas_desde_disco(db_session)
    await db_session.commit()
    return tmp_path


# ─── Tests listado ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_plantillas_retorna_archivos_permitidos(client, auth_eto_cookies, plantillas_dir):
    """GET / lista los .docx validos y excluye .exe."""
    r = await client.get("/api/v1/plantillas-documentales", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    nombres = [item["nombre_archivo"] for item in data["items"]]
    assert "ficha.docx" in nombres
    assert "procedimiento.docx" in nombres
    assert "malware.exe" not in nombres
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_listar_plantillas_incluye_metadata(client, auth_eto_cookies, plantillas_dir):
    """Cada item tiene nombre_display, descripcion, categoria, tamano_bytes, version, url_descarga."""
    r = await client.get("/api/v1/plantillas-documentales", cookies=auth_eto_cookies)
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) > 0
    item = items[0]
    for campo in ("nombre_archivo", "nombre_display", "descripcion", "categoria", "tamano_bytes", "version", "url_descarga"):
        assert campo in item, f"Falta campo {campo}"
    assert item["categoria"] == "word"
    assert item["url_descarga"].endswith("/download")


@pytest.mark.asyncio
async def test_listar_plantillas_sin_auth_retorna_401(client, plantillas_dir):
    """Sin sesion, GET / devuelve 401."""
    r = await client.get("/api/v1/plantillas-documentales")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_listar_plantillas_directorio_vacio(client, auth_eto_cookies, tmp_path, monkeypatch):
    """Directorio sin archivos devuelve total=0, items=[]."""
    empty = tmp_path / "empty_plantillas"
    empty.mkdir()
    monkeypatch.setenv("PLANTILLAS_STORAGE_PATH", str(empty))
    r = await client.get("/api/v1/plantillas-documentales", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_listar_plantillas_directorio_inexistente(client, auth_eto_cookies, monkeypatch):
    """Directorio inexistente devuelve lista vacia (no 500)."""
    monkeypatch.setenv("PLANTILLAS_STORAGE_PATH", "/tmp/no-existe-sgd-xxx-99999")
    r = await client.get("/api/v1/plantillas-documentales", cookies=auth_eto_cookies)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0


# ─── Tests descarga ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_download_plantilla_exitoso(client, auth_eto_cookies, plantillas_dir):
    """GET /{file}/download sirve el archivo con content-type correcto."""
    r = await client.get("/api/v1/plantillas-documentales/ficha.docx/download", cookies=auth_eto_cookies)
    assert r.status_code == 200
    assert r.content == b"dummy docx content 1"
    cd = r.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "ficha.docx" in cd


@pytest.mark.asyncio
async def test_download_plantilla_crea_audit_log(client, auth_eto_cookies, seed_catalogos, plantillas_dir, db_session):
    """GET /{file}/download crea una entrada en audit_log con accion=DOWNLOAD."""
    r = await client.get("/api/v1/plantillas-documentales/procedimiento.docx/download", cookies=auth_eto_cookies)
    assert r.status_code == 200
    # Commit explicito para que el audit sea visible
    await db_session.commit()

    res = await db_session.execute(
        select(AuditLog).where(AuditLog.recurso == "plantilla_documental").order_by(AuditLog.id.desc())
    )
    entry = res.scalars().first()
    assert entry is not None
    assert entry.accion == "DOWNLOAD"
    assert "procedimiento.docx" in (entry.descripcion or "")
    assert entry.detalles is not None
    assert entry.detalles.get("nombre_archivo") == "procedimiento.docx"
    assert entry.detalles.get("categoria") == "word"
    assert entry.usuario_username == "aromero"


@pytest.mark.asyncio
async def test_download_extension_invalida_retorna_415(client, auth_eto_cookies, plantillas_dir):
    """Extension no permitida (.exe) devuelve 415."""
    r = await client.get("/api/v1/plantillas-documentales/malware.exe/download", cookies=auth_eto_cookies)
    assert r.status_code == 415


@pytest.mark.asyncio
async def test_download_path_traversal_bloqueado(client, auth_eto_cookies, plantillas_dir):
    """Path traversal en el nombre NO devuelve el archivo (404 o 400, NUNCA el contenido)."""
    # Intentar salir del directorio de plantillas
    r = await client.get("/api/v1/plantillas-documentales/..%2F..%2Fetc%2Fpasswd/download", cookies=auth_eto_cookies)
    # 404 (no se encuentra la "plantilla") o 400 (nombre invalido). Lo importante
    # es que NO se sirva el contenido real de /etc/passwd ni nada del filesystem.
    assert r.status_code in (400, 404)
    # No debe haber leaking de archivos
    assert b"root:" not in r.content
    assert b"/bin/" not in r.content


@pytest.mark.asyncio
async def test_download_archivo_inexistente_retorna_404(client, auth_eto_cookies, plantillas_dir):
    """Archivo que no existe devuelve 404."""
    r = await client.get("/api/v1/plantillas-documentales/no_existe.docx/download", cookies=auth_eto_cookies)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_download_sin_auth_retorna_401(client, plantillas_dir):
    """Sin sesion, GET /download devuelve 401."""
    r = await client.get("/api/v1/plantillas-documentales/ficha.docx/download")
    assert r.status_code == 401
