import { apiGet, apiPost } from '../utils/api.js'
import { arbolOutlookDB, gerenciasDB } from '../data/gerencias.js'
import { tiposDocumentoList } from '../data/documents.js'

export const page = {
  init() {
    window.Alpine?.data('libDetallePage', () => ({
      // Tarea actual
      tarea: null,
      documento: null,
      flujo: null,
      cargando: true,
      error: '',

      // UI state
      iaEjecutado: false,
      iaLoading: false,
      showFormulario: true,
      showTree: false,
      tieneObs: false,
      obsTexto: '',
      showConfirm: false,
      confirmType: '',

      // Procesos (Fase 3)
      procesosList: [],
      procesoInput: '',
      procesoOpen: false,
      procesoSeleccionado: null,

      // Formulario campos dinámicos (mock legacy)
      tiposList: tiposDocumentoList,
      gerenciasList: gerenciasDB,
      tipoSel: 'Metodología',
      gerenciaSel: 'CAL',
      areaSel: '',
      get areasList() {
        const g = this.gerenciasList.find(g => g.id === this.gerenciaSel)
        return g ? g.areas : []
      },

      // Reemplaza a otro documento (chips)
      reemplaza: 'No',
      chipsReemplazo: [],
      reemplazaInput: '',
      addChipReemplazo() {
        const val = this.reemplazaInput.trim().toUpperCase()
        if (!val) return
        const parts = val.split(/[,\s]+/).filter(Boolean)
        parts.forEach(p => { if (!this.chipsReemplazo.includes(p)) this.chipsReemplazo.push(p) })
        this.reemplazaInput = ''
      },
      removeChipReemplazo(i) { this.chipsReemplazo.splice(i, 1) },

      // Árbol Outlook
      arbol: JSON.parse(JSON.stringify(arbolOutlookDB)).map(g => ({
        ...g, checked: true, indeterminate: false,
        subs: g.subs.map((s, i) => ({ ...s, checked: i < 3 })),
      })),

      togglePadre(grupo) {
        grupo.checked = !grupo.checked; grupo.indeterminate = false
        grupo.subs.forEach(s => s.checked = grupo.checked)
      },
      toggleHijo(grupo, hijo) {
        const todos = grupo.subs.every(s => s.checked), algunos = grupo.subs.some(s => s.checked)
        grupo.checked = todos; grupo.indeterminate = !todos && algunos
      },
      get chipsDifusion() {
        const chips = []
        this.arbol.forEach(g => {
          if (g.checked && !g.indeterminate) chips.push({ id: g.id, nombre: g.nombre, tipo: 'padre', ref: g })
          else g.subs.forEach(s => { if (s.checked) chips.push({ id: s.id, nombre: s.nombre, tipo: 'hijo', refPadre: g, refHijo: s }) })
        })
        return chips
      },
      removerChip(chip) {
        if (chip.tipo === 'padre') this.togglePadre(chip.ref)
        else this.toggleHijo(chip.refPadre, chip.refHijo)
      },
      guardarDifusion() {
        this.showTree = false
        window.toast('Grupos de difusion actualizados (' + this.chipsDifusion.length + ' grupos)', 'success')
      },

      // CRUD Revisores y Aprobadores (mock legacy)
      revisores: [
        { id: 1, nombre: 'Maria Condori (Analista de Calidad)' },
        { id: 2, nombre: 'Jasiel Sanjinés (Jefe de Excelencia)' },
      ],
      aprobadores: [{ id: 1, nombre: 'Luis Mamani (Gerente de Planta)' }],
      addRevisor() { this.revisores.push({ id: Date.now(), nombre: '' }) },
      removeRevisor(idx) {
        if (this.revisores.length <= 1) { window.toast('Debe haber al menos 1 revisor', 'warn'); return }
        this.revisores.splice(idx, 1)
      },
      addAprobador() { this.aprobadores.push({ id: Date.now(), nombre: '' }) },
      removeAprobador(idx) {
        if (this.aprobadores.length <= 1) { window.toast('Debe haber al menos 1 aprobador', 'warn'); return }
        this.aprobadores.splice(idx, 1)
      },
      guardarFormulario() {
        window.toast('Formulario de liberacion actualizado', 'success')
        this.showFormulario = false
      },

      // IA (mock legacy)
      ejecutarIA() {
        this.iaLoading = true
        setTimeout(() => { this.iaLoading = false; this.iaEjecutado = true }, 2000)
      },

      // ─── Inicializacion: cargar tarea desde API ───
      init() {
        this._cargarProcesos()
        this._cargarTarea()
      },

      async _cargarProcesos() {
        try {
          const res = await apiGet('/procesos')
          if (res.ok) this.procesosList = res.data?.items || []
        } catch (_) { /* ignore */ }
      },

      async _cargarTarea() {
        this.cargando = true
        this.error = ''
        try {
          const hash = window.location.hash.replace('#', '')
          const tareaId = new URLSearchParams(hash.split('?')[1]).get('tarea_id')
          if (!tareaId) {
            this.error = 'No se especifico una tarea'
            this.cargando = false; return
          }
          const res = await apiGet('/tareas/' + tareaId)
          if (!res.ok) { this.error = res.message || 'Error al cargar tarea'; this.cargando = false; return }
          this.tarea = res.data
          this.documento = { codigo: this.tarea.codigo_completo, titulo: this.tarea.titulo_documento }
        } catch (e) {
          this.error = e?.message || 'Error de conexion'
        } finally {
          this.cargando = false
        }
      },

      get procesosFiltrados() {
        const q = (this.procesoInput || '').toLowerCase().trim()
        if (!q) return this.procesosList
        return this.procesosList.filter(p =>
          (p.codigo || '').toLowerCase().includes(q) ||
          (p.nombre || '').toLowerCase().includes(q)
        )
      },

      seleccionarProceso(p) {
        this.procesoSeleccionado = p
        this.procesoInput = p.codigo + ' - ' + p.nombre
        this.procesoOpen = false
      },

      // ─── Liberar documento (POST real) ───
      async liberarDocumento() {
        window.authModal?.abrir({
          titulo: 'Liberar Documento',
          icono: '✅',
          mensaje: 'Esta accion enviara el documento a la etapa de Revision y Firma.',
          onSuccess: async ({ password }) => {
            try {
              const docRes = await apiGet('/documentos?codigo=' + (this.documento?.codigo || ''))
              if (!docRes.ok || !docRes.data?.items?.length) {
                window.toast('Error al buscar documento', 'error'); return
              }
              const docId = docRes.data.items[0].id
              const res = await apiPost('/documentos/' + docId + '/liberar', { password: password || '' })
              if (res.ok) {
                window.toast('Documento liberado exitosamente hacia Revision', 'success')
                window.location.hash = '/bandeja'
              } else {
                window.toast(res.message || 'Error al liberar', 'error')
              }
            } catch (e) {
              window.toast('Error: ' + (e?.message || e), 'error')
            }
          },
        })
      },

      devolverDocumento() {
        if (this.obsTexto.trim().length < 25) {
          window.toast('La observacion debe tener al menos 25 caracteres', 'warn'); return
        }
        window.authModal?.abrir({
          titulo: 'Devolver al Solicitante',
          icono: '↩',
          mensaje: 'El documento sera devuelto con las observaciones.',
          onSuccess: () => {
            window.toast('Documento devuelto al solicitante', 'warn')
            window.location.hash = '/bandeja'
          },
        })
      },
    }))
  },

  template: /* html */ `
<div x-data="libDetallePage" x-init="init()" class="animate-fade-in-page max-w-[1100px] mx-auto">

  <!-- Loading -->
  <div x-show="cargando" class="text-center py-12 text-slate-500 text-sm">Cargando datos de la tarea...</div>

  <!-- Error -->
  <div x-show="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-xs" x-text="error"></div>

  <!-- Header con datos reales -->
  <div x-show="!cargando && !error" class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="text-sm font-bold text-slate-800 m-0">
        Atender Liberacion
        <span x-text="tarea?.codigo_completo || ''"></span>
      </h1>
      <p class="text-[11px] text-slate-400 mt-1" x-text="tarea?.titulo_documento || 'Documento'"></p>
    </div>
    <a href="#/bandeja" class="btn btn-sm">← Volver a Mi Bandeja</a>
  </div>

  <!-- Formulario original (mock legacy) -->
  <div x-show="!cargando && !error" class="border border-blue-200 rounded-xl overflow-hidden mb-4">
    <div @click="showFormulario=!showFormulario"
         class="w-full px-4 py-3 bg-blue-50 text-blue-700 font-semibold text-xs cursor-pointer flex justify-between items-center border-b border-blue-200 select-none">
      <span>📋 1. Formulario de Solicitud Original (Clic para expandir / ocultar)</span>
      <span x-text="showFormulario?'↑':'↓'"></span>
    </div>
    <div x-show="showFormulario" class="p-4 bg-white max-h-[70vh] overflow-y-auto">
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Tipo de documento</label>
          <select class="form-input text-xs" x-model="tipoSel">
            <template x-for="t in tiposList" :key="t"><option :value="t" x-text="t"></option></template>
          </select>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Gerencia responsable</label>
          <select class="form-input text-xs" x-model="gerenciaSel" @change="areaSel=''">
            <template x-for="g in gerenciasList" :key="g.id"><option :value="g.id" x-text="g.nombre"></option></template>
          </select>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Area responsable</label>
          <select class="form-input text-xs" x-model="areaSel">
            <option value="">— Seleccionar area —</option>
            <template x-for="a in areasList" :key="a.cod"><option :value="a.cod" x-text="a.nombre"></option></template>
          </select>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Codigo (Oficial)</label>
          <input type="text" :value="tarea?.codigo_completo || '---'" class="form-input font-mono font-bold text-xs bg-slate-50" readonly>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Elaborador</label>
          <input type="text" value="Pendiente de integracion" class="form-input text-xs bg-slate-50" readonly disabled>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Fecha</label>
          <input type="text" :value="new Date().toLocaleDateString('es-BO')" class="form-input text-xs bg-slate-50" readonly disabled>
        </div>
      </div>
      <div class="text-right mt-3.5 border-t border-slate-100 pt-3">
        <button class="btn btn-primary btn-sm" @click="guardarFormulario()">Guardar cambios del formulario</button>
      </div>
    </div>
  </div>

  <!-- Fila: IA + Archivos + Difusion (mock legacy) -->
  <div x-show="!cargando && !error" class="grid grid-cols-2 gap-3.5 mb-4">
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-col items-center justify-center text-center gap-2.5">
      <div x-show="!iaEjecutado && !iaLoading" class="flex flex-col items-center gap-2.5">
        <div class="text-[10px] font-bold text-blue-700 uppercase tracking-widest">✦ IA — Analisis de Similitud Documental</div>
        <div class="text-[11.5px] text-blue-900 leading-relaxed">Ejecute el analisis para comparar el contenido contra la Lista Maestra.</div>
        <button class="btn btn-primary mt-1" @click="ejecutarIA()">Ejecutar Analisis de Similitud IA</button>
      </div>
      <div x-show="iaLoading" class="text-brand-500 text-xs font-semibold">Vectorizando documento...</div>
      <div x-show="iaEjecutado && !iaLoading" class="w-full">
        <div class="flex justify-between items-center mb-2">
          <div class="text-[10px] font-bold text-blue-700 uppercase">✦ IA — Similitud detectada</div>
          <div @click="iaEjecutado=false;iaLoading=false" class="btn btn-sm text-[10px] cursor-pointer">Re-ejecutar</div>
        </div>
        <div class="bg-amber-50 border border-amber-200 text-amber-800 px-2.5 py-1.5 rounded-md mb-2.5 text-[11px] font-semibold">Riesgo global: 72% — Alto</div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-card">
        <div class="text-[11px] font-bold text-slate-600 mb-2.5">Archivos cargados por el solicitante</div>
        <div class="flex flex-col gap-2">
          <div class="flex items-center gap-2.5 p-2 px-3 bg-slate-50 border border-slate-200 rounded-lg">
            <span class="text-xl">📄</span>
            <div><div class="text-xs font-semibold" x-text="(tarea?.codigo_completo || 'doc') + '.docx'"></div><div class="text-[10px] text-brand-500">Documento Principal (Word)</div></div>
          </div>
        </div>
      </div>

      <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-card">
        <div class="flex justify-between items-center mb-2.5">
          <div class="text-[11px] font-bold text-slate-600">Grupos de difusion (Outlook)</div>
          <div @click="showTree=!showTree" class="text-[11px] text-brand-500 border border-blue-200 px-2 py-0.5 rounded cursor-pointer hover:bg-blue-50 transition-colors">
            ⚙️ <span x-text="showTree?'Cerrar':'Editar grupos'"></span>
          </div>
        </div>
        <div class="flex flex-wrap gap-1.5 mb-2">
          <template x-for="chip in chipsDifusion" :key="chip.id">
            <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px]"
                  :class="chip.tipo==='padre' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-blue-50 text-brand-500 border border-blue-200'">
              <span x-text="chip.nombre"></span>
              <span @click="removerChip(chip)" class="cursor-pointer opacity-60 text-xs ml-0.5 hover:opacity-100">✕</span>
            </span>
          </template>
        </div>
      </div>
    </div>
  </div>

  <!-- Selector de Proceso (Fase 3) -->
  <div x-show="!cargando && !error" class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card mb-3.5">
    <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">Asignacion de Proceso</div>
    <div class="relative">
      <label class="form-label">Proceso al que corresponde el documento</label>
      <input type="text" class="form-input text-xs" x-model="procesoInput"
             placeholder="Buscar proceso por codigo o nombre..."
             @focus="procesoOpen=true" @input="procesoOpen=true" @click.stop>
      <div x-show="procesoOpen && procesosFiltrados.length > 0"
           class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
           style="display:none"
           :style="(procesoOpen && procesosFiltrados.length > 0) ? 'display:block' : 'display:none'" @click.stop>
        <template x-for="p in procesosFiltrados" :key="p.id">
          <button @click="seleccionarProceso(p)" type="button"
                  class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 text-[11px]">
            <span class="font-mono font-semibold" x-text="p.codigo"></span>
            <span class="text-slate-500 ml-2" x-text="p.nombre"></span>
          </button>
        </template>
      </div>
    </div>
    <div x-show="procesoSeleccionado" class="mt-2">
      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-brand-50 text-brand-700 border border-brand-200">
        <span class="font-mono font-semibold" x-text="procesoSeleccionado.codigo"></span>
        <span x-text="procesoSeleccionado.nombre"></span>
        <span @click="procesoSeleccionado=null;procesoInput=''" class="cursor-pointer opacity-60 hover:opacity-100 ml-1">✕</span>
      </span>
    </div>
  </div>

  <!-- Decision de Liberacion -->
  <div x-show="!cargando && !error" class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card">
    <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">Decision de Liberacion</div>
    <div class="flex items-center gap-3 mb-3.5 flex-wrap">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">¿Tiene observaciones al documento?</label>
        <select class="form-input text-xs max-w-[300px]" @change="tieneObs=$el.value==='Si'">
          <option value="No">No — Proceder con liberacion</option>
          <option value="Si">Si — Devolver con observaciones</option>
        </select>
      </div>
    </div>
    <div x-show="tieneObs" class="mb-3.5">
      <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Detalle sus observaciones</label>
      <textarea class="form-input text-xs" rows="3" x-model="obsTexto"></textarea>
    </div>
    <div class="flex justify-end gap-2.5">
      <button x-show="tieneObs" class="btn text-amber-600 border-amber-200 bg-amber-50 hover:bg-amber-100"
              :disabled="obsTexto.trim().length < 25"
              @click="devolverDocumento()">↩ Devolver al Solicitante</button>
      <button x-show="!tieneObs" class="btn btn-primary" @click="liberarDocumento()">✅ Liberar Documento →</button>
    </div>
  </div>

</div>`
}
