/**
 * src/store/flow.js
 * Alpine store para el estado global del flujo documental.
 * Fuente de verdad compartida entre liberación, revisión, corrección y bandeja.
 *
 * Registro: Alpine.store('flow', flowStore)
 * Uso en templates: $store.flow.procesoActivo
 * Uso en JS: Alpine.store('flow').avanzarEtapa(id, etapa)
 */

import { procesosFlujoDB } from '../data/procesosFlujo.js'

export const flowStore = {

  /* ─── State ─────────────────────────────────────────────── */
  procesos: [...procesosFlujoDB],
  procesoActivo: null,   // id del proceso seleccionado

  /* ─── Selectors ─────────────────────────────────────────── */

  getProcesoById(id) {
    return this.procesos.find(p => p.id === id) || null
  },

  getProcesoByCodigo(codigo) {
    return this.procesos.find(p => p.codigo === codigo) || null
  },

  get procesoActivoData() {
    return this.procesoActivo ? this.getProcesoById(this.procesoActivo) : null
  },

  /* ─── Actions ───────────────────────────────────────────── */

  seleccionarProceso(id) {
    this.procesoActivo = id
  },

  crearProceso(datos = {}) {
    const nuevo = {
      id: `P-${Date.now()}`,
      codigo: datos.codigo || '',
      nombre: datos.nombre || '',
      version: datos.version || '01',
      elaborador: datos.elaborador || '',
      gerencia: datos.gerencia || '',
      area: datos.area || '',
      tipo: datos.tipo || '',
      etapaActual: datos.etapaActual || 'Creación',
      revisores: [],
      aprobadores: [],
      observaciones: [],
      timeline: [],
      estado: 'Pendiente',
      fechaCreacion: new Date().toLocaleDateString('es-BO'),
      fechaLiberacion: null,
      fechaAprobacion: null,
      ...datos,
    }
    this.procesos.push(nuevo)
    return nuevo.id
  },

  avanzarEtapa(idProceso, nuevaEtapa) {
    const p = this.getProcesoById(idProceso)
    if (!p) return false
    p.etapaActual = nuevaEtapa
    p.timeline.push({
      etapa: nuevaEtapa,
      fecha: new Date().toLocaleString('es-BO'),
      usuario: window.Alpine?.store('auth')?.user?.name || 'sistema',
    })
    if (nuevaEtapa === 'Liberado') p.fechaLiberacion = new Date().toLocaleDateString('es-BO')
    if (nuevaEtapa === 'Aprobado') p.fechaAprobacion = new Date().toLocaleDateString('es-BO')
    return true
  },

  agregarObservacion(idProceso, obs) {
    const p = this.getProcesoById(idProceso)
    if (!p) return false
    p.observaciones.push({
      texto: obs,
      fecha: new Date().toLocaleString('es-BO'),
      usuario: window.Alpine?.store('auth')?.user?.name || 'sistema',
    })
    return true
  },

  asignarRevisores(idProceso, revisores) {
    const p = this.getProcesoById(idProceso)
    if (!p) return false
    p.revisores = revisores
    return true
  },

  asignarAprobadores(idProceso, aprobadores) {
    const p = this.getProcesoById(idProceso)
    if (!p) return false
    p.aprobadores = aprobadores
    return true
  },
}
