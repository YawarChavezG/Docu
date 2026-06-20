/**
 * src/components/DelegarTareaModal.js
 * Modal de confirmación de delegación de tarea/revisor
 * Extraído de #modal-delegar
 *
 * Uso:
 *   window.delegarTareaModal.abrir({ tarea, de, a, onConfirm })
 *   window.delegarTareaModal.cerrar()
 */

export function initDelegarTareaModal() {
  window.Alpine?.data('delegarTareaModalData', () => ({
    open: false,
    tarea: '',
    de: '',
    a: '',
    _onConfirm: null,

    abrir({ tarea = '', de = '', a = '', onConfirm } = {}) {
      this.tarea = tarea
      this.de = de
      this.a = a
      this._onConfirm = onConfirm || null
      this.open = true
    },

    cerrar() {
      this.open = false
      this._onConfirm = null
    },

    confirmar() {
      if (this._onConfirm) this._onConfirm()
      this.cerrar()
    },
  }))

  window.delegarTareaModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="delegarTareaModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.delegarTareaModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="delegarTareaModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const DelegarTareaModalTemplate = /* html */`
<div x-data="delegarTareaModalData">
  <template x-teleport="body">
    <div x-show="open"
         @keydown.escape.window="cerrar()"
         class="modal-overlay"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0">

      <div @click.stop class="modal-box text-center border-t-4 border-violet-600 max-h-[90vh] overflow-y-auto">
        <div class="text-4xl mb-3.5">→</div>
        <div class="text-base font-bold text-slate-800 mb-2">Delegar Tarea</div>
        <p class="text-xs text-slate-600 mb-5 leading-relaxed">
          Va a delegar la tarea <strong x-text="tarea || '—'"></strong> de <strong x-text="de || '—'"></strong> a <strong x-text="a || '—'"></strong>.
        </p>
        <div class="flex gap-2.5 justify-center">
          <button @click="cerrar()" class="btn flex-1">Cancelar</button>
          <button @click="confirmar()" class="btn btn-primary flex-1 bg-violet-600 border-violet-600 hover:bg-violet-700 hover:border-violet-700">Confirmar</button>
        </div>
      </div>

    </div>
  </template>
</div>`
