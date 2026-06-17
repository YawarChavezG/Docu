"""
Servicio: vigencia_service
Calcula la VigenciaDocumento de un documento en base a:
  - aprobacion_at
  - tipo_documento.periodo_vigencia (anos)
  - tipo_documento.indefinido
  - reglas del semaforo (semaforo_verde_dias, semaforo_amarillo_dias)

Logica:
  - Si estatus == OBSOLETO:   vigencia = OBSOLETO
  - Si tipo.indefinido:        vigencia = VIGENTE  (no vence)
  - Si no hay aprobacion_at:   vigencia = VIGENTE  (aun no se aprobo)
  - Calcular dias_restantes = (expira_at - hoy).days
  - Si dias_restantes < 0:            VENCIDO
  - Si dias_restantes <= amarillo:    POR_VENCER
  - Si dias_restantes <= verde:       VIGENTE  (cerca pero en plazo)
  - Else:                             VIGENTE

La columna vigencia en BD se persiste al CREAR o APROBAR el documento,
NO se recalcula en cada lectura (seria costoso). El trigger SQL de
obsolescencia (R5) recalculara en background.

Los umbrales vienen de configuracion_global:
  - semaforo_verde_dias  (default 10)
  - semaforo_amarillo_dias (default 5)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuracion_global import (
    ConfiguracionGlobal,
    CategoriaConfiguracion,
)
from app.models.documento import (
    Documento,
    EstatusDocumento,
    VigenciaDocumento,
)
from app.models.tipo_documento import TipoDocumento


# ─── Defaults hardcoded (fallback si no estan en BD) ───
DEFAULT_SEMAFORO_VERDE_DIAS = 10
DEFAULT_SEMAFORO_AMARILLO_DIAS = 5


async def _get_semaforo_umbrales(db: AsyncSession) -> tuple[int, int]:
    """
    Lee los umbrales del semaforo de configuracion_global.
    Returns: (verde_dias, amarillo_dias)
    """
    verde = DEFAULT_SEMAFORO_VERDE_DIAS
    amarillo = DEFAULT_SEMAFORO_AMARILLO_DIAS

    result = await db.execute(
        select(ConfiguracionGlobal)
        .where(ConfiguracionGlobal.categoria == CategoriaConfiguracion.SEMAFORO)
        .where(ConfiguracionGlobal.activo == True)
    )
    rows = result.scalars().all()
    for r in rows:
        if r.clave == "semaforo_verde_dias":
            try:
                verde = int(r.valor)
            except (ValueError, TypeError):
                pass
        elif r.clave == "semaforo_amarillo_dias":
            try:
                amarillo = int(r.valor)
            except (ValueError, TypeError):
                pass
    return verde, amarillo


def calcular_expira_at(
    aprobacion_at: datetime,
    periodo_vigencia_anos: Optional[int],
    indefinido: bool,
) -> Optional[datetime]:
    """
    Calcula expira_at segun las reglas del modelo.

    Returns None si:
      - aprobacion_at es None
      - tipo.indefinido == True (no vence nunca)
      - periodo_vigencia_anos es None o 0
    """
    if aprobacion_at is None or indefinido:
        return None
    if not periodo_vigencia_anos or periodo_vigencia_anos <= 0:
        return None
    return aprobacion_at + timedelta(days=365 * periodo_vigencia_anos)


async def calcular_vigencia(
    db: AsyncSession,
    documento: Documento,
    ahora: Optional[datetime] = None,
) -> VigenciaDocumento:
    """
    Calcula la vigencia de un documento.

    Args:
        db: sesion de BD (para leer umbrales del semaforo).
        documento: instancia con joins a tipo_documento (puede ser lazy-loaded).
        ahora: datetime de referencia (default = now UTC). Para testing.

    Returns:
        VigenciaDocumento (VIGENTE / POR_VENCER / VENCIDO / OBSOLETO).
    """
    ahora = ahora or datetime.now(timezone.utc)

    # 1. Si el estatus es OBSOLETO, la vigencia tambien.
    if documento.estatus == EstatusDocumento.OBSOLETO:
        return VigenciaDocumento.OBSOLETO

    # 2. Si no esta aprobado, sigue vigente (aun no empezo a contar).
    if documento.aprobacion_at is None or documento.expira_at is None:
        return VigenciaDocumento.VIGENTE

    # 3. Si no se cargo tipo_documento, cargarlo.
    tipo = documento.tipo_documento
    if tipo is None:
        tipo = await db.get(TipoDocumento, documento.tipo_documento_id)
    if tipo is None or tipo.indefinido:
        return VigenciaDocumento.VIGENTE

    # 4. Calcular dias restantes hasta el vencimiento.
    dias_restantes = (documento.expira_at - ahora).days

    # 5. Leer umbrales del semaforo.
    verde_dias, amarillo_dias = await _get_semaforo_umbrales(db)

    # 6. Aplicar reglas.
    if dias_restantes < 0:
        # Pero validar la regla del usuario: VENCIDO solo si esta APROBADO u OBSOLETO.
        if documento.estatus in (EstatusDocumento.APROBADO, EstatusDocumento.OBSOLETO):
            return VigenciaDocumento.VENCIDO
        # En elaboracion/revision no puede estar vencido logicamente.
        return VigenciaDocumento.VIGENTE

    if dias_restantes <= amarillo_dias:
        return VigenciaDocumento.POR_VENCER

    if dias_restantes <= verde_dias:
        # Verde: en plazo (cerca pero OK).
        return VigenciaDocumento.VIGENTE

    return VigenciaDocumento.VIGENTE


async def recalcular_y_persistir_vigencia(
    db: AsyncSession,
    documento: Documento,
) -> VigenciaDocumento:
    """
    Wrapper: calcula la vigencia y la persiste en el documento.
    NO hace commit (lo hace el caller).
    """
    nueva_vigencia = await calcular_vigencia(db, documento)
    if documento.vigencia != nueva_vigencia:
        documento.vigencia = nueva_vigencia
    return nueva_vigencia
