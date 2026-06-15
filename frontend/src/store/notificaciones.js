/**
 * src/store/notificaciones.js
 * Store global de Alpine.js para Notificaciones Globales.
 * Fuente única de verdad que sincroniza:
 *   - Badge de la Campana (Header)
 *   - Badge de "Mi Bandeja" (Sidebar)
 *   - Dropdown de Notificaciones Reactivo
 *
 * Consume datos desde src/data/tasks.js (NO crea mocks nuevos).
 * Filtra por rol de usuario en tiempo real.
 */

import {
  tareasBandejaDB,
  evaluacionesPendientesDB,
  controlesLecturaDB,
  recepcionCopiasDB,
} from '../data/tasks.js'

/* ── Mapeo de badges a clases Tailwind ─────────────────────────── */
const BADGE_MAP = {
  'badge-red':   { bg: 'bg-red-50',    text: 'text-red-700',    dot: 'bg-red-500',    label: 'Alta' },
  'badge-amber': { bg: 'bg-amber-50',  text: 'text-amber-700',  dot: 'bg-amber-500',  label: 'Media' },
  'badge-blue':  { bg: 'bg-blue-50',   text: 'text-blue-700',   dot: 'bg-blue-500',   label: 'Media' },
  'badge-green': { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', label: 'Baja' },
  'badge-gray':  { bg: 'bg-slate-100',  text: 'text-slate-600',  dot: 'bg-slate-500',  label: 'Baja' },
}

function getBadge(tipoBadge) {
  return BADGE_MAP[tipoBadge] || BADGE_MAP['badge-gray']
}

/* ── Normalización de datos fuente ─────────────────────────────── */
function buildNotificaciones() {
  const tareas = tareasBandejaDB.map(t => {
    const b = getBadge(t.tipoBadge)
    return {
      id: `t-${t.id}`,
      tipo: t.tipo,
      tipoBadge: t.tipoBadge,
      badgeBg: b.bg,
      badgeText: b.text,
      dotColor: b.dot,
      prioridadLabel: b.label,
      codigo: t.cod,
      nombre: t.nombre,
      fecha: t.fecha,
      prioridad: t.slaBadge === 'badge-red' ? 'alta' : t.slaBadge === 'badge-amber' ? 'media' : 'baja',
      ruta: t.ruta,
      categoria: 'Tarea',
    }
  })

  const evaluaciones = evaluacionesPendientesDB.map(e => {
    const b = e.urgente ? getBadge('badge-red') : getBadge('badge-amber')
    return {
      id: `e-${e.cod}`,
      tipo: e.tipo,
      tipoBadge: e.urgente ? 'badge-red' : 'badge-amber',
      badgeBg: b.bg,
      badgeText: b.text,
      dotColor: b.dot,
      prioridadLabel: b.label,
      codigo: e.cod,
      nombre: e.nombre,
      fecha: e.fechaLimite.replace(/^[^\s]+\s/, ''),
      prioridad: e.urgente ? 'alta' : 'media',
      ruta: e.ruta,
      categoria: 'Evaluación',
    }
  })

  const lecturas = controlesLecturaDB.map(c => {
    const b = getBadge('badge-blue')
    return {
      id: `l-${c.cod}`,
      tipo: c.tipo,
      tipoBadge: 'badge-blue',
      badgeBg: b.bg,
      badgeText: b.text,
      dotColor: b.dot,
      prioridadLabel: b.label,
      codigo: c.cod,
      nombre: c.nombre,
      fecha: c.plazo,
      prioridad: 'media',
      ruta: c.ruta,
      categoria: 'Lectura',
    }
  })

  const copias = recepcionCopiasDB.map((c, i) => {
    const b = getBadge(c.tipoBadge)
    return {
      id: `c-${c.cod}-${i}`,
      tipo: c.tipo,
      tipoBadge: c.tipoBadge,
      badgeBg: b.bg,
      badgeText: b.text,
      dotColor: b.dot,
      prioridadLabel: b.label,
      codigo: c.cod,
      nombre: c.nombre,
      fecha: 'Pendiente',
      prioridad: c.prioridad ? 'alta' : 'baja',
      ruta: '/bandeja',
      categoria: 'Copia',
    }
  })

  return { tareas, evaluaciones, lecturas, copias }
}

const { tareas, evaluaciones, lecturas, copias } = buildNotificaciones()

/* ── Store Export ──────────────────────────────────────────────── */
export const notificacionesStore = {
  _tareas: tareas,
  _evaluaciones: evaluaciones,
  _lecturas: lecturas,
  _copias: copias,

  /**
   * Array de notificaciones normalizadas filtradas por rol.
   * Lazy evaluation — se recalcula cada vez que Alpine accede al getter.
   */
  get items() {
    const auth = window.Alpine?.store('auth')
    const role = auth?.role
    if (!role) return []

    let items = []

    // Tareas de flujo: eto, user (visualizador y admin NO)
    if (role === 'eto' || role === 'user') {
      items = items.concat(this._tareas)
    }

    // Evaluaciones: todos excepto admin
    if (role !== 'admin') {
      items = items.concat(this._evaluaciones)
    }

    // Controles de lectura: todos excepto admin
    if (role !== 'admin') {
      items = items.concat(this._lecturas)
    }

    // Recepción de copias físicas: solo user
    if (role === 'user') {
      items = items.concat(this._copias)
    }

    return items
  },

  /** Total de notificaciones pendientes para el rol actual */
  get total() {
    return this.items.length
  },
}
