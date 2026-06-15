/**
 * src/components/ConfirmDeleteModal.js
 * Modal genérico de confirmación de eliminación.
 * Usa ModalBase como shell y expone window.confirmDeleteModal.abrir(opts)
 */
import { ModalBaseTemplate } from './ModalBase.js'

export function initConfirmDeleteModal() {
  window.Alpine?.data('confirmDeleteData', () => ({
    open: false,
    titulo: 'Confirmar eliminación',
    mensaje: '¿Está seguro de que desea eliminar este elemento?',
    itemLabel: '',
    onConfirm: null,

    abrir(opts = {}) {
      this.titulo = opts.titulo || 'Confirmar eliminación'
      this.mensaje = opts.mensaje || '¿Está seguro de que desea eliminar este elemento?'
      this.itemLabel = opts.itemLabel || ''
      this.onConfirm = opts.onConfirm || null
      this.open = true
    },
    cerrar() { this.open = false },
    confirmar() {
      if (typeof this.onConfirm === 'function') {
        this.onConfirm()
      }
      this.open = false
    },
  }))

  window.confirmDeleteModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="confirmDeleteData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.confirmDeleteModal.abrir(opts), 200)
    },
  }
}

const inner = /* html */`
  <div class="text-center">
    <div class="text-4xl mb-2">⚠️</div>
    <h3 class="text-base font-bold text-slate-900 mb-2" x-text="titulo"></h3>
    <p class="text-[13px] text-slate-600 leading-relaxed mb-1" x-html="$sanitize(mensaje)"></p>
    <p x-show="itemLabel" class="text-[12px] font-semibold text-brand-600 mb-5" x-text="itemLabel"></p>
    <div class="flex gap-2.5">
      <button @click="cerrar()" class="btn flex-1">Cancelar</button>
      <button @click="confirmar()" class="btn btn-danger flex-1">🗑 Eliminar</button>
    </div>
  </div>
`

export const ConfirmDeleteModalTemplate = ModalBaseTemplate({
  dataName: 'confirmDeleteData',
  size: 'sm',
  content: inner,
})
