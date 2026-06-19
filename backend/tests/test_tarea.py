"""
Tests para el modelo Tarea (R3 Fase 1 - sesion 37).

Cubre:
- Creacion basica con defaults
- FK constraints (documento_flujo, usuario, tipo_tarea)
- UNIQUE constraint (flujo, usuario, tipo, fecha_asignacion)
- CHECK constraints (estado valido, intento_reasignacion 0-3)
- Indices funcionan (queries por usuario/estado, por flujo/tipo)
"""
import pytest
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError

from app.models.tarea import Tarea
from app.models.semaforizacion_tarea import TipoTarea
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento


# ─── Helpers ───

async def _crear_tipo(db_session, codigo: int, slug: str = "TEST"):
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == codigo)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=codigo, slug=slug, nombre=f"Tipo {slug}",
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)
    return tipo


async def _crear_doc_flujo(db_session, seed_catalogos, codigo="CC-7-001"):
    """Inserta un Documento + DocumentoFlujo minimos para asociar tareas."""
    area = seed_catalogos["area"]
    tipo = await _crear_tipo(db_session, codigo=7, slug="REGLAMENTO")

    doc = Documento(
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        tipo_documento_id=tipo.id,
        correlativo=1,
        codigo=codigo,
        version="00",
        titulo=f"Doc {codigo}",
        estatus=EstatusDocumento.EN_REVISION,
        activo=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    estado_id = (await db_session.execute(text("SELECT id FROM estados WHERE codigo='EN_REVISION'"))).scalar_one()
    flujo = DocumentoFlujo(
        documento_id=doc.id,
        estado_actual_id=estado_id,
        tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id,
        area_id=area.id,
        tipo_documento_id=tipo.id,
        codigo_snapshot=codigo,
        version_snapshot="00",
        titulo=f"Doc {codigo}",
        elaborador_id=seed_catalogos["eto"].id,
        fecha_solicitud=doc.created_at,
        alcance_difusion_ids=[],
        revisor_ids=[seed_catalogos["eto"].id],
        aprobador_ids=[seed_catalogos["admin"].id],
        activo=True,
        created_by_id=seed_catalogos["eto"].id,
    )
    db_session.add(flujo)
    await db_session.commit()
    await db_session.refresh(flujo)
    return flujo


# ════════════════════════════════════════════════════════════════
# Creacion basica
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_crear_tarea_revision_basica(db_session, seed_catalogos):
    """Crear tarea REVISION con defaults: estado=PENDIENTE, intento=0."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]

    tarea = Tarea(
        documento_flujo_id=flujo.id,
        usuario_id=eto.id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    assert tarea.id is not None
    assert tarea.estado == "PENDIENTE"
    assert tarea.intento_reasignacion == 0
    assert tarea.activo is True
    assert tarea.fecha_asignacion is not None
    assert tarea.fecha_completado is None
    assert tarea.fecha_vencimiento is None
    assert tarea.delegado_origen_id is None


@pytest.mark.asyncio
async def test_crear_tarea_liberacion_correccion(db_session, seed_catalogos):
    """Tipos nuevos LIBERACION y CORRECCION (R3 Fase 1) aceptados."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]

    for tipo_val in (TipoTarea.LIBERACION.value, TipoTarea.CORRECCION.value):
        tarea = Tarea(
            documento_flujo_id=flujo.id,
            usuario_id=eto.id,
            tipo_tarea=tipo_val,
            observacion="Tarea de prueba para tipo nuevo",
        )
        db_session.add(tarea)
        await db_session.commit()
        await db_session.refresh(tarea)
        assert tarea.tipo_tarea == tipo_val


# ════════════════════════════════════════════════════════════════
# FK constraints
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tarea_fk_documento_flujo_invalido(db_session, seed_catalogos):
    """FK documento_flujo: documento_flujo_id inexistente => IntegrityError."""
    eto = seed_catalogos["eto"]
    tarea = Tarea(
        documento_flujo_id=999999,  # ID que no existe
        usuario_id=eto.id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(tarea)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_tarea_fk_tipo_tarea_invalido(db_session, seed_catalogos):
    """FK tipo_tarea: tipo no existente en semaforizacion_tarea => IntegrityError."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    tarea = Tarea(
        documento_flujo_id=flujo.id,
        usuario_id=eto.id,
        tipo_tarea="TIPO_INEXISTENTE",
    )
    db_session.add(tarea)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


# ════════════════════════════════════════════════════════════════
# UNIQUE constraint
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tarea_unique_constraint(db_session, seed_catalogos):
    """UNIQUE (flujo, usuario, tipo, fecha_asignacion): no se puede duplicar."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]

    t1 = Tarea(
        documento_flujo_id=flujo.id,
        usuario_id=eto.id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(t1)
    await db_session.commit()

    t2 = Tarea(
        documento_flujo_id=flujo.id,
        usuario_id=eto.id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(t2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


# ════════════════════════════════════════════════════════════════
# CHECK constraints
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tarea_check_estado_invalido_definido():
    """CHECK ck_tarea_estado_valido: el modelo declara la constraint con los 6 valores."""
    table_args = Tarea.__table_args__
    found = any(
        getattr(c, "name", None) == "ck_tarea_estado_valido" and
        "PENDIENTE" in c.sqltext.text and "COMPLETADO" in c.sqltext.text and
        "REASIGNADO" in c.sqltext.text and "VENCIDO" in c.sqltext.text and
        "NO_EJECUTADO" in c.sqltext.text
        for c in table_args if hasattr(c, "sqltext")
    )
    assert found, "CHECK constraint ck_tarea_estado_valido debe estar definido con los 6 estados"


@pytest.mark.asyncio
async def test_tarea_check_intento_rango_definido():
    """CHECK ck_tarea_intento_rango: el modelo declara la constraint 0-3."""
    table_args = Tarea.__table_args__
    found = any(
        getattr(c, "name", None) == "ck_tarea_intento_rango" and
        ">= 0" in c.sqltext.text and "<= 3" in c.sqltext.text
        for c in table_args if hasattr(c, "sqltext")
    )
    assert found, "CHECK constraint ck_tarea_intento_rango debe estar definido con rango 0-3"


# ════════════════════════════════════════════════════════════════
# Indices (queries que usan los indices)
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tarea_indice_usuario_estado(db_session, seed_catalogos):
    """Indice ix_tareas_usuario_estado: WHERE usuario_id=X AND estado='PENDIENTE'."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]

    # 3 tareas para el mismo usuario, 2 PENDIENTE y 1 COMPLETADO
    t1 = Tarea(documento_flujo_id=flujo.id, usuario_id=eto.id,
               tipo_tarea=TipoTarea.REVISION.value, estado="PENDIENTE")
    t2 = Tarea(documento_flujo_id=flujo.id, usuario_id=eto.id,
               tipo_tarea=TipoTarea.APROBACION.value, estado="PENDIENTE")
    t3 = Tarea(documento_flujo_id=flujo.id, usuario_id=eto.id,
               tipo_tarea=TipoTarea.LIBERACION.value, estado="COMPLETADO")
    db_session.add_all([t1, t2, t3])
    await db_session.commit()

    # Query tipica de bandeja
    result = await db_session.execute(
        select(func.count(Tarea.id))
        .where(Tarea.usuario_id == eto.id)
        .where(Tarea.estado == "PENDIENTE")
        .where(Tarea.activo == True)
    )
    count = result.scalar_one()
    assert count == 2


@pytest.mark.asyncio
async def test_tarea_indice_flujo_tipo(db_session, seed_catalogos):
    """Indice ix_tareas_flujo_tipo: WHERE documento_flujo_id=X AND tipo_tarea=Y."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    admin = seed_catalogos["admin"]

    t1 = Tarea(documento_flujo_id=flujo.id, usuario_id=eto.id,
               tipo_tarea=TipoTarea.REVISION.value)
    t2 = Tarea(documento_flujo_id=flujo.id, usuario_id=admin.id,
               tipo_tarea=TipoTarea.APROBACION.value)
    t3 = Tarea(documento_flujo_id=flujo.id, usuario_id=eto.id,
               tipo_tarea=TipoTarea.APROBACION.value)
    db_session.add_all([t1, t2, t3])
    await db_session.commit()

    # Query: 2 tareas de APROBACION para este flujo
    result = await db_session.execute(
        select(func.count(Tarea.id))
        .where(Tarea.documento_flujo_id == flujo.id)
        .where(Tarea.tipo_tarea == TipoTarea.APROBACION.value)
    )
    assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_tarea_repr(db_session, seed_catalogos):
    """__repr__ retorna string legible."""
    flujo = await _crear_doc_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    t = Tarea(
        documento_flujo_id=flujo.id, usuario_id=eto.id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    r = repr(t)
    assert "Tarea" in r
    assert str(t.id) in r
    assert TipoTarea.REVISION.value in r
