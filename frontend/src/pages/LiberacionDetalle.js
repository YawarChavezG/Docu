import { apiGet, apiPost, apiPatch } from '../utils/api.js'
import { arbolOutlookDB } from '../data/gerencias.js'

export const page = {
  init() {
    window.Alpine?.data('libDetallePage', () => ({
      tarea: null,
      documento: null,
      flujoActual: null,
      cargando: true,
      error: '',

      iaEjecutado: false, iaLoading: false,
      showFormulario: false, showTree: false,
      tieneObs: false, obsTexto: '',

      procesosList: [], procesoInput: '', procesoOpen: false, procesoSeleccionado: null,

      // Form fields (editables por ETO, excepto nombre/cargo/fecha)
      editTipoDoc: '',
      editGerencia: '',
      editArea: '',
      editCodigo: '',
      editTitulo: '',
      editVersion: '',
      editJustificacion: '',
      editVigencia: '',
      editRequiereEval: '',
      editRequiereLectura: '',
      elaboradorNombre: '',
      elaboradorCargo: '',
      fechaApertura: '',

      reemplaza: 'No', chipsReemplazo: [], reemplazaInput: '',
      revisores: [], aprobadores: [],
      arbol: [],

      addChipReemplazo() {
        const v = this.reemplazaInput.trim().toUpperCase()
        if (!v) return; const parts = v.split(/[,\s]+/).filter(Boolean)
        parts.forEach(p => { if (!this.chipsReemplazo.includes(p)) this.chipsReemplazo.push(p) })
        this.reemplazaInput = ''
      },
      removeChipReemplazo(i) { this.chipsReemplazo.splice(i, 1) },

      togglePadre(g) { g.checked = !g.checked; g.indeterminate = false; g.subs.forEach(s => s.checked = g.checked) },
      toggleHijo(g, h) { h.checked = !h.checked; const todos = g.subs.every(s => s.checked); g.checked = todos; g.indeterminate = !todos && g.subs.some(s => s.checked) },
      get chipsDifusion() {
        const chips = []
        this.arbol.forEach(g => {
          if (g.checked && !g.indeterminate) chips.push({ id: g.id, nombre: g.nombre })
          else g.subs.forEach(s => { if (s.checked) chips.push({ id: s.id, nombre: s.nombre }) })
        })
        return chips
      },
      removerChipChip(idx) { this.chipsDifusion.splice(idx, 1) },

      addRevisor() { this.revisores.push({ id: Date.now(), nombre: '' }) },
      removeRevisor(i) { if (this.revisores.length > 1) this.revisores.splice(i, 1) },
      addAprobador() { this.aprobadores.push({ id: Date.now(), nombre: '' }) },
      removeAprobador(i) { if (this.aprobadores.length > 1) this.aprobadores.splice(i, 1) },
      guardarFormulario() { window.toast('Formulario actualizado', 'success'); this.showFormulario = false },

      ejecutarIA() { this.iaLoading = true; setTimeout(() => { this.iaLoading = false; this.iaEjecutado = true }, 2000) },

      init() {
        this._cargarProcesos()
        this._cargarTarea()
      },

      async _cargarProcesos() {
        try { const r = await apiGet('/procesos'); if (r.ok) this.procesosList = r.data?.items || [] } catch (_) {}
      },

      async _cargarTarea() {
        this.cargando = true; this.error = ''
        try {
          const hash = window.location.hash.replace('#', '')
          const tareaId = new URLSearchParams(hash.split('?')[1]).get('tarea_id')
          if (!tareaId) { this.error = 'No se especifico tarea'; this.cargando = false; return }

          const tRes = await apiGet('/tareas/' + tareaId)
          if (!tRes.ok) { this.error = 'Error al cargar tarea'; this.cargando = false; return }
          this.tarea = tRes.data

          if (this.tarea.documento_id) {
            const dRes = await apiGet('/documentos/' + this.tarea.documento_id)
            if (dRes.ok) {
              this.documento = dRes.data
              const flujos = dRes.data.flujos || []
              if (flujos.length > 0) {
                this.flujoActual = flujos[flujos.length - 1]
                this._poblarFormulario()
              }
            }
          }
        } catch (e) { this.error = e?.message || 'Error' }
        finally { this.cargando = false }
      },

      async _poblarFormulario() {
        const f = this.flujoActual
        const d = this.documento
        if (!f || !d) return
        this.editTipoDoc = d.tipo?.nombre || ''
        this.editGerencia = d.gerencia?.sigla || ''
        this.editArea = d.area?.sigla || ''
        this.editCodigo = d.codigo || ''
        this.editTitulo = d.titulo || ''
        this.editVersion = d.version || '00'
        this.elaboradorNombre = f.cargo_elaborador || 'Pendiente'
        this.elaboradorCargo = f.cargo_elaborador || 'Pendiente'
        this.fechaApertura = f.fecha_solicitud ? new Date(f.fecha_solicitud).toLocaleDateString('es-BO') : ''
        this.editJustificacion = f.justificacion || ''
        this.editVigencia = f.tiempo_vigencia_anos ? f.tiempo_vigencia_anos + ' años' : 'Indefinido'
        this.editRequiereEval = f.requiere_evaluacion ? 'Si' : 'No'
        this.editRequiereLectura = f.requiere_control_lectura ? 'Si' : 'No'

        const userIds = [...new Set([...(f.revisor_ids || []), ...(f.aprobador_ids || [])])]
        this._usuariosLookup = {}
        try {
          const results = await Promise.all(userIds.map(id =>
            apiGet('/usuarios/' + id).then(r => r.ok ? r.data : null).catch(() => null)
          ))
          results.forEach(u => { if (u) this._usuariosLookup[u.id] = u })
        } catch (_) {}
        this.revisores = (f.revisor_ids || []).map((id, i) => {
          const u = this._usuariosLookup[id]; return { id: i + 1, user_id: id, nombre: u ? u.nombre_completo + ' (' + u.username + ')' : 'Usuario ' + id }
        })
        this.aprobadores = (f.aprobador_ids || []).map((id, i) => {
          const u = this._usuariosLookup[id]; return { id: i + 1, user_id: id, nombre: u ? u.nombre_completo + ' (' + u.username + ')' : 'Usuario ' + id }
        })

        this.arbol = JSON.parse(JSON.stringify(arbolOutlookDB)).map(g => ({
          ...g, checked: true, indeterminate: false,
          subs: g.subs.map((s, i) => ({ ...s, checked: i < 3 })),
        }))
      },

      get procesosFiltrados() {
        const q = (this.procesoInput || '').toLowerCase().trim()
        if (!q) return this.procesosList
        return this.procesosList.filter(p => (p.codigo || '').toLowerCase().includes(q) || (p.nombre || '').toLowerCase().includes(q))
      },
      seleccionarProceso(p) { this.procesoSeleccionado = p; this.procesoInput = p.codigo + ' - ' + p.nombre; this.procesoOpen = false },

      async liberarDocumento() {
        window.authModal?.abrir({
          titulo: 'Liberar Documento', icono: '✅',
          mensaje: 'Se enviara a la etapa de Revision.',
          onSuccess: async ({ password }) => {
            try {
              const res = await apiPost('/documentos/' + this.documento.id + '/liberar', { password: password || '' })
              if (res.ok) { window.toast('Documento liberado exitosamente', 'success'); window.location.hash = '/bandeja' }
              else { window.toast(res.message || 'Error al liberar', 'error') }
            } catch (e) { window.toast('Error: ' + (e?.message || e), 'error') }
          },
        })
      },

      devolverDocumento() {
        if (this.obsTexto.trim().length < 25) { window.toast('Observacion minimo 25 caracteres', 'warn'); return }
        window.authModal?.abrir({
          titulo: 'Devolver al Solicitante', icono: '↩',
          mensaje: 'Documento devuelto con observaciones.',
          onSuccess: () => { window.toast('Documento devuelto', 'warn'); window.location.hash = '/bandeja' },
        })
      },
    }))
  },

  template: /* html */ `
<div x-data="libDetallePage" x-init="init()" class="animate-fade-in-page max-w-[1100px] mx-auto">
  <div x-show="cargando" class="text-center py-12 text-slate-500 text-sm">Cargando...</div>
  <div x-show="error" class="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-xs" x-text="error"></div>

  <div x-show="!cargando && !error">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <div>
        <h1 class="text-sm font-bold text-slate-800 m-0">Atender Liberacion — <span x-text="tarea?.codigo_completo || ''"></span></h1>
        <p class="text-[11px] text-slate-400 mt-1" x-text="documento?.titulo || 'Documento'"></p>
      </div>
      <a href="#/bandeja" class="btn btn-sm">← Volver a Mi Bandeja</a>
    </div>

    <!-- FORMULARIO COMPLETO con datos reales editables por ETO -->
    <div class="border border-blue-200 rounded-xl overflow-hidden mb-4">
      <div @click="showFormulario=!showFormulario" class="w-full px-4 py-3 bg-blue-50 text-blue-700 font-semibold text-xs cursor-pointer flex justify-between items-center border-b border-blue-200 select-none">
        <span>📋 Formulario de Solicitud Original (Click para expandir / ocultar)</span>
        <span x-text="showFormulario?'↑':'↓'"></span>
      </div>
      <div x-show="showFormulario" class="p-4 bg-white max-h-[70vh] overflow-y-auto">
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Tipo de documento</label>
            <input type="text" x-model="editTipoDoc" class="form-input text-xs" placeholder="Tipo de documento">
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Gerencia responsable</label>
            <input type="text" x-model="editGerencia" class="form-input text-xs" placeholder="Gerencia">
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Area responsable</label>
            <input type="text" x-model="editArea" class="form-input text-xs" placeholder="Area">
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Tipo de solicitud</label>
            <input type="text" :value="flujoActual?.tipo_solicitud || 'CREACION'" class="form-input text-xs bg-slate-50" readonly disabled>
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Codigo oficial</label>
            <input type="text" x-model="editCodigo" class="form-input text-xs font-mono font-bold" placeholder="Codigo">
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Version</label>
            <input type="text" x-model="editVersion" class="form-input text-xs" placeholder="Version">
          </div>
          <div class="col-span-2">
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Titulo del documento</label>
            <input type="text" x-model="editTitulo" class="form-input text-xs" placeholder="Titulo">
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Elaborador (NO editable)</label>
            <input type="text" x-model="elaboradorNombre" class="form-input text-xs bg-slate-50 text-slate-400" readonly disabled>
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Cargo (NO editable)</label>
            <input type="text" x-model="elaboradorCargo" class="form-input text-xs bg-slate-50 text-slate-400" readonly disabled>
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Fecha de apertura (NO editable)</label>
            <input type="text" x-model="fechaApertura" class="form-input text-xs bg-slate-50 text-slate-400" readonly disabled>
          </div>
          <div class="col-span-2">
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Justificacion / motivo</label>
            <textarea class="form-input text-xs" rows="2" x-model="editJustificacion" placeholder="Justificacion"></textarea>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-3.5 mt-1">
          <div class="text-[11px] font-bold text-slate-600 mb-2.5">Vigencia y Evaluacion</div>
          <div class="grid grid-cols-2 gap-3 mb-3.5">
            <div>
              <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Tiempo de vigencia (Editable ETO)</label>
              <input type="text" x-model="editVigencia" class="form-input text-xs">
            </div>
            <div>
              <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Requiere evaluacion</label>
              <select class="form-input text-xs" x-model="editRequiereEval"><option value="Si">Si</option><option value="No">No</option></select>
            </div>
            <div>
              <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">Requiere control de lectura</label>
              <select class="form-input text-xs" x-model="editRequiereLectura"><option value="Si">Si</option><option value="No">No</option></select>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-3.5">
          <div class="text-[11px] font-bold text-slate-600 mb-2.5">Revisores y Aprobadores (Editables por ETO)</div>
          <div class="mb-3">
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Revisores asignados</label>
            <div class="flex flex-col gap-1.5">
              <template x-for="(r,i) in revisores" :key="r.id">
                <div class="flex gap-2">
                  <input type="text" x-model="r.nombre" class="form-input flex-1 text-xs" placeholder="Revisor...">
                  <div @click="removeRevisor(i)" class="px-2.5 h-9 flex items-center justify-center border border-red-200 bg-red-50 text-red-600 rounded-md cursor-pointer text-[13px]">✕</div>
                </div>
              </template>
            </div>
            <div @click="addRevisor()" class="inline-flex items-center gap-1 mt-1.5 text-[11px] text-brand-500 border border-brand-500 px-2.5 py-1 rounded-md cursor-pointer hover:bg-blue-50">➕ Agregar Revisor</div>
          </div>
          <div>
            <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Aprobadores asignados</label>
            <div class="flex flex-col gap-1.5">
              <template x-for="(a,i) in aprobadores" :key="a.id">
                <div class="flex gap-2">
                  <input type="text" x-model="a.nombre" class="form-input flex-1 text-xs" placeholder="Aprobador...">
                  <div @click="removeAprobador(i)" class="px-2.5 h-9 flex items-center justify-center border border-red-200 bg-red-50 text-red-600 rounded-md cursor-pointer text-[13px]">✕</div>
                </div>
              </template>
            </div>
            <div @click="addAprobador()" class="inline-flex items-center gap-1 mt-1.5 text-[11px] text-brand-500 border border-brand-500 px-2.5 py-1 rounded-md cursor-pointer hover:bg-blue-50">➕ Agregar Aprobador</div>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-3.5 mt-1">
          <div class="text-[11px] font-bold text-slate-600 mb-2.5">Reemplaza a otro documento</div>
          <div class="grid grid-cols-[200px_1fr] gap-3 items-start">
            <div>
              <select class="form-input text-xs" x-model="reemplaza"><option value="No">No</option><option value="Si">Si</option></select>
            </div>
            <div x-show="reemplaza==='Si'">
              <div class="flex flex-wrap gap-1.5 mb-1.5">
                <template x-for="(c,i) in chipsReemplazo" :key="i">
                  <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-red-50 text-red-600 border border-red-200">
                    <span x-text="c"></span><span @click="removeChipReemplazo(i)" class="cursor-pointer">✕</span>
                  </span>
                </template>
              </div>
              <div class="flex gap-1.5">
                <input type="text" x-model="reemplazaInput" class="form-input flex-1 text-xs font-mono" placeholder="Codigo (ej: MET-CAL-001)" @keydown.enter.prevent="addChipReemplazo()">
                <button class="btn btn-sm" @click="addChipReemplazo()">+</button>
              </div>
            </div>
          </div>
        </div>

        <div class="text-right mt-3.5 pt-3 border-t border-slate-100">
          <button class="btn btn-primary btn-sm" @click="guardarFormulario()">Guardar cambios</button>
        </div>
      </div>
    </div>

    <!-- Archivos cargados por el solicitante + Difusion -->
    <div class="grid grid-cols-2 gap-3.5 mb-4">
      <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-card">
        <div class="text-[11px] font-bold text-slate-600 mb-2.5">Archivos cargados por el solicitante</div>
        <div class="flex flex-col gap-2">
          <template x-for="a in (documento?.archivos || [])" :key="a.id">
            <div class="flex items-center gap-2.5 p-2 px-3 border rounded-lg justify-between"
                 :class="a.tipo_adjunto === 'PRINCIPAL' ? 'bg-slate-50 border-slate-200' : 'bg-emerald-50 border-emerald-200'">
              <div class="flex items-center gap-2.5">
                <span class="text-xl" x-text="a.tipo_adjunto === 'PRINCIPAL' ? '📄' : '📊'"></span>
                <div>
                  <div class="text-xs font-semibold" x-text="a.nombre_original"></div>
                  <div class="text-[10px]" :class="a.tipo_adjunto === 'PRINCIPAL' ? 'text-brand-500' : 'text-emerald-600'"
                       x-text="a.tipo_adjunto === 'PRINCIPAL' ? 'Documento Principal (Word)' : 'Formulario (Excel)'"></div>
                </div>
              </div>
              <div @click="window.toast('🔗 Abriendo documento en SharePoint (Office 365)...','info')"
                   class="text-[11px] text-brand-500 border border-blue-200 px-2 py-1 rounded cursor-pointer hover:bg-blue-50 flex items-center gap-1 shrink-0">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                Abrir en SharePoint
              </div>
            </div>
          </template>
          <div x-show="!documento?.archivos?.length" class="text-[11px] text-slate-400 italic p-2">Sin archivos adjuntos</div>
        </div>
      </div>
      <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-card">
        <div class="flex justify-between items-center mb-2.5">
          <div class="text-[11px] font-bold text-slate-600">Grupos de difusion</div>
          <div @click="showTree=!showTree" class="text-[11px] text-brand-500 border border-blue-200 px-2 py-0.5 rounded cursor-pointer hover:bg-blue-50 transition-colors">⚙️ <span x-text="showTree?'Cerrar':'Editar grupos'"></span></div>
        </div>
        <div class="flex flex-wrap gap-1.5 mb-2">
          <template x-for="chip in chipsDifusion" :key="chip.id">
            <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span x-text="chip.nombre"></span>
            </span>
          </template>
          <span x-show="chipsDifusion.length===0" class="text-[11.5px] text-slate-400 italic">Sin grupos seleccionados</span>
        </div>
        <div x-show="showTree" @click.stop class="bg-slate-50 border border-slate-200 rounded-lg p-3 max-h-60 overflow-y-auto">
          <template x-for="grupo in arbol" :key="grupo.id">
            <div class="mb-1">
              <label class="flex items-center gap-1.5 text-xs font-semibold text-slate-800 cursor-pointer py-0.5">
                <input type="checkbox" x-effect="$el.checked=grupo.checked;$el.indeterminate=grupo.indeterminate" @change="togglePadre(grupo)" class="w-[15px] h-[15px] cursor-pointer accent-brand-500 shrink-0">
                🏢 <span x-text="grupo.nombre"></span>
              </label>
              <div class="ml-5 flex flex-col gap-0.5">
                <template x-for="sub in grupo.subs" :key="sub.id">
                  <label class="flex items-center gap-1.5 text-[11.5px] text-slate-600 cursor-pointer py-0.5">
                    <input type="checkbox" x-model="sub.checked" @change="toggleHijo(grupo, sub)" class="w-3.5 h-3.5 cursor-pointer accent-brand-500 shrink-0">
                    <span x-text="sub.nombre"></span>
                  </label>
                </template>
              </div>
            </div>
          </template>
          <div class="text-right mt-2.5 border-t border-slate-200 pt-2">
            <button class="btn btn-primary btn-sm" @click="showTree=false;window.toast('Grupos actualizados','success')">Guardar grupos</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Selector Proceso -->
    <div class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card mb-3.5">
      <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">Asignacion de Proceso</div>
      <div class="relative">
        <label class="form-label">Proceso al que corresponde el documento</label>
        <input type="text" class="form-input text-xs" x-model="procesoInput" placeholder="Buscar proceso..." @focus="procesoOpen=true" @input="procesoOpen=true" @click.stop>
        <div x-show="procesoOpen && procesosFiltrados.length > 0" class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto" style="display:none" :style="(procesoOpen && procesosFiltrados.length > 0) ? 'display:block' : 'display:none'" @click.stop>
          <template x-for="p in procesosFiltrados" :key="p.id">
            <button @click="seleccionarProceso(p)" type="button" class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 text-[11px]">
              <span class="font-mono font-semibold" x-text="p.codigo"></span>
              <span class="text-slate-500 ml-2" x-text="p.nombre"></span>
            </button>
          </template>
        </div>
      </div>
      <div x-show="procesoSeleccionado" class="mt-2">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-brand-50 text-brand-700 border border-brand-200">
          <span class="font-mono font-semibold" x-text="procesoSeleccionado?.codigo || ''"></span>
          <span x-text="procesoSeleccionado?.nombre || ''"></span>
          <span @click="procesoSeleccionado=null;procesoInput=''" class="cursor-pointer opacity-60 hover:opacity-100 ml-1">✕</span>
        </span>
      </div>
    </div>

    <!-- Decision de Liberacion -->
    <div class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card">
      <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">Decision de Liberacion</div>
      <div class="flex items-center gap-3 mb-3.5 flex-wrap">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-[10.5px] font-semibold text-slate-500 mb-1">¿Tiene observaciones?</label>
          <select class="form-input text-xs max-w-[300px]" @change="tieneObs=$el.value==='Si'">
            <option value="No">No — Proceder con liberacion</option>
            <option value="Si">Si — Devolver con observaciones</option>
          </select>
        </div>
      </div>
      <div x-show="tieneObs" class="mb-3.5">
        <label class="block text-[10.5px] font-semibold text-slate-500 mb-1.5">Observaciones</label>
        <textarea class="form-input text-xs" rows="3" x-model="obsTexto"></textarea>
      </div>
      <div class="flex justify-end gap-2.5">
        <button x-show="tieneObs" class="btn text-amber-600 border-amber-200 bg-amber-50" :disabled="obsTexto.trim().length < 25" @click="devolverDocumento()">↩ Devolver</button>
        <button x-show="!tieneObs" class="btn btn-primary" @click="liberarDocumento()">✅ Liberar Documento →</button>
      </div>
    </div>
  </div>
</div>`
}
