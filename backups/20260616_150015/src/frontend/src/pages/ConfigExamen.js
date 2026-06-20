/**
 * pages/ConfigExamen.js — Configuración de Evaluaciones (US-6.02 ETO)
 * Single Page Form con CRUD reactivo de preguntas de selección múltiple.
 */

import { generarPreguntasIA } from '../data/evaluaciones.js'

export const page = {
  init() {
    window.Alpine?.data('configExamenPage', () => ({
      // ── Documento objetivo (desde sessionStorage tras clic en Monitor) ──
      docCodigo: '',
      docNombre: '',

      // ── Parámetros del examen ──
      numPreguntas: 10,
      tiempoMinutos: 45,
      notaMinima: 70,
      intentosMax: 2,
      fechaLimite: '',
      mezclarPreguntas: true,
      mostrarResultado: true,
      descripcion: '',

      // ── CRUD de preguntas ──
      preguntas: [],
      nextId: 1,

      // ── IA ──
      iaLoading: false,

      init() {
        const raw = sessionStorage.getItem('sgd_config_examen_doc')
        if (raw) {
          try {
            const doc = JSON.parse(raw)
            this.docCodigo = doc.codigo || ''
            this.docNombre = doc.nombre || ''
          } catch { /* ignore */ }
        }
        // Precargar 1 pregunta vacía para no mostrar pantalla vacía
        if (this.preguntas.length === 0) {
          this.addPregunta()
        }
      },

      get tituloPagina() {
        if (this.docCodigo && this.docNombre) {
          return `Configurar Examen — ${this.docCodigo} ${this.docNombre}`
        }
        return 'Configurar Examen'
      },

      get resumen() {
        return `${this.preguntas.length} preguntas · ${this.tiempoMinutos} min · Aprobación ≥${this.notaMinima}% · ${this.intentosMax} intento(s)`
      },

      // ── CRUD Preguntas ──
      addPregunta() {
        this.preguntas.push({
          id: this.nextId++,
          texto: '',
          opciones: ['', ''],
          correcta: 0,
        })
      },

      removePregunta(idx) {
        this.preguntas.splice(idx, 1)
      },

      addOpcion(pregIdx) {
        this.preguntas[pregIdx].opciones.push('')
      },

      removeOpcion(pregIdx, opIdx) {
        const preg = this.preguntas[pregIdx]
        if (preg.opciones.length <= 2) {
          window.toast('⚠️ Una pregunta debe tener al menos 2 opciones.', 'warn')
          return
        }
        preg.opciones.splice(opIdx, 1)
        if (preg.correcta >= preg.opciones.length) {
          preg.correcta = preg.opciones.length - 1
        }
      },

      setCorrecta(pregIdx, opIdx) {
        this.preguntas[pregIdx].correcta = opIdx
      },

      // ── IA ──
      sugerirIA() {
        this.iaLoading = true
        setTimeout(() => {
          const sugeridas = generarPreguntasIA(this.docCodigo || 'DEFAULT')
          const nuevas = sugeridas.map((p, i) => ({
            id: this.nextId++,
            texto: p.preg,
            opciones: [...p.ops],
            correcta: p.correcta,
          }))
          this.preguntas.push(...nuevas)
          this.iaLoading = false
          window.toast(`✅ IA generó ${nuevas.length} preguntas sugeridas.`, 'success')
        }, 1800)
      },

      // ── Exportar ──
      exportarExcel() {
        const nombre = (this.docCodigo || 'examen').replace(/-/g, '_')
        window.toast(`⬇️ Descargando Config_${nombre}.xlsx`, 'info')
      },

      // ── Guardar ──
      guardar() {
        if (!this.docCodigo) {
          window.toast('⚠️ No hay documento seleccionado.', 'warn')
          return
        }
        if (this.preguntas.length === 0) {
          window.toast('⚠️ Agregue al menos una pregunta.', 'warn')
          return
        }
        const incompletas = this.preguntas.some(p => !p.texto.trim() || p.opciones.some(o => !o.trim()))
        if (incompletas) {
          window.toast('⚠️ Complete todas las preguntas y opciones antes de guardar.', 'warn')
          return
        }
        window.authModal?.abrir({
          titulo: '💾 Guardar Configuración de Evaluación',
          icono: '💾',
          mensaje: `Se publicará la evaluación de <strong>${this.docNombre}</strong> con ${this.preguntas.length} preguntas.<br>${this.resumen}`,
          onSuccess: () => {
            window.toast('✅ Evaluación configurada y publicada en el Monitor de Evaluaciones', 'success')
            sessionStorage.removeItem('sgd_config_examen_doc')
            setTimeout(() => window.navigate('/publicacion'), 1200)
          },
        })
      },
    }))
  },

  template: /* html */`
<div x-data="configExamenPage" x-init="init()" class="animate-fade-in-page max-w-5xl mx-auto">

  <!-- Header -->
  <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="page-header" x-text="tituloPagina"></h1>
      <p class="page-subtitle">Configure los parámetros del examen y administre las preguntas de selección múltiple</p>
    </div>
    <div class="flex items-center gap-2">
      <a href="#/publicacion" class="btn btn-sm">← Volver al Monitor</a>
      <button class="btn btn-sm" @click="exportarExcel()">↓ Excel</button>
      <button class="btn btn-sm btn-primary" @click="guardar()">💾 Guardar Configuración</button>
    </div>
  </div>

  <!-- Alerta si no hay documento -->
  <div x-show="!docCodigo" class="card-base mb-4 bg-amber-50 border-amber-200">
    <div class="flex items-center gap-2 text-amber-800 text-sm">
      <span>⚠️</span>
      <span>No se detectó un documento seleccionado. Vaya al <a href="#/publicacion" class="underline font-semibold">Monitor de Evaluaciones</a> y haga clic en "Configurar Examen".</span>
    </div>
  </div>

  <!-- Parámetros -->
  <div class="card-base mb-4">
    <div class="section-header">Parámetros del Examen</div>
    <div class="form-grid-3">
      <div>
        <label class="form-label">N° de preguntas</label>
        <input type="number" x-model.number="numPreguntas" min="1" max="100" class="form-input text-xs">
      </div>
      <div>
        <label class="form-label">Tiempo límite (minutos)</label>
        <input type="number" x-model.number="tiempoMinutos" min="5" max="180" class="form-input text-xs">
      </div>
      <div>
        <label class="form-label">Nota mínima (%)</label>
        <input type="number" x-model.number="notaMinima" min="50" max="100" class="form-input text-xs">
      </div>
      <div>
        <label class="form-label">Intentos permitidos</label>
        <select x-model.number="intentosMax" class="form-input text-xs">
          <option value="1">1 intento</option>
          <option value="2">2 intentos</option>
          <option value="3">3 intentos</option>
          <option value="5">5 intentos</option>
        </select>
      </div>
      <div>
        <label class="form-label">Fecha límite</label>
        <input type="date" x-model="fechaLimite" class="form-input text-xs">
      </div>
    </div>

    <div class="flex gap-5 mt-4 flex-wrap">
      <label class="flex items-center gap-2 text-xs text-slate-700 font-medium cursor-pointer">
        <input type="checkbox" x-model="mezclarPreguntas" class="w-4 h-4 accent-brand-600 cursor-pointer">
        Mezclar orden de preguntas
      </label>
      <label class="flex items-center gap-2 text-xs text-slate-700 font-medium cursor-pointer">
        <input type="checkbox" x-model="mostrarResultado" class="w-4 h-4 accent-brand-600 cursor-pointer">
        Mostrar resultado al finalizar
      </label>
    </div>

    <div class="mt-4">
      <label class="form-label">Descripción / instrucciones para el participante</label>
      <textarea class="form-input text-xs" rows="3" x-model="descripcion" placeholder="Instrucciones adicionales que verá el participante antes de iniciar..."></textarea>
    </div>

    <div class="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800">
      <strong>Resumen:</strong> <span x-text="resumen"></span>
    </div>
  </div>

  <!-- CRUD Preguntas -->
  <div class="card-base mb-4">
    <div class="flex items-center justify-between mb-3">
      <div class="section-header !mb-0 !pb-0 !border-0">Preguntas de Selección Múltiple</div>
      <div class="flex items-center gap-2">
        <button class="btn btn-sm" :disabled="iaLoading" @click="sugerirIA()">
          <span x-show="iaLoading">⏳ Generando...</span>
          <span x-show="!iaLoading">🔍 Sugerir con IA</span>
        </button>
        <button class="btn btn-sm btn-primary" @click="addPregunta()">+ Añadir Pregunta</button>
      </div>
    </div>

    <div class="space-y-3 max-h-[600px] overflow-y-auto pr-1">
      <template x-for="(preg, pi) in preguntas" :key="preg.id">
        <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/50">
          <div class="flex items-start gap-2 mb-3">
            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-brand-100 text-brand-700 text-[11px] font-extrabold flex-shrink-0 mt-0.5" x-text="pi+1"></span>
            <input type="text" x-model="preg.texto" class="form-input text-xs flex-1" :placeholder="'Escriba la pregunta ' + (pi+1)">
            <button @click="removePregunta(pi)" class="btn btn-sm btn-danger text-[10px] px-2 py-1" title="Eliminar pregunta">🗑️</button>
          </div>

          <div class="flex flex-col gap-1.5 pl-8">
            <template x-for="(op, oi) in preg.opciones" :key="oi">
              <div class="flex items-center gap-2">
                <input type="radio" :name="'correcta_'+preg.id" :checked="preg.correcta === oi" @change="setCorrecta(pi, oi)" class="accent-brand-600 w-4 h-4 cursor-pointer flex-shrink-0" :title="'Marcar como correcta'">
                <input type="text" x-model="preg.opciones[oi]" class="form-input text-xs flex-1" :placeholder="'Opción ' + String.fromCharCode(65+oi)">
                <button @click="removeOpcion(pi, oi)" class="text-slate-400 hover:text-red-500 text-xs px-1" title="Eliminar opción">✕</button>
              </div>
            </template>
            <button @click="addOpcion(pi)" class="text-[11px] text-brand-600 font-semibold hover:underline text-left pl-6 mt-0.5">+ Añadir opción</button>
          </div>
        </div>
      </template>
    </div>

    <div x-show="preguntas.length === 0" class="text-center text-slate-400 text-sm py-8">
      No hay preguntas configuradas. Haga clic en "+ Añadir Pregunta" o "Sugerir con IA".
    </div>
  </div>

  <!-- Footer acción -->
  <div class="flex justify-end pb-6">
    <button class="btn btn-primary" @click="guardar()">💾 Guardar y Publicar Evaluación</button>
  </div>

</div>`
}
