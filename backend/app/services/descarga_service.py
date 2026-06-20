"""
Servicio: descarga_service
Control de limite de descargas de documentos editables.

Reglas (US-2.01):
- Todos los tipos: 1 descarga/dia/usuario (LEY, no configurable via BD)
- Excepcion (tipos en tipos_excluidos_limite_descarga): 
  max_descargas_editables_dia por dia/usuario (actualmente 10)
- Solo documentos NO OBSOLETO pueden descargarse
- El contador se resetea cada dia calendario
"""
import json
import logging
from datetime import date

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit
from app.models.audit_log import AuditLog
from app.models.configuracion_global import ConfiguracionGlobal
from app.models.documento import Documento, EstatusDocumento
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

LIMITE_GENERAL_POR_DIA = 1


async def contar_descargas_hoy(db: AsyncSession, usuario_id: int) -> int:
    """Cuantas descargas de EDITABLES hizo el usuario hoy (segun audit_log)."""
    hoy = date.today()
    result = await db.execute(
        select(func.count(AuditLog.id))
        .where(AuditLog.usuario_id == usuario_id)
        .where(AuditLog.accion == "DOWNLOAD")
        .where(AuditLog.recurso == "documento_editable")
        .where(func.date(AuditLog.created_at) == hoy)
    )
    return result.scalar_one() or 0


async def obtener_limite_diario(db: AsyncSession, documento: Documento) -> int:
    """
    Retorna el limite de descargas diarias para un documento.
    - Si el tipo esta en tipos_excluidos_limite_descarga: max_descargas_editables_dia
    - Si no: LIMITE_GENERAL_POR_DIA (1)
    """
    try:
        cfg = await db.execute(
            select(ConfiguracionGlobal)
            .where(ConfiguracionGlobal.clave.in_([
                "max_descargas_editables_dia",
                "tipos_excluidos_limite_descarga",
            ]))
        )
        configs = {c.clave: c.valor for c in cfg.scalars().all()}

        tipos_excluidos_str = configs.get("tipos_excluidos_limite_descarga", "[]")
        try:
            tipos_excluidos = json.loads(tipos_excluidos_str)
        except (json.JSONDecodeError, TypeError):
            tipos_excluidos = []

        tipo = documento.tipo_documento
        if tipo and tipo.slug in tipos_excluidos:
            return int(configs.get("max_descargas_editables_dia", "10"))
    except Exception as e:
        logger.warning("Error al leer config descargas: %s", e)

    return LIMITE_GENERAL_POR_DIA


async def puede_descargar(
    db: AsyncSession,
    usuario: Usuario,
    documento: Documento,
) -> tuple[bool, str, int]:
    """
    Verifica si el usuario puede descargar el documento editable.

    Returns:
        (puede, mensaje_error, limite_diario)
    """
    if documento.estatus == EstatusDocumento.OBSOLETO:
        return False, "No se puede descargar un documento OBSOLETO", 0

    limite = await obtener_limite_diario(db, documento)
    descargas_hoy = await contar_descargas_hoy(db, usuario.id)

    if descargas_hoy >= limite:
        return (
            False,
            f"Ha superado el limite diario de descargas ({limite} por dia). "
            f"Vuelva a intentar manana.",
            limite,
        )

    return True, "", limite


async def registrar_descarga(
    db: AsyncSession,
    request: Request,
    usuario: Usuario,
    documento: Documento,
) -> None:
    """Registra la descarga en audit_log. NO hace commit (el caller lo hace)."""
    await write_audit(
        db, request, usuario,
        accion="DOWNLOAD",
        recurso="documento_editable",
        recurso_id=documento.id,
        descripcion=(
            f"Descarga editable: {documento.codigo} V{documento.version} "
            f"({documento.titulo})"
        ),
        detalles={
            "codigo": documento.codigo,
            "version": documento.version,
            "titulo": documento.titulo,
            "tipo_documento_id": documento.tipo_documento_id,
        },
    )
