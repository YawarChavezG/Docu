"""
Tests para POST /documentos/{id}/archivos (Sesion 22 R2 FASE 2).

Estrategia: crear un Documento via POST primero, luego subir archivos
al documento creado.
"""
import io

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.archivo_adjunto import ArchivoAdjunto, StorageBackend as StorageBackendAdjunto
from app.models.tipo_documento import TipoDocumento


# ─── Helpers ───

async def _crear_tipo_test(db_session, codigo: int, slug: str, nombre: str):
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == codigo)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=codigo, slug=slug, nombre=nombre,
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)
    return tipo


async def _crear_doc(client, cookies, gerencia_id, area_id, tipo_id):
    """Crea un doc via POST y devuelve el id."""
    r = await client.post("/api/v1/documentos", json={
        "gerencia_id": gerencia_id, "area_id": area_id,
        "tipo_documento_id": tipo_id, "titulo": "Doc para upload",
        "tipo_solicitud": "CREACION",
    }, cookies=cookies)
    assert r.status_code == 201
    return r.json()["documento"]["id"]


# ════════════════════════════════════════════════════════════════
#  POST /documentos/{id}/archivos
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_upload_archivo_pdf_201(client: AsyncClient, seed_catalogos, db_session, tmp_path, monkeypatch):
    """Upload de un PDF de 1MB: 201 + registro en BD."""
    from app.services.storage import reset_storage_for_tests
    # Apuntar storage a tmp_path (no escribir en /app/storage del contenedor)
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    doc_id = await _crear_doc(client, cookies, area.gerencia_id, area.id, tipo.id)

    # 1MB de bytes
    file_bytes = b"%PDF-1.4\n" + b"x" * (1024 * 1024 - 9)
    files = {"archivo": ("test.pdf", io.BytesIO(file_bytes), "application/pdf")}

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files, cookies=cookies,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "archivo" in data
    assert data["archivo"]["nombre_original"] == "test.pdf"
    assert data["archivo"]["mime_type"] == "application/pdf"
    assert data["archivo"]["tamano_bytes"] == 1024 * 1024
    assert data["archivo"]["tipo_adjunto"] == "FORMULARIO"
    assert data["archivo"]["storage_backend"] == "LOCAL"
    # Verificar que se persistio en BD
    arch = await db_session.get(ArchivoAdjunto, data["archivo"]["id"])
    assert arch is not None
    assert arch.documento_id == doc_id

    reset_storage_for_tests()


@pytest.mark.asyncio
async def test_upload_archivo_excede_max_413(client: AsyncClient, seed_catalogos, db_session, tmp_path, monkeypatch):
    """Upload de archivo > max_tamano_archivo_mb (default 20MB): 413."""
    from app.services.storage import reset_storage_for_tests
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    doc_id = await _crear_doc(client, cookies, area.gerencia_id, area.id, tipo.id)

    # 25 MB > 20MB
    file_bytes = b"x" * (25 * 1024 * 1024)
    files = {"archivo": ("big.pdf", io.BytesIO(file_bytes), "application/pdf")}

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files, cookies=cookies,
    )
    assert resp.status_code == 413
    assert "excede" in resp.json()["detail"].lower()

    reset_storage_for_tests()


@pytest.mark.asyncio
async def test_upload_archivo_mime_invalido_415(client: AsyncClient, seed_catalogos, db_session, tmp_path, monkeypatch):
    """Upload de .exe (mime no permitido): 415."""
    from app.services.storage import reset_storage_for_tests
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    doc_id = await _crear_doc(client, cookies, area.gerencia_id, area.id, tipo.id)

    file_bytes = b"MZ\x90\x00" + b"x" * 100  # fake exe
    files = {"archivo": ("malware.exe", io.BytesIO(file_bytes), "application/x-msdownload")}

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files, cookies=cookies,
    )
    assert resp.status_code == 415
    assert "no permitido" in resp.json()["detail"].lower() or "mime" in resp.json()["detail"].lower()

    reset_storage_for_tests()


@pytest.mark.asyncio
async def test_upload_archivo_doc_inexistente_404(client: AsyncClient, seed_catalogos, tmp_path, monkeypatch):
    """Upload a un doc que no existe: 404."""
    from app.services.storage import reset_storage_for_tests
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    file_bytes = b"%PDF-1.4\nhola"
    files = {"archivo": ("x.pdf", io.BytesIO(file_bytes), "application/pdf")}

    resp = await client.post(
        "/api/v1/documentos/99999/archivos",
        files=files, cookies=cookies,
    )
    assert resp.status_code == 404

    reset_storage_for_tests()


# ════════════════════════════════════════════════════════════════
#  R3 item 0.4: Codigo de formularios -F01, -F02, etc.
#  Sesion 36 R3 - FASE 0
# ════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_upload_formulario_genera_codigo_F01(
    client: AsyncClient, seed_catalogos, db_session, tmp_path, monkeypatch,
):
    """R3 item 0.4: subir un FORMULARIO genera codigo -F01 automatico."""
    from app.models.documento_formulario import DocumentoFormulario
    from app.services.storage import reset_storage_for_tests

    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    doc_id = await _crear_doc(client, cookies, area.gerencia_id, area.id, tipo.id)

    file_bytes = b"%PDF-1.4\nform1"
    files = {"archivo": ("form1.pdf", io.BytesIO(file_bytes), "application/pdf")}

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files, cookies=cookies,
        data={"tipo_adjunto": "FORMULARIO"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["formulario"] is not None
    # El codigo debe ser CC-3-001-F01 (sigla CC + tipo 3 + correlativo 1 + F01)
    assert data["formulario"]["codigo_formulario"] == "CC-3-001-F01"
    assert data["formulario"]["correlativo_formulario"] == 1

    # Verificar en BD
    f = await db_session.execute(
        select(DocumentoFormulario).where(DocumentoFormulario.id == data["formulario"]["id"])
    )
    formulario_db = f.scalar_one()
    assert formulario_db.codigo_formulario == "CC-3-001-F01"
    assert formulario_db.activo is True

    reset_storage_for_tests()


@pytest.mark.asyncio
async def test_upload_multiples_formularios_correlativo_incrementa(
    client: AsyncClient, seed_catalogos, db_session, tmp_path, monkeypatch,
):
    """R3 item 0.4: 2do formulario del mismo doc debe ser -F02 (correlativo+1)."""
    from app.services.storage import reset_storage_for_tests

    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    doc_id = await _crear_doc(client, cookies, area.gerencia_id, area.id, tipo.id)

    # Subir primer formulario
    file_bytes_1 = b"%PDF-1.4\nform1"
    files_1 = {"archivo": ("f1.pdf", io.BytesIO(file_bytes_1), "application/pdf")}
    r1 = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files_1, cookies=cookies, data={"tipo_adjunto": "FORMULARIO"},
    )
    assert r1.status_code == 201
    assert r1.json()["formulario"]["codigo_formulario"] == "CC-3-001-F01"

    # Subir segundo formulario
    file_bytes_2 = b"%PDF-1.4\nform2"
    files_2 = {"archivo": ("f2.pdf", io.BytesIO(file_bytes_2), "application/pdf")}
    r2 = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files_2, cookies=cookies, data={"tipo_adjunto": "FORMULARIO"},
    )
    assert r2.status_code == 201
    assert r2.json()["formulario"]["codigo_formulario"] == "CC-3-001-F02"
    assert r2.json()["formulario"]["correlativo_formulario"] == 2

    # Subir tercer formulario
    file_bytes_3 = b"%PDF-1.4\nform3"
    files_3 = {"archivo": ("f3.pdf", io.BytesIO(file_bytes_3), "application/pdf")}
    r3 = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files_3, cookies=cookies, data={"tipo_adjunto": "FORMULARIO"},
    )
    assert r3.status_code == 201
    assert r3.json()["formulario"]["codigo_formulario"] == "CC-3-001-F03"

    reset_storage_for_tests()


@pytest.mark.asyncio
async def test_upload_principal_no_genera_formulario(
    client: AsyncClient, seed_catalogos, db_session, tmp_path, monkeypatch,
):
    """Subir un PRINCIPAL no crea formulario (el campo `formulario` es null)."""
    from app.services.storage import reset_storage_for_tests

    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    reset_storage_for_tests()

    tipo = await _crear_tipo_test(db_session, codigo=3, slug="POLITICA", nombre="Politica Test")
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    cookies = {"user_id": str(eto.id), "session": "x"}
    doc_id = await _crear_doc(client, cookies, area.gerencia_id, area.id, tipo.id)

    file_bytes = b"%PDF-1.4\nmain"
    files = {"archivo": ("main.pdf", io.BytesIO(file_bytes), "application/pdf")}

    resp = await client.post(
        f"/api/v1/documentos/{doc_id}/archivos",
        files=files, cookies=cookies, data={"tipo_adjunto": "PRINCIPAL"},
    )
    assert resp.status_code == 201
    data = resp.json()
    # PRINCIPAL no genera codigo_formulario
    assert data["formulario"] is None
    assert data["archivo"]["tipo_adjunto"] == "PRINCIPAL"

    reset_storage_for_tests()
