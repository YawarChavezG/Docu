"""
Tests para vigencia_service: calculo de expiracion y vigencia de documentos.
Cubre calcular_expira_at (funcion pura, sin BD) y calcular_vigencia (async, con BD).
"""
from datetime import datetime, timezone, timedelta

import pytest

from app.services.vigencia_service import (
    calcular_expira_at,
    calcular_vigencia,
    recalcular_y_persistir_vigencia,
)


# ════════════════════════════════════════════════════════════════
#  calcular_expira_at (funcion pura — NO requiere BD)
# ════════════════════════════════════════════════════════════════

def test_calcular_expira_at_con_periodo():
    """4 anos de vigencia desde aprobacion."""
    aprobacion = datetime(2026, 6, 1, tzinfo=timezone.utc)
    expira = calcular_expira_at(aprobacion, periodo_vigencia_anos=4, indefinido=False)
    assert expira is not None
    # 4 anos ~ 1460 dias (con años bisiestos puede variar)
    assert (expira - aprobacion).days >= 1459
    assert expira.year == 2030


def test_calcular_expira_at_indefinido():
    """Si el tipo es indefinido, retorna None (nunca vence)."""
    expira = calcular_expira_at(
        datetime(2026, 6, 1, tzinfo=timezone.utc),
        periodo_vigencia_anos=4, indefinido=True,
    )
    assert expira is None


def test_calcular_expira_at_sin_periodo():
    """Si periodo_vigencia_anos es None o 0, retorna None."""
    aprobacion = datetime(2026, 6, 1, tzinfo=timezone.utc)
    assert calcular_expira_at(aprobacion, None, False) is None
    assert calcular_expira_at(aprobacion, 0, False) is None


def test_calcular_expira_at_sin_aprobacion():
    """Si aprobacion_at es None, retorna None."""
    assert calcular_expira_at(None, 4, False) is None


# ════════════════════════════════════════════════════════════════
#  calcular_vigencia (async — requiere BD via db_session)
# ════════════════════════════════════════════════════════════════

from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento
from app.models.tipo_documento import TipoDocumento
from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion


async def _crear_tipo_y_doc(
    db_session,
    area,
    user_id,
    *,
    periodo_vigencia=4,
    indefinido=False,
    estatus=EstatusDocumento.EN_ELABORACION,
    vigencia=VigenciaDocumento.VIGENTE,
    aprobacion_at=None,
    expira_at=None,
) -> tuple[TipoDocumento, Documento]:
    """Helper: crea TipoDocumento + Documento y retorna ambos."""
    tipo = TipoDocumento(
        codigo=77, slug="VIG77", nombre="Vigencia Test",
        periodo_vigencia=periodo_vigencia, indefinido=indefinido, activo=True,
    )
    db_session.add(tipo)
    await db_session.flush()

    doc = Documento(
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        tipo_documento_id=tipo.id,
        correlativo=1,
        codigo="VIG-77-001",
        version="00",
        titulo="Test Vigencia",
        estatus=estatus,
        vigencia=vigencia,
        activo=True,
        created_by_id=user_id,
        updated_by_id=user_id,
        aprobacion_at=aprobacion_at,
        expira_at=expira_at,
    )
    db_session.add(doc)
    await db_session.flush()
    return tipo, doc


@pytest.mark.asyncio
async def test_calcular_vigencia_obsoleto(db_session, seed_catalogos):
    """Documento OBSOLETO: vigencia = OBSOLETO."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    _, doc = await _crear_tipo_y_doc(
        db_session, area, eto.id,
        estatus=EstatusDocumento.OBSOLETO,
        vigencia=VigenciaDocumento.OBSOLETO,
    )
    await db_session.commit()

    result = await calcular_vigencia(db_session, doc)
    assert result == VigenciaDocumento.OBSOLETO


@pytest.mark.asyncio
async def test_calcular_vigencia_sin_aprobacion(db_session, seed_catalogos):
    """Documento sin aprobacion_at: vigencia = VIGENTE (aun no empezo a contar)."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    _, doc = await _crear_tipo_y_doc(
        db_session, area, eto.id,
        estatus=EstatusDocumento.EN_ELABORACION,
    )
    await db_session.commit()

    result = await calcular_vigencia(db_session, doc)
    assert result == VigenciaDocumento.VIGENTE


@pytest.mark.asyncio
async def test_calcular_vigencia_vencido(db_session, seed_catalogos):
    """Documento APROBADO con expira_at en el pasado: VENCIDO."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    _, doc = await _crear_tipo_y_doc(
        db_session, area, eto.id,
        estatus=EstatusDocumento.APROBADO,
        vigencia=VigenciaDocumento.VIGENTE,
        aprobacion_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        expira_at=datetime(2020, 6, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    result = await calcular_vigencia(db_session, doc)
    assert result == VigenciaDocumento.VENCIDO


@pytest.mark.asyncio
async def test_calcular_vigencia_por_vencer(db_session, seed_catalogos):
    """Documento con pocos dias restantes: POR_VENCER."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    ahora = datetime(2026, 6, 15, tzinfo=timezone.utc)
    expira_at = ahora + timedelta(days=3)  # 3 dias < amarillo (5)
    _, doc = await _crear_tipo_y_doc(
        db_session, area, eto.id,
        estatus=EstatusDocumento.APROBADO,
        vigencia=VigenciaDocumento.VIGENTE,
        aprobacion_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        expira_at=expira_at,
    )
    await db_session.commit()

    result = await calcular_vigencia(db_session, doc, ahora=ahora)
    assert result == VigenciaDocumento.POR_VENCER


@pytest.mark.asyncio
async def test_calcular_vigencia_indefinido(db_session, seed_catalogos):
    """Tipo documento con indefinido=True: VIGENTE (nunca vence)."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    _, doc = await _crear_tipo_y_doc(
        db_session, area, eto.id,
        periodo_vigencia=None, indefinido=True,
        estatus=EstatusDocumento.APROBADO,
        vigencia=VigenciaDocumento.VIGENTE,
        aprobacion_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        expira_at=None,  # indefinido -> expira_at=None
    )
    await db_session.commit()

    result = await calcular_vigencia(db_session, doc)
    assert result == VigenciaDocumento.VIGENTE


@pytest.mark.asyncio
async def test_recalcular_y_persistir_vigencia(db_session, seed_catalogos):
    """recalcular_y_persistir_vigencia persiste el cambio en el documento."""
    area = seed_catalogos["area"]
    eto = seed_catalogos["eto"]
    # Documento VENCIDO
    _, doc = await _crear_tipo_y_doc(
        db_session, area, eto.id,
        estatus=EstatusDocumento.APROBADO,
        vigencia=VigenciaDocumento.VIGENTE,  # Actualmente VIGENTE pero deberia ser VENCIDO
        aprobacion_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        expira_at=datetime(2020, 6, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    nueva = await recalcular_y_persistir_vigencia(db_session, doc)
    assert nueva == VigenciaDocumento.VENCIDO
    assert doc.vigencia == VigenciaDocumento.VENCIDO
