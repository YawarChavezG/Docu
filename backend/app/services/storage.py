"""
Servicio: storage
Abstraccion de almacenamiento de archivos adjuntos a Documentos.

En R2 (DES) usamos LocalStorage que escribe a /app/storage/uploads/.
En QAS/PROD se usara SharePointStorage con Microsoft Graph API.

Patron: Protocol + 2 implementaciones. Se elige la implementacion via
env var SHAREPOINT_ENABLED.

Riesgos documentados (SESION-22-HANDOFF.md § 5 R4, R5):
- R4: la abstraccion debe permitir cambiar de LocalStorage a SharePoint
     sin tocar el resto del wizard.
- R5: en tests con pytest, /app/storage/uploads/ puede no existir. El
     storage acepta un parametro `root` opcional para tests (usado por
     el fixture tmp_path de pytest).

Tests (test_storage.py):
- test_local_storage_save_creates_file
- test_local_storage_save_generates_uuid
- test_local_storage_delete_removes_file
- test_local_storage_get_url_returns_path
- test_sharepoint_storage_stub_logs_only
"""
import logging
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
#  Protocol / ABC
# ════════════════════════════════════════════════════════════════

class StorageBackend(ABC):
    """Interfaz abstracta para los backends de almacenamiento."""

    @abstractmethod
    def save(self, file_bytes: bytes, dest_filename: str) -> str:
        """
        Persiste los bytes del archivo y devuelve el path interno.
        NO valida tamano ni MIME type (eso lo hace el endpoint).
        """

    @abstractmethod
    def delete(self, path: str) -> None:
        """Elimina el archivo del backend. Idempotente."""

    @abstractmethod
    def get_url(self, path: str) -> str:
        """Devuelve la URL accesible para descargar el archivo (para el front)."""


# ════════════════════════════════════════════════════════════════
#  LocalStorage (DES)
# ════════════════════════════════════════════════════════════════

class LocalStorage(StorageBackend):
    """
    Persiste archivos en un directorio del filesystem.
    Default: /app/storage/uploads (volume del contenedor backend).
    Configurable via env var STORAGE_ROOT o argumento del constructor (para tests).
    """

    def __init__(self, root: Optional[str] = None) -> None:
        # F5 (Sesion 24): aceptar tanto STORAGE_ROOT (legacy) como
        # DOCUMENTOS_STORAGE_PATH (mas descriptivo, default "/app/storage/uploads").
        env_root = os.getenv("DOCUMENTOS_STORAGE_PATH") or os.getenv("STORAGE_ROOT")
        self.root = Path(root or env_root or "/app/storage/uploads")
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_ext(self, dest_filename: str) -> str:
        """Extrae la extension de manera segura (sin path traversal)."""
        # Quitar cualquier path que venga en dest_filename (defensa en profundidad)
        safe_name = Path(dest_filename).name
        ext = Path(safe_name).suffix.lower()
        # Whitelist: solo extensiones permitidas (3 chars + .)
        if ext and len(ext) <= 6 and all(c.isalnum() or c == "." for c in ext):
            return ext
        return ""

    def _unique_name(self, dest_filename: str) -> str:
        """Genera nombre unico: {uuid4}.{ext} (evita colisiones y path traversal)."""
        ext = self._safe_ext(dest_filename)
        return f"{uuid.uuid4().hex}{ext}"

    def save(self, file_bytes: bytes, dest_filename: str) -> str:
        """Escribe los bytes en self.root con un nombre UUID + extension."""
        name = self._unique_name(dest_filename)
        full_path = self.root / name
        # Crear directorios intermedios si no existen (defensa)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        # Escribir en modo binario
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        # Devolver path absoluto (lo que se guarda en archivo_adjunto.storage_path)
        return str(full_path)

    def delete(self, path: str) -> None:
        """Elimina el archivo. Idempotente: si no existe, no falla."""
        try:
            p = Path(path)
            if p.exists() and p.is_file():
                p.unlink()
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo eliminar archivo %s: %s", path, exc)

    def get_url(self, path: str) -> str:
        """
        Devuelve la URL accesible via Nginx (/api/v1/files/...).
        En esta sesion devolvemos el path absoluto (FASE 3 lo hara accesible
        via un endpoint de descarga con auth).
        """
        # En DES la ruta /api/v1/files/<path> no existe todavia.
        # Devolvemos el path interno para que el caller sepa donde esta.
        return path


# ════════════════════════════════════════════════════════════════
#  SharePointStorage (stub DES, real en QAS/PROD)
# ════════════════════════════════════════════════════════════════

class SharePointStorage(StorageBackend):
    """
    Stub para DES. En QAS/PROD implementa Microsoft Graph API.

    No escribe nada: solo loguea la intencion. Esto permite desarrollar
    el wizard end-to-end en DES sin SharePoint real, y en QAS cambiar
    un flag (SHAREPOINT_ENABLED=true) para activar la implementacion real.
    """

    def save(self, file_bytes: bytes, dest_filename: str) -> str:
        """Stub: NO escribe. Devuelve un path ficticio sharepoint://."""
        size = len(file_bytes) if file_bytes else 0
        logger.info(
            "[STUB] SharePoint: subiendo %s (%d bytes) a la biblioteca de documentos",
            dest_filename, size,
        )
        return f"sharepoint://{dest_filename}"

    def delete(self, path: str) -> None:
        """Stub: NO elimina. Solo loguea."""
        logger.info("[STUB] SharePoint: eliminando %s", path)

    def get_url(self, path: str) -> str:
        """Stub: devuelve el path como URL."""
        return path


# ════════════════════════════════════════════════════════════════
#  Factory
# ════════════════════════════════════════════════════════════════

_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """
    Factory singleton. Elige implementacion segun env var SHAREPOINT_ENABLED.
    - SHAREPOINT_ENABLED=true  -> SharePointStorage (QAS/PROD)
    - SHAREPOINT_ENABLED=false -> LocalStorage       (DES, default)
    """
    global _instance
    if _instance is not None:
        return _instance

    if os.getenv("SHAREPOINT_ENABLED", "false").lower() == "true":
        logger.info("Storage backend: SharePoint (QAS/PROD)")
        _instance = SharePointStorage()
    else:
        logger.info("Storage backend: Local (DES)")
        _instance = LocalStorage()
    return _instance


def reset_storage_for_tests() -> None:
    """Resetea el singleton (util para tests que cambian STORAGE_ROOT)."""
    global _instance
    _instance = None
