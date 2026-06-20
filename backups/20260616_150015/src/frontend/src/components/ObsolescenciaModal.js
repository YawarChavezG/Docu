/**
 * src/components/ObsolescenciaModal.js
 * Modal global para declarar/restaurar obsolescencia de documentos.
 * Sigue la estructura de ProfileModal.js (x-teleport + modal-overlay/box).
 * Sin :style dinámico para visibilidad. Confía únicamente en x-show.
 */

export function initObsolescenciaModal() {
  window.Alpine?.data('obsolescenciaModalData', () => ({
    open: false,
    doc: null,
    comentario: '',
    isObsoleto: false,

    abrir(doc) {
      const isObs = doc.vig === 'Obsoleto'
      this.doc = doc
      this.isObsoleto = isObs
      this.comentario = isObs ? '-' : 'Modificado manualmente por ETO el ' + new Date().toLocaleDateString()
      this.open = true
    },
    cerrar() { this.open = false },

    confirmarObsModal() {
      const d = this.doc
      if (!this.isObsoleto && !this.comentario.trim()) {
        window.toast('⚠️ Debe ingresar una justificación para declarar el documento obsoleto.', 'warn')
        return
      }
      if (this.isObsoleto) {
        d.vig = 'Vigente'
        d.est = 'Aprobado'
        d.obsoleto = false
        d.com = '-'
        window.toast('✅ Documento restaurado a Vigente', 'success')
      } else {
        d.vig = 'Obsoleto'
        d.est = 'Obsoleto'
        d.obsoleto = true
        d.com = this.comentario.trim() || 'Modificado manualmente por ETO el ' + new Date().toLocaleDateString()
        window.toast('⚠️ Documento declarado Obsoleto', 'warn')
      }
      this.open = false
    },
  }))

  window.obsolescenciaModal = {
    abrir(doc) {
      const el = document.querySelector('[x-data="obsolescenciaModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(doc)
      else setTimeout(() => window.obsolescenciaModal.abrir(doc), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="obsolescenciaModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const ObsolescenciaModalTemplate = /* html */`
<div x-data="obsolescenciaModalData">
  <template x-teleport="body">
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         @keydown.escape.window="cerrar()"
         class="modal-overlay"
         style="display:none;">
      <div @click.stop class="modal-box max-w-sm max-h-[90vh] overflow-y-auto">
        <div class="flex items-center gap-2.5 mb-4">
          <div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-xl flex-shrink-0">⚠️</div>
          <div>
            <h2 class="text-sm font-bold text-slate-800" x-text="isObsoleto ? 'Restaurar Documento' : 'Declarar Obsolescencia'"></h2>
            <p class="text-[11px] text-slate-400 mt-0.5" x-text="doc ? (doc.cod + ' — ' + doc.tit) : ''"></p>
          </div>
        </div>
        <p class="text-xs text-slate-600 mb-3" x-show="isObsoleto">
          ¿Confirma la restauración de <strong x-text="doc?.tit"></strong> (<span x-text="doc?.cod"></span>) a estado Vigente?
        </p>
        <div x-show="!isObsoleto">
          <p class="text-xs text-slate-600 mb-3">
            ¿Confirma declarar <strong x-text="doc?.tit"></strong> (<span x-text="doc?.cod"></span>) como Obsoleto? Esta acción queda registrada.
          </p>
          <label class="form-label text-[10.5px]">Comentario ETO (editable)</label>
          <textarea class="form-input text-xs" x-model="comentario" rows="3"></textarea>
        </div>
        <div class="flex gap-2.5 mt-5">
          <button class="btn flex-1" @click="cerrar()">Cancelar</button>
          <button class="btn btn-primary flex-1" @click="confirmarObsModal()">
            <span x-text="isObsoleto ? '✅ Restaurar' : '⚠️ Declarar Obsoleto'"></span>
          </button>
        </div>
      </div>
    </div>
  </template>
</div>`