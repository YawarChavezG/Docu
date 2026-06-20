/**
 * pages/MonitorCC.js — Monitor de Copias Controladas (US-7.05)
 * Refactorizado Fase 3 - Lote 7
 */
import { monitorCCDB } from '../data/copias.js'

export const page = {
  init() {
    window.Alpine?.data('monitorCCPage', () => ({
      items: monitorCCDB,
      q: { id: '', cod: '', ver: '', doc: '', dest: '' },
      fechaDesde: '',
      fechaHasta: '',
      filterEstado: [],
      showFilterEstado: false,

      get filtered() {
        return this.items.filter(r => {
          const matchId = !this.q.id || String(r.id).includes(this.q.id)
          const matchCod = !this.q.cod || r.codigo.toLowerCase().includes(this.q.cod.toLowerCase())
          const matchVer = !this.q.ver || r.ver.includes(this.q.ver)
          const matchDoc = !this.q.doc || r.doc.toLowerCase().includes(this.q.doc.toLowerCase())
          const matchDest = !this.q.dest || r.destinatario.toLowerCase().includes(this.q.dest.toLowerCase())
          const matchEstado = !this.filterEstado.length || this.filterEstado.includes(r.estado)
          const matchFecha = (!this.fechaDesde || r.fechaEntregaIso >= this.fechaDesde) &&
                             (!this.fechaHasta || r.fechaEntregaIso <= this.fechaHasta)
          return matchId && matchCod && matchVer && matchDoc && matchDest && matchEstado && matchFecha
        })
      },

      estadoBadge(e) {
        return { Generado: 'badge-amber', Entregado: 'badge-blue', Devuelto: 'badge-green' }[e] || 'badge-default'
      },

      puedeDevolver(r) {
        return r.estado === 'Generado' || r.estado === 'Entregado'
      },

      iniciarDevolucion(item) {
        window.authDevolucionModal?.abrir({
          docInfo: item.codigo + ' — ' + item.doc,
          destinatario: item.destinatario,
          hideSignatureWarning: true,
          onConfirm: () => {
            item.estado = 'Devuelto'
            item.fechaDevolucion = new Date().toLocaleDateString('es-BO') + ' ' + new Date().toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' })
            window.toast('✅ Devolución confirmada. Firma digital registrada.', 'success')
          }
        })
      }
    }))
  },

  template: /* html */`
<div x-data="monitorCCPage" class="animate-fade-in-page">

  <!-- Header -->
  <div class="flex items-center justify-between mb-3.5 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Monitor de Copias Controladas</h1>
      <p class="page-subtitle">Ciclo de vida completo de copias físicas controladas</p>
    </div>
    <button class="btn btn-sm" @click="$toast('Exportando a Excel...','info')">↓ Exportar Excel</button>
  </div>

  <!-- Filtros de Fecha -->
  <div class="flex items-center gap-2 flex-wrap mb-3">
    <span class="text-[11px] text-slate-500">Entregado desde:</span>
    <input type="date" class="form-input text-[11px] px-2 py-1 w-[130px]" x-model="fechaDesde">
    <span class="text-[11px] text-slate-500">hasta:</span>
    <input type="date" class="form-input text-[11px] px-2 py-1 w-[130px]" x-model="fechaHasta">
    <button x-show="fechaDesde || fechaHasta" class="btn btn-sm btn-ghost text-[10px]" @click="fechaDesde='';fechaHasta=''">Limpiar fechas</button>
  </div>

  <!-- Tabla -->
  <div class="card-base p-0 overflow-hidden">
    <div class="flex items-center justify-between px-3.5 py-2.5 border-b border-slate-100">
      <span class="text-[10.5px] font-bold text-slate-600 uppercase tracking-widest">Registros de Copias Controladas</span>
      <span class="text-[10px] text-slate-400 font-normal normal-case" x-text="filtered.length + ' de ' + items.length + ' registros'"></span>
    </div>

    <div class="overflow-x-auto">
      <table class="data-table min-w-[900px]">
        <thead>
          <tr>
            <th style="width: 60px;">
              <div class="flex flex-col gap-1.5">
                <span>ID</span>
                <input type="text" x-model="q.id" class="form-input text-[10px] px-2 py-1 font-normal normal-case" placeholder="Buscar...">
              </div>
            </th>
            <th style="width: 140px;">
              <div class="flex flex-col gap-1.5">
                <span>CÓDIGO</span>
                <input type="text" x-model="q.cod" class="form-input text-[10px] px-2 py-1 font-normal normal-case" placeholder="Buscar código...">
              </div>
            </th>
            <th class="text-center" style="width: 60px;">
              <div class="flex flex-col gap-1.5">
                <span>VER.</span>
                <input type="text" x-model="q.ver" class="form-input text-[10px] px-2 py-1 font-normal normal-case text-center" placeholder="Ver.">
              </div>
            </th>
            <th>
              <div class="flex flex-col gap-1.5">
                <span>DOCUMENTO</span>
                <input type="text" x-model="q.doc" class="form-input text-[10px] px-2 py-1 font-normal normal-case" placeholder="Buscar documento...">
              </div>
            </th>
            <th class="text-center" style="width: 120px;">F. ENTREGADA</th>
            <th style="width: 90px;">ORIGEN</th>
            <th>
              <div class="flex flex-col gap-1.5">
                <span>DESTINATARIO</span>
                <input type="text" x-model="q.dest" class="form-input text-[10px] px-2 py-1 font-normal normal-case" placeholder="Buscar...">
              </div>
            </th>
            <th class="relative" style="width: 120px;">
              <div class="flex items-center gap-1 cursor-pointer hover:text-brand-600 transition-colors" @click.stop="showFilterEstado=!showFilterEstado">
                ESTADO <span class="text-[9px]">▼</span>
                <span x-show="filterEstado.length" class="w-4 h-4 bg-brand-600 text-white rounded-full text-[9px] flex items-center justify-center font-bold" x-text="filterEstado.length"></span>
              </div>
              <div x-show="showFilterEstado" @click.stop @click.outside="showFilterEstado=false" class="absolute top-full left-0 z-50 bg-white border border-slate-200 rounded-lg p-2 shadow-lg min-w-[160px] flex flex-col gap-1 font-normal normal-case">
                <template x-for="v in ['Generado','Entregado','Devuelto']" :key="v">
                  <label class="flex items-center gap-1.5 text-[11px] font-medium text-slate-800 cursor-pointer px-1 py-0.5 hover:bg-slate-50 rounded">
                    <input type="checkbox" :value="v" x-model="filterEstado" class="accent-brand-600">
                    <span x-text="v"></span>
                  </label>
                </template>
                <button class="btn btn-sm mt-1 text-[10px]" @click="filterEstado=[];showFilterEstado=false">Limpiar</button>
              </div>
            </th>
            <th class="text-center" style="width: 120px;">F. DEVOLUCIÓN</th>
            <th class="text-center" style="width: 90px;">DEVOLUCIÓN</th>
            <th class="text-center" style="width: 80px;">ACCIÓN</th>
          </tr>
        </thead>
        <tbody>
          <template x-for="(r, index) in filtered" :key="r.id || index">
            <tr class="hover:bg-brand-50/40 transition-colors">
              <td class="table-cell-mono font-bold text-slate-500" x-text="r.id"></td>
              <td class="table-cell-mono font-bold text-brand-600" x-text="r.codigo"></td>
              <td class="text-center table-cell-mono text-slate-600" x-text="r.ver"></td>
              <td class="text-[11.5px] font-medium text-slate-700" x-text="r.doc"></td>
              <td class="text-center text-xs text-slate-500" x-text="r.fechaEntregada"></td>
              <td class="text-[11px] text-slate-500" x-text="r.origen"></td>
              <td class="text-[11.5px] font-medium text-slate-700" x-text="r.destinatario"></td>
              <td><span :class="'badge ' + estadoBadge(r.estado)" x-text="r.estado"></span></td>
              <td class="text-center text-xs text-slate-500" x-text="r.fechaDevolucion"></td>
              <td class="text-center">
                <template x-if="r.estado === 'Devuelto'">
                  <span class="text-base text-emerald-600">✅</span>
                </template>
                <template x-if="puedeDevolver(r)">
                  <input type="checkbox" @change="$event.target.checked && iniciarDevolucion(r); $event.target.checked = false" class="w-4 h-4 cursor-pointer accent-brand-600">
                </template>
              </td>
              <td class="text-center">
                <button @click="window.pdfViewer?.abrir({cod:r.codigo,titulo:r.doc,tipo:'CONTROLADA',esVencido:false,esObsoleto:false,returnRoute:'/copias-cc'})" class="px-2 py-0.5 text-[10px] font-bold rounded border border-brand-200 bg-brand-50 text-brand-600 hover:bg-brand-100 transition-colors">⊙ Mostrar</button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</div>`
}
