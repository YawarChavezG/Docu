/**
 * src/data/procesosFlujo.js
 * Estado compartido del flujo documental (Fase 1 — centralización)
 * Permite compartir estado entre liberación, revisión, corrección y bandeja.
 */

export const procesosFlujoDB = [
  {
    id: 'P-246',
    codigo: 'MET-CAL-002',
    nombre: 'Metodología de Análisis de Causa Raíz',
    version: '01',
    elaborador: 'Juan Perez',
    gerencia: 'CALIDAD',
    area: 'Control Calidad',
    tipo: 'Metodología',
    etapaActual: 'Liberación ETO',
    revisores: [
      { id: 1, nombre: 'Maria Condori (Analista de Calidad)' },
      { id: 2, nombre: 'Jasiel Sanjinés (Jefe de Excelencia)' },
    ],
    aprobadores: [
      { id: 1, nombre: 'Luis Mamani (Gerente de Planta)' },
    ],
    observaciones: [],
    timeline: [],
    estado: 'Pendiente',
    fechaCreacion: '12/01/2026',
    fechaLiberacion: null,
    fechaAprobacion: null,
  },
  {
    id: 'P-247',
    codigo: 'PRO-LOG-018',
    nombre: 'Procedimiento de Recepción de Insumos',
    version: '01',
    elaborador: 'Carlos Flores',
    gerencia: 'LOGÍSTICA',
    area: 'Almacenes',
    tipo: 'Procedimiento',
    etapaActual: 'Liberación ETO',
    revisores: [],
    aprobadores: [],
    observaciones: [],
    timeline: [],
    estado: 'Pendiente',
    fechaCreacion: '14/01/2026',
    fechaLiberacion: null,
    fechaAprobacion: null,
  },
  {
    id: 'P-248',
    codigo: 'FOR-RRHH-008',
    nombre: 'Formulario de Vacaciones',
    version: '01',
    elaborador: 'Maria Condori',
    gerencia: 'RRHH',
    area: 'Administración',
    tipo: 'Formulario',
    etapaActual: 'Liberación ETO',
    revisores: [],
    aprobadores: [],
    observaciones: [],
    timeline: [],
    estado: 'Pendiente',
    fechaCreacion: '16/01/2026',
    fechaLiberacion: null,
    fechaAprobacion: null,
  },
]

export function getProcesoByCodigo(codigo) {
  return procesosFlujoDB.find(p => p.codigo === codigo) || null
}

export function getProcesoById(id) {
  return procesosFlujoDB.find(p => p.id === id) || null
}

export function actualizarEtapa(idProceso, nuevaEtapa) {
  const p = getProcesoById(idProceso)
  if (!p) return false
  p.etapaActual = nuevaEtapa
  p.timeline.push({ etapa: nuevaEtapa, fecha: new Date().toLocaleString('es-BO'), usuario: window.Alpine?.store('auth')?.user || 'sistema' })
  return true
}

export function agregarObservacion(idProceso, obs) {
  const p = getProcesoById(idProceso)
  if (!p) return false
  p.observaciones.push({ texto: obs, fecha: new Date().toLocaleString('es-BO'), usuario: window.Alpine?.store('auth')?.user || 'sistema' })
  return true
}

export function asignarRevisores(idProceso, revisores) {
  const p = getProcesoById(idProceso)
  if (!p) return false
  p.revisores = revisores
  return true
}

export function asignarAprobadores(idProceso, aprobadores) {
  const p = getProcesoById(idProceso)
  if (!p) return false
  p.aprobadores = aprobadores
  return true
}
