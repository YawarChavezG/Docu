/**
 * src/components/ParametrosDifusionModal.js
 * Modal de configuración de parámetros de difusión de documento
 * Incluye árbol jerárquico de grupos Outlook con chips editables
 *
 * Uso:
 *   window.parametrosDifusionModal.abrir({ docNombre, docCodigo, tipo, config })
 *   window.parametrosDifusionModal.cerrar()
 */

import { gerenciasDB } from '../data/gerencias.js'

export function initParametrosDifusionModal() {
  window.Alpine?.data('parametrosDifusionModalData', () => ({
    open: false,
    docNombre: '',
    docCodigo: '',
    tipo: 'ControlLectura',
    chkLectura: true,
    chkEval: false,
    fechaInicio: '',
    fechaLimite: '',
    gruposSeleccionados: [],
    showTreePanel: false,
    treeData: [],

    abrir({ docNombre = '', docCodigo = '', tipo = 'ControlLectura', config = {} } = {}) {
      this.docNombre = docNombre
      this.docCodigo = docCodigo
      this.tipo = tipo
      this.fechaInicio = config.fechaInicio || ''
      this.fechaLimite = config.fechaLimite || ''
      this.gruposSeleccionados = config.grupos || []
      this.showTreePanel = false
      this.treeData = this._buildTree()
      this.open = true
    },

    cerrar() {
      this.open = false
      this.showTreePanel = false
    },

    _buildTree() {
      return gerenciasDB.map(g => ({
        id: g.id,
        nombre: g.nombre,
        checked: false,
        indeterminate: false,
        subs: g.areas.map(a => ({
          id: a.cod,
          nombre: a.nombre,
          checked: this.gruposSeleccionados.includes(a.nombre),
        })),
      }))
    },

    toggleGrupo(nombre) {
      const idx = this.gruposSeleccionados.indexOf(nombre)
      if (idx === -1) {
        this.gruposSeleccionados.push(nombre)
      } else {
        this.gruposSeleccionados.splice(idx, 1)
      }
    },

    toggleGrupoNode() {
      this.showTreePanel = !this.showTreePanel
      this.treeData = this._buildTree()
    },

    togglePadre(grupo) {
      grupo.checked = !grupo.checked
      grupo.indeterminate = false
      grupo.subs.forEach(s => { s.checked = grupo.checked })
      this._syncGrupos()
    },

    toggleHijo(grupo, hijo) {
      hijo.checked = !hijo.checked
      const todos = grupo.subs.every(s => s.checked)
      const algunos = grupo.subs.some(s => s.checked)
      grupo.checked = todos
      grupo.indeterminate = !todos && algunos
      this._syncGrupos()
    },

    _syncGrupos() {
      const selected = []
      this.treeData.forEach(g => {
        if (g.checked && !g.indeterminate) {
          selected.push(g.nombre)
          g.subs.forEach(s => { s.checked = true })
        } else {
          g.subs.forEach(s => {
            if (s.checked && !selected.includes(s.nombre)) {
              selected.push(s.nombre)
            }
          })
        }
      })
      this.gruposSeleccionados = selected
    },

    agregarGrupo() {
      const nombre = window.prompt('Nombre del nuevo grupo de Outlook:')
      if (nombre && nombre.trim()) {
        const val = nombre.trim()
        if (!this.gruposSeleccionados.includes(val)) {
          this.gruposSeleccionados.push(val)
        }
      }
    },

    quitarGrupo(nombre) {
      this.gruposSeleccionados = this.gruposSeleccionados.filter(g => g !== nombre)
    },

    guardar() {
      if (!this.fechaInicio || !this.fechaLimite) {
        window.toast('⚠️ Configure fecha de inicio y fecha límite.', 'warn')
        return
      }
      if (this.fechaInicio > this.fechaLimite) {
        window.toast('⚠️ La fecha fin no puede ser anterior a la fecha de inicio.', 'warn')
        return
      }
      this.open = false
      window.toast('✅ Parámetros de difusión guardados.', 'success')
    },

    reabrirCiclo() {
      if (!this.fechaInicio || !this.fechaLimite) {
        window.toast('⚠️ Configure fecha de inicio y fecha límite.', 'warn')
        return
      }
      if (this.fechaInicio > this.fechaLimite) {
        window.toast('⚠️ La fecha fin no puede ser anterior a la fecha de inicio.', 'warn')
        return
      }
      window.dispatchEvent(new CustomEvent('reabrir-difusion', {
        detail: { docCodigo: this.docCodigo, docNombre: this.docNombre, fechaInicio: this.fechaInicio, fechaLimite: this.fechaLimite }
      }))
      this.cerrar()
    },
  }))

  window.parametrosDifusionModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="parametrosDifusionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.parametrosDifusionModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="parametrosDifusionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const ParametrosDifusionModalTemplate = /* html */`
<div x-data="parametrosDifusionModalData">
  <template x-teleport="body">
    <div x-show="open"
         @keydown.escape.window="cerrar()"
         class="modal-overlay"
         style="display:none"
         :style="open ? 'display:flex' : 'display:none'">

      <div @click.stop
           class="bg-white rounded-2xl shadow-glass-lg p-6 w-full max-w-lg flex flex-col max-h-[90vh] overflow-visible">

        <!-- Título -->
        <div class="mb-1">
          <div class="text-base font-semibold text-brand-600">Configurar Parámetros de Difusión</div>
          <div class="text-xs text-slate-500 mt-1 leading-relaxed">
            Documento: <strong x-text="docNombre || '—'"></strong>
            (<span class="font-mono text-[11px]" x-text="docCodigo || '—'"></span>)
          </div>
        </div>

        <!-- Requerimiento según tipo -->
        <div class="p-3.5 mb-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div class="text-[11.5px] font-bold text-blue-700 mb-2 uppercase tracking-wide">Requerimiento de Difusión Actual</div>
          <div class="flex gap-5">
            <label x-show="tipo === 'Control Lectura'" class="flex items-center gap-1.5 text-xs text-slate-800">
              <input type="checkbox" checked disabled class="accent-brand-600 w-4 h-4"> Control de Lectura
            </label>
            <label x-show="tipo === 'Evaluación'" class="flex items-center gap-1.5 text-xs text-slate-800">
              <input type="checkbox" checked disabled class="accent-brand-600 w-4 h-4"> Evaluación (Examen)
            </label>
          </div>
        </div>

        <!-- Fechas -->
        <div class="form-grid-2 mb-4">
          <div>
            <label class="form-label">Fecha de Inicio</label>
            <input type="date" x-model="fechaInicio" class="form-input text-xs">
          </div>
          <div>
            <label class="form-label">Fecha Límite</label>
            <input type="date" x-model="fechaLimite" class="form-input text-xs">
          </div>
        </div>

        <!-- Grupos Outlook - Árbol Jerárquico -->
        <div class="mb-6 relative">
          <label class="form-label">Grupos a notificar (Outlook)</label>

          <!-- Chips seleccionados -->
          <div class="flex flex-wrap gap-1.5 mb-2.5 min-h-[28px]">
            <template x-for="grupo in gruposSeleccionados" :key="grupo">
              <span class="inline-flex items-center gap-1.5 bg-green-50 border border-green-200 text-green-800 px-2 py-0.5 rounded-full text-[11px]">
                ✓ <span x-text="grupo"></span>
                <span @click="quitarGrupo(grupo)" class="cursor-pointer font-bold text-[10px] text-red-500 hover:opacity-100 opacity-60 ml-1">✕</span>
              </span>
            </template>
          </div>

          <!-- Botón Abrir Árbol + Panel flotante -->
          <div class="relative">
            <button type="button" @click="toggleGrupoNode()" class="btn btn-sm bg-blue-50 text-brand-600 border-blue-200 hover:bg-blue-100">
              🏢 <span x-text="showTreePanel ? 'Cerrar árbol' : '☰ Seleccionar grupos del árbol'"></span>
            </button>

            <!-- Panel flotante del árbol -->
            <div x-show="showTreePanel"
                 @click.stop
                 class="absolute top-full left-0 mt-1.5 z-50 bg-white border border-blue-200 rounded-xl p-3.5 w-[420px] max-h-72 overflow-y-auto shadow-card-md"
                 style="display:none" :style="showTreePanel ? 'display:block' : 'display:none'">

              <div class="text-[11px] font-bold text-slate-500 mb-2.5 pb-2 border-b border-slate-100">
                Jerarquía de grupos — haga clic para seleccionar
              </div>

              <template x-for="grupo in treeData" :key="grupo.id">
                <div class="mb-2">
                  <label class="flex items-center gap-1.5 text-xs font-semibold text-slate-800 cursor-pointer py-0.5">
                    <input type="checkbox"
                           :checked="grupo.checked"
                           :indeterminate="grupo.indeterminate"
                           @change="togglePadre(grupo)"
                           class="w-3.5 h-3.5 cursor-pointer accent-brand-600 flex-shrink-0">
                    🏢 <span x-text="grupo.nombre"></span>
                  </label>
                  <div class="ml-5 flex flex-col gap-0.5 pl-1 border-l-2 border-slate-100">
                    <template x-for="sub in grupo.subs" :key="sub.id">
                      <label class="flex items-center gap-1.5 text-[11.5px] text-slate-600 cursor-pointer py-0.5">
                        <input type="checkbox"
                               :checked="sub.checked"
                               @change="toggleHijo(grupo, sub)"
                               class="w-3.5 h-3.5 cursor-pointer accent-brand-600 flex-shrink-0">
                        <span x-text="sub.nombre"></span>
                      </label>
                    </template>
                  </div>
                </div>
              </template>

              <div class="flex gap-2 mt-3 pt-2.5 border-t border-slate-100">
                <button type="button" @click="showTreePanel=false" class="btn btn-sm flex-1">Cerrar</button>
                <button type="button" @click="showTreePanel=false" class="btn btn-sm btn-primary flex-1">Aplicar</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between gap-2 pt-4 border-t border-slate-100 mt-auto">
          <button @click="reabrirCiclo()" class="btn btn-sm btn-danger" title="Crear un nuevo ciclo a partir de hoy">🔄 Re-abrir</button>
          <div class="flex items-center gap-2">
            <button @click="cerrar()" class="btn btn-sm">Cancelar</button>
            <button @click="guardar()" class="btn btn-sm btn-primary">Guardar y Continuar →</button>
          </div>
        </div>

      </div>
    </div>
  </template>
</div>`
