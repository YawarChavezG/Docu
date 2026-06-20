/**
 * src/data/movimientos.js
 * Extraído del HTML: s-consulta-user (timeline/accordion), historial revision
 * Contiene: MovimientosDocumento[] (para el timeline/accordion de Consulta Docs)
 */

export const MovimientosDocumentoDB = [
  {
    procesoId: 'CC-1-692',
    cod: 'CC-1-692',
    usuario: 'gchambi',
    area: 'CONTROL DE CALIDAD',
    f_sol: '15/09/25',
    f_lib: '17/09/25',
    f_rev: '26/09/25',
    f_apr: '10/10/25',
    etapa: 'Finalizado',
    resp: 'Sistema',
    estado: 'Concluido',
    log: [
      { etapa: 'Solicitud',        user: 'gchambi',   acc: 'Creado',         fecha: '15/09/25', hora: '08:30', obs: '-' },
      { etapa: 'Liberación ETO',   user: 'aromero',   acc: 'Liberado',       fecha: '17/09/25', hora: '10:00', obs: 'Documento cumple con los formatos estándar.' },
      { etapa: 'Revisión (R1)',    user: 'jsanjines', acc: 'Aprobado',       fecha: '22/09/25', hora: '11:00', obs: '-' },
      { etapa: 'Aprobación (A1)',  user: 'vvillegas', acc: 'Aprobado Final', fecha: '10/10/25', hora: '15:45', obs: '-' },
    ],
  },
  {
    procesoId: 'CC-1-1020',
    cod: 'CC-1-1020',
    usuario: 'faguilar',
    area: 'CONTROL DE CALIDAD',
    f_sol: '14/04/26',
    f_lib: '—',
    f_rev: '—',
    f_apr: '—',
    etapa: 'Liberación ETO',
    resp: 'aromero',
    estado: 'En ejecución',
    log: [
      { etapa: 'Solicitud',      user: 'faguilar', acc: 'Creado',    fecha: '14/04/26', hora: '10:45', obs: 'Nueva solicitud de manual.' },
      { etapa: 'Liberación ETO', user: 'aromero',  acc: 'Pendiente', fecha: '14/04/26', hora: '10:46', obs: 'Tarea pendiente de auditoría de Calidad.' },
    ],
  },
  {
    procesoId: 'PRO-2-115',
    cod: 'PRO-2-115',
    usuario: 'mrodriguez',
    area: 'PRODUCCIÓN',
    f_sol: '18/04/26',
    f_lib: '19/04/26',
    f_rev: '—',
    f_apr: '—',
    etapa: 'Revisión Paralela',
    resp: 'jsanjines, faguilar, lteran',
    estado: 'En ejecución',
    log: [
      { etapa: 'Solicitud',      user: 'mrodriguez', acc: 'Creado',    fecha: '18/04/26', hora: '09:00', obs: 'Actualización de procedimiento.' },
      { etapa: 'Liberación ETO', user: 'aromero',    acc: 'Liberado',  fecha: '19/04/26', hora: '11:30', obs: 'Enviado a revisión técnica.' },
      { etapa: 'Revisión (R1)',  user: 'jsanjines',  acc: 'Pendiente', fecha: '19/04/26', hora: '11:31', obs: 'Esperando visto bueno técnico.' },
      { etapa: 'Revisión (R2)',  user: 'faguilar',   acc: 'Pendiente', fecha: '19/04/26', hora: '11:31', obs: 'Esperando visto bueno de planta.' },
      { etapa: 'Revisión (R3)',  user: 'lteran',     acc: 'Pendiente', fecha: '19/04/26', hora: '11:31', obs: 'Esperando validación de seguridad.' },
    ],
  },
  {
    procesoId: 'LOG-3-001',
    cod: 'LOG-3-001',
    usuario: 'cparedes',
    area: 'LOGISTICA',
    f_sol: '15/10/25',
    f_lib: '17/10/25',
    f_rev: '—',
    f_apr: '—',
    etapa: 'Anulado',
    resp: 'cparedes',
    estado: 'Eliminado',
    log: [
      { etapa: 'Solicitud',    user: 'cparedes',  acc: 'Creado',     fecha: '15/10/25', hora: '16:00', obs: '-' },
      { etapa: 'Eliminación',  user: 'cparedes',  acc: 'Eliminado',  fecha: '18/10/25', hora: '09:00', obs: 'Se anula proceso por error de matriz.' },
    ],
  },
]

export const historialEtapasProceso = [
  { etapa: 'Solicitud',    accion: 'Creado',     color: 'icon-blue'   },
  { etapa: 'Liberación ETO', accion: 'Liberado', color: 'icon-green'  },
  { etapa: 'Revisión',    accion: 'Aprobado',   color: 'icon-green'  },
  { etapa: 'Revisión Paralela', accion: 'Revisión Multiple', color: 'icon-blue' },
  { etapa: 'Corrección',   accion: 'Corregido',  color: 'icon-blue'   },
  { etapa: 'Aprobación',   accion: 'Aprobado',   color: 'icon-green'  },
  { etapa: 'Finalizado',   accion: 'Publicado',  color: 'icon-green'  },
  { etapa: 'Anulado',      accion: 'Eliminado',  color: 'icon-red'    },
]

export function getMovimientoPorId(procesoId) {
  return MovimientosDocumentoDB.find(m => m.procesoId === procesoId) || null
}

export function getEtapaIndex(etapa) {
  const etapas = ['Solicitud', 'Liberación ETO', 'Revisión Paralela', 'Corrección', 'Aprobación', 'Finalizado', 'Anulado']
  return etapas.indexOf(etapa)
}

export function getEstadoBadgeClass(estado) {
  if (estado === 'Concluido' || estado === 'Finalizado') return 'badge-green'
  if (estado === 'En ejecución') return 'badge-amber'
  if (estado === 'Eliminado') return 'badge-red'
  return 'badge-gray'
}