/**
 * src/data/bitacora.js
 * Extraído del HTML: s-reportes (bitácora MAN-LOG-003), procesosConsultaDB log
 * Contiene: EntradasBitacora[], LogsProceso[]
 */

export const EntradasBitacoraDB = [
  {
    fecha: '12/01/2026 09:15',
    usuario: 'Maria Condori',
    accion: 'Aprobación',
    detalle: 'Aprobó revisión — firma digital registrada',
    doc: 'MAN-LOG-003',
    etapa: 'Revisión',
  },
  {
    fecha: '11/01/2026 14:32',
    usuario: 'Jasiel Sanjinés',
    accion: 'Observación',
    detalle: 'Ingresó observación en sección 3.2',
    doc: 'MAN-LOG-003',
    etapa: 'Revisión',
  },
  {
    fecha: '10/01/2026 08:00',
    usuario: 'Sistema SGD',
    accion: 'Notificación',
    detalle: 'Enviado a revisores paralelos',
    doc: 'MAN-LOG-003',
    etapa: 'Revisión',
  },
  {
    fecha: '08/01/2026 11:20',
    usuario: 'Aracely Romero',
    accion: 'Liberación',
    detalle: 'Liberado por gestor — modificó aprobador',
    doc: 'MAN-LOG-003',
    etapa: 'Liberación',
  },
  {
    fecha: '05/01/2026 16:45',
    usuario: 'Carlos Flores',
    accion: 'Elaboración',
    detalle: 'Cargó v01 del documento — solicitó editable',
    doc: 'MAN-LOG-003',
    etapa: 'Elaboración',
  },
  {
    fecha: '20/04/2026 10:30',
    usuario: 'aromero',
    accion: 'Publicación',
    detalle: 'Documento publicado y habilitado en Lista Maestra',
    doc: 'CC-MET-287',
    etapa: 'Finalizado',
  },
  {
    fecha: '18/04/2026 15:20',
    usuario: 'jmamani',
    accion: 'Aprobación',
    detalle: 'Aprobó revisión técnica',
    doc: 'PRO-CAL-045',
    etapa: 'Revisión',
  },
]

export const LogsProcesoDB = [
  {
    procesoId: 'CC-1-692',
    doc: 'CC-1-692',
    usuario: 'gchambi',
    log: [
      { etapa: 'Solicitud',    user: 'gchambi',  acc: 'Creado',        fecha: '15/09/25', hora: '08:30', obs: '-' },
      { etapa: 'Liberación ETO', user: 'aromero', acc: 'Liberado',     fecha: '17/09/25', hora: '10:00', obs: 'Documento cumple con los formatos estándar.' },
      { etapa: 'Revisión (R1)', user: 'jsanjines', acc: 'Aprobado',    fecha: '22/09/25', hora: '11:00', obs: '-' },
      { etapa: 'Aprobación (A1)', user: 'vvillegas', acc: 'Aprobado Final', fecha: '10/10/25', hora: '15:45', obs: '-' },
    ],
  },
  {
    procesoId: 'CC-1-1020',
    doc: 'CC-1-1020',
    usuario: 'faguilar',
    log: [
      { etapa: 'Solicitud',    user: 'faguilar', acc: 'Creado',    fecha: '14/04/26', hora: '10:45', obs: 'Nueva solicitud de manual.' },
      { etapa: 'Liberación ETO', user: 'aromero', acc: 'Pendiente', fecha: '14/04/26', hora: '10:46', obs: 'Tarea pendiente de auditoría de Calidad.' },
    ],
  },
  {
    procesoId: 'PRO-2-115',
    doc: 'PRO-2-115',
    usuario: 'mrodriguez',
    log: [
      { etapa: 'Solicitud',     user: 'mrodriguez', acc: 'Creado',    fecha: '18/04/26', hora: '09:00', obs: 'Actualización de procedimiento.' },
      { etapa: 'Liberación ETO', user: 'aromero',    acc: 'Liberado', fecha: '19/04/26', hora: '11:30', obs: 'Enviado a revisión técnica.' },
      { etapa: 'Revisión (R1)', user: 'jsanjines',  acc: 'Pendiente',fecha: '19/04/26', hora: '11:31', obs: 'Esperando visto bueno técnico.' },
      { etapa: 'Revisión (R2)', user: 'faguilar',   acc: 'Pendiente',fecha: '19/04/26', hora: '11:31', obs: 'Esperando visto bueno de planta.' },
      { etapa: 'Revisión (R3)', user: 'lteran',     acc: 'Pendiente',fecha: '19/04/26', hora: '11:31', obs: 'Esperando validación de seguridad.' },
    ],
  },
  {
    procesoId: 'LOG-3-001',
    doc: 'LOG-3-001',
    usuario: 'cparedes',
    log: [
      { etapa: 'Solicitud',    user: 'cparedes',  acc: 'Creado',     fecha: '15/10/25', hora: '16:00', obs: '-' },
      { etapa: 'Eliminación',  user: 'cparedes',  acc: 'Eliminado',  fecha: '18/10/25', hora: '09:00', obs: 'Se anula proceso por error de matriz.' },
    ],
  },
]

export const TIMELINE_CONFIG = {
  Creado:        { cls: 'icon-blue',  icon: 'S', color: '#3b82f6',  msgClass: 'msg-blue',  title: 'Mensaje adjunto:' },
  Corregido:     { cls: 'icon-blue',  icon: 'C', color: '#3b82f6',  msgClass: 'msg-blue',  title: 'Mensaje adjunto:' },
  Liberado:      { cls: 'icon-green', icon: 'E', color: '#10b981',  msgClass: 'msg-green', title: 'Mensaje adjunto:' },
  Aprobado:      { cls: 'icon-green', icon: '✓', color: '#10b981',  msgClass: 'msg-green', title: 'Mensaje adjunto:' },
  'Aprobado Final': { cls: 'icon-green', icon: '✓', color: '#10b981', msgClass: 'msg-green', title: 'Mensaje adjunto:' },
  Devuelto:      { cls: 'icon-red',   icon: 'X', color: '#ef4444',  msgClass: 'msg-red',   title: 'Observación adjunta:' },
  Eliminado:     { cls: 'icon-red',   icon: 'X', color: '#ef4444',  msgClass: 'msg-red',   title: 'Observación adjunta:' },
  Pendiente:     { cls: 'icon-amber', icon: '⏳', color: '#d97706',  msgClass: 'msg-amber', title: 'Estado de Tarea:' },
  Reasignado:    { cls: 'icon-gray',  icon: 'R', color: '#6b7280',  msgClass: 'msg-gray',  title: 'Reasignación ETO:' },
}

export function getAccionColor(accion) {
  if (accion === 'Aprobación' || accion === 'Liberación' || accion === 'Publicación') return 'badge-green'
  if (accion === 'Observación') return 'badge-amber'
  return 'badge-blue'
}

export function getLogPorProceso(procesoId) {
  return LogsProcesoDB.find(l => l.procesoId === procesoId) || null
}

// ─── Timeline estático de Revisión (página Revision.js) ──────────────────────
export const timelineRevisionDB = [
  {icono:'S',color:'#2563eb',bg:'#eff6ff',txt:'Enviado a Liberación por elaborador',meta:'10/01/2026 · Carlos Flores'},
  {icono:'E',color:'#059669',bg:'#ecfdf5',txt:'Liberado por Gestor Documental (ETO)',meta:'11/01/2026 · Aracely Romero'},
  {icono:'✕',color:'#dc2626',bg:'#fef2f2',txt:'Devuelto con Observaciones',meta:'12/01/2026 · Maria Condori (Revisor 1)',bold:true},
  {icono:'C',color:'#2563eb',bg:'#eff6ff',txt:'Corrección enviada por elaborador',meta:'13/01/2026 · Carlos Flores'},
  {icono:'✓',color:'#059669',bg:'#ecfdf5',txt:'Aprobado por Revisor 1',meta:'13/01/2026 · Maria Condori'},
  {icono:'✓',color:'#059669',bg:'#ecfdf5',txt:'Aprobado por Revisor 3',meta:'14/01/2026 · Lucia Terán'},
  {icono:'✕',color:'#dc2626',bg:'#fef2f2',txt:'Devuelto con Observaciones',meta:'14/01/2026 · Jasiel Sanjinés (Revisor 2)',bold:true},
  {icono:'⏳',color:'#94a3b8',bg:'#f8fafc',txt:'Pendiente: Firma de Aprobación Final',meta:'Luis Mamani (Aprobador 1) - Esperando Revisores',pending:true},
]

// ─── Observación activa en fase de Revisión ──────────────────────────────────
export const observacionActivaRevision = {
  de: 'Jasiel Sanjinés (Revisor 2)',
  fecha: '14/01/2026 10:15 a.m.',
  texto: 'He revisado el documento, pero en el punto 3.2 falta incluir la referencia a la norma ISO 9001:2015 sección 7.5. Favor considerarlo.',
}

// ─── Historial dinámico: Fase de Revisores ───────────────────────────────────
// Solicitud (Concluido) -> Liberación ETO (Concluido) -> Revisión (1 aprobado, 2 pendientes)
export const historialRevision = [
  { icono: 'S', color: 'text-blue-600', bg: 'bg-blue-50', borderColor: 'border-blue-600', txt: 'Solicitud registrada por elaborador', meta: '10/01/2026 · Carlos Flores' },
  { icono: 'E', color: 'text-emerald-600', bg: 'bg-emerald-50', borderColor: 'border-emerald-600', txt: 'Liberado por Gestor Documental (ETO)', meta: '11/01/2026 · Aracely Romero' },
  { icono: '✓', color: 'text-emerald-600', bg: 'bg-emerald-50', borderColor: 'border-emerald-600', txt: 'Aprobado por Revisor 1 (Maria Condori)', meta: '13/01/2026' },
  { icono: '⏳', color: 'text-amber-600', bg: 'bg-amber-50', borderColor: 'border-amber-600', txt: 'Pendiente: Revisor 2 (Jasiel Sanjinés)', meta: 'En espera de revisión técnica' },
  { icono: '⏳', color: 'text-amber-600', bg: 'bg-amber-50', borderColor: 'border-amber-600', txt: 'Pendiente: Revisor 3 (Lucia Terán)', meta: 'En espera de validación' },
]

// ─── Historial dinámico: Fase de Aprobadores ─────────────────────────────────
// Todos los revisores concluidos -> Pasó a fase de Aprobadores
export const historialAprobacion = [
  { icono: 'S', color: 'text-blue-600', bg: 'bg-blue-50', borderColor: 'border-blue-600', txt: 'Solicitud registrada por elaborador', meta: '10/01/2026 · Carlos Flores' },
  { icono: 'E', color: 'text-emerald-600', bg: 'bg-emerald-50', borderColor: 'border-emerald-600', txt: 'Liberado por Gestor Documental (ETO)', meta: '11/01/2026 · Aracely Romero' },
  { icono: '✓', color: 'text-emerald-600', bg: 'bg-emerald-50', borderColor: 'border-emerald-600', txt: 'Aprobado por Revisor 1 (Maria Condori)', meta: '13/01/2026' },
  { icono: '✓', color: 'text-emerald-600', bg: 'bg-emerald-50', borderColor: 'border-emerald-600', txt: 'Aprobado por Revisor 2 (Jasiel Sanjinés)', meta: '14/01/2026' },
  { icono: '✓', color: 'text-emerald-600', bg: 'bg-emerald-50', borderColor: 'border-emerald-600', txt: 'Aprobado por Revisor 3 (Lucia Terán)', meta: '14/01/2026' },
  { icono: '⏳', color: 'text-amber-600', bg: 'bg-amber-50', borderColor: 'border-amber-600', txt: 'Pendiente: Aprobador 1 (Luis Mamani)', meta: 'Esperando firma de aprobación final' },
]
