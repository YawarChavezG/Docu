"""
Tests para el modelo Notificacion (R3 Fase 1 - sesion 37).
Cola persistente de notificaciones con tracking de lectura + email.
"""
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.notificacion import Notificacion


@pytest.mark.asyncio
async def test_crear_notificacion_basica(db_session, seed_catalogos):
    """Crear notificacion con defaults: leida=False, email_enviado=False."""
    eto = seed_catalogos["eto"]
    n = Notificacion(
        usuario_destino_id=eto.id,
        titulo="Tarea asignada",
        mensaje="Tenes una nueva tarea de revision",
        tipo_notificacion="ASIGNACION_TAREA",
    )
    db_session.add(n)
    await db_session.commit()
    await db_session.refresh(n)
    assert n.id is not None
    assert n.leida is False
    assert n.email_enviado is False
    assert n.fecha_lectura is None
    assert n.usuario_origen_id is None


@pytest.mark.asyncio
async def test_tipos_notificacion_validos(db_session, seed_catalogos):
    """9 tipos validos segun US-3.x: ASIGNACION_TAREA, REASIGNACION, etc."""
    eto = seed_catalogos["eto"]
    tipos = [
        "ASIGNACION_TAREA", "REASIGNACION", "VENCIMIENTO",
        "DEVOLUCION", "CORRECCION", "PUBLICACION",
        "CONTROL_LECTURA", "EVALUACION", "SISTEMA",
    ]
    for tipo in tipos:
        db_session.add(Notificacion(
            usuario_destino_id=eto.id,
            titulo=f"Test {tipo}",
            mensaje=f"Mensaje {tipo}",
            tipo_notificacion=tipo,
        ))
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(Notificacion.id))
        .where(Notificacion.usuario_destino_id == eto.id)
    )
    assert result.scalar_one() == 9


@pytest.mark.asyncio
async def test_check_tipo_valido_definido():
    """CHECK ck_notif_tipo_valido: el modelo declara la constraint con los 9 tipos."""
    table_args = Notificacion.__table_args__
    found = any(
        getattr(c, "name", None) == "ck_notif_tipo_valido" and
        "ASIGNACION_TAREA" in c.sqltext.text and
        "PUBLICACION" in c.sqltext.text and
        "SISTEMA" in c.sqltext.text
        for c in table_args if hasattr(c, "sqltext")
    )
    assert found, "CHECK constraint ck_notif_tipo_valido debe estar definido con los 9 tipos"


@pytest.mark.asyncio
async def test_marcar_leida(db_session, seed_catalogos):
    """Flujo de lectura: marcar como leida + fecha_lectura + leida_en."""
    from datetime import datetime
    eto = seed_catalogos["eto"]
    n = Notificacion(
        usuario_destino_id=eto.id,
        titulo="Test", mensaje="Mensaje", tipo_notificacion="SISTEMA",
    )
    db_session.add(n)
    await db_session.commit()
    await db_session.refresh(n)

    # Marcar leida
    n.leida = True
    n.fecha_lectura = datetime.now()
    n.leida_en = "127.0.0.1"
    await db_session.commit()
    await db_session.refresh(n)

    assert n.leida is True
    assert n.fecha_lectura is not None
    assert n.leida_en == "127.0.0.1"


@pytest.mark.asyncio
async def test_indice_no_leidas(db_session, seed_catalogos):
    """Indice ix_notif_usuario_no_leidas: badge campana WHERE leida=FALSE."""
    eto = seed_catalogos["eto"]
    for i in range(3):
        db_session.add(Notificacion(
            usuario_destino_id=eto.id, titulo=f"T{i}", mensaje="x",
            tipo_notificacion="SISTEMA", leida=(i == 0),  # 1 leida, 2 no
        ))
    await db_session.commit()

    result = await db_session.execute(
        select(func.count(Notificacion.id))
        .where(Notificacion.usuario_destino_id == eto.id)
        .where(Notificacion.leida == False)
    )
    assert result.scalar_one() == 2


@pytest.mark.asyncio
async def test_fk_usuario_destino_invalido(db_session):
    """FK usuario_destino_id: usuario inexistente => IntegrityError."""
    n = Notificacion(
        usuario_destino_id=999999,
        titulo="Test", mensaje="x", tipo_notificacion="SISTEMA",
    )
    db_session.add(n)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_repr(db_session, seed_catalogos):
    eto = seed_catalogos["eto"]
    n = Notificacion(
        usuario_destino_id=eto.id,
        titulo="T", mensaje="M", tipo_notificacion="SISTEMA",
    )
    db_session.add(n)
    await db_session.commit()
    await db_session.refresh(n)
    r = repr(n)
    assert "Notificacion" in r
    assert "SISTEMA" in r
