import os
from pathlib import Path
from zipfile import ZipFile

base = '/app/storage/documentos/CAL/CC/PRO-5-4001/V00'
Path(base).mkdir(parents=True, exist_ok=True)

docx_path = os.path.join(base, 'PRO-5-4001 PROCEDIMIENTO DE CONTROL DE CALIDAD V00.docx')
with ZipFile(docx_path, 'w') as z:
    z.writestr('word/document.xml', '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>PROCEDIMIENTO DE CONTROL DE CALIDAD - V00</w:t></w:r></w:p></w:body></w:document>')
    z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/></Types>')
    z.writestr('word/_rels/document.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')

xlsx_path = os.path.join(base, 'PRO-5-4001-F01 REGISTRO DE CONTROL DE CALIDAD V00.xlsx')
with ZipFile(xlsx_path, 'w') as z:
    z.writestr('xl/workbook.xml', '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Datos" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets></workbook>')
    z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
    z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
    z.writestr('xl/worksheets/sheet1.xml', '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Control CALIDAD - PRO-5-4001</t></is></c></row></sheetData></worksheet>')

print(f'Creado: {docx_path}')
print(f'Creado: {xlsx_path}')
