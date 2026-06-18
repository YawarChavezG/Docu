/**
 * ConfirmDelegadoModal.js — Modal para Issue 3.1
 *
 * Reemplaza el confirm() nativo cuando se guarda un usuario con rol
 * que sugiere delegado pero no se asignó uno.
 * Mismo patron que ConfirmCancelModal.js.
 */
export function initConfirmDelegadoModal() {
  window.Alpine?.data('confirmDelegadoModalData', () => ({
    open: false,
    mensaje: '',
    _onConfirm: null,

    abrir({ mensaje = 'Este rol sugiere asignar un delegado. \u00bfGuardar de todos modos?', onConfirm } = {}) {
      this.mensaje = mensaje
      this._onConfirm = onConfirm || null
      this.open = true
    },

    cerrar() {
      this.open = false
      this._onConfirm = null
    },

    confirmar() {
      this.open = false
      if (this._onConfirm) this._onConfirm()
      this._onConfirm = null
    },
  }))

  window.confirmDelegadoModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="confirmDelegadoModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.confirmDelegadoModal.abrir(opts), 200)
    },
  }
}

export const ConfirmDelegadoModalTemplate = /* html */`
<div x-data="confirmDelegadoModalData">
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
         style="z-index:8600">
      <div @click.stop
           x-transition:enter="transition ease-out duration-200"
           x-transition:enter-start="opacity-0 scale-95"
           x-transition:enter-end="opacity-100 scale-100"
           x-transition:leave="transition ease-in duration-150"
           x-transition:leave-start="opacity-100 scale-100"
           x-transition:leave-end="opacity-0 scale-95"
           class="modal-box max-w-sm text-center max-h-[90vh] overflow-y-auto">
        <div class="w-12 h-12 rounded-full bg-amber-50 border border-amber-100 flex items-center justify-center mx-auto mb-4">
          <span class="text-2xl">⚠️</span>
        </div>
        <h2 class="text-[15px] font-bold text-slate-800 mb-2">Delegado no asignado</h2>
        <p class="text-xs text-slate-500 mb-6 leading-relaxed" x-text="mensaje"></p>
        <div class="flex gap-3">
          <button @click="cerrar()" class="btn flex-1">Cancelar</button>
          <button @click="confirmar()" class="btn flex-1 bg-amber-500 hover:bg-amber-600 text-white border-amber-500 hover:border-amber-600">Guardar de todos modos</button>
        </div>
      </div>
    </div>
  </template>
</div>`
