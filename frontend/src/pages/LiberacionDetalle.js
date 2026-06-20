/**
 * pages/LiberacionDetalle.js — Atender Liberación ETO (US-4.02 a 4.06)
 * Árbol Outlook reactivo + CRUD revisores/aprobadores + chips de difusión
 */
import { arbolOutlookDB, gerenciasDB } from '../data/gerencias.js'
import { tiposDocumentoList } from '../data/documents.js'
import { apiGet } from '../utils/api.js'

export const page = {
  init() {
    window.Alpine?.data('libDetallePage', () => ({
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

      async init() {
        await this._cargarProcesos()
      },

      async _cargarProcesos() {
        try {
          const res = await apiGet('/procesos')
          if (res.ok) this.procesosList = res.data?.items || []
        } catch (_) { /* ignore */ }
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
        this.procesoInput = `${p.codigo} - ${p.nombre}`
        this.procesoOpen = false
      },

      // Formulario campos dinámicos
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

      // Árbol Outlook reactivo (copiado de arbolOutlookDB)
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
        window.toast('✅ Grupos de difusión actualizados (' + this.chipsDifusion.length + ' grupos)', 'success')
      },

      // CRUD Revisores y Aprobadores
      revisores: [
        { id: 1, nombre: 'Maria Condori (Analista de Calidad)' },
        { id: 2, nombre: 'Jasiel Sanjinés (Jefe de Excelencia)' },
      ],
      aprobadores: [
        { id: 1, nombre: 'Luis Mamani (Gerente de Planta)' },
      ],
      addRevisor() { this.revisores.push({ id: Date.now(), nombre: '' }) },
      removeRevisor(idx) {
        if (this.revisores.length <= 1) { window.toast('⚠️ Debe haber al menos 1 revisor', 'warn'); return }
        this.revisores.splice(idx, 1)
      },
      addAprobador() { this.aprobadores.push({ id: Date.now(), nombre: '' }) },
      removeAprobador(idx) {
        if (this.aprobadores.length <= 1) { window.toast('⚠️ Debe haber al menos 1 aprobador', 'warn'); return }
        this.aprobadores.splice(idx, 1)
      },
      guardarFormulario() {
        window.toast('✅ Formulario de liberación actualizado correctamente', 'success')
        this.showFormulario = false
      },

      // IA
      ejecutarIA() {
        this.iaLoading = true
        setTimeout(() => { this.iaLoading = false; this.iaEjecutado = true }, 2000)
      },

      // Decisión de liberación
      confirmarAccion(type) { this.confirmType = type; this.showConfirm = true },
      procesarAccion() {
        this.showConfirm = false
        window.authModal?.abrir({
          titulo: this.confirmType === 'liberar' ? '✅ Liberar Documento' : '↩ Devolver al Solicitante',
          icono: this.confirmType === 'liberar' ? '✅' : '↩',
          mensaje: this.confirmType === 'liberar'
            ? 'El documento <strong>MET-CAL-002</strong> será liberado y enviado a la etapa de Revisión y Firma. Esta acción registrará su aprobación digital en la bitácora del sistema.'
            : `El documento será devuelto al elaborador con las observaciones: <em>"${this.obsTexto}"</em>. El solicitante recibirá una notificación.`,
          onSuccess: () => {
            if (this.confirmType === 'liberar') {
              window.toast('✅ Documento liberado exitosamente hacia Revisión', 'success')
            } else {
              window.toast('↩ Documento devuelto al solicitante con observaciones', 'warn')
            }
            window.navigate('/bandeja')
          },
        })
      },
    }))
  },

  template: /* html */`
<div x-data="libDetallePage" x-init="init()" class="animate-fade-in-page max-w-[1100px] mx-auto">

  <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="text-sm font-bold text-slate-800 m-0">Atender Liberación — MET-CAL-002</h1>
      <p class="text-[11px] text-slate-400 mt-1">Metodología de Análisis de Causa Raíz · Elaborador: Juan Perez</p>
    </div>
    <a href="#/bandeja" class="btn btn-sm">← Volver a Mi Bandeja</a>
  </div>

  <!-- Formulario original (collapsible) -->
  <div class="border border-blue-200 rounded-xl overflow-hidden mb-4">
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
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Área responsable</label>
          <select class="form-input text-xs" x-model="areaSel">
            <option value="">— Seleccionar área —</option>
            <template x-for="a in areasList" :key="a.cod"><option :value="a.cod" x-text="a.nombre"></option></template>
          </select>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Código (Oficial — editable ETO)</label>
          <input type="text" value="MET-CAL-002" class="form-input font-mono font-bold text-xs">
        </div>
        <div><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Versión</label><input type="text" value="01" class="form-input text-xs"></div>
        <div class="col-span-2"><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Título del documento</label><input type="text" value="Metodología de Análisis de Causa Raíz" class="form-input text-xs"></div>
        <div><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Elaborador</label><input type="text" value="Juan Perez" class="form-input text-xs" disabled></div>
        <div><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Cargo</label><input type="text" value="Analista de Calidad" class="form-input text-xs" disabled></div>
        <div><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Fecha de apertura</label><input type="text" value="12/01/2026" class="form-input text-xs" disabled></div>
        <div class="col-span-2"><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Justificación del solicitante</label><textarea class="form-input text-xs" rows="2">Se requiere estandarizar el proceso de investigación de desviaciones...</textarea></div>
      </div>

      <div class="border-t border-slate-100 pt-3.5 mt-1">
        <div class="text-[11px] font-bold text-slate-600 mb-2.5">2. Vigencia y evaluación</div>
        <div class="grid grid-cols-2 gap-3 mb-3.5">
          <div><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Tiempo de vigencia (Editable ETO)</label>
            <select class="form-input text-xs"><option>1 año</option><option>2 años</option><option>3 años</option><option selected>4 años</option><option>5 años</option></select>
          </div>
          <div><label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Requiere evaluación</label>
            <select class="form-input text-xs"><option>Sí — evaluación obligatoria</option><option>No</option></select>
          </div>
        </div>
      </div>

      <!-- Revisores reactivos -->
      <div class="border-t border-slate-100 pt-3.5">
        <div class="text-[11px] font-bold text-slate-600 mb-2.5">3. Revisores y Aprobadores (Editables por ETO)</div>
        <div class="mb-3">
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Revisores asignados</label>
          <div class="flex flex-col gap-1.5">
            <template x-for="(r,i) in revisores" :key="r.id">
              <div class="flex gap-2">
                <input type="text" x-model="r.nombre" list="lista-empleados-rev" class="form-input flex-1 text-xs" placeholder="Nombre del revisor...">
                <div @click="removeRevisor(i)" class="px-2.5 h-9 flex items-center justify-center border border-red-200 bg-red-50 text-red-600 rounded-md cursor-pointer text-[13px]">✕</div>
              </div>
            </template>
          </div>
          <div @click="addRevisor()" class="inline-flex items-center gap-1 mt-1.5 text-[11px] text-brand-500 border border-brand-500 px-2.5 py-1 rounded-md cursor-pointer hover:bg-blue-50 transition-colors">
            ➕ Agregar Revisor
          </div>
        </div>
        <div>
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Aprobadores asignados</label>
          <div class="flex flex-col gap-1.5">
            <template x-for="(a,i) in aprobadores" :key="a.id">
              <div class="flex gap-2">
                <input type="text" x-model="a.nombre" list="lista-empleados-rev" class="form-input flex-1 text-xs" placeholder="Nombre del aprobador...">
                <div @click="removeAprobador(i)" class="px-2.5 h-9 flex items-center justify-center border border-red-200 bg-red-50 text-red-600 rounded-md cursor-pointer text-[13px]">✕</div>
              </div>
            </template>
          </div>
          <div @click="addAprobador()" class="inline-flex items-center gap-1 mt-1.5 text-[11px] text-brand-500 border border-brand-500 px-2.5 py-1 rounded-md cursor-pointer hover:bg-blue-50 transition-colors">
            ➕ Agregar Aprobador
          </div>
        </div>
        <datalist id="lista-empleados-rev">
          <option value="Maria Condori (Analista de Calidad)"></option>
          <option value="Jasiel Sanjinés (Jefe de Excelencia)"></option>
          <option value="Lucia Terán (Analista Sr.)"></option>
          <option value="Luis Mamani (Gerente de Planta)"></option>
          <option value="Carlos Flores (Jefe de Logística)"></option>
          <option value="Aracely Romero (ETO Calidad)"></option>
        </datalist>
      </div>

      <!-- Reemplaza a otro documento -->
      <div class="border-t border-slate-100 pt-3.5 mt-1">
        <div class="text-[11px] font-bold text-slate-600 mb-2.5">4. ¿Reemplaza a otro documento?</div>
        <div class="grid grid-cols-[200px_1fr] gap-3 items-start">
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">¿Reemplaza?</label>
            <select class="form-input text-xs" x-model="reemplaza">
              <option value="No">No</option>
              <option value="Si">Sí</option>
            </select>
          </div>
          <div x-show="reemplaza==='Si'">
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Códigos de documentos reemplazados</label>
            <div class="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px]">
              <template x-for="(c,i) in chipsReemplazo" :key="i">
                <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-red-50 text-red-600 border border-red-200">
                  <span x-text="c"></span>
                  <span @click="removeChipReemplazo(i)" class="cursor-pointer text-[13px] opacity-70 hover:opacity-100 transition-opacity">✕</span>
                </span>
              </template>
              <span x-show="chipsReemplazo.length===0" class="text-[11px] text-slate-400 italic self-center">Sin documentos reemplazados</span>
            </div>
            <div class="flex gap-1.5">
              <input type="text" x-model="reemplazaInput" class="form-input flex-1 text-xs font-mono"
                     placeholder="Código (ej: MET-CAL-001) — ENTER o COMA para agregar"
                     @keydown.enter.prevent="addChipReemplazo()"
                     @keydown="if($event.key===','){$event.preventDefault();addChipReemplazo()}">
              <button class="btn btn-sm" @click="addChipReemplazo()">+ Agregar</button>
            </div>
          </div>
        </div>
      </div>

      <div class="text-right mt-3.5 border-t border-slate-100 pt-3">
        <button class="btn btn-primary btn-sm" @click="guardarFormulario()">💾 Guardar cambios del formulario</button>
      </div>
    </div>
  </div>

  <!-- Fila: IA + Archivos + Difusión -->
  <div class="grid grid-cols-2 gap-3.5 mb-4">

    <!-- IA Similitud -->
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-col items-center justify-center text-center gap-2.5">
      <div x-show="!iaEjecutado && !iaLoading" class="flex flex-col items-center gap-2.5">
        <div class="text-[10px] font-bold text-blue-700 uppercase tracking-widest">✦ IA — Análisis de Similitud Documental</div>
        <div class="text-[11.5px] text-blue-900 leading-relaxed">Ejecute el análisis para comparar el contenido del nuevo documento contra toda la Lista Maestra vigente.</div>
        <button class="btn btn-primary mt-1" @click="ejecutarIA()">🔍 Ejecutar Análisis de Similitud IA</button>
      </div>
      <div x-show="iaLoading" class="text-brand-500 text-xs font-semibold">⏳ Vectorizando documento y comparando con Lista Maestra...</div>
      <div x-show="iaEjecutado && !iaLoading" class="w-full">
        <div class="flex justify-between items-center mb-2">
          <div class="text-[10px] font-bold text-blue-700 uppercase tracking-widest">✦ IA — Similitud detectada</div>
          <div @click="iaEjecutado=false;iaLoading=false" class="btn btn-sm text-[10px] cursor-pointer">🔄 Re-ejecutar</div>
        </div>
        <div class="bg-amber-50 border border-amber-200 text-amber-800 px-2.5 py-1.5 rounded-md mb-2.5 text-[11px] font-semibold">⚠️ Riesgo global: 72% — Alto</div>
        <div class="text-[11.5px] text-blue-900 mb-2">Se encontraron 2 documentos con contenido similar (>70%):</div>
        <div class="flex flex-col gap-1.5">
          <div class="bg-white border border-slate-200 rounded-md p-2 text-[11px] flex justify-between items-center">
            <div><strong class="text-brand-500 font-mono">PRO-CAL-001</strong><br><span class="text-slate-500 text-[10.5px]">Procedimiento de Control de Documentos del SIG</span></div>
            <span class="badge badge-red">75% coincidencia</span>
          </div>
          <div class="bg-white border border-slate-200 rounded-md p-2 text-[11px] flex justify-between items-center">
            <div><strong class="text-brand-500 font-mono">INS-CAL-004</strong><br><span class="text-slate-500 text-[10.5px]">Instructivo de Revisión Crítica</span></div>
            <span class="badge badge-amber">70% coincidencia</span>
          </div>
        </div>
        <div class="mt-2.5 text-[10.5px] text-slate-500 italic">La IA es un soporte — decisión no vinculante. ETO puede devolver por duplicidad o justificar la continuación.</div>
      </div>
    </div>

    <!-- Archivos + Difusión -->
    <div class="flex flex-col gap-3">
      <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-card">
        <div class="text-[11px] font-bold text-slate-600 mb-2.5">Archivos cargados por el solicitante</div>
        <div class="flex flex-col gap-2">
          <div @click="window.toast('🖊️ Abriendo MET-CAL-002_v01.docx en Office 365...','info')" class="flex items-center gap-2.5 p-2 px-3 bg-slate-50 border border-slate-200 rounded-lg cursor-pointer transition-colors duration-150 hover:border-brand-500">
            <span class="text-xl">📄</span>
            <div><div class="text-xs font-semibold">MET-CAL-002_v01.docx</div><div class="text-[10px] text-brand-500">Documento Principal (Word)</div></div>
          </div>
          <div @click="window.toast('🖊️ Abriendo Formulario_Anexo_01.xlsx en Office 365...','info')" class="flex items-center gap-2.5 p-2 px-3 bg-emerald-50 border border-emerald-200 rounded-lg cursor-pointer transition-colors duration-150 hover:border-emerald-600">
            <span class="text-xl">📊</span>
            <div><div class="text-xs font-semibold">Formulario_Anexo_01.xlsx</div><div class="text-[10px] text-emerald-600">Anexo (Excel)</div></div>
          </div>
        </div>
      </div>

      <!-- Árbol Difusión Outlook -->
      <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-card">
        <div class="flex justify-between items-center mb-2.5">
          <div class="text-[11px] font-bold text-slate-600">Grupos de difusión (Outlook)</div>
          <div @click="showTree=!showTree" class="text-[11px] text-brand-500 border border-blue-200 px-2 py-0.5 rounded cursor-pointer hover:bg-blue-50 transition-colors">
            ⚙️ <span x-text="showTree?'Cerrar':'Editar grupos'"></span>
          </div>
        </div>

        <!-- Chips de difusión -->
        <div class="flex flex-wrap gap-1.5 mb-2">
          <template x-for="chip in chipsDifusion" :key="chip.id">
            <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px]"
                  :class="chip.tipo==='padre' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-blue-50 text-brand-500 border border-blue-200'">
              <span x-text="chip.nombre"></span>
              <span @click="removerChip(chip)" class="cursor-pointer opacity-60 text-xs ml-0.5 hover:opacity-100 transition-opacity">✕</span>
            </span>
          </template>
          <span x-show="chipsDifusion.length===0" class="text-[11.5px] text-slate-400 italic">Sin grupos seleccionados</span>
        </div>

        <!-- Árbol desplegable -->
        <div x-show="showTree" @click.stop class="bg-slate-50 border border-slate-200 rounded-lg p-3 max-h-60 overflow-y-auto">
          <template x-for="grupo in arbol" :key="grupo.id">
            <div class="mb-1">
              <label class="flex items-center gap-1.5 text-xs font-semibold text-slate-800 cursor-pointer py-0.5">
                <input type="checkbox"
                       x-effect="$el.checked=grupo.checked;$el.indeterminate=grupo.indeterminate"
                       @change="togglePadre(grupo)"
                       class="w-[15px] h-[15px] cursor-pointer accent-brand-500 shrink-0">
                🏢 <span x-text="grupo.nombre"></span>
              </label>
              <div class="ml-5 flex flex-col gap-0.5">
                <template x-for="sub in grupo.subs" :key="sub.id">
                  <label class="flex items-center gap-1.5 text-[11.5px] text-slate-600 cursor-pointer py-0.5">
                    <input type="checkbox"
                           x-model="sub.checked"
                           @change="toggleHijo(grupo, sub)"
                           class="w-3.5 h-3.5 cursor-pointer accent-brand-500 shrink-0">
                    <span x-text="sub.nombre"></span>
                  </label>
                </template>
              </div>
            </div>
          </template>
          <div class="text-right mt-2.5 border-t border-slate-200 pt-2">
            <button class="btn btn-primary btn-sm" @click="guardarDifusion()">Guardar grupos</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Selector de Proceso (ETO) - Fase 3 -->
  <div class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card mb-3.5">
    <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">Asignación de Proceso</div>
    <div class="relative">
      <label class="form-label">Proceso al que corresponde el documento *</label>
      <input type="text" class="form-input text-xs" x-model="procesoInput"
             placeholder="Buscar proceso por codigo o nombre..."
             @focus="procesoOpen=true" @input="procesoOpen=true" @click.stop>
      <div x-show="procesoOpen && procesosFiltrados.length > 0"
           class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
           style="display:none"
           :style="(procesoOpen && procesosFiltrados.length > 0) ? 'display:block' : 'display:none'" @click.stop>
        <template x-for="p in procesosFiltrados" :key="p.id">
          <button @click="seleccionarProceso(p)" type="button"
                  class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]">
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

  <!-- Decisión de Liberación -->
  <div class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card">
    <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">Decisión de Liberación</div>
    <div class="flex items-center gap-3 mb-3.5 flex-wrap">
      <div class="flex-1 min-w-[200px]">
        <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">¿Tiene observaciones al documento?</label>
        <select class="form-input text-xs max-w-[300px]" @change="tieneObs=$el.value==='Si'">
          <option value="No">No — Proceder con liberación</option>
          <option value="Si">Sí — Devolver con observaciones</option>
        </select>
      </div>
    </div>
    <div x-show="tieneObs" class="mb-3.5">
      <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Detalle sus observaciones</label>
      <textarea class="form-input text-xs" rows="3" x-model="obsTexto" placeholder="Indique qué debe corregir el solicitante antes de liberar el documento..."></textarea>
    </div>
    <div class="flex justify-end gap-2.5">
      <button x-show="tieneObs" class="btn text-amber-600 border-amber-200 bg-amber-50 hover:bg-amber-100 hover:border-amber-300 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="obsTexto.trim().length < 25"
              @click="window.confirmLiberacionModal?.abrir({modo:'devolver',onConfirm:()=>{window.location.hash='/bandeja'}})">↩ Devolver al Solicitante</button>
      <button x-show="!tieneObs" class="btn btn-primary"
              @click="window.confirmLiberacionModal?.abrir({modo:'liberar',onConfirm:()=>{window.location.hash='/bandeja'}})">✅ Liberar Documento →</button>
    </div>
  </div>

</div>`
}
