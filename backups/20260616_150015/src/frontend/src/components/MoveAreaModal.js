/**
 * src/components/MoveAreaModal.js
 * Modal para mover un Área de una Gerencia a otra.
 */
import { ModalBaseTemplate } from './ModalBase.js'

export function initMoveAreaModal() {
  window.Alpine?.data('moveAreaData', () => ({
    open: false,
    area: null,
    origenId: null,
    destinoId: null,
    gerencias: [],
    onConfirmar: null,

    abrir(opts = {}) {
      this.area = opts.area || null
      this.origenId = opts.origenId || null
      this.destinoId = null
      this.gerencias = opts.gerencias || []
      this.onConfirmar = opts.onConfirmar || null
      this.open = true
    },
    cerrar() { this.open = false },
    confirmar() {
      if (!this.destinoId) {
        window.toast('⚠️ Seleccione una gerencia destino', 'warn')
        return
      }
      if (String(this.destinoId) === String(this.origenId)) {
        window.toast('⚠️ La gerencia destino debe ser diferente a la origen', 'warn')
        return
      }
      if (typeof this.onConfirmar === 'function') {
        this.onConfirmar(Number(this.destinoId))
      }
      this.open = false
    },
  }))

  window.moveAreaModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="moveAreaData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.moveAreaModal.abrir(opts), 200)
    },
  }
}

const inner = /* html */`
  <div>
    <div class="text-center mb-4">
      <div class="text-3xl mb-2">🏢➡️🏢</div>
      <h3 class="text-base font-bold text-slate-900 mb-1">Mover Área de Gerencia</h3>
      <p class="text-[12px] text-slate-500">Trasladar <strong x-text="area?.n ?? ''"></strong> a otra gerencia</p>
    </div>

    <div class="mb-5">
      <label class="form-label">Gerencia destino</label>
      <select x-model="destinoId" class="form-input text-xs">
        <option value="">Seleccionar gerencia...</option>
        <template x-for="g in gerencias" :key="g.id">
          <option :value="g.id" :disabled="g.id === origenId" x-text="g.nombre + (g.id === origenId ? ' (actual)' : '')"></option>
        </template>
      </select>
    </div>

    <div class="flex gap-2.5">
      <button @click="cerrar()" class="btn flex-1">Cancelar</button>
      <button @click="confirmar()" class="btn btn-primary flex-1">✓ Confirmar Traslado</button>
    </div>
  </div>
`

export const MoveAreaModalTemplate = ModalBaseTemplate({
  dataName: 'moveAreaData',
  size: 'sm',
  content: inner,
})
