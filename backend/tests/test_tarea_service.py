"""
Tests para tarea_service + endpoints de tareas (Fase 5 - R3 Fase 2).
Cubre: creacion, completado, rechazo, reasignacion, propagacion, notificaciones.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import select, func

from app.models.tarea import Tarea
from app.models.tarea_observacion import TareaObservacion
from app.models.notificacion import Notificacion
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.documento import Documento, VigenciaDocumento, EstatusDocumento
from app.services.tarea_service import crear_tarea, completar_tarea, rechazar_tarea
from app.services.notificacion_service import crear_notificacion, contar_no_leidas, marcar_leida


@pytest.fixture
async def flujo_test(db_session, seed_catalogos):
    """Crea un Documento + DocumentoFlujo para los tests."""
    area = seed_catalogos["area"]
    tipo = seed_catalogos.get("tipo_documento")
    if not tipo:
        from app.models.tipo_documento import TipoDocumento
        tipo = TipoDocumento(codigo=99, slug="TEST", nombre="Test", activo=True)
        db_session.add(tipo)
        await db_session.flush()

    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id,
        tipo_documento_id=tipo.id, correlativo=8888,
        codigo="TEST-88-888", version="00",
        titulo="Documento test tarea service",
        vigencia=VigenciaDocumento.VIGENTE,
        estatus=EstatusDocumento.LIBERACION_ETO, activo=True,
    )
    db_session.add(doc)
    await db_session.flush()

    flujo = DocumentoFlujo(
        documento_id=doc.id, tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id,
        tipo_documento_id=tipo.id, codigo_snapshot="TEST-88-888",
        version_snapshot="00", titulo="Documento test",
        elaborador_id=seed_catalogos["eto"].id,
        cargo_elaborador="Test",
        fecha_solicitud=datetime.now(timezone.utc),
        revisor_ids=[seed_catalogos["eto"].id],
        aprobador_ids=[seed_catalogos["admin"].id],
    )
    db_session.add(flujo)
    await db_session.flush()
    return flujo, doc


class TestTareaService:

    @pytest.mark.asyncio
    async def test_crear_tarea_pendiente(self, db_session, flujo_test, seed_catalogos):
        """Crear tarea basica con estado PENDIENTE."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        assert t.id is not None
        assert t.estado == "PENDIENTE"
        assert t.tipo_tarea == "REVISION"

    @pytest.mark.asyncio
    async def test_completar_tarea_ok(self, db_session, flujo_test, seed_catalogos, monkeypatch):
        """Completar tarea cambia estado a COMPLETADO."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        await db_session.flush()

        async def mock_validar(db, user, pwd): return True
        monkeypatch.setattr("app.services.tarea_service._validar_password", mock_validar)
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test"}

        t_final, accion = await completar_tarea(
            db_session, mock_request, seed_catalogos["eto"], t.id, "testpass"
        )
        assert t_final.estado == "COMPLETADO"
        assert t_final.fecha_completado is not None

    @pytest.mark.asyncio
    async def test_rechazar_tarea_con_observacion(self, db_session, flujo_test, seed_catalogos, monkeypatch):
        """Rechazar tarea crea TareaObservacion y cambia estado."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        await db_session.flush()

        async def mock_validar(db, user, pwd): return True
        monkeypatch.setattr("app.services.tarea_service._validar_password", mock_validar)
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test"}

        obs = "El documento no cumple con el formato ISO 9001 en la seccion 3.2"
        t_final, accion = await rechazar_tarea(
            db_session, mock_request, seed_catalogos["eto"], t.id, obs, "testpass"
        )
        assert t_final.estado == "RECHAZADO"
        assert t_final.observacion == obs

        obs_count = (await db_session.execute(
            select(func.count(TareaObservacion.id))
            .where(TareaObservacion.tarea_id == t.id)
        )).scalar_one()
        assert obs_count == 1

    @pytest.mark.asyncio
    async def test_crear_notificacion(self, db_session, seed_catalogos):
        """Crear notificacion basica."""
        n = await crear_notificacion(
            db_session,
            usuario_destino_id=seed_catalogos["eto"].id,
            titulo="Nueva tarea asignada",
            mensaje="Tiene una nueva tarea de revision pendiente",
            tipo_notificacion="ASIGNACION_TAREA",
        )
        assert n.id is not None
        assert n.leida is False

    @pytest.mark.asyncio
    async def test_contar_no_leidas(self, db_session, seed_catalogos):
        """Contar notificaciones no leidas."""
        for i in range(3):
            await crear_notificacion(
                db_session,
                usuario_destino_id=seed_catalogos["eto"].id,
                titulo=f"Notif {i}", mensaje=f"Mensaje {i}",
                tipo_notificacion="SISTEMA",
            )
        count = await contar_no_leidas(db_session, seed_catalogos["eto"].id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_marcar_leida(self, db_session, seed_catalogos):
        """Marcar notificacion como leida."""
        n = await crear_notificacion(
            db_session,
            usuario_destino_id=seed_catalogos["eto"].id,
            titulo="Test", mensaje="Test msg",
            tipo_notificacion="SISTEMA",
        )
        await db_session.flush()
        nid = n.id

        await marcar_leida(db_session, nid, "127.0.0.1")
        await db_session.flush()

        from app.models.notificacion import Notificacion
        n2 = await db_session.get(Notificacion, nid)
        assert n2.leida is True
        assert n2.fecha_lectura is not None

    @pytest.mark.asyncio
    async def test_crear_tarea_rechazo_valida_observacion(self, db_session, flujo_test, seed_catalogos):
        """EL servicio rechazar_tarea valida observacion >= 10 caracteres."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        await db_session.flush()

        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as excinfo:
            await rechazar_tarea(
                db_session, mock_request, seed_catalogos["eto"],
                t.id, "corto", "testpass"
            )
        assert excinfo.value.status_code == 422

    @pytest.mark.asyncio
    async def test_doble_completar_rechazado(self, db_session, flujo_test, seed_catalogos, monkeypatch):
        """Completar tarea ya completada da error 409."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        await db_session.flush()

        async def mock_validar(db, user, pwd): return True
        monkeypatch.setattr("app.services.tarea_service._validar_password", mock_validar)
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test"}

        await completar_tarea(db_session, mock_request, seed_catalogos["eto"], t.id, "pass")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as excinfo:
            await completar_tarea(db_session, mock_request, seed_catalogos["eto"], t.id, "pass")
        assert excinfo.value.status_code == 409

    @pytest.mark.asyncio
    async def test_completar_tarea_otro_usuario_403(self, db_session, flujo_test, seed_catalogos, monkeypatch):
        """Completar tarea de otro usuario da 403."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        await db_session.flush()

        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        from fastapi import HTTPException
        otro_user = seed_catalogos["admin"]
        with pytest.raises(HTTPException) as excinfo:
            await completar_tarea(db_session, mock_request, otro_user, t.id, "pass")
        assert excinfo.value.status_code == 403

    @pytest.mark.asyncio
    async def test_reasignar_tarea_ok(self, db_session, flujo_test, seed_catalogos):
        """Reasignar tarea marca original REASIGNADA y crea nueva."""
        flujo, doc = flujo_test
        t = await crear_tarea(db_session, documento_flujo_id=flujo.id,
                              usuario_id=seed_catalogos["eto"].id,
                              tipo_tarea="REVISION")
        await db_session.flush()

        from app.services.tarea_service import reasignar_tarea
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"user-agent": "test"}

        nuevo_user = seed_catalogos["admin"]
        nueva = await reasignar_tarea(
            db_session, mock_request, seed_catalogos["eto"],
            t.id, nuevo_user.id, "Delegado asignado por vacaciones"
        )
        await db_session.flush()

        assert t.estado == "REASIGNADO"
        assert nueva.id != t.id
        assert nueva.usuario_id == nuevo_user.id
        assert nueva.estado == "PENDIENTE"
        assert nueva.delegado_origen_id == seed_catalogos["eto"].id

    @pytest.mark.asyncio
    async def test_notificacion_tipo_invalido(self, db_session):
        """Tipo de notificacion invalido lanza ValueError."""
        from app.services.notificacion_service import crear_notificacion
        with pytest.raises(ValueError) as excinfo:
            await crear_notificacion(
                db_session,
                usuario_destino_id=1,
                titulo="Test",
                mensaje="Test",
                tipo_notificacion="INVALIDO",
            )
        assert "invalido" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_listar_notificaciones_paginado(self, db_session, seed_catalogos):
        """Listar notificaciones con paginacion."""
        from app.services.notificacion_service import listar_notificaciones
        for i in range(5):
            from app.services.notificacion_service import crear_notificacion
            await crear_notificacion(
                db_session,
                usuario_destino_id=seed_catalogos["eto"].id,
                titulo=f"N{i}", mensaje=f"M{i}",
                tipo_notificacion="SISTEMA",
            )

        rows, total = await listar_notificaciones(
            db_session, seed_catalogos["eto"].id,
            limit=3, offset=0,
        )
        assert total == 5
        assert len(rows) == 3
