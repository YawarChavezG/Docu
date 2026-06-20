"""
Tests para el servicio de validacion de caratula (R3 item 0.3).
Sesion 36 R3 - FASE 0.
"""
from app.services.caratula_service import (
    extraer_caratula,
    validar_caratula,
)

from tests.docx_helpers import (
    crear_docx_caratula,
    crear_docx_sin_caratula,
)


def test_extraer_caratula_campos_correctos():
    """Crea un .docx con codigo+titulo+version, los extrae correctamente."""
    docx = crear_docx_caratula(
        codigo="CC-3-005",
        titulo="PROCEDIMIENTO DE MUESTREO",
        version="00",
    )
    caratula = extraer_caratula(docx)
    assert caratula.exitoso is True
    assert caratula.codigo == "CC-3-005"
    assert caratula.version == "00"
    assert "PROCEDIMIENTO" in (caratula.titulo or "").upper()


def test_validar_caratula_coincide():
    """Si codigo/titulo/version coinciden, no hay warnings."""
    docx = crear_docx_caratula(
        codigo="CC-3-005",
        titulo="PROCEDIMIENTO DE MUESTREO",
        version="00",
    )
    resultado = validar_caratula(
        docx, codigo_esperado="CC-3-005",
        version_esperada="00", titulo_esperado="PROCEDIMIENTO DE MUESTREO",
    )
    assert resultado.coincide is True
    assert resultado.warnings == []


def test_validar_caratula_codigo_distinto_warning():
    """Codigo distinto: warning pero NO bloqueante."""
    docx = crear_docx_caratula(
        codigo="CC-3-005",
        titulo="PROCEDIMIENTO DE MUESTREO",
        version="00",
    )
    resultado = validar_caratula(
        docx, codigo_esperado="CC-3-099",
        version_esperada="00", titulo_esperado="PROCEDIMIENTO DE MUESTREO",
    )
    assert resultado.coincide is False
    assert len(resultado.warnings) == 1
    assert "CC-3-005" in resultado.warnings[0]
    assert "CC-3-099" in resultado.warnings[0]


def test_validar_caratula_version_distinta_warning():
    """Version distinta: warning."""
    docx = crear_docx_caratula(
        codigo="CC-3-005",
        titulo="PROCEDIMIENTO DE MUESTREO",
        version="00",
    )
    resultado = validar_caratula(
        docx, codigo_esperado="CC-3-005",
        version_esperada="01", titulo_esperado="PROCEDIMIENTO DE MUESTREO",
    )
    assert resultado.coincide is False
    assert any("version" in w.lower() for w in resultado.warnings)


def test_validar_caratula_sin_campos_no_warning():
    """Si el .docx no tiene codigo/version, no se puede validar (NO warning)."""
    docx = crear_docx_sin_caratula(texto_libre="este es un documento sin codigo")
    resultado = validar_caratula(
        docx, codigo_esperado="CC-3-005",
        version_esperada="00", titulo_esperado="Cualquier titulo",
    )
    # No se puede validar -> no warning (no se penaliza al usuario)
    assert resultado.coincide is True
    assert resultado.warnings == []


def test_validar_caratula_bytes_invalidos_no_warning():
    """Bytes que no son un .docx valido: no warning, exitoso=False."""
    resultado = validar_caratula(
        b"esto no es un docx valido jajaja",
        codigo_esperado="CC-3-005",
        version_esperada="00",
        titulo_esperado="X",
    )
    assert resultado.coincide is True
    assert resultado.warnings == []
    assert resultado.caratula.exitoso is False


# ════════════════════════════════════════════════════════════════
#  Tests de extraccion desde HEADER del .docx (coverage gap)
# ════════════════════════════════════════════════════════════════


def test_extraer_caratula_desde_header():
    """Codigo y version en el header del .docx se extraen correctamente."""
    from tests.docx_helpers import crear_docx_con_header
    docx = crear_docx_con_header(
        header_text="CC-3-005  PROCEDIMIENTO DE MUESTREO  V00",
        body_text="Cuerpo del documento sin codigo",
    )
    caratula = extraer_caratula(docx)
    assert caratula.exitoso is True
    assert caratula.codigo == "CC-3-005"
    assert caratula.version == "00"


def test_extraer_caratula_version_con_acento():
    """'Versión' con acento agudo se reconoce como version."""
    from tests.docx_helpers import crear_docx_con_header
    docx = crear_docx_con_header(
        header_text="CC-3-005  PROCEDIMIENTO  Versión: 03",
    )
    caratula = extraer_caratula(docx)
    assert caratula.exitoso is True
    assert caratula.version == "03"


def test_extraer_caratula_version_ver_dot():
    """'VER. 01' se reconoce como version (formato compacto)."""
    from tests.docx_helpers import crear_docx_con_header
    docx = crear_docx_con_header(
        header_text="CC-3-005  PROCEDIMIENTO  VER. 01",
    )
    caratula = extraer_caratula(docx)
    assert caratula.exitoso is True
    assert caratula.version == "01"


def test_extraer_caratula_desde_tabla_en_header():
    """Tabla en el header con codigo y version en celdas separadas."""
    from tests.docx_helpers import crear_docx_con_header_tabla
    docx = crear_docx_con_header_tabla(
        header_cells=[
            "CC-3-005",
            "PROCEDIMIENTO DE MUESTREO",
            "V02",
        ],
        body_text="Contenido del documento",
    )
    caratula = extraer_caratula(docx)
    assert caratula.exitoso is True
    assert caratula.codigo == "CC-3-005"
    assert caratula.version == "02"
