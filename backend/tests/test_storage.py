"""
Tests para el servicio de storage (LocalStorage + SharePointStorage stub).

Estrategia: usar `tmp_path` (fixture pytest) para no escribir en /app/storage
del contenedor ni depender de permisos.
"""
import logging
import os
import re
from pathlib import Path

import pytest

from app.services.storage import (
    LocalStorage,
    SharePointStorage,
    get_storage,
    reset_storage_for_tests,
)


# ─── LocalStorage ──────────────────────────────────────────────────────

class TestLocalStorage:
    """5 tests del LocalStorage."""

    def test_local_storage_save_creates_file(self, tmp_path: Path):
        """save() crea un archivo fisico en el root configurado."""
        storage = LocalStorage(root=str(tmp_path))
        path = storage.save(b"hello world", "doc.pdf")

        assert path is not None
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == b"hello world"

    def test_local_storage_save_generates_uuid(self, tmp_path: Path):
        """save() genera un nombre con UUID (no usa el nombre original)."""
        storage = LocalStorage(root=str(tmp_path))
        path = storage.save(b"x", "mi_archivo_original.docx")

        # El path NO debe contener "mi_archivo_original" (es UUID + ext)
        filename = Path(path).name
        assert "mi_archivo_original" not in filename
        # Formato esperado: 32 chars hex (uuid4 sin guiones) + .docx
        assert re.match(r"^[a-f0-9]{32}\.docx$", filename), f"Nombre inesperado: {filename}"

    def test_local_storage_save_preserves_extension(self, tmp_path: Path):
        """save() preserva la extension del nombre original (whitelist)."""
        storage = LocalStorage(root=str(tmp_path))
        for ext in ["pdf", "docx", "xlsx", "png", "jpg"]:
            path = storage.save(b"x", f"file.{ext}")
            assert path.endswith(f".{ext}"), f"Extension {ext} no preservada: {path}"

    def test_local_storage_save_rejects_path_traversal(self, tmp_path: Path):
        """save() bloquea path traversal en el filename."""
        storage = LocalStorage(root=str(tmp_path))
        # Aunque el filename tenga path traversal, el nombre guardado NO debe
        # permitir escribir fuera del root
        path = storage.save(b"x", "../../../etc/passwd")
        # El path resultante debe estar DENTRO de tmp_path
        assert str(tmp_path) in path, f"path traversal permitido: {path}"
        # Y no debe contener ".."
        assert ".." not in Path(path).name

    def test_local_storage_delete_removes_file(self, tmp_path: Path):
        """delete() elimina el archivo. Idempotente (no falla si no existe)."""
        storage = LocalStorage(root=str(tmp_path))
        path = storage.save(b"x", "test.txt")
        assert os.path.exists(path)

        storage.delete(path)
        assert not os.path.exists(path)

        # Idempotente: borrar 2da vez no falla
        storage.delete(path)  # No debe lanzar excepcion

    def test_local_storage_get_url_returns_path(self, tmp_path: Path):
        """get_url() devuelve el path (placeholder; FASE 3 implementa URL real)."""
        storage = LocalStorage(root=str(tmp_path))
        path = storage.save(b"x", "x.pdf")
        url = storage.get_url(path)
        assert url == path


# ─── SharePointStorage (stub) ──────────────────────────────────────────

class TestSharePointStorage:
    """1 test del stub SharePoint (no escribe nada, solo loguea)."""

    def test_sharepoint_storage_stub_logs_only(self, caplog):
        """save() NO escribe nada, solo loguea la intencion y devuelve path ficticio."""
        storage = SharePointStorage()
        with caplog.at_level(logging.INFO):
            path = storage.save(b"contenido", "demo.docx")

        # Path ficticio con el esquema sharepoint://
        assert path == "sharepoint://demo.docx"
        # Log emitido
        assert any("SharePoint" in rec.message for rec in caplog.records)
        # NO se escribio nada en disco (verificamos que no existe en CWD)
        assert not os.path.exists("demo.docx")

    def test_sharepoint_storage_delete_is_noop(self, caplog):
        """delete() NO hace nada, solo loguea."""
        storage = SharePointStorage()
        with caplog.at_level(logging.INFO):
            storage.delete("sharepoint://whatever.docx")
        assert any("SharePoint" in rec.message for rec in caplog.records)

    def test_sharepoint_storage_get_url_returns_path(self):
        """get_url() devuelve el path como esta."""
        storage = SharePointStorage()
        assert storage.get_url("sharepoint://x.docx") == "sharepoint://x.docx"


# ─── Factory get_storage() ─────────────────────────────────────────────

class TestStorageFactory:
    """Tests del factory singleton."""

    def test_get_storage_returns_local_by_default(self, tmp_path: Path, monkeypatch):
        """Sin SHAREPOINT_ENABLED, devuelve LocalStorage."""
        monkeypatch.setenv("SHAREPOINT_ENABLED", "false")
        monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
        reset_storage_for_tests()

        s = get_storage()
        assert isinstance(s, LocalStorage)

    def test_get_storage_returns_sharepoint_when_enabled(self, monkeypatch):
        """Con SHAREPOINT_ENABLED=true, devuelve SharePointStorage."""
        monkeypatch.setenv("SHAREPOINT_ENABLED", "true")
        reset_storage_for_tests()

        s = get_storage()
        assert isinstance(s, SharePointStorage)
        reset_storage_for_tests()  # Cleanup para otros tests
