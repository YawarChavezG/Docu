"""
Servicio: plantilla_manager_service
Gestiona el CRUD de plantillas documentales (subir, renombrar, eliminar).

Estrategia: usa un archivo JSON (`plantillas_meta.json`) como metadata
junto a los archivos .docx en el directorio de plantillas.
Cuando se elimina una plantilla, el archivo se mueve a `_deleted/`.
"""
import json
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _get_storage_root() -> Path:
    env_root = __import__('os').getenv("PLANTILLAS_STORAGE_PATH")
    if env_root:
        return Path(env_root)
    p = Path("/app/storage/plantillas")
    if p.exists():
        return p
    repo = Path(__file__).resolve().parent.parent.parent / "storage" / "plantillas"
    if repo.exists():
        return repo
    return p


def _meta_path() -> Path:
    return _get_storage_root() / "plantillas_meta.json"


def _deleted_dir() -> Path:
    d = _get_storage_root() / "_deleted"
    d.mkdir(exist_ok=True)
    return d


def _load_meta() -> dict:
    path = _meta_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Error leyendo plantillas_meta.json: %s", e)
    return {}


def _save_meta(meta: dict):
    _meta_path().write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def listar_plantillas() -> list[dict]:
    root = _get_storage_root()
    if not root.exists():
        return []
    meta = _load_meta()
    items = []
    for entry in sorted(root.iterdir()):
        if not entry.is_file() or entry.name in ("plantillas_meta.json",):
            continue
        ext = entry.suffix.lower()
        if ext not in (".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf"):
            continue
        m = meta.get(entry.name, {})
        items.append({
            "nombre_archivo": entry.name,
            "nombre_display": m.get("nombre_display", entry.name.replace("_", " ").replace(ext, "").title().strip()),
            "descripcion": m.get("descripcion", ""),
            "tamano_bytes": entry.stat().st_size,
            "activo": True,
        })
    # Agregar plantillas eliminadas (en _deleted/)
    deleted_dir = _deleted_dir()
    if deleted_dir.exists():
        for entry in sorted(deleted_dir.iterdir()):
            if not entry.is_file():
                continue
            m = meta.get(entry.name, {})
            items.append({
                "nombre_archivo": entry.name,
                "nombre_display": m.get("nombre_display", entry.name.replace("_", " ").replace(entry.suffix, "").title().strip()),
                "descripcion": m.get("descripcion", ""),
                "tamano_bytes": entry.stat().st_size,
                "activo": False,
            })
    return items


def subir_plantilla(nombre_archivo: str, contenido: bytes, nombre_display: str = "", descripcion: str = "") -> dict:
    root = _get_storage_root()
    root.mkdir(exist_ok=True)
    dest = root / nombre_archivo
    dest.write_bytes(contenido)
    meta = _load_meta()
    meta[nombre_archivo] = {
        "nombre_display": nombre_display or nombre_archivo.replace("_", " ").replace(dest.suffix, "").title().strip(),
        "descripcion": descripcion,
    }
    _save_meta(meta)
    logger.info("Plantilla subida: %s (%d bytes)", nombre_archivo, len(contenido))
    return {"nombre_archivo": nombre_archivo, "nombre_display": meta[nombre_archivo]["nombre_display"], "activo": True}


def renombrar_plantilla(nombre_actual: str, nuevo_nombre_display: str, nueva_descripcion: str = "") -> Optional[dict]:
    root = _get_storage_root()
    archivo = root / nombre_actual
    if not archivo.exists():
        # Buscar en _deleted/
        archivo = _deleted_dir() / nombre_actual
        if not archivo.exists():
            logger.warning("Plantilla no encontrada para renombrar: %s", nombre_actual)
            return None
    meta = _load_meta()
    m = meta.get(nombre_actual, {})
    m["nombre_display"] = nuevo_nombre_display
    if nueva_descripcion:
        m["descripcion"] = nueva_descripcion
    meta[nombre_actual] = m
    _save_meta(meta)
    return {"nombre_archivo": nombre_actual, "nombre_display": nuevo_nombre_display, "activo": True}


def eliminar_plantilla(nombre_archivo: str) -> bool:
    root = _get_storage_root()
    archivo = root / nombre_archivo
    if not archivo.exists():
        logger.warning("Plantilla no encontrada para eliminar: %s", nombre_archivo)
        return False
    # Mover a _deleted/
    dest = _deleted_dir() / nombre_archivo
    shutil.move(str(archivo), str(dest))
    logger.info("Plantilla eliminada (movida a _deleted/): %s", nombre_archivo)
    return True
