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
    Formato: {codigo}/{version}

    Ejemplos:
        formatear_codigo_completo("CC-3-005", "00") -> "CC-3-005/00"
        formatear_codigo_completo("CC-3-005", "01") -> "CC-3-005/01"
    """
    return f"{codigo}/{version}"
