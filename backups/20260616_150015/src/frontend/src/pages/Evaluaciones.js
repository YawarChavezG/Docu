/**
 * pages/Evaluaciones.js — Expediente de Evaluaciones y Controles de Lectura
 */
import { expedienteEvaluacionesDB } from '../data/evaluaciones.js'

function parseDMY(str) {
  if (!str || str === '—' || str === 'N/A') return null
  const [d, m, y] = str.split('/')
  if (!d || !m || !y) return null
  const fullYear = y.length === 2 ? (parseInt(y, 10) >= 26 ? '19' + y : '20' + y) : y
  return new Date(parseInt(fullYear, 10), parseInt(m, 10) - 1, parseInt(d, 10))
}

export const page = {
  init() {
    window.Alpine?.data('evalsPage', () => ({
      rows: expedienteEvaluacionesDB,
      q: '',
      filterTipoDifusion: '',
      filterEstado: '',
      filterResultado: '',
      filterFechaRealizacionDesde: '',
      filterFechaRealizacionHasta: '',
      filterFechaLimiteDesde: '',
      filterFechaLimiteHasta: '',

      get filtered() {
        return this.rows.filter(r => {
          const matchesQ = !this.q ||
            `${r.codigo} ${r.nombre}`.toLowerCase().includes(this.q.toLowerCase())
          const matchesTipo = !this.filterTipoDifusion || r.tipoDifusion === this.filterTipoDifusion
          const matchesEstado = !this.filterEstado || r.estado === this.filterEstado
          const matchesResultado = !this.filterResultado || r.resultado === this.filterResultado

          const fechaRealizacion = parseDMY(r.fechaRealizacion)
          const desdeRealizacion = this.filterFechaRealizacionDesde ? new Date(this.filterFechaRealizacionDesde) : null
          const hastaRealizacion = this.filterFechaRealizacionHasta ? new Date(this.filterFechaRealizacionHasta) : null
          const matchesFechaRealizacion =
            (!desdeRealizacion || (fechaRealizacion && fechaRealizacion >= desdeRealizacion)) &&
            (!hastaRealizacion || (fechaRealizacion && fechaRealizacion <= hastaRealizacion))

          const fechaLimite = parseDMY(r.fechaLimite)
          const desdeLimite = this.filterFechaLimiteDesde ? new Date(this.filterFechaLimiteDesde) : null
          const hastaLimite = this.filterFechaLimiteHasta ? new Date(this.filterFechaLimiteHasta) : null
          const matchesFechaLimite =
            (!desdeLimite || (fechaLimite && fechaLimite >= desdeLimite)) &&
            (!hastaLimite || (fechaLimite && fechaLimite <= hastaLimite))

          return matchesQ && matchesTipo && matchesEstado && matchesResultado && matchesFechaRealizacion && matchesFechaLimite
        })
      },

      get kpis() {
        const aprobadas = this.rows.filter(r => r.resultado === 'APROBADO' || r.resultado === 'LEÍDO').length
        const reprobadas = this.rows.filter(r => r.resultado === 'REPROBADO' || r.resultado === 'NO LEÍDO').length
        const pendientes = this.rows.filter(r => r.estado === 'PENDIENTE').length
        const conNota = this.rows.filter(r => r.nota !== null && r.nota !== undefined)
        const promedio = conNota.length
          ? Math.round(conNota.reduce((a, b) => a + b.nota, 0) / conNota.length)
          : 0
        return { aprobadas, reprobadas, pendientes, promedio }
      },

      get uniqueTipos() {
        return [...new Set(this.rows.map(r => r.tipoDifusion))]
      },
      get uniqueEstados() {
        return [...new Set(this.rows.map(r => r.estado))]
      },
      get uniqueResultados() {
        return [...new Set(this.rows.map(r => r.resultado))].filter(Boolean)
      },

      descargarExpediente() {
        window.toast && window.toast('Descargando expediente de evaluaciones...', 'info')
      },
    }))
  },

  template: /* html */`
<div x-data="evalsPage" class="animate-fade-in-page">

  <!-- Header -->
  <div class="flex items-start justify-between mb-5">
    <div>
      <h1 class="page-header">Evaluaciones y Controles de Lectura</h1>
      <p class="page-subtitle">Expediente completo de evaluaciones de conocimiento y confirmaciones de lectura</p>
    </div>
    <button @click="descargarExpediente" class="btn btn-primary">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Descargar mi expediente
    </button>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
    <div class="kpi-card">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Aprobadas</span>
        <div class="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
      </div>
      <div class="text-[26px] font-bold text-emerald-600 leading-none" x-text="kpis.aprobadas"></div>
      <div class="text-[10.5px] text-slate-400 mt-1">Evaluaciones aprobadas</div>
    </div>

    <div class="kpi-card-red">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Reprobadas</span>
        <div class="w-8 h-8 rounded-lg bg-red-50 border border-red-200 flex items-center justify-center text-red-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
        </div>
      </div>
      <div class="text-[26px] font-bold text-red-600 leading-none" x-text="kpis.reprobadas"></div>
      <div class="text-[10.5px] text-slate-400 mt-1">Evaluaciones reprobadas</div>
    </div>

    <div class="kpi-card-amber">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Pendientes</span>
        <div class="w-8 h-8 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
      </div>
      <div class="text-[26px] font-bold text-amber-600 leading-none" x-text="kpis.pendientes"></div>
      <div class="text-[10.5px] text-slate-400 mt-1">Evaluaciones + Lecturas</div>
    </div>

    <div class="kpi-card">
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Mi Promedio</span>
        <div class="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        </div>
      </div>
      <div class="text-[26px] font-bold text-brand-500 leading-none" x-text="kpis.promedio + '%'"></div>
      <div class="text-[10.5px] text-slate-400 mt-1">Promedio general</div>
    </div>
  </div>

  <!-- Tabla Maestra -->
  <div class="card-base overflow-hidden">
    <div class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th>
              Documento / Código
              <input x-model="q" type="text" placeholder="Buscar..." class="th-filter" />
            </th>
            <th>Fecha Lanzamiento</th>
            <th>
              Tipo Difusión
              <select x-model="filterTipoDifusion" class="th-filter">
                <option value="">Todos</option>
                <template x-for="t in uniqueTipos" :key="t">
                  <option :value="t" x-text="t"></option>
                </template>
              </select>
            </th>
            <th>
              Estado
              <select x-model="filterEstado" class="th-filter">
                <option value="">Todos</option>
                <template x-for="e in uniqueEstados" :key="e">
                  <option :value="e" x-text="e"></option>
                </template>
              </select>
            </th>
            <th class="text-center">Nota</th>
            <th>
              Resultado
              <select x-model="filterResultado" class="th-filter">
                <option value="">Todos</option>
                <template x-for="r in uniqueResultados" :key="r">
                  <option :value="r" x-text="r"></option>
                </template>
              </select>
            </th>
            <th>Tiempo</th>
            <th>
              Fecha Realización
              <div class="flex gap-1 mt-1.5">
                <input x-model="filterFechaRealizacionDesde" type="date" class="th-filter w-1/2" title="Desde" />
                <input x-model="filterFechaRealizacionHasta" type="date" class="th-filter w-1/2" title="Hasta" />
              </div>
            </th>
            <th>
              Fecha Límite
              <div class="flex gap-1 mt-1.5">
                <input x-model="filterFechaLimiteDesde" type="date" class="th-filter w-1/2" title="Desde" />
                <input x-model="filterFechaLimiteHasta" type="date" class="th-filter w-1/2" title="Hasta" />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <template x-for="row in filtered" :key="row.codigo + row.fechaLimite">
            <tr>
              <td>
                <div class="font-mono text-[11px] font-semibold text-slate-500" x-text="row.codigo"></div>
                <div class="text-[11.5px] text-slate-700 font-medium" x-text="row.nombre"></div>
              </td>
              <td x-text="row.fechaLanzamiento"></td>
              <td>
                <span class="badge"
                  :class="row.tipoDifusion === 'Evaluación' ? 'badge-blue' : 'badge-purple'"
                  x-text="row.tipoDifusion"></span>
              </td>
              <td>
                <span class="badge"
                  :class="row.estado === 'FINALIZADO' ? 'badge-green' : 'badge-amber'"
                  x-text="row.estado"></span>
              </td>
              <td class="text-center">
                <span x-show="row.nota !== null" class="text-[13px] font-bold"
                  :class="row.nota >= 70 ? 'text-emerald-600' : 'text-red-600'"
                  x-text="row.nota + '%'"></span>
                <span x-show="row.nota === null" class="text-slate-300 text-[11px]">—</span>
              </td>
              <td>
                <span class="badge"
                  :class="{
                    'badge-green':  row.resultado === 'APROBADO' || row.resultado === 'LEÍDO',
                    'badge-red':    row.resultado === 'REPROBADO' || row.resultado === 'NO LEÍDO',
                    'badge-gray':   row.resultado === '—'
                  }"
                  x-text="row.resultado"></span>
              </td>
              <td x-text="row.tiempo"></td>
              <td x-text="row.fechaRealizacion"></td>
              <td x-text="row.fechaLimite"></td>
            </tr>
          </template>
          <tr x-show="filtered.length === 0">
            <td colspan="9" class="text-center py-8 text-slate-400 text-[11.5px]">
              No se encontraron registros con los filtros aplicados.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</div>`
}
