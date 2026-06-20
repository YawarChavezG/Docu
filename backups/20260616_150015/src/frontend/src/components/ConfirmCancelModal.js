/**
 * src/components/ConfirmCancelModal.js
 * Modal global de confirmación para acciones destructivas (cancelar, salir, etc.)
 */

export function initConfirmCancelModal() {
  window.Alpine?.data('confirmCancelModalData', () => ({
    open: false,
    titulo: 'Confirmar cancelación',
    mensaje: '',
    _onConfirm: null,

    abrir({ titulo = 'Confirmar cancelación', mensaje = '', onConfirm } = {}) {
      this.titulo = titulo
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

  window.confirmCancelModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="confirmCancelModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.confirmCancelModal.abrir(opts), 200)
    },
  }
}

export const ConfirmCancelModalTemplate = /* html */`
<div x-data="confirmCancelModalData">
  <template x-teleport="body">
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrar()"
         class="modal-overlay">
      <div @click.stop
           x-transition:enter="transition ease-out duration-200"
           x-transition:enter-start="opacity-0 scale-95"
           x-transition:enter-end="opacity-100 scale-100"
           x-transition:leave="transition ease-in duration-150"
           x-transition:leave-start="opacity-100 scale-100"
           x-transition:leave-end="opacity-0 scale-95"
           class="modal-box max-w-sm text-center max-h-[90vh] overflow-y-auto">
        <div class="w-12 h-12 rounded-full bg-red-50 border border-red-100 flex items-center justify-center mx-auto mb-4">
          <span class="text-2xl">⚠️</span>
        </div>
        <h2 class="text-[15px] font-bold text-slate-800 mb-2" x-text="titulo"></h2>
        <p class="text-xs text-slate-500 mb-6 leading-relaxed" x-text="mensaje"></p>
        <div class="flex gap-3">
          <button @click="cerrar()" class="btn flex-1">No, continuar</button>
          <button @click="confirmar()" class="btn btn-danger flex-1">Sí, cancelar</button>
        </div>
      </div>
    </div>
  </template>
</div>`
