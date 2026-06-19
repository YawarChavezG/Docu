"""
Tests para el modelo BitacoraTimeline (R3 Fase 1 - sesion 37).
Append-only timeline del documento (US-8.01).
"""
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.bitacora_timeline import BitacoraTimeline
from app.models.documento import Documento, EstatusDocumento
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.tipo_documento import TipoDocumento


async def _crear_flujo(db_session, seed_catalogos, codigo="CC-7-100"):
    area = seed_catalogos["area"]
    tipo = (await db_session.execute(
        select(TipoDocumento).where(TipoDocumento.codigo == 8)
    )).scalar_one_or_none()
    if not tipo:
        tipo = TipoDocumento(
            codigo=8, slug="PROCEDIMIENTO", nombre="Procedimiento",
            periodo_vigencia=4, indefinido=False, max_descargas_dia=10, activo=True,
        )
        db_session.add(tipo)
        await db_session.commit()
        await db_session.refresh(tipo)

    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=100, codigo=codigo, version="00", titulo="Test",
        estatus=EstatusDocumento.EN_REVISION, activo=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    from sqlalchemy import text
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
    return flujo


# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_crear_nodo_basico(db_session, seed_catalogos):
    """Crear nodo con defaults: color_nodo='azul', created_at auto."""
    flujo = await _crear_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    nodo = BitacoraTimeline(
        documento_flujo_id=flujo.id, usuario_id=eto.id,
        accion="CREADO",
    )
    db_session.add(nodo)
    await db_session.commit()
    await db_session.refresh(nodo)
    assert nodo.id is not None
    assert nodo.accion == "CREADO"
    assert nodo.color_nodo == "azul"
    assert nodo.created_at is not None
    assert nodo.estado_origen is None
    assert nodo.estado_destino is None
    assert nodo.observacion is None


@pytest.mark.asyncio
async def test_colores_us_8_01(db_session, seed_catalogos):
    """5 colores validos segun US-8.01: azul/verde/rojo/ambar/gris."""
    flujo = await _crear_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    for color in ("azul", "verde", "rojo", "ambar", "gris"):
        n = BitacoraTimeline(
            documento_flujo_id=flujo.id, usuario_id=eto.id,
            accion=f"TEST_{color}", color_nodo=color,
        )
        db_session.add(n)
    await db_session.commit()
    result = await db_session.execute(
        select(func.count(BitacoraTimeline.id))
        .where(BitacoraTimeline.documento_flujo_id == flujo.id)
    )
    assert result.scalar_one() == 5


@pytest.mark.asyncio
async def test_check_color_valido_definido():
    """CHECK ck_bitacora_color_valido: el modelo declara la constraint con los 5 colores US-8.01."""
    table_args = BitacoraTimeline.__table_args__
    found = any(
        getattr(c, "name", None) == "ck_bitacora_color_valido" and
        all(color in c.sqltext.text for color in ("azul", "verde", "rojo", "ambar", "gris"))
        for c in table_args if hasattr(c, "sqltext")
    )
    assert found, "CHECK constraint ck_bitacora_color_valido debe estar definido con los 5 colores"


@pytest.mark.asyncio
async def test_nodo_con_tarea(db_session, seed_catalogos):
    """Nodo puede referenciar una tarea (opcional)."""
    from app.models.tarea import Tarea
    from app.models.semaforizacion_tarea import TipoTarea
    flujo = await _crear_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    tarea = Tarea(
        documento_flujo_id=flujo.id, usuario_id=eto.id,
        tipo_tarea=TipoTarea.REVISION.value,
    )
    db_session.add(tarea)
    await db_session.commit()
    await db_session.refresh(tarea)

    nodo = BitacoraTimeline(
        documento_flujo_id=flujo.id, usuario_id=eto.id,
        tarea_id=tarea.id, accion="APROBADO", color_nodo="verde",
        observacion="OK",
    )
    db_session.add(nodo)
    await db_session.commit()
    await db_session.refresh(nodo)
    assert nodo.tarea_id == tarea.id
    assert nodo.color_nodo == "verde"


@pytest.mark.asyncio
async def test_fk_documento_flujo_invalido(db_session, seed_catalogos):
    """FK documento_flujo: inexistente => IntegrityError."""
    eto = seed_catalogos["eto"]
    n = BitacoraTimeline(
        documento_flujo_id=999999, usuario_id=eto.id, accion="CREADO",
    )
    db_session.add(n)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_indice_flujo_orden_cronologico(db_session, seed_catalogos):
    """Indice ix_bitacora_flujo: WHERE documento_flujo_id=X ORDER BY created_at."""
    flujo = await _crear_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    # 3 nodos en orden
    for i, acc in enumerate(["CREADO", "LIBERADO_ETO", "APROBADO"]):
        db_session.add(BitacoraTimeline(
            documento_flujo_id=flujo.id, usuario_id=eto.id,
            accion=acc, color_nodo=("azul" if i == 0 else "verde"),
        ))
    await db_session.commit()

    result = await db_session.execute(
        select(BitacoraTimeline.accion)
        .where(BitacoraTimeline.documento_flujo_id == flujo.id)
        .order_by(BitacoraTimeline.created_at)
    )
    acciones = [r[0] for r in result.all()]
    assert acciones == ["CREADO", "LIBERADO_ETO", "APROBADO"]


@pytest.mark.asyncio
async def test_repr(db_session, seed_catalogos):
    flujo = await _crear_flujo(db_session, seed_catalogos)
    eto = seed_catalogos["eto"]
    n = BitacoraTimeline(
        documento_flujo_id=flujo.id, usuario_id=eto.id,
        accion="CREADO", color_nodo="azul",
    )
    db_session.add(n)
    await db_session.commit()
    await db_session.refresh(n)
    r = repr(n)
    assert "BitacoraTimeline" in r
    assert "CREADO" in r
