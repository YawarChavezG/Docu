/**
 * src/data/parametrosSistema.js
 * Fuente única de verdad para el módulo de Parametrización General.
 * Cero hardcodeo en vistas — todo debe importarse desde aquí.
 */

/* ═══════════════════════════════════════════════════════════════
   1. RESTRICCIONES Y LÍMITES DEL SISTEMA
   ═══════════════════════════════════════════════════════════════ */
export const ParametrosGlobalesDB = {
  restriccionesArchivo: {
    maxAdjuntos: 5,
    maxSizeMB: 20,
    tiposPermitidos: ['.docx', '.xlsx', '.pdf'],
  },
  limitesDescarga: {
    maxDescargasDia: 3,
    tiposExcluidos: ['Formulario', 'Manual'],
  },
  paginacion: {
    bandejaRegistros: 20,
    opciones: [10, 20, 30, 50],
  },
  politicaEditable: {
    descargasPorDia: 1,
    excepcionesMetodologia: 10,
  },
}

export const exclusionTiposDB = ['Formulario', 'Manual']

export const tiposExcluiblesDB = ['Metodología', 'Instructivo', 'Procedimiento', 'Política']

/* ═══════════════════════════════════════════════════════════════
   2. HISTORIAL / LOGS DE CAMBIOS (semilla inicial)
   ═══════════════════════════════════════════════════════════════ */
export const historialParametrosDB = [
  { fecha: '10/04/2026 09:12', parametro: 'Tiempo de vigencia', anterior: '2 años', nuevo: '3 años', usuario: 'aromero', tab: 'tiempos' },
  { fecha: '05/02/2026 14:30', parametro: 'Plazo máx. revisión', anterior: '10 días', nuevo: '15 días', usuario: 'aromero', tab: 'tiempos' },
  { fecha: '01/01/2026 08:00', parametro: 'Auto-delegación', anterior: '5 días', nuevo: '3 días', usuario: 'aromero', tab: 'tiempos' },
  { fecha: '15/12/2025 16:20', parametro: 'Límite de archivos', anterior: '3', nuevo: '5', usuario: 'aromero', tab: 'restricciones' },
  { fecha: '01/12/2025 08:00', parametro: 'Paginación bandeja', anterior: '10', nuevo: '20', usuario: 'lhdt', tab: 'tiempos' },
]

/* ═══════════════════════════════════════════════════════════════
   3. TIEMPOS Y SLAs
   ═══════════════════════════════════════════════════════════════ */
export const tiemposSLADB = {
  plazoRevision: 10,
  plazoLectura: 30,
  slaVerde: 5,
  slaAmarillo: 3,
}

/** Vigencia por tipo de documento (años) */
export const vigenciaPorDocumentoDB = [
  { tipo: 'Manuales', años: 4 },
  { tipo: 'Procedimientos', años: 3 },
  { tipo: 'Instructivos', años: 2 },
  { tipo: 'Metodologías', años: 3 },
  { tipo: 'Formularios', años: 2 },
  { tipo: 'Políticas', años: 5 },
]

/* ═══════════════════════════════════════════════════════════════
   4. DICCIONARIOS Y ENRUTAMIENTO
   ═══════════════════════════════════════════════════════════════ */
export const tiposDocParamDB = [
  { tipo: 'Procedimiento', cod: 'PRO' },
  { tipo: 'Instructivo', cod: 'INS' },
  { tipo: 'Formulario', cod: 'FOR' },
  { tipo: 'Metodología', cod: 'MET' },
  { tipo: 'Manual', cod: 'MAN' },
  { tipo: 'Política', cod: 'POL' },
]

export const estadosProcesoParamDB = [
  { est: 'Elaboración', ctx: 'Tarea' },
  { est: 'Liberación ETO', ctx: 'Tarea' },
  { est: 'Revisión Paralela', ctx: 'Proceso' },
  { est: 'Finalizado', ctx: 'Proceso' },
  { est: 'Anulado', ctx: 'Proceso' },
]

export const matrizETOParamDB = [
  { gerencia: 'Calidad', analista: 'aromero', disponible: true, delegado: '' },
  { gerencia: 'Producción', analista: 'jmamani', disponible: true, delegado: '' },
  { gerencia: 'Logística', analista: 'cflores', disponible: false, delegado: 'jmamani' },
  { gerencia: 'RRHH', analista: 'aromero', disponible: true, delegado: '' },
  { gerencia: 'Gerencia', analista: 'jmamani', disponible: true, delegado: '' },
]

export const analistasETODB = ['aromero', 'jmamani', 'cflores']

/* ═══════════════════════════════════════════════════════════════
   5. GERENCIAS Y ÁREAS
   ═══════════════════════════════════════════════════════════════ */
export const gerenciasParamDB = [
  { id: 1, nombre: 'Gerencia de Calidad', cod: 'CAL', areas: [{ n: 'Garantía de Calidad', c: 'GAR' }, { n: 'Validaciones', c: 'VAL' }, { n: 'Dirección Técnica', c: 'DTE' }] },
  { id: 2, nombre: 'Gerencia de Producción', cod: 'PRO', areas: [{ n: 'Planta Líquidos', c: 'LIQ' }, { n: 'Planta Sólidos', c: 'SOL' }, { n: 'Empaque', c: 'EMP' }] },
  { id: 3, nombre: 'Gerencia de Logística', cod: 'LOG', areas: [{ n: 'Almacenes', c: 'ALM' }, { n: 'Distribución', c: 'DIS' }] },
  { id: 4, nombre: 'Administración y Finanzas', cod: 'ADM', areas: [{ n: 'Contabilidad', c: 'CON' }, { n: 'Finanzas', c: 'FIN' }, { n: 'Tesorería', c: 'TES' }] },
]

/* ═══════════════════════════════════════════════════════════════
   6. PLANTILLAS DE NOTIFICACIÓN
   ═══════════════════════════════════════════════════════════════ */
export const plantillasNotificacionParamDB = [
  { nombre: 'Nueva Tarea Asignada', trigger: 'Al crear y asignar una tarea de flujo documental', asunto: '[COFAR · SGD] Nueva tarea asignada: {{CODIGO}} — {{TITULO}}', cuerpo: 'Estimado/a {{USUARIO}},\n\nSe le ha asignado una nueva tarea de {{ETAPA}} en el Sistema de Gestión Documental de COFAR.\n\nDocumento: {{TITULO}} ({{CODIGO}})\nFecha límite de atención: {{FECHA_LIMITE}}\nGerencia: {{GERENCIA}}\n\nPara atender esta tarea, ingrese al sistema:\nhttps://sgd.cofar.com/bandeja\n\nSaludos,\nSistema de Gestión Documental — COFAR' },
  { nombre: 'Alerta de Vencimiento', trigger: '30 días antes del vencimiento de un documento', asunto: '[COFAR · SGD] ⚠️ Alerta: documento próximo a vencer', cuerpo: 'Estimado/a {{USUARIO}},\n\nEl siguiente documento está próximo a vencer:\n\nCódigo: {{CODIGO}}\nTítulo: {{TITULO}}\nFecha de vencimiento: {{FECHA_LIMITE}}\n\nSaludos,\nSistema de Gestión Documental — COFAR' },
  { nombre: 'Alerta de realizar tarea', trigger: 'Faltan 3 días para la fecha límite de una tarea asignada', asunto: '[COFAR · SGD] ⏰ Recordatorio: tarea pendiente — {{TITULO}}', cuerpo: 'Estimado/a {{USUARIO}},\n\nLe recordamos que la tarea <strong>{{ETAPA}}</strong> del documento <strong>{{TITULO}}</strong> ({{CODIGO}}) vence en 3 días ({{FECHA_LIMITE}}).\n\nPor favor atiéndala a la brevedad.\n\nSaludos,\nSistema de Gestión Documental — COFAR' },
  { nombre: 'Documento Aprobado', trigger: 'Al publicar un documento (última firma de aprobación)', asunto: '[COFAR · SGD] Nuevo documento vigente: {{CODIGO}}', cuerpo: '' },
  { nombre: 'Evaluación Pendiente', trigger: 'Al asignar examen a grupo de difusión', asunto: '[COFAR · SGD] Evaluación pendiente: {{TITULO}}', cuerpo: '' },
  { nombre: 'Auto-delegación Activada', trigger: 'Por inactividad de 10 días hábiles', asunto: '[COFAR · SGD] Reasignación automática de tarea', cuerpo: '' },
]

export const etiquetasPlantillaDB = [
  '{{CODIGO}}', '{{TITULO}}', '{{USUARIO}}', '{{FECHA_LIMITE}}', '{{ETAPA}}', '{{LINK}}', '{{GERENCIA}}', '{{OBSERVACION}}'
]

/* ═══════════════════════════════════════════════════════════════
   7. USUARIOS
   ═══════════════════════════════════════════════════════════════ */
export const usuariosParamDB = [
  { initials: 'AR', nombre: 'Aracely Romero', user: 'aromero', rol: 'Admin', area: 'Gestión Documental (ETO)', delegado: 'A. Mario B.', vacaciones: false, ausente: false, periodoVacaciones: '' },
  { initials: 'MB', nombre: 'Mario Bustamante', user: 'mbustamante', rol: 'ETO', area: 'Manufactura / Producción', delegado: 'A. Carmen C.', vacaciones: false, ausente: true, periodoVacaciones: '' },
  { initials: 'CC', nombre: 'Carmen Cárdenas', user: 'ccardenas', rol: 'Estándar', area: 'Control de Calidad / Calidad', delegado: 'A. Aracely R.', vacaciones: false, ausente: false, periodoVacaciones: '' },
  { initials: 'RV', nombre: 'Roberto Vargas', user: 'rvargas', rol: 'Visualizador', area: 'Almacenes / Logística', delegado: 'Sin delegado', vacaciones: false, ausente: false, periodoVacaciones: '' },
  { initials: 'LH', nombre: 'Lucía Herrera', user: 'lherrera', rol: 'Visualizador', area: 'Tecnología / TI / Sistemas', delegado: 'Sin delegado', vacaciones: false, ausente: false, periodoVacaciones: '' },
  { initials: 'PM', nombre: 'Pedro Mamani', user: 'pmamani', rol: 'Estándar', area: 'Planta Líquidos / Manufactura', delegado: 'A. Aracely R.', vacaciones: false, ausente: false, periodoVacaciones: '' },
]

export const rolesSistemaDB = ['Admin', 'ETO', 'Estándar', 'Visualizador']

/* ═══════════════════════════════════════════════════════════════
   8. HELPERS DE MUTACIÓN (simulan persistencia en memoria)
   ═══════════════════════════════════════════════════════════════ */

export function agregarChipExclusion(tipo) {
  if (!exclusionTiposDB.includes(tipo)) {
    exclusionTiposDB.push(tipo)
    return true
  }
  return false
}

export function eliminarChipExclusion(tipo) {
  const idx = exclusionTiposDB.indexOf(tipo)
  if (idx > -1) {
    exclusionTiposDB.splice(idx, 1)
    return true
  }
  return false
}

export function guardarRestricciones(config) {
  if (config.maxAdjuntos !== undefined) ParametrosGlobalesDB.restriccionesArchivo.maxAdjuntos = config.maxAdjuntos
  if (config.maxSizeMB !== undefined) ParametrosGlobalesDB.restriccionesArchivo.maxSizeMB = config.maxSizeMB
  if (config.maxDescargasDia !== undefined) ParametrosGlobalesDB.limitesDescarga.maxDescargasDia = config.maxDescargasDia
  if (config.bandejaRegistros !== undefined) ParametrosGlobalesDB.paginacion.bandejaRegistros = config.bandejaRegistros
}

/** Genera una fecha/hora formateada para logs */
export function nowLogString() {
  const d = new Date()
  return d.toLocaleDateString('es-BO') + ' ' + d.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' })
}
