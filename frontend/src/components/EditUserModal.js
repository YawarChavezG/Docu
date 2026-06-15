/**
 * src/components/EditUserModal.js
 * Modal de edición de usuario (Rol, Delegado, Periodo de vacaciones)
 * Estilo basado en ProfileModal.js
 */
import { ModalBaseTemplate } from './ModalBase.js'
import { rolesSistemaDB } from '../data/parametrosSistema.js'

export function initEditUserModal() {
  window.Alpine?.data('editUserData', () => ({
    open: false,
    user: null,
    editRol: '',
    editDelegado: '',
    editVacaciones: false,
    editFechaInicio: '',
    editFechaFin: '',
    listaDelegados: [],
    onGuardar: null,

    abrir(opts = {}) {
      this.user = opts.user || null
      this.editRol = opts.user?.rol || ''
      this.editDelegado = opts.user?.delegado || ''
      this.editVacaciones = opts.user?.vacaciones || false
      this.editFechaInicio = ''
      this.editFechaFin = ''
      this.listaDelegados = opts.listaDelegados || []
      this.onGuardar = opts.onGuardar || null
      this.open = true
    },
    cerrar() { this.open = false },
    guardar() {
      if (this.editVacaciones && (!this.editFechaInicio || !this.editFechaFin)) {
        window.toast('⚠️ Indique fecha de inicio y fin de vacaciones', 'warn')
        return
      }
      if (this.editVacaciones && this.editFechaInicio > this.editFechaFin) {
        window.toast('⚠️ La fecha de inicio no puede ser mayor a la fecha de fin', 'warn')
        return
      }
      const periodo = this.editVacaciones
        ? `${this.editFechaInicio} al ${this.editFechaFin}`
        : ''
      if (typeof this.onGuardar === 'function') {
        this.onGuardar({
          rol: this.editRol,
          delegado: this.editDelegado,
          vacaciones: this.editVacaciones,
          periodoVacaciones: periodo,
        })
      }
      this.open = false
    },
  }))

  window.editUserModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="editUserData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.editUserModal.abrir(opts), 200)
    },
  }

  window._rolesSistema = rolesSistemaDB
}

const inner = /* html */`
  <div>
    <div class="flex items-center justify-between mb-5">
      <h3 class="text-base font-bold text-slate-900">✏️ Editar Usuario</h3>
      <button @click="cerrar()" class="text-slate-400 hover:text-red-500 transition-colors text-lg leading-none cursor-pointer">✕</button>
    </div>

    <!-- Avatar + nombre -->
    <div class="flex items-center gap-3 mb-5 pb-4 border-b border-slate-100">
      <div class="w-12 h-12 rounded-full bg-gradient-to-br from-brand-500 to-blue-400 flex items-center justify-center text-base font-extrabold text-white flex-shrink-0"
           x-text="user?.initials ?? '??'"></div>
      <div>
        <div class="text-sm font-bold text-slate-900" x-text="user?.nombre ?? ''"></div>
        <div class="text-[11px] text-slate-500" x-text="'@' + (user?.user ?? '')"></div>
      </div>
    </div>

    <!-- Formulario -->
    <div class="space-y-3.5">
      <div>
        <label class="form-label">Rol del sistema</label>
        <select x-model="editRol" class="form-input text-xs">
          <option value="">Seleccionar rol...</option>
          <template x-for="r in (_rolesSistema || [])" :key="r">
            <option :value="r" x-text="r"></option>
          </template>
        </select>
      </div>

      <div>
        <label class="form-label">Delegado (Back-up)</label>
        <input type="text" x-model="editDelegado" list="lista-delegados-edit"
               placeholder="Escriba para buscar..." class="form-input text-xs">
        <datalist id="lista-delegados-edit">
          <template x-for="d in (listaDelegados || [])" :key="d">
            <option :value="d"></option>
          </template>
        </datalist>
      </div>

      <!-- Vacaciones -->
      <div class="border-t border-slate-100 pt-3 mt-2">
        <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer text-slate-800 mb-2">
          <input type="checkbox" x-model="editVacaciones" class="w-4 h-4 accent-brand-500 cursor-pointer">
          ✈️ Marcar como en vacaciones
        </label>
        <div x-show="editVacaciones" class="grid grid-cols-2 gap-2.5">
          <div>
            <label class="text-[10.5px] text-slate-500 font-semibold block mb-1">Desde:</label>
            <input type="date" x-model="editFechaInicio" class="form-input text-[11px] py-1.5">
          </div>
          <div>
            <label class="text-[10.5px] text-slate-500 font-semibold block mb-1">Hasta:</label>
            <input type="date" x-model="editFechaFin" class="form-input text-[11px] py-1.5">
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-slate-100">
      <button @click="cerrar()" class="btn">Cancelar</button>
      <button @click="guardar()" class="btn btn-primary">💾 Guardar Cambios</button>
    </div>
  </div>
`

export const EditUserModalTemplate = ModalBaseTemplate({
  dataName: 'editUserData',
  size: 'md',
  content: inner,
})
