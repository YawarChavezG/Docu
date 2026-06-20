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
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Extensiones permitidas para almacenamiento
ALLOWED_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.pdf', '.pptx', '.ppt', '.png', '.jpg', '.jpeg', '.dwg'}


def safe_filename(name: str, max_length: int = 200) -> str:
    """
    Sanitiza un nombre de archivo: elimina caracteres peligrosos
    para el sistema de archivos (path traversal, caracteres especiales).
    """
    # Extraer nombre y extensión
    p = Path(name)
    stem = p.stem
    ext = p.suffix.lower()

    # Validar extensión
    if ext and ext not in ALLOWED_EXTENSIONS:
        ext = ""

    # Eliminar caracteres peligrosos del stem
    stem = re.sub(r'[/\\:*?"<>|]', '', stem)
    # Prevenir path traversal (eliminar ..)
    stem = stem.replace('..', '')
    # Recortar largo máximo
    stem = stem[:max_length]

    safe = stem.strip()
    if not safe:
        safe = "documento"

    return f"{safe}{ext}"


# ════════════════════════════════════════════════════════════════
#  Protocol / ABC
# ════════════════════════════════════════════════════════════════

class StorageBackend(ABC):
    """Interfaz abstracta para los backends de almacenamiento."""

    @abstractmethod
    def save(self, file_bytes: bytes, dest_filename: str, subdir: str = "") -> str:
        """
        Persiste los bytes del archivo y devuelve el path interno.
        NO valida tamano ni MIME type (eso lo hace el endpoint).

        Args:
            file_bytes: contenido del archivo
            dest_filename: nombre final del archivo (ej: "CC-5-001 PROCEDIMIENTO V00.docx")
            subdir: subdirectorio relativo (ej: "CC/CC/CC-5-001/V00")
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
    Default: /app/storage/documentos (volume del contenedor backend).
    Configurable via env var DOCUMENTOS_STORAGE_PATH.
    """

    def __init__(self, root: Optional[str] = None) -> None:
        env_root = os.getenv("DOCUMENTOS_STORAGE_PATH")
        self.root = Path(root or env_root or "/app/storage/documentos")
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, file_bytes: bytes, dest_filename: str, subdir: str = "") -> str:
        """
        Escribe los bytes en self.root/{subdir}/{dest_filename} con nombre legible.
        Ej: /app/storage/documentos/CC/CC/CC-5-001/V00/CC-5-001 PROCEDIMIENTO V00.docx

        Args:
            file_bytes: contenido binario del archivo
            dest_filename: nombre con formato: "{codigo} {TITULO} V{version}.{ext}"
                           o "{codigo}-F{corr} {TITULO} V{version}.{ext}"
            subdir: subdirectorio relativo desde root (ej: "CC/CC/CC-5-001/V00")
        """
        # Sanitizar nombre de archivo
        safe_name = safe_filename(dest_filename)

        # Construir directorio de destino
        target_dir = self.root
        if subdir:
            # Sanitizar cada componente del subdir
            parts = [safe_filename(p) for p in subdir.replace('\\', '/').split('/') if p]
            for p in parts:
                target_dir = target_dir / p

        target_dir.mkdir(parents=True, exist_ok=True)
        full_path = target_dir / safe_name

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        logger.info("Archivo guardado: %s (%d bytes)", full_path, len(file_bytes))
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
    Stub para DES. En QAS/PROD implementa Microsoft Graph API (Fase 9).
    """

    def save(self, file_bytes: bytes, dest_filename: str, subdir: str = "") -> str:
        """Stub: NO escribe. Devuelve un path ficticio sharepoint://."""
        size = len(file_bytes) if file_bytes else 0
        logger.info(
            "[STUB] SharePoint: subiendo %s (%d bytes) a %s",
            dest_filename, size, subdir or "(raiz)",
        )
        return f"sharepoint://{subdir}/{dest_filename}" if subdir else f"sharepoint://{dest_filename}"

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
