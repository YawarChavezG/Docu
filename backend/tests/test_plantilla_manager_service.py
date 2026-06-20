"""
Tests para plantilla_manager_service: CRUD de plantillas documentales en BD.
Sesion 38 R3 — Admin de plantillas.
"""
import os
import tempfile
from pathlib import Path

import pytest

from app.models.plantilla import Plantilla
from app.services.plantilla_manager_service import (
    listar_plantillas_db,
    listar_plantillas_admin_db,
    subir_plantilla_db,
    renombrar_plantilla_db,
    eliminar_plantilla_db,
    seed_plantillas_desde_disco,
)


@pytest.mark.asyncio
async def test_listar_plantillas_db_vacia(db_session):
    """Sin plantillas en BD: lista vacia."""
    result = await listar_plantillas_db(db_session)
    assert result == []


@pytest.mark.asyncio
async def test_subir_plantilla_db(db_session):
    """Subir una plantilla: se persiste en BD y en filesystem."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PLANTILLAS_STORAGE_PATH"] = tmpdir
        try:
            result = await subir_plantilla_db(
                db_session, "test_doc.docx",
                b"contenido del docx",
                nombre_display="Test Document",
                descripcion="Una descripcion",
                created_by_id=None,
            )
            await db_session.commit()
            assert result["nombre_archivo"] == "test_doc.docx"
            assert result["nombre_display"] == "Test Document"
            assert result["activo"] is True

            # Verificar en BD
            plantilla = await db_session.get(Plantilla, result["id"])
            assert plantilla is not None
            assert plantilla.nombre_archivo == "test_doc.docx"
            assert plantilla.tamano_bytes == len(b"contenido del docx")

            # Verificar archivo en disco
            p = Path(tmpdir) / "test_doc.docx"
            assert p.read_bytes() == b"contenido del docx"
        finally:
            os.environ.pop("PLANTILLAS_STORAGE_PATH", None)


@pytest.mark.asyncio
async def test_subir_plantilla_nombre_display_automatico(db_session):
    """Sin nombre_display: se genera desde el nombre del archivo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PLANTILLAS_STORAGE_PATH"] = tmpdir
        try:
            result = await subir_plantilla_db(
                db_session, "informe_anual_2026.docx",
                b"data",
            )
            await db_session.commit()
            assert "Informe" in result["nombre_display"]
            assert "Anual" in result["nombre_display"]
        finally:
            os.environ.pop("PLANTILLAS_STORAGE_PATH", None)


@pytest.mark.asyncio
async def test_renombrar_plantilla_db(db_session):
    """Renombrar cambia nombre_display y opcionalmente descripcion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PLANTILLAS_STORAGE_PATH"] = tmpdir
        try:
            r1 = await subir_plantilla_db(
                db_session, "plantilla_vieja.docx", b"data",
                nombre_display="Nombre Viejo",
            )
            await db_session.commit()

            r2 = await renombrar_plantilla_db(
                db_session, "plantilla_vieja.docx",
                "Nombre Nuevo", "Nueva descripcion",
            )
            assert r2 is not None
            assert r2["nombre_display"] == "Nombre Nuevo"
        finally:
            os.environ.pop("PLANTILLAS_STORAGE_PATH", None)


@pytest.mark.asyncio
async def test_renombrar_plantilla_no_existe(db_session):
    """Renombrar plantilla que no existe: retorna None."""
    result = await renombrar_plantilla_db(db_session, "no_existe.docx", "X")
    assert result is None


@pytest.mark.asyncio
async def test_eliminar_plantilla_db_soft_delete(db_session):
    """Eliminar plantilla: soft-delete (activo=False)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PLANTILLAS_STORAGE_PATH"] = tmpdir
        try:
            r1 = await subir_plantilla_db(
                db_session, "a_eliminar.docx", b"data",
                nombre_display="A Eliminar",
            )
            await db_session.commit()
            pid = r1["id"]

            ok = await eliminar_plantilla_db(db_session, "a_eliminar.docx")
            assert ok is True
            await db_session.commit()

            plantilla = await db_session.get(Plantilla, pid)
            assert plantilla.activo is False
        finally:
            os.environ.pop("PLANTILLAS_STORAGE_PATH", None)


@pytest.mark.asyncio
async def test_eliminar_plantilla_no_existe(db_session):
    """Eliminar plantilla que no existe: retorna False."""
    ok = await eliminar_plantilla_db(db_session, "no_existe.docx")
    assert ok is False


@pytest.mark.asyncio
async def test_seed_plantillas_desde_disco(db_session):
    """seed_plantillas_desde_disco migra archivos del disco a BD."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PLANTILLAS_STORAGE_PATH"] = tmpdir
        try:
            # Crear archivos de prueba en el directorio
            root = Path(tmpdir)
            (root / "plantilla1.docx").write_bytes(b"contenido 1")
            (root / "plantilla2.xlsx").write_bytes(b"contenido 2")
            (root / "not_a_plantilla.txt").write_bytes(b"ignorado")  # extension no soportada
            (root / "plantillas_meta.json").write_bytes(b"{}")  # ignorado por nombre

            count = await seed_plantillas_desde_disco(db_session)
            await db_session.commit()
            assert count == 2  # solo .docx y .xlsx

            # Verificar en BD
            todas = (await db_session.execute(
                __import__("sqlalchemy").select(Plantilla).order_by(Plantilla.nombre_display)
            )).scalars().all()
            assert len(todas) == 2
        finally:
            os.environ.pop("PLANTILLAS_STORAGE_PATH", None)


@pytest.mark.asyncio
async def test_seed_idempotente(db_session):
    """seed ejecutado 2 veces: la 2da no duplica registros."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["PLANTILLAS_STORAGE_PATH"] = tmpdir
        try:
            root = Path(tmpdir)
            (root / "unica.docx").write_bytes(b"data")

            count1 = await seed_plantillas_desde_disco(db_session)
            await db_session.commit()
            assert count1 == 1

            count2 = await seed_plantillas_desde_disco(db_session)
            await db_session.commit()
            assert count2 == 0  # ya existe, no se duplica

            todas = (await db_session.execute(
                __import__("sqlalchemy").select(Plantilla)
            )).scalars().all()
            assert len(todas) == 1
        finally:
            os.environ.pop("PLANTILLAS_STORAGE_PATH", None)
