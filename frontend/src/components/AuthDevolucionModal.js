/**
 * src/components/AuthDevolucionModal.js
 * Modal de doble auth para devolución de copia controlada
 * Extraído de #modal-auth-dev
 *
 * Uso:
 *   window.authDevolucionModal.abrir({ docInfo, destinatario, onConfirm })
 *   window.authDevolucionModal.cerrar()
 */

import { ModalBaseTemplate } from './ModalBase.js'

export function initAuthDevolucionModal() {
  window.Alpine?.data('authDevolucionModalData', () => ({
    open: false,
    docInfo: '',
    destinatario: '',
    hideSignatureWarning: false,
    _onConfirm: null,

    abrir({ docInfo = '', destinatario = '', onConfirm, hideSignatureWarning = false } = {}) {
      this.docInfo = docInfo
      this.destinatario = destinatario
      this.hideSignatureWarning = hideSignatureWarning
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

  window.authDevolucionModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="authDevolucionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.authDevolucionModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="authDevolucionModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

const AuthDevolucionContent = /* html */`
  <div class="text-center">
    <div class="text-[44px] mb-3.5">↩</div>
    <div class="text-base font-bold text-slate-800 mb-2">Confirmar Devolución</div>
    <p class="text-xs text-slate-600 mb-4 leading-relaxed">
      Va a confirmar la devolución de la copia controlada.<br>
      Documento: <strong x-text="docInfo || '—'"></strong><br>
      Destinatario: <strong x-text="destinatario || '—'"></strong>
    </p>
    <p x-show="!hideSignatureWarning" class="text-[11px] text-slate-400 mb-5">Se requerirá su firma digital para registrar la devolución.</p>

    <div class="flex gap-2.5 justify-center">
      <button @click="cerrar()" class="btn flex-1">Cancelar</button>
      <button @click="confirmar()" class="btn flex-1" style="background:#d97706;color:#fff;border-color:#d97706;">Confirmar</button>
    </div>
  </div>
`

export const AuthDevolucionModalTemplate = ModalBaseTemplate({
  dataName: 'authDevolucionModalData',
  size: 'md',
  content: AuthDevolucionContent,
})
