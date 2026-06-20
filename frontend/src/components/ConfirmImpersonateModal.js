/**
 * src/components/ConfirmImpersonateModal.js
 * Modal de confirmacion para impersonate (reemplaza confirm() nativo del browser)
 *
 * Sesion 27: el confirm() nativo es feo, no muestra contexto y rompe la UI
 * con un alert del SO. Este modal muestra la info del usuario a impersonar,
 * el impacto (rol, permisos) y pide confirmacion explicita.
 */
export function initConfirmImpersonateModal() {
  window.Alpine?.data('confirmImpersonateData', () => ({
    open: false,
    submitting: false,
    target: null,           // { id, username, nombre_completo, cargo, area_sigla, gerencia_sigla, roles, ad_info }
    me: null,               // { username, nombre_completo } (sesion real)
    _onConfirm: null,

    abrir({ target, me, onConfirm }) {
      this.target = target || null
      this.me = me || null
      this.submitting = false
      this._onConfirm = onConfirm || null
      this.open = true
    },

    cerrar() {
      this.open = false
      this.submitting = false
    },

    confirmar() {
      if (this.submitting) return
      this.submitting = true
      const cb = this._onConfirm
      this._onConfirm = null
      this.open = false
      this.submitting = false
      if (cb) cb()
    },

    get targetRolLabel() {
      const rol = (this.target?.roles || [])[0] || ''
      const map = {
        'ADMIN': 'Administrador',
        'ETO': 'Gestor Documental ETO',
        'ELABORADOR - REVISOR': 'Elaborador - Revisor',
        'ELABORADOR - REVISOR - APROBADOR': 'Elaborador - Revisor - Aprobador',
        'VISUALIZADOR (CL-EVAL)': 'Visualizador',
      }
      return map[rol] || rol
    },
  }))

  window.confirmImpersonate = {
    abrir(opts) {
      const el = document.querySelector('[x-data="confirmImpersonateData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.confirmImpersonate.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="confirmImpersonateData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const ConfirmImpersonateModalTemplate = /* html */`
<div x-data="confirmImpersonateData">
  <template x-teleport="body">
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrar()"
         class="modal-overlay"
         style="z-index:8600;display:none;">

      <div @click.stop
           x-transition:enter="transition ease-out duration-200"
           x-transition:enter-start="opacity-0 scale-95"
           x-transition:enter-end="opacity-100 scale-100"
           class="modal-box max-w-[440px] relative max-h-[90vh] overflow-y-auto">

        <button @click="cerrar()" :disabled="submitting"
                class="absolute top-3.5 right-3.5 text-slate-400 hover:text-red-500 transition-colors text-lg leading-none cursor-pointer disabled:opacity-30">✕</button>

        <!-- Header con icono + titulo -->
        <div class="text-center mb-5">
          <div class="w-[68px] h-[68px] rounded-full bg-gradient-to-br from-amber-500 to-orange-500 mx-auto mb-3.5 flex items-center justify-center text-3xl shadow-lg">🕵️</div>
          <h2 class="text-[16px] font-bold text-slate-800">Impersonar a este usuario</h2>
          <p class="text-[11.5px] text-slate-500 mt-1.5 leading-snug">
            Vas a iniciar sesion <strong>como el usuario</strong> de abajo. Tu sesion real queda en segundo plano.
          </p>
        </div>

        <!-- Card del usuario a impersonar -->
        <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-full bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                 x-text="(target?.nombre_completo || '?').split(' ').map(n => n[0]).slice(0,2).join('').toUpperCase()"></div>
            <div class="min-w-0 flex-1">
              <div class="text-[13px] font-bold text-slate-800 truncate" x-text="target?.nombre_completo || '—'"></div>
              <div class="text-[10.5px] text-slate-500 font-mono" x-text="'@' + (target?.username || '—')"></div>
            </div>
          </div>
          <div class="mt-3 grid grid-cols-2 gap-2 text-[10.5px]">
            <div>
              <div class="text-slate-400 font-semibold">Rol</div>
              <div class="text-amber-700 font-bold" x-text="targetRolLabel"></div>
            </div>
            <div>
              <div class="text-slate-400 font-semibold">Cargo</div>
              <div class="text-slate-700 truncate" x-text="target?.cargo || '—'"></div>
            </div>
            <div>
              <div class="text-slate-400 font-semibold">Area</div>
              <div class="text-slate-700 truncate"
                   x-text="target?.gerencia_sigla ? (target.gerencia_sigla + (target.area_sigla ? ' / ' + target.area_sigla : '')) : (target?.ad_info || '—')"></div>
            </div>
            <div>
              <div class="text-slate-400 font-semibold">Estado</div>
              <div class="text-slate-700" x-text="target?.estado || '—'"></div>
            </div>
          </div>
        </div>

        <!-- Banner de impacto -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-start gap-2">
          <span class="text-base flex-shrink-0">ℹ️</span>
          <div class="text-[10.5px] text-blue-800 leading-snug">
            <strong>Que va a pasar:</strong> la aplicacion se va a recargar y vas a ver
            la pantalla de inicio del usuario impersonado, con su sidebar y permisos.
            Para volver a tu sesion real, hace click en
            <span class="font-mono bg-blue-100 px-1 py-0.5 rounded">✕ Terminar Impersonate</span>
            en el banner superior.
          </div>
        </div>

        <!-- Sesion real -->
        <div class="text-[10.5px] text-slate-500 text-center mb-4">
          Sesion real: <span class="font-mono font-semibold text-slate-700" x-text="me?.username || '—'"></span>
        </div>

        <!-- Footer con botones -->
        <div class="flex gap-2.5">
          <button @click="cerrar()" :disabled="submitting"
                  class="btn flex-1">Cancelar</button>
          <button @click="confirmar()" :disabled="submitting"
                  class="btn flex-1 bg-amber-500 hover:bg-amber-600 text-white border-amber-500 hover:border-amber-600"
                  :class="submitting && 'opacity-60 cursor-not-allowed'">
            <span x-text="submitting ? 'Iniciando...' : '🕵️ Si, impersonar'"></span>
          </button>
        </div>
      </div>
    </div>
  </template>
</div>`
