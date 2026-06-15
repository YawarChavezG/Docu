/**
 * src/components/RespuestasExamenModal.js
 * Modal de visualización de respuestas de examen por usuario
 * Se abre al clicar una Nota en el Expediente (rol ETO)
 *
 * Uso:
 *   window.respuestasExamenModal.abrir({ key: 'CODIGO_Nombre Usuario' })
 *   window.respuestasExamenModal.cerrar()
 */

import { respuestasExamenDB } from '../data/evaluaciones.js'

export function initRespuestasExamenModal() {
  window.Alpine?.data('respuestasExamenModalData', () => ({
    open: false,
    key: '',
    data: null,

    abrir({ key = '' } = {}) {
      this.key = key
      this.data = respuestasExamenDB[key] || null
      this.open = true
    },

    cerrar() {
      this.open = false
      this.data = null
      this.key = ''
    },

    letra(idx) {
      return String.fromCharCode(65 + idx)
    },

    claseOpcion(preg, oi) {
      if (oi === preg.correcta && oi === preg.respondio) return 'bg-emerald-50 border-emerald-200 text-emerald-800 font-semibold'
      if (oi === preg.correcta) return 'bg-emerald-50 border-emerald-200 text-emerald-800 font-semibold'
      if (oi === preg.respondio) return 'bg-red-50 border-red-200 text-red-800 font-semibold'
      return 'bg-slate-50 border-slate-200'
    },

    iconoOpcion(preg, oi) {
      if (oi === preg.correcta && oi === preg.respondio) return '✅ Correcta'
      if (oi === preg.correcta) return '✅ Correcta'
      if (oi === preg.respondio) return '❌ Incorrecta'
      return ''
    },
  }))

  window.respuestasExamenModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="respuestasExamenModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.respuestasExamenModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="respuestasExamenModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const RespuestasExamenModalTemplate = /* html */`
<div x-data="respuestasExamenModalData">
  <template x-teleport="body">
    <div x-show="open"
         @keydown.escape.window="cerrar()"
         class="modal-overlay"
         style="display:none"
         :style="open ? 'display:flex' : 'display:none'">

      <div @click.stop
           class="bg-white rounded-2xl shadow-glass-lg p-6 w-full max-w-2xl flex flex-col max-h-[90vh] overflow-hidden">

        <!-- Header -->
        <div class="flex items-center justify-between border-b border-slate-100 pb-3 mb-4 flex-shrink-0">
          <div>
            <div class="text-base font-bold text-brand-600">Respuestas del Examen</div>
            <div class="text-[11px] text-slate-500 mt-0.5">
              <span x-show="data" x-text="data?.codigo + ' — ' + data?.titulo + ' | Usuario: ' + data?.usuario"></span>
              <span x-show="!data">No hay datos disponibles para esta evaluación.</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="$toast('Exportando Excel...','info')" class="btn btn-sm">📗 Exportar a Excel</button>
            <button @click="cerrar()" class="btn btn-sm btn-danger">✕ Cerrar</button>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto pr-1">
          <template x-if="data">
            <div class="space-y-4">
              <!-- Resumen -->
              <div class="flex items-center gap-4">
                <div class="text-3xl font-extrabold" :class="data.nota >= 70 ? 'text-emerald-600' : 'text-red-600'" x-text="data.nota + '/100'"></div>
                <div class="text-xs text-slate-500">
                  <div><strong x-text="data.preguntas.length"></strong> preguntas</div>
                  <div x-text="data.preguntas.filter(p => p.respondio === p.correcta).length + ' correctas'"></div>
                </div>
              </div>

              <!-- Preguntas -->
              <template x-for="(preg, pi) in data.preguntas" :key="pi">
                <div class="border border-slate-200 rounded-xl p-4">
                  <div class="flex items-start gap-2 mb-2.5">
                    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-brand-100 text-brand-700 text-[11px] font-extrabold flex-shrink-0 mt-0.5" x-text="pi+1"></span>
                    <div class="text-sm font-semibold text-slate-800 leading-snug" x-text="preg.pregunta"></div>
                  </div>
                  <div class="flex flex-col gap-1.5 pl-8">
                    <template x-for="(op, oi) in preg.opciones" :key="oi">
                      <div :class="'flex items-center gap-2 px-3 py-2 rounded-lg border text-xs ' + claseOpcion(preg, oi)">
                        <span class="font-bold w-5" x-text="letra(oi) + '.'"></span>
                        <span x-text="op"></span>
                        <span class="ml-auto text-[10px] font-bold" x-text="iconoOpcion(preg, oi)"></span>
                      </div>
                    </template>
                  </div>
                </div>
              </template>
            </div>
          </template>

          <template x-if="!data">
            <div class="text-center text-slate-500 text-sm py-10">
              No se encontraron respuestas registradas para este examen y usuario.
            </div>
          </template>
        </div>

      </div>
    </div>
  </template>
</div>`
