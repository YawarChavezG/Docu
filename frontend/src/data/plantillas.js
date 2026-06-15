/**
 * src/data/plantillas.js
 * Extraído de PLANTILLAS_DOC_DB del HTML original
 */

export const plantillasDocDB = [
  { id: 1, tipo: 'word',  nombre: 'Plantilla de Procedimientos (SOP)',       descripcion: 'Para SOPs bajo norma ISO con estructura BPM-2024. Incluye secciones de control de cambios y firmas digitales.',   version: 'v3', ultimaActualizacion: '15/01/2026', estado: 'Activa'   },
  { id: 2, tipo: 'word',  nombre: 'Plantilla de Instructivos Técnicos',       descripcion: 'Formato estándar para instructivos paso a paso. Compatible con flujo de aprobación de 2 etapas.',              version: 'v2', ultimaActualizacion: '10/12/2025', estado: 'Activa'   },
  { id: 3, tipo: 'excel', nombre: 'Formulario de Registro General',           descripcion: 'Registro de datos operativos con campos validados. Incluye macros para cálculo automático de indicadores.',      version: 'v4', ultimaActualizacion: '20/01/2026', estado: 'Activa'   },
  { id: 4, tipo: 'word',  nombre: 'Plantilla de Metodología de Análisis',     descripcion: 'Metodologías de calidad y validación. Estructura conforme a ISO/IEC 17025 y guías GMP vigentes.',              version: 'v2', ultimaActualizacion: '05/11/2025', estado: 'Activa'   },
  { id: 5, tipo: 'excel', nombre: 'Matriz de Evaluación de Riesgos',          descripcion: 'Análisis de riesgos por área con matriz de probabilidad/impacto. Incluye plan de mitigación preconfigurado.',  version: 'v1', ultimaActualizacion: '01/09/2025', estado: 'Activa'   },
  { id: 6, tipo: 'word',  nombre: 'Plantilla de Manual de Funciones',         descripcion: 'Descripción de puestos y cargos con competencias requeridas. Actualmente en revisión para actualización.',      version: 'v1', ultimaActualizacion: '15/08/2024', estado: 'Inactiva' },
  { id: 7, tipo: 'word',  nombre: 'Protocolo de Validación de Equipos',       descripcion: 'Para calificación IQ/OQ/PQ según requerimientos regulatorios BPF. Incluye anexos de pruebas estandarizadas.',   version: 'v2', ultimaActualizacion: '18/02/2026', estado: 'Activa'   },
  { id: 8, tipo: 'excel', nombre: 'Reporte de Desviación de Proceso',         descripcion: 'Registro y seguimiento de desviaciones con clasificación de criticidad y acciones correctivas/preventivas.',    version: 'v3', ultimaActualizacion: '22/03/2026', estado: 'Activa'   },
  { id: 9, tipo: 'ppt',   nombre: 'Presentación de Resultados BPM',           descripcion: 'Slides para reuniones de revisión BPM. Diseño corporativo COFAR con gráficas de indicadores de desempeño.',     version: 'v1', ultimaActualizacion: '10/04/2026', estado: 'Activa'   },
]

export function tipoIcono(tipo) {
  if (tipo === 'excel') return '📊'
  if (tipo === 'ppt')   return '📑'
  return '📄'
}

export function tipoLabel(tipo) {
  if (tipo === 'excel') return '.xlsx'
  if (tipo === 'ppt')   return '.pptx'
  return '.docx'
}

export function tipoColor(tipo) {
  if (tipo === 'excel') return '#3b6d11'
  if (tipo === 'ppt')   return '#c0392b'
  return '#185fa5'
}
