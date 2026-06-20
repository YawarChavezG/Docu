/**
 * src/data/copias.js
 * Extraído del HTML: s-bandeja (recepcionCopiasDB), s-monitor-cc, s-monitor-cn, s-modulo-copias
 * Contiene: CopiasControladas[], CopiasNoControladas[], destinatarios[]
 */

export const CopiasControladasDB = [
  {
    id: '1',
    cod: 'CC-MET-287',
    ver: '01',
    doc: 'Alibrom solución oftálmica',
    tipo: 'Copia Controlada',
    numCopia: 1,
    fe: '15/04/26 10:30',
    fd: null,
    orig: 'A. Romero',
    dest: 'Juan Perez',
    est: 'Generado',
    prioridad: false,
    estadoRecepcion: 'Pendiente',
  },
  {
    id: '2',
    cod: 'CC-MET-287',
    ver: '01',
    doc: 'Alibrom solución oftálmica',
    tipo: 'Copia Controlada',
    numCopia: 2,
    fe: '14/04/26 09:15',
    fd: null,
    orig: 'A. Romero',
    dest: 'Maria Gomez',
    est: 'Entregado',
    prioridad: false,
    estadoRecepcion: 'Recibido',
  },
  {
    id: '3',
    cod: 'PRO-PRO-012',
    ver: '03',
    doc: 'Limpieza de Tanque Agitador',
    tipo: 'Copia Controlada',
    numCopia: 1,
    fe: '10/04/26 14:00',
    fd: '12/04/26 16:30',
    orig: 'A. Romero',
    dest: 'Luis Lopez',
    est: 'Devuelto',
    prioridad: false,
    estadoRecepcion: 'Devuelto',
  },
  {
    id: '4',
    cod: 'INS-LOG-005',
    ver: '02',
    doc: 'Ingreso de Materia Prima',
    tipo: 'Copia Controlada',
    numCopia: 5,
    fe: '16/04/26 08:00',
    fd: null,
    orig: 'A. Romero',
    dest: 'Ana Torroja',
    est: 'Generado',
    prioridad: true,
    estadoRecepcion: 'Pendiente',
  },
  {
    id: '5',
    cod: 'PRO-PRO-012',
    ver: '03',
    doc: 'Limpieza de Tanque Agitador',
    tipo: 'Copia Controlada',
    numCopia: 2,
    fe: '16/04/26 11:00',
    fd: null,
    orig: 'A. Romero',
    dest: 'Carlos Mamani',
    est: 'Generado',
    prioridad: false,
    estadoRecepcion: 'Pendiente',
  },
]

export const CopiasNoControladasDB = [
  {
    id: '1',
    cod: 'MAN-RRHH-001',
    ver: '05',
    doc: 'Manual de Bienvenida',
    tipo: 'Copia No Controlada',
    numCopia: 3,
    fe: '16/04/26 09:00',
    orig: 'A. Romero',
    dest: 'Nuevo Empleado',
    est: 'Entregado',
    estadoRecepcion: 'Recibido',
  },
  {
    id: '2',
    cod: 'MAN-RRHH-001',
    ver: '05',
    doc: 'Manual de Bienvenida',
    tipo: 'Copia No Controlada',
    numCopia: 4,
    fe: '16/04/26 09:15',
    orig: 'A. Romero',
    dest: 'Nuevo Empleado 2',
    est: 'Generado',
    estadoRecepcion: 'Pendiente',
  },
  {
    id: '3',
    cod: 'FOR-PRO-022',
    ver: '01',
    doc: 'Registro de Temperatura',
    tipo: 'Copia No Controlada',
    numCopia: 1,
    fe: '12/04/26 11:00',
    orig: 'A. Romero',
    dest: 'Supervisor Planta',
    est: 'Entregado',
    estadoRecepcion: 'Recibido',
  },
]

export const destinatariosPosibles = [
  'Juan Perez (Analista de Calidad)',
  'Maria Gomez (Técnico de Calidad)',
  'Luis Lopez (Jefe de Manufactura)',
  'Carlos Mamani (Operario Planta)',
  'Ana Torroja (Supervisora Almacén)',
  'Pedro Sanchez (Encargado Logística)',
  'Roberto Vargas (Auxiliar Almacén)',
  'Silvana Torres (Especialista Regulatorio)',
  'Mario Bustamante (Analista Producción)',
  'Carmen Cárdenas (Analista Calidad)',
  'Nuevo Empleado (Inducción)',
  'Nuevo Empleado 2 (Inducción)',
  'Supervisor Planta (Producción)',
]

export const generadosCopiaDB = [
  { idCopia: 'CC-001', dest: 'Juan Perez', responsable: 'A. Romero', tipo: 'Controlada', codDoc: 'CC-MET-287', ver: '01' },
  { idCopia: 'CC-002', dest: 'Maria Gomez', responsable: 'A. Romero', tipo: 'Controlada', codDoc: 'CC-MET-287', ver: '01' },
]

export function generarIdCopia(tipo) {
  const prefijo = tipo === 'Controlada' ? 'CC' : 'CNC'
  const num = String(Math.floor(Math.random() * 900) + 100)
  return `${prefijo}-${num}`
}

export function estadoColor(est) {
  if (est === 'Entregado' || est === 'Recibido') return '#639922'
  if (est === 'Devuelto') return '#a32d2d'
  return '#854f0b'
}

export function tipoBadge(tipo) {
  if (tipo === 'Copia Controlada') return 'badge-green'
  return 'badge-amber'
}

// ─── Monitor de Copias Controladas (página MonitorCC.js) ─────────────────────
export const monitorCCDB = [
  {id:1,codigo:'CC-MET-287',ver:'01',doc:'Alibrom solución oftálmica',fechaEntregada:'15/04/26 10:30',fechaEntregaIso:'2026-04-15',origen:'A. Romero',destinatario:'Juan Perez',estado:'Generado',fechaDevolucion:'—'},
  {id:2,codigo:'CC-MET-287',ver:'01',doc:'Alibrom solución oftálmica',fechaEntregada:'14/04/26 09:15',fechaEntregaIso:'2026-04-14',origen:'A. Romero',destinatario:'Maria Gomez',estado:'Entregado',fechaDevolucion:'—'},
  {id:3,codigo:'PRO-PRO-812',ver:'03',doc:'Limpieza de Tanque Agitador',fechaEntregada:'10/04/26 14:00',fechaEntregaIso:'2026-04-10',origen:'A. Romero',destinatario:'Luis Lopez',estado:'Devuelto',fechaDevolucion:'12/04/26 16:30'},
  {id:4,codigo:'INS-LOG-085',ver:'02',doc:'Ingreso de Materia Prima',fechaEntregada:'16/04/26 09:00',fechaEntregaIso:'2026-04-16',origen:'A. Romero',destinatario:'Ana Torroja',estado:'Generado',fechaDevolucion:'—'},
  {id:5,codigo:'PRO-PRO-812',ver:'03',doc:'Limpieza de Tanque Agitador',fechaEntregada:'18/04/26 11:30',fechaEntregaIso:'2026-04-18',origen:'A. Romero',destinatario:'Carlos Mamani',estado:'Generado',fechaDevolucion:'—'},
  {id:6,codigo:'FOR-PRO-422',ver:'02',doc:'Registro de Temperatura',fechaEntregada:'20/04/26 08:00',fechaEntregaIso:'2026-04-20',origen:'A. Romero',destinatario:'Supervisor Planta',estado:'Entregado',fechaDevolucion:'—'},
]

// ─── Monitor de Copias No Controladas (página MonitorCN.js) ──────────────────
export const monitorCNDB = [
  {id:1,codigo:'MAN-RRHH-001',ver:'05',doc:'Manual de Bienvenida',fechaEntregada:'16/04/26 09:00',fechaEntregaIso:'2026-04-16',origen:'A. Romero',destinatario:'Nuevo Empleado',estado:'Entregado'},
  {id:2,codigo:'MAN-RRHH-001',ver:'05',doc:'Manual de Bienvenida',fechaEntregada:'16/04/26 09:15',fechaEntregaIso:'2026-04-16',origen:'A. Romero',destinatario:'Nuevo Empleado 2',estado:'Generado'},
  {id:3,codigo:'FOR-PRO-422',ver:'01',doc:'Registro de Temperatura',fechaEntregada:'12/04/26 11:00',fechaEntregaIso:'2026-04-12',origen:'A. Romero',destinatario:'Supervisor Planta',estado:'Entregado'},
  {id:4,codigo:'INS-LOG-085',ver:'02',doc:'Ingreso de Materia Prima',fechaEntregada:'18/04/26 14:00',fechaEntregaIso:'2026-04-18',origen:'A. Romero',destinatario:'Ana Torroja',estado:'Generado'},
]
