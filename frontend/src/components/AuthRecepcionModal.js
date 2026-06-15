/**
 * src/components/AuthRecepcionModal.js
 * Modal de doble auth para confirmar recepción de copia física
 * Extraído de #modal-auth-recepcion
 *
 * Uso:
 *   window.authRecepcionModal.abrir({ docInfo, destinatario, onConfirm })
 *   window.authRecepcionModal.cerrar()
 */

import { ModalBaseTemplate } from './ModalBase.js'

export function initAuthRecepcionModal() {
  window.Alpine?.data('authRecepcionModalData', () => ({
    open: false,
    docInfo: '',
    destinatario: '',
    _onConfirm: null,

    abrir({ docInfo = '', destinatario = '', onConfirm } = {}) {
      this.docInfo = docInfo
      this.destinatario = destinatario
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

  window.authRecepcionModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="authRecepcionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.authRecepcionModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="authRecepcionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

const AuthRecepcionContent = /* html */`
  <div class="text-center">
    <div class="text-[44px] mb-3.5">✅</div>
    <div class="text-base font-bold text-slate-800 mb-2">Confirmar Recepción</div>
    <p class="text-xs text-slate-600 mb-4 leading-relaxed">
      Va a confirmar la recepción física de la copia controlada.<br>
      Documento: <strong x-text="docInfo || '—'"></strong><br>
      Destinatario: <strong x-text="destinatario || '—'"></strong>
    </p>
    <p class="text-[11px] text-slate-400 mb-5">Se requerirá su firma digital para completar la recepción.</p>

    <div class="flex gap-2.5 justify-center">
      <button @click="cerrar()" class="btn flex-1">Cancelar</button>
      <button @click="confirmar()" class="btn flex-1" style="background:#059669;color:#fff;border-color:#059669;">Confirmar</button>
    </div>
  </div>
`

export const AuthRecepcionModalTemplate = ModalBaseTemplate({
  dataName: 'authRecepcionModalData',
  size: 'md',
  content: AuthRecepcionContent,
})
