"""
Tests para Proceso (R3 Fase 1 - sesion 37).
Catalogo de procesos documentales (PROPUESTA-R3-TABLAS.md §1.5.6).
"""
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.proceso import Proceso


@pytest.mark.asyncio
async def test_crear_proceso_basico(db_session):
    """Crear proceso con defaults: activo=True."""
    p = Proceso(nombre="ANALISIS")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    assert p.id is not None
    assert p.nombre == "ANALISIS"
    assert p.activo is True
    assert p.descripcion is None
    assert p.created_at is not None


@pytest.mark.asyncio
async def test_nombre_unico(db_session):
    """UNIQUE en nombre: no se permiten duplicados."""
    db_session.add(Proceso(nombre="FABRICACION"))
    await db_session.commit()

    db_session.add(Proceso(nombre="FABRICACION"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_seed_basico_10_procesos(db_session):
    """Seed minimo de 10 procesos genericos sugerido en PROPUESTA §1.5.6."""
    nombres = [
        "ANALISIS", "FABRICACION", "CONTROL CALIDAD", "LOGISTICA",
        "COMERCIAL", "ADMINISTRACION", "INVESTIGACION", "DESARROLLO",
        "MANTENIMIENTO", "PLANIFICACION",
    ]
    for n in nombres:
        db_session.add(Proceso(nombre=n, activo=True))
    await db_session.commit()

    result = await db_session.execute(select(func.count(Proceso.id)))
    assert result.scalar_one() == 10


@pytest.mark.asyncio
async def test_borrado_logico(db_session):
    """activo=False marca como inactivo (no se hace DELETE fisico)."""
    p = Proceso(nombre="OBSOLETO_PROCESO")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    p.activo = False
    await db_session.commit()
    await db_session.refresh(p)
    assert p.activo is False
    # Sigue existiendo en BD
    found = (await db_session.execute(
        select(Proceso).where(Proceso.id == p.id)
    )).scalar_one()
    assert found is not None


@pytest.mark.asyncio
async def test_actualizar_nombre(db_session):
    """PATCH del nombre (no del ID)."""
    p = Proceso(nombre="VIEJO_NOMBRE")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    p.nombre = "NUEVO_NOMBRE"
    await db_session.commit()
    await db_session.refresh(p)
    assert p.nombre == "NUEVO_NOMBRE"


@pytest.mark.asyncio
async def test_filtro_activos(db_session):
    """Query tipica: WHERE activo=TRUE para listar en dropdowns."""
    db_session.add_all([
        Proceso(nombre="P1", activo=True),
        Proceso(nombre="P2", activo=False),
        Proceso(nombre="P3", activo=True),
    ])
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(Proceso.id)).where(Proceso.activo == True)
    )
    assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_repr(db_session):
    p = Proceso(nombre="TEST_REPR")
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)
    rv = repr(p)
    assert "Proceso" in rv
    assert "TEST_REPR" in rv
