"""
Tests unitarios de correlativo_service.py y formatear_codigo.
No requieren BD: son tests de funciones puras + logica async con session mock.
"""
import pytest

from app.services.correlativo_service import (
    formatear_codigo,
    formatear_codigo_completo,
    siguiente_correlativo_advisory,
)


# ════════════════════════════════════════════════════════════════
#  formatear_codigo (funcion pura)
# ════════════════════════════════════════════════════════════════

def test_formatear_codigo_basico():
    assert formatear_codigo("CC", 3, 5) == "CC-3-005"


def test_formatear_codigo_cero_pad():
    """Correlativo < 10 debe tener 3 digitos con zero-pad."""
    assert formatear_codigo("CC", 3, 1) == "CC-3-001"
    assert formatear_codigo("CC", 3, 9) == "CC-3-009"


def test_formatear_codigo_tres_digitos_o_mas():
    """Correlativo >= 10 NO debe tener padding adicional (3 digitos es el minimo)."""
    assert formatear_codigo("CC", 3, 10) == "CC-3-010"
    assert formatear_codigo("CC", 3, 999) == "CC-3-999"
    assert formatear_codigo("PRO", 7, 1234) == "PRO-7-1234"


def test_formatear_codigo_sigla_larga():
    """Sigla de hasta 10 chars (limite del modelo areas.sigla)."""
    assert formatear_codigo("PROM29402", 5, 1) == "PROM29402-5-001"


# ════════════════════════════════════════════════════════════════
#  formatear_codigo_completo (funcion pura)
# ════════════════════════════════════════════════════════════════

def test_formatear_codigo_completo_v00():
    assert formatear_codigo_completo("CC-3-005", "00") == "CC-3-005/00"


def test_formatear_codigo_completo_v99():
    assert formatear_codigo_completo("PRO-7-001", "99") == "PRO-7-001/99"


def test_formatear_codigo_completo_con_guion():
    """Codigos con guiones tambien funcionan."""
    assert formatear_codigo_completo("PROM29402-5-001", "01") == "PROM29402-5-001/01"


# ════════════════════════════════════════════════════════════════
#  siguiente_correlativo_advisory (requiere session async)
# ════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_siguiente_correlativo_sin_docs(db_session):
    """Sin documentos previos: correlativo = 1."""
    from sqlalchemy import select, func
    from app.models.documento import Documento

    # Crear area y tipo primero
    from app.models.area import Area
    from app.models.gerencia import Gerencia
    from app.models.tipo_documento import TipoDocumento

    ger = Gerencia(sigla="TEST", nombre="TEST", activo=True)
    db_session.add(ger)
    await db_session.flush()
    area = Area(gerencia_id=ger.id, sigla="TST", nombre="TEST", activo=True)
    db_session.add(area)
    await db_session.flush()
    tipo = TipoDocumento(
        codigo=99, slug="TST99", nombre="Test",
        periodo_vigencia=4, indefinido=False, activo=True,
    )
    db_session.add(tipo)
    await db_session.flush()

    correlativo = await siguiente_correlativo_advisory(db_session, area.id, tipo.id)
    assert correlativo == 1


@pytest.mark.asyncio
async def test_siguiente_correlativo_con_doc_existente(db_session):
    """Con 1 doc existente: correlativo = 2."""
    from app.models.area import Area
    from app.models.gerencia import Gerencia
    from app.models.tipo_documento import TipoDocumento
    from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento
    from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion

    # Setup
    ger = Gerencia(sigla="TEST2", nombre="TEST2", activo=True)
    db_session.add(ger)
    await db_session.flush()
    area = Area(gerencia_id=ger.id, sigla="TS2", nombre="TS2", activo=True)
    db_session.add(area)
    await db_session.flush()
    tipo = TipoDocumento(
        codigo=100, slug="TST100", nombre="Test100",
        periodo_vigencia=4, indefinido=False, activo=True,
    )
    db_session.add(tipo)
    await db_session.flush()
    usr = Usuario(
        username="tst_corr", email="tst_corr@test", nombre_completo="TST", iniciales="T",
        cargo="TST", area_id=area.id, estado=EstadoUsuario.ACTIVO,
        estado_delegacion=EstadoDelegacion.NA, ad_postal_code="99999999",
    )
    db_session.add(usr)
    await db_session.flush()

    # Insertar doc con correlativo=1
    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=1, codigo="TS2-100-001", version="00", titulo="X",
        estatus=EstatusDocumento.EN_ELABORACION, vigencia=VigenciaDocumento.VIGENTE,
        activo=True, created_by_id=usr.id, updated_by_id=usr.id,
    )
    db_session.add(doc)
    await db_session.commit()

    correlativo = await siguiente_correlativo_advisory(db_session, area.id, tipo.id)
    assert correlativo == 2


@pytest.mark.asyncio
async def test_siguiente_correlativo_skip_inactivos(db_session):
    """Documentos con activo=False NO cuentan para el correlativo."""
    from app.models.area import Area
    from app.models.gerencia import Gerencia
    from app.models.tipo_documento import TipoDocumento
    from app.models.documento import Documento, EstatusDocumento, VigenciaDocumento
    from app.models.usuario import Usuario, EstadoUsuario, EstadoDelegacion

    ger = Gerencia(sigla="TEST3", nombre="TEST3", activo=True)
    db_session.add(ger)
    await db_session.flush()
    area = Area(gerencia_id=ger.id, sigla="TS3", nombre="TS3", activo=True)
    db_session.add(area)
    await db_session.flush()
    tipo = TipoDocumento(
        codigo=101, slug="TST101", nombre="Test101",
        periodo_vigencia=4, indefinido=False, activo=True,
    )
    db_session.add(tipo)
    await db_session.flush()
    usr = Usuario(
        username="tst_corr2", email="tst_corr2@test", nombre_completo="TST", iniciales="T",
        cargo="TST", area_id=area.id, estado=EstadoUsuario.ACTIVO,
        estado_delegacion=EstadoDelegacion.NA, ad_postal_code="99999998",
    )
    db_session.add(usr)
    await db_session.flush()

    # Insertar doc con correlativo=5 pero activo=False
    doc = Documento(
        gerencia_id=area.gerencia_id, area_id=area.id, tipo_documento_id=tipo.id,
        correlativo=5, codigo="TS3-101-005", version="00", titulo="X",
        estatus=EstatusDocumento.EN_ELABORACION, vigencia=VigenciaDocumento.VIGENTE,
        activo=False, created_by_id=usr.id, updated_by_id=usr.id,
    )
    db_session.add(doc)
    await db_session.commit()

    # El correlativo sugerido es 1 (porque el unico doc esta inactivo)
    correlativo = await siguiente_correlativo_advisory(db_session, area.id, tipo.id)
    assert correlativo == 1
