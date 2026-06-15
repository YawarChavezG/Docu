/**
 * src/data/evaluaciones.js
 * Extraído del HTML original: monitor publicación, mis evaluaciones, certificados, examen
 */

// ─── Monitor de Evaluaciones / Controles (US-6.01) — datos del HTML ──────────
export const monitorEvaluacionesDB = [
  { cod: 'PRO-CAL-045', nombre: 'Procedimiento de Muestreo',   lanzamiento: 'Inicial',      plazo: '10/01/26 - 17/01/26', tipo: 'EVALUACIÓN',      est: 'PENDIENTE',  alcance: '23/35',   prom: '62%', cancelable: true,  configExamen: true  },
  { cod: 'FOR-RRHH-020',nombre: 'Formulario de Inducción',     lanzamiento: 'Inicial',      plazo: '10/02/26 - 20/02/26', tipo: 'CONTROL LECTURA',  est: 'PENDIENTE',  alcance: '5/100',   prom: 'N/A', cancelable: true,  configExamen: false },
  { cod: 'MAN-LOG-003', nombre: 'Manual de Logística',         lanzamiento: 'Anual 2024',   plazo: '15/01/24 - 15/02/24', tipo: 'CONTROL LECTURA',  est: 'FINALIZADO', alcance: '40/40',   prom: 'N/A', cancelable: false, configExamen: false },
  { cod: 'POL-GER-001', nombre: 'Política de Calidad',         lanzamiento: 'Anual 2025',   plazo: '01/01/25 - 31/01/25', tipo: 'EVALUACIÓN',      est: 'FINALIZADO', alcance: '200/200', prom: '92%', cancelable: false, configExamen: true  },
  { cod: 'INS-PRO-012', nombre: 'Instructivo de Limpieza',     lanzamiento: 'Inicial',      plazo: '01/02/26 - N/A',      tipo: 'SIN CONTROL',      est: 'FINALIZADO', alcance: 'N/A',     prom: 'N/A', cancelable: false, configExamen: false },
  { cod: 'MET-LOG-008', nombre: 'Metodología de Inventario',   lanzamiento: 'Inicial',      plazo: '10/04/26 - 15/04/26', tipo: 'EVALUACIÓN',      est: 'CANCELADO',  alcance: '0/15',    prom: '—',   cancelable: false, configExamen: true  },
  { cod: 'FOR-PRO-022', nombre: 'Registro de Temperatura',     lanzamiento: 'Inicial',      plazo: '12/04/26 - 18/04/26', tipo: 'CONTROL LECTURA',  est: 'CANCELADO',  alcance: '0/10',    prom: 'N/A', cancelable: false, configExamen: false },
  { cod: 'MET-PRD-005', nombre: 'Metodología de Pesaje',       lanzamiento: '16/04/26',     plazo: '16/04/26 - 30/04/26', tipo: 'EVALUACIÓN',      est: 'PENDIENTE',  alcance: '0/50',    prom: '—',   cancelable: true,  configExamen: true  },
  { cod: 'MAN-LOG-003', nombre: 'Manual de Logística (R)',     lanzamiento: '16/04/26',     plazo: '16/04/26 - 25/04/26', tipo: 'CONTROL LECTURA',  est: 'PENDIENTE',  alcance: '0/40',    prom: 'N/A', cancelable: true,  configExamen: false },
  { cod: 'PRO-LOG-018', nombre: 'Procedimiento de Recepción',  lanzamiento: 'Inicial',      plazo: '05/04/26 - 20/04/26', tipo: 'EVALUACIÓN',      est: 'PENDIENTE',  alcance: '14/15',   prom: '88%', cancelable: true,  configExamen: true  },
]

// ─── Mis Evaluaciones / Pendientes (página Evaluaciones.js) ─────────────────
export const misEvaluacionesPendientesDB = [
  {
    cod: 'PRO-RRHH-001', nombre: 'Política de Asistencia',
    tipo: 'Evaluación', fechaLimite: '15/01/2026',
    urgente: true, // VENCE HOY
    ruta: '/pre-eval',
  },
  {
    cod: 'MET-CAL-005', nombre: 'Metodología HPLC',
    tipo: 'Evaluación', fechaLimite: '17/01/2026',
    urgente: false,
    ruta: '/pre-eval',
  },
  {
    cod: 'POL-GER-002', nombre: 'Política de Seguridad MA',
    tipo: 'Control de Lectura', fechaLimite: '10/02/2026',
    urgente: false,
    ruta: '/tomar-lectura',
  },
]

// ─── Historial de Evaluaciones ────────────────────────────────────────────────
export const historialEvaluacionesDB = [
  { cod: 'PRO-CAL-001', nombre: 'Control de Calidad de MP',            tipo: 'Evaluación',       fecha: '10/11/2025', puntaje: 92,   aprobado: true  },
  { cod: 'MAN-LOG-003', nombre: 'Manual de Logística y Distribución',  tipo: 'Control de Lectura',fecha: '05/10/2025', puntaje: null, aprobado: true  },
  { cod: 'POL-GER-002', nombre: 'Política de Seguridad MA',            tipo: 'Evaluación',       fecha: '20/09/2025', puntaje: 65,   aprobado: false },
  { cod: 'INS-PRO-012', nombre: 'Instructivo de Limpieza',             tipo: 'Control de Lectura',fecha: '12/08/2025', puntaje: null, aprobado: true  },
  { cod: 'MET-CAL-005', nombre: 'Metodología HPLC',                    tipo: 'Evaluación',       fecha: '01/07/2025', puntaje: 88,   aprobado: true  },
]

// ─── Mis Certificados (página Certificados / s-mis-certificados) ─────────────
// Datos extraídos de misCerts del HTML original + extras del historial
export const misCertificadosDB = [
  { cod: 'PRO-CAL-001', tit: 'Control de Calidad de Materia Prima',     tipo: 'Evaluación',       nota: 92,   fecha: '10/11/2025', valido: true  },
  { cod: 'MAN-LOG-003', tit: 'Manual de Logística y Distribución',      tipo: 'Control de Lectura',nota: null, fecha: '05/10/2025', valido: true  },
  { cod: 'MET-CAL-005', tit: 'Metodología de Análisis HPLC',            tipo: 'Evaluación',       nota: 88,   fecha: '01/07/2025', valido: true  },
  { cod: 'INS-PRO-012', tit: 'Instructivo de Limpieza de Manufactura',  tipo: 'Control de Lectura',nota: null, fecha: '12/08/2025', valido: true  },
  { cod: 'POL-GER-001', tit: 'Política General de Calidad',             tipo: 'Evaluación',       nota: 78,   fecha: '15/03/2025', valido: false },
  // Del HTML original (misCerts):
  { cod: 'CC-MET-287',  tit: 'Alibrom solución oftálmica',              tipo: 'Evaluación',       nota: 95,   fecha: '14/04/2026', valido: true  },
  { cod: 'MAN-RRHH-001',tit: 'Manual de Inducción Corporativa',         tipo: 'Evaluación',       nota: 100,  fecha: '10/01/2026', valido: true  },
]

// ─── Preguntas de examen de ejemplo ──────────────────────────────────────────
export const examenEjemploDB = {
  cod: 'PRO-RRHH-001',
  titulo: 'Política de Asistencia',
  tiempoMinutos: 45,
  notaMinima: 70,
  intentosPermitidos: 2,
  preguntas: [
    {
      pregunta: '¿Cuál es el horario límite de ingreso antes de considerar retraso?',
      opciones: ['08:00 AM exacto', '08:05 AM (5 minutos de tolerancia)', '08:15 AM', '08:30 AM'],
      correcta: 1,
    },
    {
      pregunta: '¿Qué justificación es válida para una ausencia sin previo aviso?',
      opciones: ['Tráfico vehicular severo en la ciudad', 'Baja médica certificada por el ente gestor correspondiente (Caja de Salud)', 'Motivos personales no especificados', 'Visita familiar imprevista'],
      correcta: 1,
    },
    {
      pregunta: '¿Con cuántas horas de anticipación debe comunicarse una ausencia planificada?',
      opciones: ['12 horas antes', '24 horas antes', '48 horas antes', 'No es necesario comunicar'],
      correcta: 1,
    },
    {
      pregunta: '¿Cuántas llegadas tardías acumuladas generan una amonestación formal?',
      opciones: ['2 llegadas tardías en el mes', '3 llegadas tardías en el mes', '5 llegadas tardías en el mes', 'Una sola llegada tardía'],
      correcta: 1,
    },
  ],
}

// ─── Documentos disponibles para configurar examen (página ConfigExamen.js) ──
export const docsDisponiblesExamenDB = [
  {cod:'PRO-RRHH-001',titulo:'Política de Asistencia',tipo:'Procedimiento'},
  {cod:'MET-CAL-480',titulo:'Control de Desviaciones',tipo:'Metodología'},
  {cod:'FOR-PRO-022',titulo:'Registro de Temperatura',tipo:'Formulario'},
  {cod:'MAN-LOG-003',titulo:'Manual de Logística',tipo:'Manual'},
  {cod:'POL-GER-001',titulo:'Política General de Calidad',tipo:'Política'},
  {cod:'PRO-CAL-045',titulo:'Procedimiento de Muestreo',tipo:'Procedimiento'},
]

// ─── Preguntas generadas por IA para ConfigExamen.js ─────────────────────────
export const iaPreguntasMockDB = {
  'PRO-RRHH-001': [
    {preg:'¿Cuál es el tiempo máximo de tolerancia por llegada tarde según la política?', ops:['5 minutos','10 minutos','15 minutos','20 minutos'], correcta:1},
    {preg:'¿Cuántas inasistencias injustificadas consecutivas activan la notificación a RRHH?', ops:['1','2','3','5'], correcta:2},
    {preg:'¿Qué documento debe presentar el empleado para justificar una ausencia médica?', ops:['Correo electrónico','Certificado médico','Declaración verbal','Mensaje de WhatsApp'], correcta:1},
    {preg:'¿En qué plazo debe notificarse una ausencia programada según la política?', ops:['El mismo día','24 horas antes','48 horas antes','72 horas antes'], correcta:2},
  ],
  'MET-CAL-480': [
    {preg:'¿Qué herramienta se utiliza como primera instancia en el análisis de causa raíz?', ops:['Diagrama de Gantt','Diagrama de Ishikawa','AMFE','5S'], correcta:1},
    {preg:'¿Cuántos "¿Por qué?" se aplican como mínimo en la metodología 5-Why?', ops:['2','3','5','7'], correcta:2},
    {preg:'¿Cuál es el plazo máximo para cerrar una desviación crítica (Cat. I)?', ops:['24 horas','48 horas','72 horas','7 días'], correcta:2},
    {preg:'¿Quién debe aprobar el plan de acción de una desviación mayor?', ops:['El operario','El jefe de turno','El director técnico','El ETO'], correcta:2},
  ],
}

export function generarPreguntasIA(cod) {
  return iaPreguntasMockDB[cod] || [
    {preg:'¿Cuál es el objetivo principal del documento seleccionado?', ops:['Registrar actividades','Estandarizar procesos','Auditar resultados','Capacitar al personal'], correcta:1},
    {preg:'¿A qué área aplica principalmente este documento?', ops:['Logística','Producción','Calidad','RRHH'], correcta:2},
    {preg:'¿Con qué frecuencia debe revisarse este documento según la política general?', ops:['Cada 6 meses','Cada año','Cada 2 años','Cada 3 años'], correcta:2},
  ]
}

// ─── Expediente Maestro de Evaluaciones (página Evaluaciones.js) ─────────────
export const expedienteEvaluacionesDB = [
  { codigo:'PRO-RRHH-001', nombre:'Política de Asistencia',        fechaLanzamiento:'01/01/2026', tipoDifusion:'Evaluación',       estado:'PENDIENTE',  nota:null, resultado:'—',      tiempo:'—',       fechaRealizacion:'—',         fechaLimite:'15/01/2026' },
  { codigo:'MET-CAL-005',  nombre:'Metodología HPLC',              fechaLanzamiento:'05/01/2026', tipoDifusion:'Evaluación',       estado:'PENDIENTE',  nota:null, resultado:'—',      tiempo:'—',       fechaRealizacion:'—',         fechaLimite:'17/01/2026' },
  { codigo:'POL-GER-002',  nombre:'Política de Seguridad MA',      fechaLanzamiento:'10/01/2026', tipoDifusion:'Control Lectura', estado:'PENDIENTE',  nota:null, resultado:'NO LEÍDO', tiempo:'—',       fechaRealizacion:'—',         fechaLimite:'10/02/2026' },
  { codigo:'PRO-CAL-001',  nombre:'Control de Calidad de MP',      fechaLanzamiento:'15/08/2025', tipoDifusion:'Evaluación',       estado:'FINALIZADO', nota:92,  resultado:'APROBADO', tiempo:'05:12 min', fechaRealizacion:'10/11/2025', fechaLimite:'15/11/2025' },
  { codigo:'MAN-LOG-003',  nombre:'Manual de Logística',           fechaLanzamiento:'01/09/2025', tipoDifusion:'Control Lectura', estado:'FINALIZADO', nota:null, resultado:'LEÍDO',  tiempo:'03:45 min', fechaRealizacion:'05/10/2025', fechaLimite:'10/10/2025' },
  { codigo:'POL-GER-002',  nombre:'Política de Seguridad MA',      fechaLanzamiento:'01/09/2025', tipoDifusion:'Evaluación',       estado:'FINALIZADO', nota:65,  resultado:'REPROBADO',tiempo:'04:05 min', fechaRealizacion:'20/09/2025', fechaLimite:'25/09/2025' },
  { codigo:'INS-PRO-012',  nombre:'Instructivo de Limpieza',       fechaLanzamiento:'01/07/2025', tipoDifusion:'Control Lectura', estado:'FINALIZADO', nota:null, resultado:'LEÍDO',  tiempo:'02:30 min', fechaRealizacion:'12/08/2025', fechaLimite:'20/08/2025' },
  { codigo:'MET-CAL-005',  nombre:'Metodología HPLC',              fechaLanzamiento:'01/06/2025', tipoDifusion:'Evaluación',       estado:'FINALIZADO', nota:88,  resultado:'APROBADO', tiempo:'06:10 min', fechaRealizacion:'01/07/2025', fechaLimite:'05/07/2025' },
  { codigo:'FOR-RRHH-020', nombre:'Formulario de Inducción',       fechaLanzamiento:'01/02/2026', tipoDifusion:'Control Lectura', estado:'PENDIENTE',  nota:null, resultado:'NO LEÍDO', tiempo:'—',       fechaRealizacion:'—',         fechaLimite:'20/02/2026' },
  { codigo:'MET-PRD-005',  nombre:'Metodología de Pesaje',         fechaLanzamiento:'16/04/2026', tipoDifusion:'Evaluación',       estado:'PENDIENTE',  nota:null, resultado:'—',      tiempo:'—',       fechaRealizacion:'—',         fechaLimite:'30/04/2026' },
]

// ─── Certificados Maestro (página Certificados.js) ───────────────────────────
export const certificadosDB = [
  { id:'PRO-CAL-001',  codigo:'PRO-CAL-001',  documento:'Control de Calidad de Materia Prima',    tipo:'Evaluación',       nota:92,  fechaObtencion:'10/11/2025', valido:true  },
  { id:'MAN-LOG-003',  codigo:'MAN-LOG-003',  documento:'Manual de Logística y Distribución',     tipo:'Control Lectura', nota:null, fechaObtencion:'05/10/2025', valido:true  },
  { id:'MET-CAL-005',  codigo:'MET-CAL-005',  documento:'Metodología de Análisis HPLC',           tipo:'Evaluación',       nota:88,  fechaObtencion:'01/07/2025', valido:true  },
  { id:'INS-PRO-012',  codigo:'INS-PRO-012',  documento:'Instructivo de Limpieza de Manufactura', tipo:'Control Lectura', nota:null, fechaObtencion:'12/08/2025', valido:true  },
  { id:'POL-GER-001',  codigo:'POL-GER-001',  documento:'Política General de Calidad',            tipo:'Evaluación',       nota:78,  fechaObtencion:'15/03/2025', valido:false },
  { id:'CC-MET-287',   codigo:'CC-MET-287',   documento:'Alibrom solución oftálmica',             tipo:'Evaluación',       nota:95,  fechaObtencion:'14/04/2026', valido:true  },
  { id:'MAN-RRHH-001', codigo:'MAN-RRHH-001', documento:'Manual de Inducción Corporativa',        tipo:'Evaluación',       nota:100, fechaObtencion:'10/01/2026', valido:true  },
]

// ─── Evaluaciones Pendientes (página Evaluaciones.js) ────────────────────────
export const evaluacionesPendientesPageDB = [
  {codigo:'PRO-RRHH-001',nombre:'Política de Asistencia',tipo:'Evaluación',fechaLimite:'15/01/2026',urgente:true,route:'/pre-eval'},
  {codigo:'MET-CAL-005',nombre:'Metodología HPLC',tipo:'Evaluación',fechaLimite:'17/01/2026',urgente:false,route:'/pre-eval'},
  {codigo:'POL-GER-002',nombre:'Política de Seguridad MA',tipo:'Control de Lectura',fechaLimite:'10/02/2026',urgente:false,route:'/tomar-lectura'},
]

// ─── Historial de Evaluaciones (página Evaluaciones.js) ──────────────────────
export const evaluacionesHistorialPageDB = [
  {codigo:'PRO-CAL-001',nombre:'Control de Calidad de MP',tipo:'Evaluación',fecha:'10/11/2025',puntaje:92,aprobado:true},
  {codigo:'MAN-LOG-003',nombre:'Manual de Logística',tipo:'Control de Lectura',fecha:'05/10/2025',puntaje:null,aprobado:true},
  {codigo:'POL-GER-002',nombre:'Política de Seguridad MA',tipo:'Evaluación',fecha:'20/09/2025',puntaje:65,aprobado:false},
  {codigo:'INS-PRO-012',nombre:'Instructivo de Limpieza',tipo:'Control de Lectura',fecha:'12/08/2025',puntaje:null,aprobado:true},
  {codigo:'MET-CAL-005',nombre:'Metodología HPLC',tipo:'Evaluación',fecha:'01/07/2025',puntaje:88,aprobado:true},
]

// ─── Mis Certificados (página Certificados.js) ───────────────────────────────
export const certificadosPageDB = [
  {id:1, codigo:'PRO-CAL-001', nombre:'Control de Calidad de Materia Prima',       tipo:'Evaluación',       fecha:'10/11/2025', puntaje:92, valido:true},
  {id:2, codigo:'MAN-LOG-003', nombre:'Manual de Logística y Distribución',         tipo:'Control de Lectura',fecha:'05/10/2025', puntaje:null,valido:true},
  {id:3, codigo:'MET-CAL-005', nombre:'Metodología de Análisis HPLC',               tipo:'Evaluación',       fecha:'01/07/2025', puntaje:88, valido:true},
  {id:4, codigo:'INS-PRO-012', nombre:'Instructivo de Limpieza de Manufactura',     tipo:'Control de Lectura',fecha:'12/08/2025', puntaje:null,valido:true},
  {id:5, codigo:'POL-GER-001', nombre:'Política General de Calidad',                tipo:'Evaluación',       fecha:'15/03/2025', puntaje:78, valido:false},
]

// ─── Detalle de alcance para modal (datos ejemplo) ────────────────────────────
export const detalleAlcanceDB = {
  'PRO-CAL-045': [
    { id:1, nombre: 'Juan Perez',      cargo: 'Analista de Calidad',  area: 'Control de Calidad',  est: 'PENDIENTE',  nota: '—',  fecha: '—', tiempo:'—' },
    { id:2, nombre: 'Maria Condori',   cargo: 'Técnico de Calidad',   area: 'Garantía de Calidad', est: 'APROBADO',   nota: '88', fecha: '12/01/26', tiempo:'04:32 min' },
    { id:3, nombre: 'Carlos Flores',   cargo: 'Jefe de Logística',    area: 'Almacenes',           est: 'REPROBADO',  nota: '55', fecha: '11/01/26', tiempo:'03:10 min' },
    { id:4, nombre: 'Silvana Torres',  cargo: 'Especialista Reg.',    area: 'Regulatorio',         est: 'PENDIENTE',  nota: '—',  fecha: '—', tiempo:'—' },
    { id:5, nombre: 'Pedro Mamani',    cargo: 'Operario',             area: 'Planta Líquidos',     est: 'APROBADO',   nota: '76', fecha: '13/01/26', tiempo:'05:45 min' },
  ],
  'POL-GER-001': [
    { id:1, nombre: 'Ana Romero',      cargo: 'Directora Técnica',    area: 'Gerencia',            est: 'APROBADO',   nota: '95', fecha: '10/01/25', tiempo:'06:12 min' },
    { id:2, nombre: 'Luis Torrico',    cargo: 'Supervisor Calidad',   area: 'Control de Calidad',  est: 'APROBADO',   nota: '92', fecha: '11/01/25', tiempo:'05:50 min' },
    { id:3, nombre: 'Carmen Rojas',    cargo: 'Auditora Interna',     area: 'Auditoria',           est: 'APROBADO',   nota: '88', fecha: '12/01/25', tiempo:'04:20 min' },
  ],
  'MAN-LOG-003': [
    { id:1, nombre: 'Juan Perez',      cargo: 'Operario',             area: 'Almacenes',           est: 'APROBADO',   nota: '—',  fecha: '15/01/24', tiempo:'02:30 min' },
    { id:2, nombre: 'Luis Lopez',      cargo: 'Analista',             area: 'Logística',           est: 'APROBADO',   nota: 'N/A', fecha: '16/01/24', tiempo:'03:00 min' },
    { id:3, nombre: 'Ana Torroja',     cargo: 'Supervisora',          area: 'Distribución',        est: 'PENDIENTE',  nota: '—',  fecha: '—',        tiempo:'—' },
  ],
}

// ─── Expediente de Personal (página Publicacion.js) ───────────────────────────
export const expedientePersonalDB = [
  { id: 1, codigo:'EMP-001', nombre:'Juan Perez', cargo:'Analista de Calidad', area:'Control de Calidad', gerencia:'CALIDAD',
    historial:[
      { doc:'PRO-CAL-045', tipo:'Evaluación',      estado:'APROBADO',  nota:85, fecha:'14/01/2026', tiempo:'05:12 min' },
      { doc:'POL-GER-001', tipo:'Evaluación',      estado:'APROBADO',  nota:92, fecha:'10/01/2025', tiempo:'06:05 min' },
      { doc:'MAN-LOG-003', tipo:'Control Lectura', estado:'APROBADO',  nota:null,fecha:'05/10/2025', tiempo:'03:45 min' },
      { doc:'MET-CAL-480', tipo:'Evaluación',      estado:'REPROBADO', nota:55, fecha:'20/03/2026', tiempo:'04:10 min' },
    ]
  },
  { id: 2, codigo:'EMP-002', nombre:'Maria Gomez', cargo:'Supervisora', area:'Calidad', gerencia:'CALIDAD',
    historial:[
      { doc:'PRO-CAL-045', tipo:'Evaluación', estado:'APROBADO', nota:90, fecha:'14/01/2026', tiempo:'04:45 min' },
      { doc:'FOR-RRHH-020',tipo:'Control Lectura', estado:'PENDIENTE', nota:null, fecha:'—', tiempo:'—' },
    ]
  },
  { id: 3, codigo:'EMP-003', nombre:'Luis Lopez', cargo:'Analista', area:'Logística', gerencia:'LOGÍSTICA',
    historial:[
      { doc:'MAN-LOG-003', tipo:'Control Lectura', estado:'APROBADO', nota:null, fecha:'15/01/2024', tiempo:'02:30 min' },
      { doc:'PRO-LOG-018', tipo:'Evaluación',      estado:'APROBADO', nota:78, fecha:'18/04/2026', tiempo:'05:00 min' },
    ]
  },
]

// ─── Respuestas de Examen para modal (indexado por codigo + usuario) ──────────
export const respuestasExamenDB = {
  'PRO-CAL-045_Juan Perez': {
    usuario: 'Juan Perez',
    codigo: 'PRO-CAL-045',
    titulo: 'Procedimiento de Muestreo',
    nota: 85,
    preguntas: [
      { pregunta:'¿Cuál es el primer paso del muestreo de materia prima?', opciones:['Identificación','Registro','Muestreo','Etiquetado'], correcta:0, respondio:0 },
      { pregunta:'¿Qué norma ISO aplica al muestreo?', opciones:['ISO 9001','ISO 17025','ISO 14001','ISO 45001'], correcta:1, respondio:1 },
      { pregunta:'¿Cuántas muestras se toman por lote?', opciones:['1','3','5','Depende del plan'], correcta:3, respondio:2 },
      { pregunta:'¿Quién aprueba el informe de muestreo?', opciones:['Operario','Jefe de Turno','Analista','ETO'], correcta:2, respondio:2 },
      { pregunta:'¿En qué temperatura se conservan las muestras biológicas?', opciones:['2-8°C','15-25°C','-20°C','30°C'], correcta:0, respondio:0 },
    ]
  },
  'PRO-CAL-045_Maria Gomez': {
    usuario: 'Maria Gomez',
    codigo: 'PRO-CAL-045',
    titulo: 'Procedimiento de Muestreo',
    nota: 90,
    preguntas: [
      { pregunta:'¿Cuál es el primer paso del muestreo de materia prima?', opciones:['Identificación','Registro','Muestreo','Etiquetado'], correcta:0, respondio:0 },
      { pregunta:'¿Qué norma ISO aplica al muestreo?', opciones:['ISO 9001','ISO 17025','ISO 14001','ISO 45001'], correcta:1, respondio:1 },
      { pregunta:'¿Cuántas muestras se toman por lote?', opciones:['1','3','5','Depende del plan'], correcta:3, respondio:3 },
      { pregunta:'¿Quién aprueba el informe de muestreo?', opciones:['Operario','Jefe de Turno','Analista','ETO'], correcta:2, respondio:2 },
      { pregunta:'¿En qué temperatura se conservan las muestras biológicas?', opciones:['2-8°C','15-25°C','-20°C','30°C'], correcta:0, respondio:1 },
    ]
  },
  'POL-GER-001_Ana Romero': {
    usuario: 'Ana Romero',
    codigo: 'POL-GER-001',
    titulo: 'Política General de Calidad',
    nota: 95,
    preguntas: [
      { pregunta:'¿Cuál es el compromiso de la alta dirección?', opciones:['Cumplimiento legal','Mejora continua','Satisfacción del cliente','Todas las anteriores'], correcta:3, respondio:3 },
      { pregunta:'¿Con qué frecuencia se revisa la política?', opciones:['Cada 6 meses','Cada año','Cada 2 años','Cada 3 años'], correcta:1, respondio:1 },
    ]
  },
}
