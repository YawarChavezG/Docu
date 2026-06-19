"""
Helpers para tests: crea un .docx en memoria con la caratula especificada.
Usado por tests del servicio de validacion de caratula (R3 item 0.3).
"""
from io import BytesIO

from docx import Document
from docx.shared import Pt


def crear_docx_caratula(
    codigo: str = "CC-3-005",
    titulo: str = "PROCEDIMIENTO DE MUESTREO",
    version: str = "00",
) -> bytes:
    """
    Crea un .docx en memoria con una caratula simple (3 lineas: codigo,
    titulo, version). Usado para tests del servicio de validacion.
    """
    doc = Document()
    p1 = doc.add_paragraph(codigo)
    p1.runs[0].font.size = Pt(14)
    p1.runs[0].bold = True
    p2 = doc.add_paragraph(titulo)
    p2.runs[0].font.size = Pt(18)
    p2.runs[0].bold = True
    p3 = doc.add_paragraph(f"V{version}")
    p3.runs[0].font.size = Pt(12)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def crear_docx_sin_caratula(texto_libre: str = "lorem ipsum dolor sit amet") -> bytes:
    """Crea un .docx sin codigo/titulo/version reconocibles."""
    doc = Document()
    doc.add_paragraph(texto_libre)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
