/**
 * src/components/ProfileModal.js
 * Modal "Mi Perfil" + Delegación + Ausencias
 */

import { listaEmpleados } from '../data/users.js'

export function initProfileModal() {
  window.Alpine?.data('profileModalData', () => ({
    open: false,
    delegarOpen: false,
    nombre: '',
    cargo: '',
    area: '',
    iniciales: '',
    delegadoActual: 'No asignado',
    delegadoDesvinculado: false,
    inputDelegado: '',
    isAusente: false,
    fechaInicio: '',
    fechaFin: '',
    delegarNombre: '',
    delegarCargo: '',

    abrir() {
      const auth = window.Alpine?.store('auth')
      if (auth) {
        this.nombre    = auth.user?.name      || 'Usuario'
        this.cargo     = auth.user?.roleLabel || 'Sin cargo'
        this.area      = auth.user?.area      || 'Sin área'
        this.iniciales = auth.user?.initials  || '??'
        this.delegadoDesvinculado = auth.user?.hasDelegadoAlert || false
      }
      if (this.delegadoDesvinculado) {
        this.inputDelegado = ''
        this.delegadoActual = '⚠️ Sin delegado (desvinculado)'
      }
      this.open = true
    },

    cerrar() { this.open = false },

    toggleFechasAusencia() {},

    guardar() {
      const delegado = this.inputDelegado.trim()
      if (!delegado && (this.delegadoActual === 'No asignado' || this.delegadoDesvinculado)) {
        window.toast('⚠️ Por favor, seleccione un delegado válido de la lista.', 'warn')
        return
      }
      const nombreFinal = delegado || this.delegadoActual.split('\n')[0]

      if (this.isAusente) {
        if (!this.fechaInicio || !this.fechaFin) {
          window.toast('⚠️ Debe indicar la fecha de inicio y fin de su ausencia.', 'warn')
          return
        }
        if (this.fechaInicio > this.fechaFin) {
          window.toast('⚠️ La fecha de inicio no puede ser mayor a la fecha de fin.', 'warn')
          return
        }
        const fmt = (d) => {
          const [y,m,day] = d.split('-')
          return `${day}/${m}/${y}`
        }
        this.delegadoActual = `${nombreFinal} · ✈️ AUSENTE: ${fmt(this.fechaInicio)} al ${fmt(this.fechaFin)}`
        window.toast('✅ Ausencia programada. Tareas enrutadas al delegado.', 'success')
      } else {
        this.delegadoActual = nombreFinal
        window.toast('✅ Delegado actualizado. Usted sigue recibiendo sus tareas.', 'success')
      }

      if (delegado) {
        this.delegadoDesvinculado = false
        const auth = window.Alpine?.store('auth')
        if (auth && auth.user) auth.user.hasDelegadoAlert = false
      }
    },

    abrirDelegar(nombre, cargo) {
      this.delegarNombre = nombre
      this.delegarCargo  = cargo
      this.delegarOpen   = true
    },
    confirmarDelegacion() {
      this.delegarOpen = false
      window.toast('Responsabilidad delegada exitosamente. Se ha notificado al sucesor.', 'success')
      setTimeout(() => window.navigate('/bandeja'), 1200)
    },
  }))

  window.profileModal = {
    abrir() {
      const el = document.querySelector('[x-data="profileModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir()
      else setTimeout(() => window.profileModal.abrir(), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="profileModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
    abrirDelegar(nombre, cargo) {
      const el = document.querySelector('[x-data="profileModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrirDelegar(nombre, cargo)
    },
  }

  window._listaEmpleados = listaEmpleados

  window.addEventListener('open-profile', () => {
    window.profileModal?.abrir()
  })
}

export const ProfileModalTemplate = /* html */`
<div x-data="profileModalData">
  <template x-teleport="body">

    <!-- Modal Mi Perfil -->
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrar()"
         class="modal-overlay" style="z-index:8000">

      <div @click.stop
           class="modal-box max-w-[400px] relative max-h-[90vh] overflow-y-auto">

        <button @click="cerrar()"
                class="absolute top-3.5 right-3.5 text-slate-400 hover:text-red-500 transition-colors text-lg leading-none cursor-pointer">✕</button>

        <!-- Avatar + Datos -->
        <div class="text-center mb-5">
          <div class="w-[90px] h-[90px] rounded-full bg-gradient-to-br from-brand-500 to-blue-400 mx-auto mb-3.5 flex items-center justify-center text-3xl font-extrabold text-white border-[3px] border-blue-200 shadow-lg" x-text="iniciales"></div>
          <div class="text-xl font-bold text-slate-900 -tracking-wide" x-text="nombre"></div>
          <div class="text-[13px] text-brand-500 font-semibold mt-0.5" x-text="cargo"></div>
          <div class="text-[11.5px] text-slate-500 mt-1.5 inline-flex items-center gap-1 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200">
            🏢 Área: <span class="font-semibold text-slate-700" x-text="area"></span>
          </div>
        </div>

        <!-- Banner delegado desvinculado -->
        <div x-show="delegadoDesvinculado"
             class="bg-red-50 border border-red-300 rounded-xl p-3 mb-4 flex items-start gap-2.5"
             style="display:none"
             :style="delegadoDesvinculado ? 'display:flex' : 'display:none'">
          <span class="text-xl flex-shrink-0">⚠️</span>
          <div>
            <div class="text-xs font-bold text-red-700 mb-0.5">Delegado desvinculado</div>
            <div class="text-[11px] text-red-800 leading-snug">Su delegado anterior ya no pertenece a la organización o cambió de área. Por favor asigne un nuevo delegado.</div>
          </div>
        </div>

        <!-- Sección Delegado -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <div class="text-[13px] font-bold text-slate-700 mb-1.5 flex items-center gap-1.5">🤝 Delegado (Back-up) y Ausencias</div>
          <p class="text-[11px] text-slate-500 mb-3.5 leading-snug">Seleccione la persona que asumirá sus tareas. Puede programar una ausencia para activar el desvío automático.</p>

          <div class="mb-3">
            <input type="text" x-model="inputDelegado" list="lista-empleados-profile"
                   placeholder="Escriba para buscar a su delegado..."
                   class="form-input text-xs">
            <datalist id="lista-empleados-profile">
              <template x-for="emp in (_listaEmpleados || [])" :key="emp">
                <option :value="emp"></option>
              </template>
            </datalist>
          </div>

          <!-- Checkbox ausencia -->
          <div class="border-t border-slate-200 pt-3 mt-3.5">
            <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer text-slate-800">
              <input type="checkbox" x-model="isAusente" class="w-4 h-4 accent-brand-500 cursor-pointer">
              ✈️ Marcarme como ausente (Vacaciones / Licencia)
            </label>
          </div>

          <!-- Fechas ausencia -->
          <div x-show="isAusente"
               class="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3"
               style="display:none"
               :style="isAusente ? 'display:block' : 'display:none'">
            <div class="text-[10.5px] text-blue-700 mb-2.5 leading-snug">Durante este periodo, las nuevas tareas se enrutarán automáticamente a su delegado.</div>
            <div class="grid grid-cols-2 gap-2.5">
              <div>
                <label class="text-[10.5px] text-blue-700 font-semibold block mb-1">Desde:</label>
                <input type="date" x-model="fechaInicio" class="form-input text-[11px] py-1.5">
              </div>
              <div>
                <label class="text-[10.5px] text-blue-700 font-semibold block mb-1">Hasta:</label>
                <input type="date" x-model="fechaFin" class="form-input text-[11px] py-1.5">
              </div>
            </div>
          </div>

          <!-- Footer delegado -->
          <div class="flex justify-between items-center mt-4 border-t border-dashed border-slate-300 pt-3">
            <div class="text-[11px] text-slate-600">
              Estado actual:<br>
              <strong class="text-brand-500 text-xs" x-text="delegadoActual"></strong>
            </div>
            <button @click="guardar()" class="btn btn-primary rounded-full px-5">Guardar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Delegar Tarea -->
    <div x-show="delegarOpen"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="delegarOpen=false"
         class="modal-overlay" style="z-index:8500;display:none">

      <div @click.stop class="modal-box max-w-[360px] text-center max-h-[90vh] overflow-y-auto">
        <div class="text-4xl mb-2.5">👤➡️👤</div>
        <div class="text-base font-bold text-slate-900 mb-2.5">Delegar Responsabilidad</div>
        <div class="text-[13px] text-slate-600 mb-5 leading-relaxed">
          Usted va a delegar la revisión/aprobación de este documento a su reemplazo configurado en el sistema:
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div class="text-[15px] font-bold text-blue-700 mb-1" x-text="delegarNombre"></div>
          <div class="text-xs text-brand-500" x-text="delegarCargo"></div>
        </div>
        <div class="flex gap-2.5">
          <button @click="delegarOpen=false" class="btn flex-1">Cancelar</button>
          <button @click="confirmarDelegacion()" class="btn btn-primary flex-1">Confirmar Delegación</button>
        </div>
      </div>
    </div>

  </template>
</div>`