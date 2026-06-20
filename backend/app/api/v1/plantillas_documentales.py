"""
api/v1/plantillas_documentales.py — Plantillas documentales (Sesion 24 / Bloque E).

Las plantillas son archivos estaticos servidos desde /app/storage/plantillas/.
No se persisten en BD: el listado se genera escaneando el directorio en cada
request (hay 8 archivos, es despreciable).

Endpoints (todos bajo prefix /api/v1/plantillas-documentales):
  GET  /                          lista las plantillas disponibles (auth required)
  GET  /{nombre_archivo}/download  descarga la plantilla (auth + audit_log)

Auditoria: cada descarga queda registrada en audit_log con accion=DOWNLOAD
y recurso=plantilla_documental.
"""
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit
from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import require_authenticated, require_eto_or_admin
from app.schemas.plantilla_documental import PlantillaDocumentalOut, PlantillaListResponse
from app.services.plantilla_manager_service import listar_plantillas, subir_plantilla, renombrar_plantilla, eliminar_plantilla

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plantillas-documentales", tags=["Plantillas Documentales"])


# ─── Metadata hardcoded de las plantillas ───────────────────────────────
# Como no hay tabla en BD, la descripcion legible + version se mantiene
# aqui. Es estatico: si se agregan/renombran archivos, hay que actualizar
# esta constante. En R3 (cuando se persistan en BD) esto se migra a la tabla.
_PLANTILLAS_META: dict[str, dict] = {
    "ficha_caracterizacion.docx": {
        "nombre_display": "Ficha de Caracterizacion",
        "descripcion": "Formato estandar para fichas de caracterizacion de procesos.",
        "version": "v1",
    },
    "instructivo.docx": {
        "nombre_display": "Instructivo",
        "descripcion": "Formato para instructivos paso a paso.",
        "version": "v1",
    },
    "instructivo_tecnico_mantenimiento.docx": {
        "nombre_display": "Instructivo Tecnico (Mantenimiento)",
        "descripcion": "Formato para instructivos tecnicos de mantenimiento.",
        "version": "v1",
    },
    "manual_proceso.docx": {
        "nombre_display": "Manual de Proceso",
        "descripcion": "Formato para manuales de proceso.",
        "version": "v1",
    },
    "manual_usuario.docx": {
        "nombre_display": "Manual de Usuario",
        "descripcion": "Formato para manuales de usuario.",
        "version": "v1",
    },
    "plan.docx": {
        "nombre_display": "Plan",
        "descripcion": "Formato para planes (operativos, estrategicos, etc.).",
        "version": "v1",
    },
    "politica.docx": {
        "nombre_display": "Politica",
        "descripcion": "Formato para politicas institucionales.",
        "version": "v1",
    },
    "procedimiento.docx": {
        "nombre_display": "Procedimiento (SOP)",
        "descripcion": "Formato para procedimientos operativos estandar bajo BPM-2024.",
        "version": "v1",
    },
}

_EXT_TO_CATEGORIA: dict[str, str] = {
    ".doc": "word",
    ".docx": "word",
    ".xls": "excel",
    ".xlsx": "excel",
    ".ppt": "ppt",
    ".pptx": "ppt",
    ".pdf": "otro",
}


# ─── Helpers ────────────────────────────────────────────────────────────

def _get_storage_root() -> Path:
    """Devuelve la ruta absoluta al directorio de plantillas.

    Configurable via env var PLANTILLAS_STORAGE_PATH (default: /app/storage/plantillas).
    En tests se puede pasar un directorio temporal.
    """
    env_root = os.getenv("PLANTILLAS_STORAGE_PATH")
    if env_root:
        return Path(env_root)
    # Default: asumimos que el contenedor expone /app/storage/plantillas.
    # Si el path no existe (ej: dev nativo en Windows), fallback a una
    # ruta relativa al backend para no romper el endpoint.
    container_default = Path("/app/storage/plantillas")
    if container_default.exists():
        return container_default
    # Fallback dev: backend/storage/plantillas (donde start-stack-des.bat copia los archivos)
    repo_default = Path(__file__).resolve().parent.parent.parent / "storage" / "plantillas"
    if repo_default.exists():
        return repo_default
    return container_default  # el endpoint devolvera lista vacia


def _is_safe_filename(nombre: str) -> bool:
    """Valida que el nombre no contenga path traversal ni caracteres raros."""
    if not nombre:
        return False
    if "/" in nombre or "\\" in nombre or ".." in nombre:
        return False
    # Solo permitir alfanumerico, guion bajo, guion medio, punto
    return all(c.isalnum() or c in "._-" for c in nombre)


def _safe_ext(path: Path) -> str:
    """Extrae la extension de manera segura y la devuelve normalizada."""
    return path.suffix.lower()


# ─── Endpoints ──────────────────────────────────────────────────────────

@router.get("", response_model=PlantillaListResponse)
async def list_plantillas(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Lista las plantillas disponibles."""
    await require_authenticated(request, db)
    items = listar_plantillas()
    out = []
    for p in items:
        ext = Path(p["nombre_archivo"]).suffix.lower()
        out.append(PlantillaDocumentalOut(
            nombre_archivo=p["nombre_archivo"],
            nombre_display=p["nombre_display"],
            descripcion=p.get("descripcion", ""),
            categoria=_EXT_TO_CATEGORIA.get(ext, "otro"),
            tamano_bytes=p["tamano_bytes"],
            version="v1",
            url_descarga=f"/api/v1/plantillas-documentales/{p['nombre_archivo']}/download",
            activo=p.get("activo", True),
        ))
    return PlantillaListResponse(total=len(out), items=out)


@router.get("/{nombre_archivo}/download")
async def download_plantilla(
    nombre_archivo: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Descarga una plantilla. Auth required. Se audita en audit_log.

    Validaciones:
      - nombre_archivo: sin path traversal, sin caracteres raros
      - extension: debe estar en la whitelist (.doc, .docx, .xls, .xlsx, .ppt, .pptx, .pdf)
      - archivo debe existir en el directorio de plantillas
    """
    user = await require_authenticated(request, db)

    if not _is_safe_filename(nombre_archivo):
        raise HTTPException(400, f"Nombre de archivo invalido: {nombre_archivo}")

    ext = _safe_ext(Path(nombre_archivo))
    if ext not in _EXT_TO_CATEGORIA:
        raise HTTPException(415, f"Extension no permitida: {ext}")

    root = _get_storage_root()
    file_path = root / nombre_archivo
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(404, f"Plantilla '{nombre_archivo}' no encontrada")

    # Determinar media type segun extension
    media_types = {
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    # Auditar la descarga (en transaccion separada para no afectar el stream)
    try:
        await write_audit(
            db, request, user,
            accion="DOWNLOAD",
            recurso="plantilla_documental",
            recurso_id=None,
            descripcion=f"Descarga plantilla '{nombre_archivo}'",
            detalles={
                "nombre_archivo": nombre_archivo,
                "tamano_bytes": file_path.stat().st_size,
                "categoria": _EXT_TO_CATEGORIA[ext],
            },
        )
        await db.commit()
    except Exception as exc:  # noqa: BLE001
        # Si falla el audit, logueamos pero dejamos descargar (no bloqueamos
        # el negocio por un fallo de auditoria).
        logger.warning("No se pudo auditar descarga de plantilla %s: %s", nombre_archivo, exc)

    logger.info("Descarga plantilla '%s' por user=%s", nombre_archivo, user.username)

    return FileResponse(
        path=str(file_path),
        filename=nombre_archivo,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
            "X-Plantilla-Nombre": nombre_archivo,
        },
    )


# ════════════════════════════════════════════════════════════════
#  Endpoints ADMIN (solo ETO/ADMIN)
# ════════════════════════════════════════════════════════════════

@router.post("/admin/upload")
async def upload_plantilla_admin(
    request: Request,
    archivo: UploadFile = File(...),
    nombre_display: str = Form(""),
    descripcion: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Sube una nueva plantilla. Requiere ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    if not archivo.filename:
        raise HTTPException(400, "Nombre de archivo requerido")
    contenido = await archivo.read()
    if len(contenido) > 50 * 1024 * 1024:
        raise HTTPException(413, "Archivo demasiado grande (max 50MB)")
    result = subir_plantilla(archivo.filename, contenido, nombre_display, descripcion)
    await write_audit(db, request, await require_authenticated(request, db),
                      accion="UPLOAD", recurso="plantilla_documental", recurso_id=None,
                      descripcion=f"Plantilla subida: {archivo.filename}")
    await db.commit()
    return result


@router.patch("/admin/{nombre_archivo}")
async def rename_plantilla_admin(
    nombre_archivo: str,
    request: Request,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Renombra el nombre_display de una plantilla. Requiere ETO o ADMIN."""
    await require_eto_or_admin(request, db)
    nuevo_nombre = payload.get("nombre_display", "").strip()
    nueva_desc = payload.get("descripcion", "").strip()
    if not nuevo_nombre:
        raise HTTPException(422, "nombre_display requerido")
    result = renombrar_plantilla(nombre_archivo, nuevo_nombre, nueva_desc)
    if not result:
        raise HTTPException(404, "Plantilla no encontrada")
    return result


@router.delete("/admin/{nombre_archivo}")
async def delete_plantilla_admin(
    nombre_archivo: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Elimina (desactiva) una plantilla. Requiere ETO o ADMIN."""
    user = await require_eto_or_admin(request, db)
    ok = eliminar_plantilla(nombre_archivo)
    if not ok:
        raise HTTPException(404, "Plantilla no encontrada")
    await write_audit(db, request, user,
                      accion="DELETE", recurso="plantilla_documental", recurso_id=None,
                      descripcion=f"Plantilla eliminada: {nombre_archivo}")
    await db.commit()
    return {"ok": True}
