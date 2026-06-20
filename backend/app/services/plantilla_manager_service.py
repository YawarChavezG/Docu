"""
Servicio: plantilla_manager_service
Gestiona el CRUD de plantillas documentales con persistencia en BD.
"""
import logging
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plantilla import Plantilla

logger = logging.getLogger(__name__)

_EXT_MIME = {
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".pdf": "application/pdf",
}

_EXT_CATEGORIA = {k: "word" if k in (".doc", ".docx") else ("excel" if k in (".xls", ".xlsx") else ("ppt" if k in (".ppt", ".pptx") else "otro")) for k in _EXT_MIME}


def _get_storage_root() -> Path:
    env_root = os.getenv("PLANTILLAS_STORAGE_PATH")
    if env_root:
        p = Path(env_root)
        p.mkdir(exist_ok=True)
        return p
    for candidate in [Path("/app/storage/plantillas"), Path(__file__).resolve().parent.parent.parent / "storage" / "plantillas"]:
        if candidate.exists():
            return candidate
    p = Path("/app/storage/plantillas")
    p.mkdir(exist_ok=True)
    return p


async def listar_plantillas_db(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(
        select(Plantilla).where(Plantilla.activo == True).order_by(Plantilla.nombre_display)
    )).scalars().all()
    return [{
        "id": r.id,
        "nombre_archivo": r.nombre_archivo,
        "nombre_display": r.nombre_display,
        "descripcion": r.descripcion or "",
        "tamano_bytes": r.tamano_bytes,
        "activo": r.activo,
    } for r in rows]


async def listar_plantillas_admin_db(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(
        select(Plantilla).order_by(Plantilla.activo.desc(), Plantilla.nombre_display)
    )).scalars().all()
    return [{
        "id": r.id,
        "nombre_archivo": r.nombre_archivo,
        "nombre_display": r.nombre_display,
        "descripcion": r.descripcion or "",
        "tamano_bytes": r.tamano_bytes,
        "activo": r.activo,
    } for r in rows]


async def subir_plantilla_db(db: AsyncSession, nombre_archivo: str, contenido: bytes, nombre_display: str = "", descripcion: str = "", created_by_id: Optional[int] = None) -> dict:
    root = _get_storage_root()
    root.mkdir(exist_ok=True)
    dest = root / nombre_archivo
    dest.write_bytes(contenido)
    ext = dest.suffix.lower()
    if not nombre_display:
        nombre_display = dest.stem.replace("_", " ").replace("-", " ").title().strip()
    plantilla = Plantilla(
        nombre_archivo=nombre_archivo,
        nombre_display=nombre_display,
        descripcion=descripcion,
        tamano_bytes=len(contenido),
        mime_type=_EXT_MIME.get(ext, "application/octet-stream"),
        storage_path=str(dest),
        activo=True,
        created_by_id=created_by_id,
    )
    db.add(plantilla)
    await db.flush()
    await db.refresh(plantilla)
    logger.info("Plantilla %s subida (%d bytes)", nombre_archivo, len(contenido))
    return {"id": plantilla.id, "nombre_archivo": nombre_archivo, "nombre_display": nombre_display, "activo": True}


async def renombrar_plantilla_db(db: AsyncSession, nombre_archivo: str, nuevo_nombre_display: str, nueva_descripcion: str = "") -> Optional[dict]:
    result = await db.execute(select(Plantilla).where(Plantilla.nombre_archivo == nombre_archivo, Plantilla.activo == True))
    p = result.scalar_one_or_none()
    if not p:
        return None
    p.nombre_display = nuevo_nombre_display
    if nueva_descripcion:
        p.descripcion = nueva_descripcion
    await db.flush()
    return {"nombre_archivo": p.nombre_archivo, "nombre_display": p.nombre_display, "activo": True}


async def eliminar_plantilla_db(db: AsyncSession, nombre_archivo: str) -> bool:
    result = await db.execute(select(Plantilla).where(Plantilla.nombre_archivo == nombre_archivo, Plantilla.activo == True))
    p = result.scalar_one_or_none()
    if not p:
        return False
    p.activo = False
    await db.flush()
    logger.info("Plantilla %s desactivada (soft delete)", nombre_archivo)
    return True


async def seed_plantillas_desde_disco(db: AsyncSession) -> int:
    """Migra plantillas del filesystem a BD si no existen."""
    root = _get_storage_root()
    if not root.exists():
        return 0
    count = 0
    for entry in sorted(root.iterdir()):
        if not entry.is_file() or entry.name in ("plantillas_meta.json",):
            continue
        ext = entry.suffix.lower()
        if ext not in _EXT_MIME:
            continue
        existe = (await db.execute(
            select(Plantilla).where(Plantilla.nombre_archivo == entry.name)
        )).scalar_one_or_none()
        if existe:
            continue
        nombre_display = entry.stem.replace("_", " ").replace("-", " ").title().strip()
        p = Plantilla(
            nombre_archivo=entry.name,
            nombre_display=nombre_display,
            descripcion="",
            tamano_bytes=entry.stat().st_size,
            mime_type=_EXT_MIME[ext],
            storage_path=str(entry),
            activo=True,
        )
        db.add(p)
        count += 1
    if count:
        await db.flush()
        logger.info("Seed: %d plantillas migradas del disco a BD", count)
    return count
