/**
 * pages/Publicacion.js — Monitor de Evaluaciones / Controles (US-6.01)
 */
import { publicacionesDB } from '../data/documents.js'
import { expedientePersonalDB, detalleAlcanceDB } from '../data/evaluaciones.js'

export const page = {
  init() {
    window.Alpine?.data('publicacionPage', () => ({
      // ── Tabla principal ───────────────────────────
      items: publicacionesDB.map((r, idx) => ({ id: idx + 1, ...r })),
      q: '',
      filterCodigo: '',
      filterNombre: '',
      filterTipo: [],
      filterEstado: [],
      showFilterTipo: false,
      showFilterEstado: false,

      get filtrados() {
        return this.items.filter(r => {
          const matchCodigo = !this.filterCodigo || r.codigo.toLowerCase().includes(this.filterCodigo.toLowerCase())
          const matchNombre = !this.filterNombre || r.nombre.toLowerCase().includes(this.filterNombre.toLowerCase())
          const matchTipo = !this.filterTipo.length || this.filterTipo.includes(r.tipo)
          const matchEstado = !this.filterEstado.length || this.filterEstado.includes(r.estado)
          return matchCodigo && matchNombre && matchTipo && matchEstado
        })
      },

      // ── Expediente de Personal ────────────────────
      expedienteQ: '',
      mostrarExpediente: false,
      expedienteResultado: null,

      buscarExpediente() {
        const qq = this.expedienteQ.trim().toLowerCase()
        if (!qq) {
          this.mostrarExpediente = false
          this.expedienteResultado = null
          return
        }
        const found = expedientePersonalDB.find(e =>
          e.nombre.toLowerCase().includes(qq) ||
          e.codigo.toLowerCase().includes(qq) ||
          e.cargo.toLowerCase().includes(qq)
        )
        this.expedienteResultado = found || null
        this.mostrarExpediente = true
      },

      limpiarExpediente() {
        this.expedienteQ = ''
        this.mostrarExpediente = false
        this.expedienteResultado = null
      },

      // ── Evento global: Re-abrir difusión desde modal ──
      reabrirDifusion({ detail }) {
        const original = this.items.find(i => i.codigo === detail.docCodigo)
        const fmt = d => d ? new Date(d + 'T00:00:00').toLocaleDateString('es-ES', { day:'2-digit', month:'2-digit', year:'2-digit' }).replace(/\//g, '/') : '—'

        const nuevo = {
          id: Date.now(),
          codigo: detail.docCodigo,
          nombre: detail.docNombre,
          fechaLanz: fmt(detail.fechaInicio),
          fechaFin: fmt(detail.fechaLimite),
          tipo: original?.tipo ?? 'Evaluación',
          estado: 'Pendiente',
          alcance: '0/0',
          prom: '—',
          btnEnabled: true,
          isNew: true
        }

        this.items.unshift(nuevo)
        this.items = [...this.items]
        const nuevoId = nuevo.id
        setTimeout(() => {
          const target = this.items.find(i => i.id === nuevoId)
          if (target) target.isNew = false
        }, 3000)
        window.toast(`🔄 Nuevo ciclo creado para ${detail.docCodigo} con estado Pendiente.`, 'success')
      },

      // ── Helpers ───────────────────────────────────
      estadoBadge(e) {
        return { Pendiente:'badge-blue', Finalizado:'badge-green', Cancelado:'badge-red' }[e] || 'badge-amber'
      },
      tipoBadge(t) {
        return { 'Evaluación':'badge-blue', 'Control Lectura':'badge-amber', 'Sin Control':'badge-default' }[t] || 'badge-default'
      },
      promColor(p) {
        if (p === 'N/A' || p === '—') return 'text-slate-400'
        return parseInt(p) >= 70 ? 'text-emerald-600' : 'text-red-600'
      },
      notaEsEnlace() {
        const auth = window.Alpine?.store('auth')
        return auth?.role === 'eto'
      },

      // ── Acciones ──────────────────────────────────
      abrirAlcance(r) {
        const datos = detalleAlcanceDB[r.codigo] || [
          { id:1, nombre:'Sin datos', cargo:'—', area:'—', est:'PENDIENTE', nota:'—', fecha:'—', tiempo:'—' }
        ]
        window.alcanceModal?.abrir({
          codigo: r.codigo,
          nombre: r.nombre,
          tipo: r.tipo,
          datos: datos.map(d => ({...d, estadoClase: d.est==='APROBADO'?'badge-green':d.est==='REPROBADO'?'badge-red':'badge-amber'}))
        })
      },

      abrirRespuestas(reg) {
        if (!this.notaEsEnlace()) return
        const key = reg.doc + '_' + (this.expedienteResultado?.nombre ?? '')
        window.respuestasExamenModal?.abrir({ key })
      },

      cancelar(r) {
        window.authModal?.abrir({
          titulo: '✕ Cancelar Lanzamiento',
          icono: '✕',
          mensaje: `Va a cancelar el lanzamiento de "${r.nombre}". Esta acción detendrá la difusión activa.`,
          onSuccess: () => {
            r.estado = 'Cancelado'
            window.toast('✅ Lanzamiento cancelado correctamente.', 'warn')
          }
        })
      },

      reactivar(r) {
        r.estado = 'Pendiente'
        window.toast('✅ Lanzamiento reactivado.', 'success')
      },
    }))
  },

  template: /* html */`
<div x-data="publicacionPage" class="animate-fade-in-page" @reabrir-difusion.window="reabrirDifusion($event)">

  <!-- Header -->
  <div class="flex items-center justify-between mb-3.5 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Monitor de Evaluaciones / Controles</h1>
      <p class="page-subtitle">Seguimiento global de difusiones documentales y lanzamientos</p>
    </div>
    <button class="btn btn-sm" @click="$toast('Exportando reporte consolidado...','info')">↓ Excel Global</button>
  </div>

  <!-- Buscador de Expediente -->
  <div class="card-base mb-3">
    <div class="flex items-center gap-2 flex-wrap">
      <div class="relative flex-1 min-w-[240px]">
        <input class="form-input w-full pl-3 pr-9 text-xs" placeholder="Buscar expediente de personal (nombre, código, cargo)..."
               x-model="expedienteQ" @keydown.enter="buscarExpediente()">
        <span class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 text-xs">🔍</span>
      </div>
      <button class="btn btn-sm" @click="buscarExpediente()">Buscar</button>
      <button class="btn btn-sm btn-ghost" @click="limpiarExpediente()" x-show="mostrarExpediente">Limpiar</button>
    </div>
  </div>

  <!-- ═══ EXPEDIENTE DE PERSONAL ═══ -->
  <div x-show="mostrarExpediente" x-transition class="mb-4">
    <div x-show="!expedienteResultado" class="card-base text-center text-slate-500 text-sm py-8">
      No se encontró ningún empleado con ese criterio.
    </div>

    <template x-if="expedienteResultado">
      <div class="space-y-3">
        <!-- Card del empleado -->
        <div class="card-base flex items-center gap-4 flex-wrap">
          <div class="w-12 h-12 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center text-lg font-bold"
               x-text="expedienteResultado.nombre.split(' ').map(n=>n[0]).join('').substring(0,2)"></div>
          <div>
            <div class="text-sm font-bold text-slate-800" x-text="expedienteResultado.nombre"></div>
            <div class="text-[11px] text-slate-500" x-text="expedienteResultado.codigo + ' · ' + expedienteResultado.cargo + ' · ' + expedienteResultado.area"></div>
          </div>
          <div class="ml-auto flex gap-3">
            <div class="text-center px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-200">
              <div class="text-lg font-extrabold text-brand-600" x-text="expedienteResultado.historial.length"></div>
              <div class="text-[10px] text-slate-500 uppercase tracking-wide">Registros</div>
            </div>
            <div class="text-center px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-200">
              <div class="text-lg font-extrabold text-emerald-600"
                   x-text="expedienteResultado.historial.filter(h=>h.estado==='APROBADO').length"></div>
              <div class="text-[10px] text-slate-500 uppercase tracking-wide">Aprobados</div>
            </div>
            <div class="text-center px-3 py-1.5 bg-slate-50 rounded-lg border border-slate-200">
              <div class="text-lg font-extrabold text-red-500"
                   x-text="expedienteResultado.historial.filter(h=>h.estado==='REPROBADO').length"></div>
              <div class="text-[10px] text-slate-500 uppercase tracking-wide">Reprobados</div>
            </div>
          </div>
        </div>

        <!-- Tabla historial -->
        <div class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>Documento</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th class="w-[100px] text-center">Nota</th>
                <th class="w-[100px] text-center">Fecha</th>
                <th class="w-[100px] text-center">Tiempo</th>
              </tr>
            </thead>
            <tbody>
              <template x-for="reg in expedienteResultado.historial" :key="reg.doc + reg.fecha">
                <tr>
                  <td class="table-cell-mono font-semibold text-brand-600" x-text="reg.doc"></td>
                  <td><span :class="'badge ' + tipoBadge(reg.tipo)" x-text="reg.tipo"></span></td>
                  <td>
                    <span :class="'badge ' + (reg.estado==='APROBADO'?'badge-green':reg.estado==='REPROBADO'?'badge-red':'badge-blue')" x-text="reg.estado"></span>
                  </td>
                  <td class="w-[100px] text-center">
                    <template x-if="reg.nota !== null && notaEsEnlace()">
                      <a href="#" class="text-brand-500 hover:underline cursor-pointer font-semibold" @click.prevent="abrirRespuestas(reg)" x-text="reg.nota + '/100'"></a>
                    </template>
                    <template x-if="reg.nota !== null && !notaEsEnlace()">
                      <span class="font-semibold text-slate-700" x-text="reg.nota + '/100'"></span>
                    </template>
                    <span x-show="reg.nota === null" class="text-slate-400">—</span>
                  </td>
                  <td class="w-[100px] text-center text-xs text-slate-500" x-text="reg.fecha"></td>
                  <td class="w-[100px] text-center text-xs text-slate-500" x-text="reg.tiempo"></td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>

  <!-- ═══ TABLA PRINCIPAL ═══ -->
  <div x-show="!mostrarExpediente" x-transition>
    <div class="card-base p-0 overflow-hidden">
      <div class="flex items-center justify-between px-3.5 py-2.5 border-b border-slate-100">
        <span class="text-[10.5px] font-bold text-slate-600 uppercase tracking-widest">Seguimiento Global de Documentos y Lanzamientos</span>
        <span class="text-[10px] text-slate-400 font-normal normal-case" x-text="filtrados.length + ' de ' + items.length + ' registros'"></span>
      </div>

      <div class="overflow-x-auto">
        <table class="data-table min-w-[900px]">
          <thead>
            <tr>
              <th style="width: 140px;">
                <div class="flex flex-col gap-1.5">
                  <span>CÓDIGO</span>
                  <input type="text" x-model="filterCodigo" class="form-input text-[10px] px-2 py-1 font-normal normal-case" placeholder="Buscar código...">
                </div>
              </th>
              <th style="width: 200px;">
                <div class="flex flex-col gap-1.5">
                  <span>NOMBRE DOCUMENTO</span>
                  <input type="text" x-model="filterNombre" class="form-input text-[10px] px-2 py-1 font-normal normal-case" placeholder="Buscar nombre...">
                </div>
              </th>
              <th class="text-center">Fecha Lanzam.</th>
              <th class="text-center">FECHA FIN</th>
              <th class="relative">
                <div class="flex items-center gap-1 cursor-pointer hover:text-brand-600 transition-colors" @click.stop="showFilterTipo=!showFilterTipo">
                  TIPO <span class="text-[9px]">▼</span>
                  <span x-show="filterTipo.length" class="w-4 h-4 bg-brand-600 text-white rounded-full text-[9px] flex items-center justify-center font-bold" x-text="filterTipo.length"></span>
                </div>
                <div x-show="showFilterTipo" @click.stop @click.outside="showFilterTipo=false" class="absolute top-full left-0 z-50 bg-white border border-slate-200 rounded-lg p-2 shadow-lg min-w-[160px] flex flex-col gap-1 font-normal normal-case">
                  <template x-for="v in ['Evaluación','Control Lectura','Sin Control']" :key="v">
                    <label class="flex items-center gap-1.5 text-[11px] font-medium text-slate-800 cursor-pointer px-1 py-0.5 hover:bg-slate-50 rounded">
                      <input type="checkbox" :value="v" x-model="filterTipo" class="accent-brand-600">
                      <span x-text="v"></span>
                    </label>
                  </template>
                  <button class="btn btn-sm mt-1 text-[10px]" @click="filterTipo=[];showFilterTipo=false">Limpiar</button>
                </div>
              </th>
              <th class="relative">
                <div class="flex items-center gap-1 cursor-pointer hover:text-brand-600 transition-colors" @click.stop="showFilterEstado=!showFilterEstado">
                  ESTADO <span class="text-[9px]">▼</span>
                  <span x-show="filterEstado.length" class="w-4 h-4 bg-brand-600 text-white rounded-full text-[9px] flex items-center justify-center font-bold" x-text="filterEstado.length"></span>
                </div>
                <div x-show="showFilterEstado" @click.stop @click.outside="showFilterEstado=false" class="absolute top-full left-0 z-50 bg-white border border-slate-200 rounded-lg p-2 shadow-lg min-w-[160px] flex flex-col gap-1 font-normal normal-case">
                  <template x-for="v in ['Pendiente','Finalizado','Cancelado']" :key="v">
                    <label class="flex items-center gap-1.5 text-[11px] font-medium text-slate-800 cursor-pointer px-1 py-0.5 hover:bg-slate-50 rounded">
                      <input type="checkbox" :value="v" x-model="filterEstado" class="accent-brand-600">
                      <span x-text="v"></span>
                    </label>
                  </template>
                  <button class="btn btn-sm mt-1 text-[10px]" @click="filterEstado=[];showFilterEstado=false">Limpiar</button>
                </div>
              </th>
              <th class="text-center">Alcance</th>
              <th class="text-center">Promedio</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="(r, index) in filtrados" :key="r.id || index">
              <tr :class="r.isNew ? 'bg-emerald-100 transition-colors duration-1000' : 'hover:bg-brand-50/40 transition-colors'">
                <td class="table-cell-mono font-bold text-brand-600" x-text="r.codigo"></td>
                <td class="text-[11.5px] font-medium text-slate-700" x-text="r.nombre"></td>
                <td class="text-center text-xs text-slate-500" x-text="r.fechaLanz"></td>
                <td class="text-center text-xs text-slate-500" x-text="r.fechaFin || r.plazo"></td>
                <td><span :class="'badge ' + tipoBadge(r.tipo)" x-text="r.tipo"></span></td>
                <td><span :class="'badge ' + estadoBadge(r.estado)" x-text="r.estado"></span></td>
                <td class="text-center text-xs">
                  <a href="#" class="text-brand-500 hover:underline cursor-pointer" @click.prevent="abrirAlcance(r)" x-text="r.alcance"></a>
                </td>
                <td class="text-center text-xs font-semibold" :class="promColor(r.prom)" x-text="r.prom"></td>
                <td>
                  <div class="flex items-center gap-2 justify-start">
                    <button @click="window.parametrosDifusionModal?.abrir({docNombre:r.nombre,docCodigo:r.codigo,tipo:r.tipo})" class="btn btn-sm" title="Configurar Parámetros">⚙️</button>
                    <button x-show="r.tipo==='Evaluación'" @click="sessionStorage.setItem('sgd_config_examen_doc', JSON.stringify({codigo:r.codigo,nombre:r.nombre})); window.location.hash='/config-examen'" class="btn btn-primary btn-sm" title="Configurar Examen">📝</button>
                    <button x-show="r.estado==='Pendiente'" @click="cancelar(r)" class="btn btn-sm border-red-200 text-red-600 hover:bg-red-50" title="Cancelar">❌</button>
                    <button x-show="r.estado==='Cancelado'" @click="reactivar(r)" class="btn btn-sm border-emerald-200 text-emerald-600 hover:bg-emerald-50" title="Reactivar">↺</button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>`
}
