"""
Tests para TareaObservacion (R3 Fase 1 - sesion 37).
Observaciones por tarea (US-3.04: min 10 chars).
"""
import pytest
from sqlalchemy import select, func

from app.models.tarea_observacion import TareaObservacion
from app.models.tarea import Tarea
from app.models.semaforizacion_tarea import TipoTarea
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento
from sqlalchemy import text


async def _crear_tarea(db_session, seed_catalogos, codigo="CC-7-300"):
    area = seed_catalogos["area"]
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 6)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=6, slug="INSTRUCTIVO", nombre="Instructivo",
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)

    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=300, codigo=codigo, version="00", titulo="Test",
        estatus=EstatusDocumento.EN_REVISION, activo=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    estado_id = (await db_session.execute(text("SELECT id FROM estados WHERE codigo='EN_REVISION'"))).scalar_one()
    flujo = DocumentoFlujo(
        documento_id=doc.id, estado_actual_id=estado_id,
        tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        codigo_snapshot=codigo, version_snapshot="00", titulo="Test",
        elaborador_id=seed_catalogos["eto"].id, fecha_solicitud=doc.created_at,
        alcance_difusion_ids=[], revisor_ids=[], aprobador_ids=[],
        activo=True, created_by_id=seed_catalogos["eto"].id,
    )
    db_session.add(flujo)
    await db_session.commit()
    await db_session.refresh(flujo)

    tarea = Tarea(
        documento_flujo_id=flujo.id, usuario_id=seed_catalogos["eto"].id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)
    return tarea


# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_crear_observacion_basica(db_session, seed_catalogos):
    """Crear observacion con defaults: corregida=False."""
    tarea = await _crear_tarea(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    obs = TareaObservacion(
        tarea_id=tarea.id, usuario_id=eto.id,
        observacion="Falta detalle en el punto 3 del procedimiento",
    )
    db_session.add(obs)
    await db_session.commit()
    await db_session.refresh(obs)
    assert obs.id is not None
    assert obs.observacion == "Falta detalle en el punto 3 del procedimiento"
    assert obs.corregida is False
    assert obs.corregida_at is None


@pytest.mark.asyncio
async def test_check_min_10_chars_definido():
    """CHECK ck_observacion_min_10_chars: el modelo declara la constraint length >= 10."""
    table_args = TareaObservacion.__table_args__
    found = any(
        getattr(c, "name", None) == "ck_observacion_min_10_chars" and
        "length" in c.sqltext.text.lower() and ">= 10" in c.sqltext.text
        for c in table_args if hasattr(c, "sqltext")
    )
    assert found, "CHECK constraint ck_observacion_min_10_chars debe estar definido con length >= 10"


@pytest.mark.asyncio
async def test_observacion_marca_corregida(db_session, seed_catalogos):
    """Marcar observacion como corregida: setea flag + corregida_at."""
    from datetime import datetime
    tarea = await _crear_tarea(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    obs = TareaObservacion(
        tarea_id=tarea.id, usuario_id=eto.id,
        observacion="Corregir formato de la tabla 2",
    )
    db_session.add(obs)
    await db_session.commit()
    await db_session.refresh(obs)

    obs.corregida = True
    obs.corregida_at = datetime.now()
    await db_session.commit()
    await db_session.refresh(obs)
    assert obs.corregida is True
    assert obs.corregida_at is not None


@pytest.mark.asyncio
async def test_indice_pendientes(db_session, seed_catalogos):
    """Indice ix_obs_pendientes: WHERE tarea_id=X AND corregida=FALSE."""
    tarea = await _crear_tarea(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    db_session.add_all([
        TareaObservacion(tarea_id=tarea.id, usuario_id=eto.id,
                         observacion="Observacion pendiente 1", corregida=False),
        TareaObservacion(tarea_id=tarea.id, usuario_id=eto.id,
                         observacion="Observacion corregida 2", corregida=True),
        TareaObservacion(tarea_id=tarea.id, usuario_id=eto.id,
                         observacion="Observacion pendiente 3", corregida=False),
    ])
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(TareaObservacion.id))
        .where(TareaObservacion.tarea_id == tarea.id)
        .where(TareaObservacion.corregida == False)
    )
    assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_observaciones_multiples_por_tarea(db_session, seed_catalogos):
    """Una tarea puede tener N observaciones (no hay UNIQUE)."""
    tarea = await _crear_tarea(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    for i in range(3):
        db_session.add(TareaObservacion(
            tarea_id=tarea.id, usuario_id=eto.id,
            observacion=f"Observacion numero {i+1} con suficiente largo",
        ))
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(TareaObservacion.id))
        .where(TareaObservacion.tarea_id == tarea.id)
    )
    assert result.scalar_one() == 3


@pytest.mark.asyncio
async def test_fk_tarea_invalido(db_session, seed_catalogos):
    """FK tarea_id: inexistente => IntegrityError."""
    from sqlalchemy.exc import IntegrityError
    eto = seed_catalogos["eto"]
    obs = TareaObservacion(
        tarea_id=999999, usuario_id=eto.id,
        observacion="Esto no deberia poder insertarse",
    )
    db_session.add(obs)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_repr(db_session, seed_catalogos):
    tarea = await _crear_tarea(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    obs = TareaObservacion(
        tarea_id=tarea.id, usuario_id=eto.id,
        observacion="Repr test observation content",
    )
    db_session.add(obs)
    await db_session.commit()
    await db_session.refresh(obs)
    rv = repr(obs)
    assert "TareaObservacion" in rv
    assert "corregida=False" in rv
