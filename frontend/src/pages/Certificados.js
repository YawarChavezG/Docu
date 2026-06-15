/**
 * pages/Certificados.js — Mis Certificados Obtenidos
 */
import { certificadosDB } from '../data/evaluaciones.js'

export const page = {
  init() {
    window.Alpine?.data('certsPage', () => ({
      rows: certificadosDB,
      q: '',
      filterTipo: '',

      get filtered() {
        return this.rows.filter(r => {
          const matchesQ = !this.q ||
            `${r.codigo} ${r.documento}`.toLowerCase().includes(this.q.toLowerCase())
          const matchesTipo = !this.filterTipo || r.tipo === this.filterTipo
          return matchesQ && matchesTipo
        })
      },

      get uniqueTipos() {
        return [...new Set(this.rows.map(r => r.tipo))]
      },

      verCertificado(id) {
        window.location.hash = '#/certificado-imprimible?id=' + encodeURIComponent(id)
      },
    }))
  },

  template: /* html */`
<div x-data="certsPage" class="animate-fade-in-page">

  <div class="mb-5">
    <h1 class="page-header">Mis Certificados Obtenidos</h1>
    <p class="page-subtitle">Historial de evaluaciones y controles de lectura completados</p>
  </div>

  <div class="card-base overflow-hidden">
    <div class="overflow-x-auto">
      <table class="data-table">
        <thead>
          <tr>
            <th>
              Código
              <input x-model="q" type="text" placeholder="Buscar..." class="th-filter" />
            </th>
            <th>Documento / Capacitación</th>
            <th class="text-center">Nota</th>
            <th>Fecha Obtención</th>
            <th class="text-center">Acción</th>
          </tr>
        </thead>
        <tbody>
          <template x-for="row in filtered" :key="row.id">
            <tr>
              <td>
                <div class="font-mono text-[11px] font-semibold text-slate-500" x-text="row.codigo"></div>
              </td>
              <td>
                <div class="text-[11.5px] text-slate-700 font-medium" x-text="row.documento"></div>
                <div class="mt-0.5">
                  <span class="badge"
                    :class="row.tipo === 'Evaluación' ? 'badge-blue' : 'badge-purple'"
                    x-text="row.tipo"></span>
                  <span x-show="!row.valido" class="badge badge-gray ml-1">Vencido</span>
                </div>
              </td>
              <td class="text-center">
                <span x-show="row.nota !== null && row.nota !== undefined"
                  class="text-[13px] font-bold"
                  :class="row.nota >= 70 ? 'text-emerald-600' : 'text-red-600'"
                  x-text="row.nota + '%'"></span>
                <span x-show="row.nota === null || row.nota === undefined"
                  class="text-slate-300 text-[11px]">N/A</span>
              </td>
              <td x-text="row.fechaObtencion"></td>
              <td class="text-center">
                <button @click="verCertificado(row.id)" class="btn btn-sm btn-primary">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                  Ver mi certificado
                </button>
              </td>
            </tr>
          </template>
          <tr x-show="filtered.length === 0">
            <td colspan="5" class="text-center py-8 text-slate-400 text-[11.5px]">
              No se encontraron certificados con los filtros aplicados.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Info -->
  <div class="mt-5 bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2.5">
    <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
    <p class="text-[11.5px] text-amber-800 leading-relaxed m-0">
      Los certificados tienen la misma vigencia que el documento al que corresponden.
      Al vencer el documento, el certificado pasa a estado <strong>Vencido</strong> y deberá rendir una nueva evaluación.
    </p>
  </div>

</div>`
}
