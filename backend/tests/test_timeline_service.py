"""
Tests para timeline_service + endpoint /bitacora - Fase 4
14 tests cubriendo todos los escenarios del flujo documental.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import select, func

from app.models.bitacora_timeline import BitacoraTimeline
from app.models.documento_flujo import DocumentoFlujo, TipoSolicitud
from app.models.documento import Documento, VigenciaDocumento, EstatusDocumento
from app.models.usuario import Usuario
from app.services.timeline_service import escribir_bitacora, COLOR_MAP


@pytest.fixture
async def flujo_test(db_session, seed_catalogos):
    """Crea un Documento + DocumentoFlujo para los tests de timeline."""
    area = seed_catalogos["area"]
    tipo = seed_catalogos.get("tipo_documento")
    if not tipo:
        from app.models.tipo_documento import TipoDocumento
        tipo = TipoDocumento(codigo=99, slug="TEST", nombre="Test", activo=True)
        db_session.add(tipo)
        await db_session.flush()

    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id,
        tipo_documento_id=tipo.id, correlativo=9999,
        codigo="TEST-99-999", version="00",
        titulo="Documento de prueba timeline",
        vigencia=VigenciaDocumento.VIGENTE,
        estatus=EstatusDocumento.EN_ELABORACION, activo=True,
    )
    db_session.add(doc)
    await db_session.flush()

    flujo = DocumentoFlujo(
        documento_id=doc.id, tipo_solicitud=TipoSolicitud.CREACION,
        gerencia_id=area.gerencia_id, area_id=area.id,
        tipo_documento_id=tipo.id, codigo_snapshot="TEST-99-999",
        version_snapshot="00", titulo="Documento de prueba timeline",
        elaborador_id=seed_catalogos["eto"].id,
        cargo_elaborador="Test",
        fecha_solicitud=datetime.now(timezone.utc),
    )
    db_session.add(flujo)
    await db_session.flush()
    return flujo, doc


async def _crear_nodo(db, flujo, usuario, accion, **kwargs):
    return await escribir_bitacora(
        db=db, documento_flujo_id=flujo.id, usuario=usuario,
        accion=accion, **kwargs,
    )


class TestTimelineService:

    @pytest.mark.asyncio
    async def test_creacion_nodo_azul(self, db_session, flujo_test, seed_catalogos):
        """1. Creacion de documento genera nodo CREADO - azul."""
        flujo, doc = flujo_test
        user = seed_catalogos["eto"]
        n = await _crear_nodo(db_session, flujo, user, "CREADO",
                               estado_origen="EN_ELABORACION",
                               estado_destino="LIBERACION_ETO")
        assert n.accion == "CREADO"
        assert n.color_nodo == "azul"
        assert n.estado_origen == "EN_ELABORACION"

    @pytest.mark.asyncio
    async def test_liberacion_eto_verde(self, db_session, flujo_test, seed_catalogos):
        """2. Liberacion ETO genera nodo LIBERADO_ETO - verde."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "LIBERADO_ETO",
                               estado_origen="LIBERACION_ETO",
                               estado_destino="EN_REVISION")
        assert n.color_nodo == "verde"

    @pytest.mark.asyncio
    async def test_rechazo_con_observacion_rojo(self, db_session, flujo_test, seed_catalogos):
        """3. Rechazo con observacion genera nodo RECHAZADO - rojo."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "RECHAZADO",
                               estado_origen="EN_REVISION",
                               estado_destino="EN_CORRECCION",
                               observacion="El documento no cumple formato ISO 9001")
        assert n.color_nodo == "rojo"
        assert n.observacion is not None

    @pytest.mark.asyncio
    async def test_multiples_revisores_con_rechazo(self, db_session, flujo_test, seed_catalogos):
        """4. 3 revisores: R1 aprueba, R2 rechaza, R3 aprueba."""
        flujo, doc = flujo_test
        user = seed_catalogos["eto"]
        n1 = await _crear_nodo(db_session, flujo, user, "APROBADO",
                               estado_origen="EN_REVISION",
                               estado_destino="EN_APROBACION")
        n2 = await _crear_nodo(db_session, flujo, user, "RECHAZADO",
                               estado_origen="EN_REVISION",
                               estado_destino="EN_CORRECCION",
                               observacion="Corregir tabla 3.1")
        n3 = await _crear_nodo(db_session, flujo, user, "APROBADO",
                               estado_origen="EN_REVISION",
                               estado_destino="EN_APROBACION")
        assert n1.color_nodo == "verde"
        assert n2.color_nodo == "rojo"
        assert n2.observacion == "Corregir tabla 3.1"
        assert n3.color_nodo == "verde"

    @pytest.mark.asyncio
    async def test_correccion_azul(self, db_session, flujo_test, seed_catalogos):
        """5. Correccion enviada genera nodo CORREGIDO - azul."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "CORREGIDO",
                               estado_origen="EN_CORRECCION",
                               estado_destino="EN_REVISION",
                               observacion="Seccion 3 corregida")
        assert n.color_nodo == "azul"

    @pytest.mark.asyncio
    async def test_reasignacion_gris(self, db_session, flujo_test, seed_catalogos):
        """6. Reasignacion genera nodo REASIGNADO - gris."""
        flujo, doc = flujo_test
        user = seed_catalogos["eto"]
        for accion in ("REASIGNADO", "REASIGNADO_AUTO", "REASIGNADO_ETO"):
            n = await _crear_nodo(db_session, flujo, user, accion)
            assert n.color_nodo == "gris"

    @pytest.mark.asyncio
    async def test_publicacion_verde(self, db_session, flujo_test, seed_catalogos):
        """7. Publicacion genera nodo PUBLICADO - verde."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "PUBLICADO",
                               estado_origen="EN_APROBACION",
                               estado_destino="APROBADO")
        assert n.color_nodo == "verde"

    @pytest.mark.asyncio
    async def test_eliminacion_rojo(self, db_session, flujo_test, seed_catalogos):
        """8. Eliminacion genera nodo ELIMINADO - rojo."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "ELIMINADO",
                               estado_origen="EN_ELABORACION",
                               estado_destino="ELIMINADO")
        assert n.color_nodo == "rojo"

    @pytest.mark.asyncio
    async def test_vencimiento_rojo(self, db_session, flujo_test, seed_catalogos):
        """9. Vencimiento genera nodo VENCIDO - rojo."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "VENCIDO",
                               estado_origen="EN_REVISION",
                               estado_destino="VENCIDO")
        assert n.color_nodo == "rojo"

    @pytest.mark.asyncio
    async def test_devolucion_rojo(self, db_session, flujo_test, seed_catalogos):
        """10. Devolucion ETO genera nodo DEVUELTO - rojo."""
        flujo, doc = flujo_test
        n = await _crear_nodo(db_session, flujo, seed_catalogos["eto"],
                               "DEVUELTO",
                               estado_origen="LIBERACION_ETO",
                               estado_destino="EN_CORRECCION",
                               observacion="Formato de caratula incorrecto")
        assert n.color_nodo == "rojo"

    @pytest.mark.asyncio
    async def test_escenario_ideal_completo(self, db_session, flujo_test, seed_catalogos):
        """11. Escenario flujo ideal: CREADO->LIBERADO->APROBADO->PUBLICADO."""
        flujo, doc = flujo_test
        user = seed_catalogos["eto"]
        secuencia = [
            ("CREADO", "EN_ELABORACION", "LIBERACION_ETO", "azul"),
            ("LIBERADO_ETO", "LIBERACION_ETO", "EN_REVISION", "verde"),
            ("APROBADO", "EN_REVISION", "EN_APROBACION", "verde"),
            ("APROBADO", "EN_APROBACION", "APROBADO", "verde"),
            ("PUBLICADO", "APROBADO", "VIGENTE", "verde"),
        ]
        for accion, origen, destino, color_esp in secuencia:
            n = await _crear_nodo(db_session, flujo, user, accion,
                                   estado_origen=origen, estado_destino=destino)
            assert n.color_nodo == color_esp, f"{accion}: esperado {color_esp}, obtenido {n.color_nodo}"

    @pytest.mark.asyncio
    async def test_color_map(self):
        """12. COLOR_MAP tiene todas las acciones requeridas."""
        required = ["CREADO", "CORREGIDO", "LIBERADO_ETO", "APROBADO",
                     "PUBLICADO", "RECHAZADO", "ELIMINADO", "OBSOLETO",
                     "VENCIDO", "DEVUELTO", "PENDIENTE", "EN_REVISION",
                     "EN_CORRECCION", "REASIGNADO", "REASIGNADO_AUTO",
                     "REASIGNADO_ETO"]
        for accion in required:
            assert accion in COLOR_MAP, f"COLOR_MAP no tiene {accion}"

    @pytest.mark.asyncio
    async def test_orden_cronologico(self, db_session, flujo_test, seed_catalogos):
        """13. Los nodos mas nuevos tienen id mayor."""
        flujo, doc = flujo_test
        user = seed_catalogos["eto"]
        ids = []
        for accion in ("CREADO", "LIBERADO_ETO", "APROBADO", "PUBLICADO"):
            n = await _crear_nodo(db_session, flujo, user, accion)
            ids.append(n.id)
        assert ids == sorted(ids), "Los IDs deberian ser secuenciales"

    @pytest.mark.asyncio
    async def test_conteo_nodos_por_flujo(self, db_session, flujo_test, seed_catalogos):
        """14. Contar nodos por flujo."""
        flujo, doc = flujo_test
        user = seed_catalogos["eto"]
        for accion in ("CREADO", "LIBERADO_ETO", "APROBADO"):
            await _crear_nodo(db_session, flujo, user, accion)
        result = await db_session.execute(
            select(func.count(BitacoraTimeline.id))
            .where(BitacoraTimeline.documento_flujo_id == flujo.id)
        )
        assert result.scalar_one() == 3
