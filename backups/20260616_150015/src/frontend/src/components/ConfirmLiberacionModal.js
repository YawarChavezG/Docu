/**
 * src/components/ConfirmLiberacionModal.js
 * Modal de confirmación dinámica para liberar o devolver documento
 * Extraído de #modal-confirm-liberacion (líneas 1438–1448) y lógica de decisión
 *
 * Uso:
 *   window.confirmLiberacionModal.abrir({ modo, titulo, mensaje, onConfirm })
 *   window.confirmLiberacionModal.cerrar()
 *
 * Modos: 'liberar' | 'devolver' | 'observacion'
 */

export function initConfirmLiberacionModal() {
  window.Alpine?.data('confirmLiberacionModalData', () => ({
    open: false,
    modo: 'liberar',
    titulo: 'Liberar Documento',
    icono: '✅',
    mensaje: '',
    _onConfirm: null,

    abrir({ modo = 'liberar', titulo = '', mensaje = '', onConfirm } = {}) {
      this.modo = modo
      if (!titulo) {
        this.titulo = modo === 'liberar' ? 'Liberar Documento' : modo === 'devolver' ? 'Devolver Documento' : 'Confirmar Acción'
      } else {
        this.titulo = titulo
      }
      this.icono = modo === 'liberar' ? '✅' : modo === 'devolver' ? '↩️' : '⚠️'
      this.mensaje = mensaje || (modo === 'liberar'
        ? '¿Está seguro que desea liberar este documento? Se notificará a los revisores y estará disponible en la Lista Maestra.'
        : modo === 'devolver'
        ? '¿Está seguro que desea devolver este documento al elaborador? Se le notificará con sus observaciones.'
        : '¿Está seguro que desea continuar?')
      this._onConfirm = onConfirm || null
      this.open = true
    },

    cerrar() {
      this.open = false
    },

    confirmar() {
      this.open = false
      window.toast(this.modo === 'liberar' ? '✅ Documento liberado exitosamente. Se ha notificado a los revisores.' : '↩️ Documento devuelto al elaborador.', 'success')
      if (this._onConfirm) this._onConfirm({ modo: this.modo })
    },
  }))

  window.confirmLiberacionModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="confirmLiberacionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.confirmLiberacionModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="confirmLiberacionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const ConfirmLiberacionModalTemplate = /* html */`
<div x-data="confirmLiberacionModalData">
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
        <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4"
             :class="modo === 'devolver' ? 'bg-amber-50 border border-amber-100' : 'bg-blue-50 border border-blue-100'">
          <span class="text-2xl" x-text="icono"></span>
        </div>
        <h2 class="text-[15px] font-bold text-slate-800 mb-2" x-text="titulo"></h2>
        <p class="text-xs text-slate-500 mb-6 leading-relaxed" x-text="mensaje"></p>
        <div class="flex gap-3">
          <button @click="cerrar()" class="btn flex-1">Cancelar</button>
          <button @click="confirmar()"
                  class="btn flex-1"
                  :class="modo === 'devolver' ? 'bg-amber-700 text-white border-amber-700 hover:bg-amber-800' : 'btn-primary'">
            Confirmar
          </button>
        </div>
      </div>
    </div>
  </template>
</div>`
