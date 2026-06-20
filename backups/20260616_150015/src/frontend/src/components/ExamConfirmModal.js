/**
 * src/components/ExamConfirmModal.js
 * Modal de confirmación antes de terminar examen
 * Extraído de #exam-modal
 *
 * Uso:
 *   window.examConfirmModal.abrir({ onConfirm, onCancel })
 *   window.examConfirmModal.cerrar()
 */

export function initExamConfirmModal() {
  window.Alpine?.data('examConfirmModalData', () => ({
    open: false,
    respondidas: 0,
    total: 0,
    _onConfirm: null,
    _onCancel: null,

    abrir({ respondidas = 0, total = 0, onConfirm, onCancel } = {}) {
      this.respondidas = respondidas
      this.total = total
      this._onConfirm = onConfirm || null
      this._onCancel = onCancel || null
      this.open = true
    },

    cerrar() {
      this.open = false
      if (this._onCancel) this._onCancel()
      this._onConfirm = null
      this._onCancel = null
    },

    confirmar() {
      if (this._onConfirm) this._onConfirm()
      this.cerrar()
    },
  }))

  window.examConfirmModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="examConfirmModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.examConfirmModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="examConfirmModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const ExamConfirmModalTemplate = /* html */`
<div x-data="examConfirmModalData">

  <!-- ── Modal Confirmar Terminar Examen ────────────────────────────────── -->
  <div x-show="open"
       @keydown.escape.window="cerrar()"
       class="modal-overlay"
       style="display:none;"
       :style="open ? 'display:flex' : 'display:none'">

    <div @click.stop
         class="modal-box max-w-sm text-center max-h-[90vh] overflow-y-auto border-t-4 border-red-600">

      <div class="text-[44px] mb-3.5">🎓</div>
      <div class="text-base font-bold text-slate-800 mb-2">¿Terminar Examen?</div>
      <p class="text-xs text-slate-600 mb-4 leading-relaxed">
        Usted ha respondido <strong x-text="respondidas + ' de ' + total"></strong> preguntas.
      </p>
      <p x-show="respondidas < total"
         class="text-[11px] text-red-600 mb-4 font-semibold">
        ⚠️ Hay preguntas sin responder. ¿Está seguro que desea terminar?
      </p>
      <p x-show="respondidas === total"
         class="text-[11px] text-emerald-600 mb-4 font-semibold">
        ✅ Todas las preguntas respondidas. Puede enviar el examen.
      </p>

      <div class="flex gap-2.5 justify-center">
        <button @click="cerrar()" class="btn flex-1">Continuar Examen</button>
        <button @click="confirmar()" class="btn btn-danger flex-1 bg-red-600 border-red-600 hover:bg-red-700 hover:border-red-700">Terminar y Enviar</button>
      </div>
    </div>
  </div>

</div>`