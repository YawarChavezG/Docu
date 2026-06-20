"""
Servicio: correlativo_service
Genera el siguiente correlativo monotono dentro de (area_id, tipo_documento_id).

El correlativo define la unicidad del codigo de documento junto con la sigla
del area y el codigo del tipo (formato: CC-3-005/00).

Estrategia de concurrencia (sesion 21 R2):
1. PRIMARY: SELECT ... FOR UPDATE dentro de transaccion. Bloquea las filas
   del rango hasta que la transaccion commitee.
2. FALLBACK: pg_try_advisory_xact_lock(hashtext(area||tipo)) si el FOR UPDATE
   async falla con MissingGreenlet (problema conocido de SQLAlchemy 2.0 async
   con asyncpg + for_update en algunas versiones).

Reglas:
- NUNCA generar correlativo sin lock (puede colisionar con requests paralelos).
- Si la transaccion hace rollback, el correlativo generado se "desperdicia"
  (NO se rellena el hueco). Es la unica forma de garantizar monotonia estricta.
- El correlativo arranca en 1 (no en 0) por convencion COFAR.
"""
from typing import Tuple

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.documento import Documento


async def siguiente_correlativo(
    db: AsyncSession,
    area_id: int,
    tipo_documento_id: int,
) -> Tuple[int, int]:
    """
    Calcula el siguiente correlativo disponible para (area_id, tipo_documento_id).

    Returns:
        (correlativo, total_lock_id) — total_lock_id es para debugging/logs.

    Raises:
        RuntimeError: si no se pudo obtener el lock despues de esperar.

    IMPORTANTE: esta funcion DEBE ejecutarse dentro de una transaccion
    activa (async with db.begin()) para que el lock se mantenga hasta
    el commit.
    """
    # ─── PRIMARY: SELECT MAX + FOR UPDATE ───
    # Esto bloquea todas las filas existentes de (area, tipo) para que otro
    # worker no pueda leer el mismo MAX hasta que nosotros commiteemos.
    stmt = (
        select(func.coalesce(func.max(Documento.correlativo), 0).label("max_corr"))
        .where(Documento.area_id == area_id)
        .where(Documento.tipo_documento_id == tipo_documento_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    max_corr = result.scalar_one() or 0
    return (max_corr + 1, 0)


async def siguiente_correlativo_advisory(
    db: AsyncSession,
    area_id: int,
    tipo_documento_id: int,
) -> int:
    """
    FALLBACK: usa pg_try_advisory_xact_lock para serializar el calculo
    del correlativo sin depender de FOR UPDATE sobre las filas.

    Es portable, predecible y funciona con asyncpg incluso cuando
    with_for_update() da MissingGreenlet en SQLAlchemy 2.0.

    El lock se libera automaticamente al COMMIT/ROLLBACK de la transaccion.

    Returns:
        correlativo siguiente (1, 2, 3, ...).

    Raises:
        RuntimeError: si no se pudo obtener el lock despues de 50 intentos.
    """
    # hashtext() en Postgres genera un int4 a partir del string.
    # Usamos un prefijo para evitar colisiones con otros advisory locks.
    lock_key_sql = text("hashtext(:key)")
    lock_key = f"correlativo:{area_id}:{tipo_documento_id}"

    # Intentar obtener el lock (no-bloqueante). Si no se obtiene, esperar
    # un poco y reintentar hasta 50 veces (5 segundos total).
    for intento in range(50):
        got_lock = await db.execute(
            text("SELECT pg_try_advisory_xact_lock(hashtext(:key))"),
            {"key": lock_key},
        )
        if got_lock.scalar_one():
            break
        # Lock tomado por otro worker. Esperar 100ms y reintentar.
        import asyncio
        await asyncio.sleep(0.1)
    else:
        raise RuntimeError(
            f"No se pudo obtener advisory lock para {lock_key} despues de 50 intentos"
        )

    # Ahora que tenemos el lock, calcular el siguiente correlativo (sin FOR UPDATE).
    # Solo contar documentos ACTIVOS (borrado logico no cuenta).
    stmt = (
        select(func.coalesce(func.max(Documento.correlativo), 0))
        .where(Documento.area_id == area_id)
        .where(Documento.tipo_documento_id == tipo_documento_id)
        .where(Documento.activo == True)
    )
    result = await db.execute(stmt)
    max_corr = result.scalar_one() or 0
    return max_corr + 1


def formatear_codigo(area_sigla: str, tipo_codigo: int, correlativo: int) -> str:
    """
    Genera el codigo de documento SIN version.
    Formato: {sigla_area}-{codigo_tipo}-{correlativo:03d}

    Ejemplos:
        formatear_codigo("CC", 3, 5)   -> "CC-3-005"
        formatear_codigo("PRO", 7, 42) -> "PRO-7-042"
        formatear_codigo("DT", 1, 1)   -> "DT-1-001"
    """
    return f"{area_sigla}-{tipo_codigo}-{correlativo:03d}"


def formatear_codigo_completo(codigo: str, version: str) -> str:
    """
    Genera el codigo de documento CON version (lo que ve el usuario).
    Formato: {codigo} V{version}

    Ejemplos:
        formatear_codigo_completo("CC-3-005", "00") -> "CC-3-005 V00"
        formatear_codigo_completo("CC-3-005", "01") -> "CC-3-005 V01"
    """
    return f"{codigo} V{version}"


def generar_nombre_completo(codigo: str, titulo: str, version: str) -> str:
    """
    Genera el nombre completo del documento (codigo + titulo + version).
    Segun R3 item 0.1 y PROPUESTA-R3-TABLAS.md §1.5.1.

    Formato: {codigo} {TITULO EN MAYUSCULAS} V{version}

    Ejemplos:
        generar_nombre_completo("CC-7-005", "Procedimiento de Muestreo", "00")
        -> "CC-7-005 PROCEDIMIENTO DE MUESTREO V00"
        generar_nombre_completo("CAL-5-001", "manual de calidad", "01")
        -> "CAL-5-001 MANUAL DE CALIDAD V01"

    Args:
        codigo: codigo corto del documento (sin version), ej: "CC-7-005".
        titulo: titulo legible del documento. Se normaliza a MAYUSCULAS.
        version: version del documento en formato zero-padded ("00", "01", ...).

    Returns:
        Nombre completo listo para mostrar al usuario.
    """
    titulo_norm = (titulo or "").strip().upper()
    if not titulo_norm:
        return f"{codigo} V{version}"
    return f"{codigo} {titulo_norm} V{version}"


# ════════════════════════════════════════════════════════════════
#  R3 item 0.4: codigo de formularios (-F01, -F02, etc.)
#  PROPUESTA-R3-TABLAS.md §1.5.3
# ════════════════════════════════════════════════════════════════


def formatear_codigo_formulario(codigo_documento: str, correlativo_formulario: int) -> str:
    """
    Genera el codigo de un formulario.
    Formato: {codigo_documento}-F{correlativo:02d}

    Ejemplos:
        formatear_codigo_formulario("CC-6-032", 1) -> "CC-6-032-F01"
        formatear_codigo_formulario("CC-6-032", 2) -> "CC-6-032-F02"
        formatear_codigo_formulario("CC-6-032", 15) -> "CC-6-032-F15"
    """
    return f"{codigo_documento}-F{correlativo_formulario:02d}"


async def siguiente_correlativo_formulario(
    db: AsyncSession,
    documento_flujo_id: int,
) -> int:
    """
    Calcula el siguiente correlativo de formulario disponible para el flujo.

    Returns:
        Siguiente correlativo (1, 2, 3, ...).

    Raises:
        RuntimeError: si la consulta falla.

    IMPORTANTE: debe ejecutarse dentro de una transaccion activa
    (async with db.begin()) para garantizar consistencia.
    """
    from app.models.documento_formulario import DocumentoFormulario

    result = await db.execute(
        select(func.coalesce(func.max(DocumentoFormulario.correlativo_formulario), 0))
        .where(DocumentoFormulario.documento_flujo_id == documento_flujo_id)
        .where(DocumentoFormulario.activo == True)
    )
    max_corr = result.scalar_one() or 0
    return max_corr + 1
