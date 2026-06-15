/**
 * pages/ListaMaestra.js — Lista Maestra de Documentos
 * Campos en listaMaestraDB: ger, area, proc, tipo, cod, ver, tit, f_ap, f_ex, vig, est, ant, com, forms[], obsoleto
 */
import { listaMaestraDB } from '../data/documents.js'

export const page = {
  init() {
    window.Alpine?.data('listaMaestra', () => ({
      docs: listaMaestraDB,
      q: '',
      filterTipo: '',
      filterGer: '',
      filterVig: [],
      filterEst: [],
      expanded: {},
      showFiltroVig: false,
      showFiltroEst: false,

      get isETO() {
        return window.Alpine?.store('auth')?.role === 'eto'
      },

      get filtered() {
        const q = this.q.toLowerCase().trim()
        const fv = this.filterVig
        const fe = this.filterEst
        const ft = this.filterTipo
        const fg = this.filterGer
        return this.docs.filter(d => {
          if (!this.isETO && d.obsoleto) return false
          if (fv.length && !fv.includes(d.vig)) return false
          if (fe.length && !fe.includes(d.est)) return false
          if (ft && d.tipo !== ft) return false
          if (fg && d.ger !== fg) return false
          if (!q) return true
          return (
            d.cod.toLowerCase().includes(q) ||
            d.tit.toLowerCase().includes(q) ||
            d.ger.toLowerCase().includes(q) ||
            d.area.toLowerCase().includes(q)
          )
        })
      },

      get kpis() {
        const all = this.docs
        return {
          vigentes:  all.filter(d => d.vig === 'Vigente').length,
          porVencer: all.filter(d => d.vig === 'Por vencer').length,
          vencidos:  all.filter(d => d.vig === 'Vencido').length,
          enProceso: all.filter(d => ['En revisión','En liberación','En corrección','En elaboración'].includes(d.est)).length,
          obsoletos: all.filter(d => d.obsoleto).length,
        }
      },

      toggleVig(v) {
        const i = this.filterVig.indexOf(v)
        if (i === -1) this.filterVig.push(v); else this.filterVig.splice(i, 1)
      },
      toggleEst(v) {
        const i = this.filterEst.indexOf(v)
        if (i === -1) this.filterEst.push(v); else this.filterEst.splice(i, 1)
      },
      togRow(id) {
        this.expanded[id] = !this.expanded[id]
      },

      vigBadgeClass(v) {
        return ({
          'Vigente':    'badge-green',
          'Por vencer': 'badge-amber',
          'Vencido':    'badge-red',
          'Obsoleto':   'badge-red',
        })[v] || 'badge-gray'
      },

      estBadgeClass(e) {
        return ({
          'Aprobado':      'badge-green',
          'En revisión':   'badge-blue',
          'En liberación': 'badge-amber',
          'En corrección': 'badge-red',
          'En elaboración':'badge-purple',
          'Obsoleto':      'badge-red',
        })[e] || 'badge-gray'
      },

      verDoc(d) {
        if (this.isETO) {
          window.toast('🖊️ Abriendo ' + d.cod + ' en Office 365 (modo edición)...', 'info')
        } else {
          window.pdfViewer?.abrir({
            cod: d.cod, titulo: d.tit,
            tipo: d.vig === 'Obsoleto' ? 'obsoleto' : 'original',
            esVencido: d.vig === 'Vencido',
            esObsoleto: d.vig === 'Obsoleto',
            marcaAgua: d.vig === 'Vencido' ? 'VENCIDO' : d.vig === 'Obsoleto' ? 'OBSOLETO' : null,
            returnRoute: '/lista',
          })
        }
      },
      verDocUser(d) {
        window.pdfViewer?.abrir({
          cod: d.cod, titulo: d.tit,
          tipo: d.vig === 'Obsoleto' ? 'obsoleto' : 'original',
          esVencido: d.vig === 'Vencido',
          esObsoleto: d.vig === 'Obsoleto',
          marcaAgua: d.vig === 'Vencido' ? 'VENCIDO' : d.vig === 'Obsoleto' ? 'OBSOLETO' : null,
          returnRoute: '/lista',
        })
      },
      genCV(d) {
        // Unificamos: enviamos la orden al visor y que él decida si mostrar alerta
        window.pdfViewer?.abrir({
          cod: d.cod,
          titulo: d.tit,
          tipo: 'VISUALIZACION',
          esVencido: d.vig === 'Vencido',
          esObsoleto: d.vig === 'Obsoleto',
          marcaAgua: d.vig === 'Vencido' ? 'VENCIDO' : d.vig === 'Obsoleto' ? 'OBSOLETO' : null,
          returnRoute: '/lista',
        })
      },

      irAModuloCopias(tipo, d) {
        sessionStorage.setItem('moduloCopiasConfig', JSON.stringify({
          tipo: tipo === 'cc' ? 'CONTROLADA' : 'NO CONTROLADA',
          cod: d.cod,
          tit: d.tit,
          ver: d.ver,
        }))
        window.location.hash = '#/modulo-copias'
      },
    }))
  },

  template: /* html */`
<div x-data="listaMaestra" @click.outside="showFiltroVig=false;showFiltroEst=false" class="animate-fade-in-page">

  <!-- Header -->
  <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Lista Maestra de Documentos</h1>
      <p class="page-subtitle">Repositorio documental oficial de COFAR</p>
    </div>
    <button class="btn btn-sm" @click="window.toast('Exportando lista maestra...','info')">↓ Exportar</button>
  </div>

  <!-- KPIs -->
  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
    <div class="kpi-card">
      <div class="metric-value text-slate-800" x-text="kpis.vigentes"></div>
      <div class="metric-label">Documentos vigentes</div>
      <div class="metric-sub">+12 este mes</div>
    </div>
    <div class="kpi-card-amber">
      <div class="metric-value text-amber-600" x-text="kpis.porVencer"></div>
      <div class="metric-label">Por vencer (30 días)</div>
      <div class="metric-sub">requieren renovación</div>
    </div>
    <div class="kpi-card-red">
      <div class="metric-value text-red-600" x-text="kpis.vencidos"></div>
      <div class="metric-label">Documentos vencidos</div>
      <div class="metric-sub">renovación inmediata</div>
    </div>
    <div class="kpi-card">
      <div class="metric-value text-slate-800" x-text="kpis.enProceso"></div>
      <div class="metric-label">En proceso (flujo)</div>
      <div class="metric-sub">pendientes de acción</div>
    </div>
    <div x-show="isETO" class="kpi-card bg-slate-50">
      <div class="metric-value text-slate-500" x-text="kpis.obsoletos"></div>
      <div class="metric-label text-slate-500">Obsoletos</div>
      <div class="metric-sub">solo gestor</div>
    </div>
  </div>

  <!-- Filtros barra -->
  <div class="flex gap-2 mb-3 flex-wrap">
    <div class="relative flex-1 min-w-[180px]">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"/></svg>
      <input type="search" class="form-input pl-8 text-xs" placeholder="Buscar código, título, área…" x-model="q">
    </div>
    <select class="form-input text-xs w-auto" x-model="filterTipo">
      <option value="">Todos los tipos</option>
      <option>Procedimiento</option><option>Instructivo</option><option>Formulario</option>
      <option>Metodología</option><option>Manual</option><option>Política</option>
    </select>
    <select class="form-input text-xs w-auto" x-model="filterGer">
      <option value="">Todas las gerencias</option>
      <option>CALIDAD</option><option>PRODUCCIÓN</option><option>LOGÍSTICA</option>
      <option>RRHH</option><option>GERENCIA</option>
    </select>
  </div>

  <!-- Tabla -->
  <div class="card-base p-0 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="data-table min-w-[1200px]">
        <thead>
          <tr>
            <th class="w-8 text-center"></th>
            <th>Gerencia</th>
            <th>Área</th>
            <th>Proceso</th>
            <th>Tipo</th>
            <th>Código</th>
            <th class="text-center w-10">Ver.</th>
            <th class="min-w-[200px]">Título</th>
            <th class="text-center w-[90px]">Aprobación</th>
            <th class="text-center w-[90px]">Expira</th>

            <!-- Vigencia con filtro checkbox -->
            <th class="min-w-[110px] relative">
              <div class="flex items-center gap-1.5 cursor-pointer text-brand-600 whitespace-nowrap pr-1" @click.stop="showFiltroVig=!showFiltroVig;showFiltroEst=false">
                <span class="text-[10px] font-semibold uppercase tracking-wider">Vigencia</span>
                <span class="text-[9px]">▼</span>
                <span x-show="filterVig.length" class="ml-auto w-3.5 h-3.5 bg-brand-600 text-white rounded-full text-[8px] flex items-center justify-center font-bold" x-text="filterVig.length"></span>
              </div>
              <div x-show="showFiltroVig" @click.stop class="absolute top-full left-0 z-50 bg-white border border-slate-200 rounded-lg p-2 shadow-lg min-w-[160px] flex flex-col gap-1">
                <template x-for="v in ['Vigente','Por vencer','Vencido','Obsoleto']" :key="v">
                  <label class="flex items-center gap-1.5 text-[11px] font-medium text-slate-800 cursor-pointer px-1 py-0.5">
                    <input type="checkbox" :value="v" :checked="filterVig.includes(v)" @change="toggleVig(v)" class="accent-brand-600">
                    <span x-text="v"></span>
                  </label>
                </template>
                <button class="btn btn-sm mt-1 text-[10px]" @click="filterVig=[];showFiltroVig=false">Limpiar</button>
              </div>
            </th>

            <!-- Estatus con filtro checkbox -->
            <th class="min-w-[130px] relative">
              <div class="flex items-center gap-1.5 cursor-pointer text-brand-600 whitespace-nowrap pr-1" @click.stop="showFiltroEst=!showFiltroEst;showFiltroVig=false">
                <span class="text-[10px] font-semibold uppercase tracking-wider">Estatus</span>
                <span class="text-[9px]">▼</span>
                <span x-show="filterEst.length" class="ml-auto w-3.5 h-3.5 bg-brand-600 text-white rounded-full text-[8px] flex items-center justify-center font-bold" x-text="filterEst.length"></span>
              </div>
              <div x-show="showFiltroEst" @click.stop class="absolute top-full left-0 z-50 bg-white border border-slate-200 rounded-lg p-2 shadow-lg min-w-[160px] flex flex-col gap-1">
                <template x-for="e in ['Aprobado','En revisión','En liberación','En corrección','En elaboración','Obsoleto']" :key="e">
                  <label class="flex items-center gap-1.5 text-[11px] font-medium text-slate-800 cursor-pointer px-1 py-0.5">
                    <input type="checkbox" :value="e" :checked="filterEst.includes(e)" @change="toggleEst(e)" class="accent-brand-600">
                    <span x-text="e"></span>
                  </label>
                </template>
                <button class="btn btn-sm mt-1 text-[10px]" @click="filterEst=[];showFiltroEst=false">Limpiar</button>
              </div>
            </th>

            <th class="w-[90px]">Ant.</th>
            <th x-show="isETO" class="w-[160px]">Comentarios ETO</th>
            <th class="text-center w-[130px]">Acción</th>
          </tr>
        </thead>
          <template x-for="d in filtered" :key="d.id">
            <tbody class="border-b border-slate-100">
              <!-- Fila principal -->
              <tr :class="d.obsoleto ? 'opacity-75 bg-slate-50' : ''" class="transition-colors duration-100 hover:bg-blue-50/40">
                <td class="text-center">
                  <button x-show="d.forms && d.forms.length > 0" @click="togRow(d.id)"
                          class="w-5 h-5 rounded border border-slate-200 bg-slate-50 inline-flex items-center justify-center text-[11px] hover:bg-blue-50 hover:border-brand-500 transition-all">
                    <span x-text="expanded[d.id] ? '−' : '+'"></span>
                  </button>
                </td>
                <td class="text-[10.5px] text-slate-600 font-medium" x-text="d.ger"></td>
                <td class="text-[10.5px] text-slate-500" x-text="d.area"></td>
                <td class="text-[10.5px] text-slate-500" x-text="d.proc"></td>
                <td>
                  <span class="badge badge-gray text-[10px]" x-text="d.tipo"></span>
                </td>
                <td class="font-mono font-bold text-brand-600 text-[11px]" x-text="d.cod"></td>
                <td class="text-center font-mono text-[11px] text-slate-500" x-text="d.ver"></td>
                <td class="text-[11.5px] font-medium text-slate-800" x-text="d.tit"></td>
                <td class="text-center text-[10.5px] text-slate-500" x-text="d.f_ap"></td>
                <td class="text-center text-[10.5px]" :class="(d.vig==='Vencido'||d.vig==='Por vencer') ? 'text-red-600 font-semibold' : 'text-slate-500'" x-text="d.f_ex"></td>

                <!-- Vigencia pill -->
                <td>
                  <span class="badge" :class="vigBadgeClass(d.vig)" x-text="d.vig"></span>
                </td>

                <!-- Estatus pill + toggle ETO -->
                <td>
                  <div class="flex items-center gap-1">
                    <span class="badge" :class="estBadgeClass(d.est)" x-text="d.est"></span>
                    <button x-show="isETO && (d.vig==='Vigente'||d.vig==='Obsoleto')"
                            @click="window.obsolescenciaModal?.abrir(d)" title="Cambiar Estado"
                            class="w-[18px] h-[18px] rounded border border-slate-200 bg-slate-50 inline-flex items-center justify-center text-[10px] hover:bg-blue-50 transition-colors">
                      ⇄
                    </button>
                  </div>
                </td>

                <td class="text-[10.5px] text-slate-500 font-mono" x-text="d.ant||'N/A'"></td>
                <td x-show="isETO" class="text-[10.5px] text-red-600 italic" x-text="d.com||'—'"></td>

                <!-- Acciones -->
                <td class="text-center">
                  <template x-if="isETO">
                    <div class="flex items-center justify-center gap-1 flex-nowrap">
                      <button @click="verDoc(d)" class="btn btn-sm py-0.5 px-1.5 text-[10px] whitespace-nowrap" title="Abrir en Office 365">⊙ Ver</button>
                      <button @click="genCV(d)" class="btn btn-sm py-0.5 px-1.5 text-[10px] bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100" title="Copia de Visualización (PDF)">CV</button>
                      <button @click="irAModuloCopias('cc', d)" x-show="!d.obsoleto" class="btn btn-sm py-0.5 px-1.5 text-[10px] bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100" title="Generar Copia Controlada">CC</button>
                      <button @click="irAModuloCopias('cn', d)" x-show="!d.obsoleto" class="btn btn-sm py-0.5 px-1.5 text-[10px] bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100" title="Generar Copia No Controlada">CN</button>
                    </div>
                  </template>
                  <template x-if="!isETO">
                    <button @click="verDocUser(d)" class="btn btn-sm">⊙ Ver</button>
                  </template>
                </td>
              </tr>

              <!-- Accordion: formularios -->
              <tr x-show="expanded[d.id] && d.forms && d.forms.length > 0">
                <td colspan="16" class="p-0 bg-slate-50 border-b border-slate-200">
                  <div class="py-2.5 pl-12 pr-4 flex flex-col gap-1.5">
                    <div class="flex items-center gap-2.5 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-[11px]">
                      <span class="badge badge-blue text-[10px]">DOCUMENTO ORIGINAL</span>
                      <span class="font-mono font-bold text-brand-600" x-text="d.cod"></span>
                      <button @click="verDoc(d)" class="btn btn-sm text-[10px] py-0.5 px-2">⊙ Visualizar original</button>
                    </div>
                    <template x-for="f in d.forms" :key="f">
                      <div class="flex items-center gap-2.5 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] ml-3">
                        <span class="badge badge-gray text-[10px]">FORMULARIO</span>
                        <span class="font-mono text-[11px] text-slate-500" x-text="d.cod+'/'+f"></span>
                        <button @click="window.toast('⬇️ Descargando '+d.cod+'/'+f+'...','success')" class="btn btn-sm text-[10px] py-0.5 px-2 ml-auto">⬇ Descargar</button>
                      </div>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </template>

          <tbody x-show="filtered.length===0">
            <tr>
              <td colspan="16" class="text-center py-10 text-slate-400 italic">
                No hay documentos con los filtros aplicados.
              </td>
            </tr>
          </tbody>
      </table>
    </div>
  </div>

  <!-- Footer pagination -->
  <div class="flex justify-between items-center mt-3 flex-wrap gap-2">
    <span class="text-[10.5px] text-slate-400" x-text="'Mostrando '+filtered.length+' de '+docs.length+' documentos'"></span>
    <div class="flex gap-1">
      <button class="btn btn-sm">← Ant</button>
      <button class="btn btn-sm btn-primary">1</button>
      <button class="btn btn-sm">2</button>
      <button class="btn btn-sm">Sig →</button>
    </div>
  </div>

</div>`
}
