/**
 * pages/Revision.js — Pantalla de Revisión (US-3.02 a 3.04)
 * Para revisores técnicos
 */
import { historialRevision, observacionActivaRevision } from '../data/bitacora.js'

export const page = {
  init() {
    window.Alpine?.data('revisionPage', () => ({
      obs: '',
      mostrarObs: false,
      historial: historialRevision,
      observacion: observacionActivaRevision,

      toggleDevolver() {
        if (this.mostrarObs) {
          this.iniciarAccion('devolver')
        } else {
          this.mostrarObs = true
        }
      },

      iniciarAccion(tipo) {
        if (tipo === 'devolver' && this.obs.trim().length < 10) {
          window.toast('⚠️ Debe ingresar una observación detallada (mínimo 10 caracteres)', 'warn')
          return
        }
        const esAprobar = tipo === 'aprobar'
        window.authModal?.abrir({
          titulo: esAprobar ? '✓ Aprobar Documento' : '↩ Devolver con Observaciones',
          icono: esAprobar ? '✓' : '↩',
          mensaje: esAprobar
            ? 'Va a firmar digitalmente la <strong>aprobación</strong> de <strong>MAN-LOG-003 v01</strong>. Esta acción queda registrada en la bitácora del sistema.'
            : `Va a <strong>devolver</strong> el documento con la observación: <em>"${this.obs}"</em>. El elaborador recibirá una notificación para hacer las correcciones.`,
          onSuccess: () => {
            if (esAprobar) {
              window.toast('✅ Firma digital registrada. Documento aprobado.', 'success')
            } else {
              window.toast('↩ Documento devuelto con observaciones al elaborador.', 'warn')
            }
            window.location.hash = '/bandeja'
          },
        })
      },

      delegar() {
        window.delegarTareaModal?.abrir({
          tarea: 'MAN-LOG-003 v01',
          de: 'Juan Perez (Actual)',
          a: 'Maria Condori (Nuevo)',
          onConfirm: () => {
            window.toast('✅ Tarea Delegada correctamente.', 'success')
            window.location.hash = '/bandeja'
          }
        })
      },
    }))
  },

  template: /* html */`
<div x-data="revisionPage" class="animate-fade-in-page">

  <div class="flex items-center justify-between mb-3.5 flex-wrap gap-2">
    <div class="flex items-center gap-2.5 flex-wrap">
      <h1 class="text-sm font-bold text-slate-800">Tarea - Revisores — MAN-LOG-003 Manual de Logística y Distribución</h1>
      <span class="badge badge-blue">MAN-LOG-003 · v01</span>
      <span class="badge badge-amber">En revisión paralela</span>
    </div>
    <a href="#/bandeja" class="btn btn-sm">← Volver a Bandeja</a>
  </div>

  <!-- Archivos -->
  <div class="card-base mb-4">
    <div class="section-header">Archivos a revisar (Office 365 Web)</div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <div @click="window.toast('🖊️ Abriendo MAN-LOG-003_v01.docx en Office 365 (modo revisión + Control de Cambios)...','info')"
           class="flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl cursor-pointer transition-all duration-150 hover:border-brand-500 hover:shadow-card-md">
        <span class="text-2xl">📄</span>
        <div class="min-w-0">
          <div class="text-xs font-semibold text-slate-800 truncate">MAN-LOG-003_v01.docx</div>
          <div class="text-[10px] text-brand-600">Documento Principal (Word)</div>
        </div>
      </div>
      <div @click="window.toast('🖊️ Abriendo FOR-LOG-001_Matriz.xlsx en Office 365...','info')"
           class="flex items-center gap-3 p-3 bg-white border border-emerald-200 rounded-xl cursor-pointer transition-all duration-150 hover:border-emerald-500 hover:shadow-card-md">
        <span class="text-2xl">📊</span>
        <div class="min-w-0">
          <div class="text-xs font-semibold text-slate-800 truncate">FOR-LOG-001_Matriz.xlsx</div>
          <div class="text-[10px] text-emerald-600">Anexo (Excel)</div>
        </div>
      </div>
      <div @click="window.toast('🖊️ Abriendo FOR-LOG-002_Checklist.xlsx en Office 365...','info')"
           class="flex items-center gap-3 p-3 bg-white border border-emerald-200 rounded-xl cursor-pointer transition-all duration-150 hover:border-emerald-500 hover:shadow-card-md">
        <span class="text-2xl">📊</span>
        <div class="min-w-0">
          <div class="text-xs font-semibold text-slate-800 truncate">FOR-LOG-002_Checklist.xlsx</div>
          <div class="text-[10px] text-emerald-600">Anexo (Excel)</div>
        </div>
      </div>
    </div>
    <div class="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-[11px] text-amber-800">
      📌 <strong>Nota:</strong> En esta etapa, el documento Word se visualiza en modo Edición con Control de Cambios activado.
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <!-- Timeline + Acciones -->
    <div class="lg:col-span-2 space-y-4">
      <div class="card-base">
        <div class="section-header mb-3 pb-2">Historial del documento en este ciclo</div>
        <div class="max-h-60 overflow-y-auto flex flex-col">
          <template x-for="(n, i) in historial" :key="i">
            <div class="flex gap-2.5 relative">
              <div class="flex flex-col items-center w-6 shrink-0">
                <div class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-extrabold border-2"
                     :class="[n.bg, n.borderColor, n.color]" x-text="n.icono"></div>
                <div x-show="i < historial.length - 1" class="w-0.5 flex-1 bg-slate-200 min-h-5 my-0.5"></div>
              </div>
              <div class="pb-3.5 flex-1">
                <div class="text-[11.5px] font-medium text-slate-800" x-text="n.txt"></div>
                <div class="text-[10px] text-slate-400 mt-0.5" x-text="n.meta"></div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="bg-amber-50 border border-amber-200 rounded-xl p-3">
        <div class="flex items-center gap-1.5 font-bold text-[11.5px] text-amber-800 mb-1.5">⚠️ Observación activa de otro Revisor</div>
        <div class="text-[11px] leading-relaxed text-amber-900">
          <strong x-text="observacion.de"></strong> — <span x-text="observacion.fecha"></span>:<br>
          "<span x-text="observacion.texto"></span>"
        </div>
      </div>

      <div class="card-base">
        <div class="section-header mb-3 pb-2">Mi acción como Revisor</div>
        <div x-show="mostrarObs" x-transition class="mb-3.5">
          <label class="form-label text-[10.5px]">Comentarios u observaciones (Obligatorio si devuelve)</label>
          <textarea class="form-input text-xs" rows="4" x-model="obs" placeholder="Ingrese su observación detallada para que el solicitante pueda corregir el documento..."></textarea>
        </div>
        <div class="flex justify-between flex-wrap gap-4">
          <div class="flex gap-3">
            <button class="btn" :class="mostrarObs ? 'bg-amber-50 text-amber-800 border-amber-200' : ''" @click="toggleDevolver()">
              <span x-text="mostrarObs ? '↩ Confirmar Devolución' : '↩ Devolver (Con obs.)'"></span>
            </button>
            <button class="btn" @click="delegar()">→ Delegar</button>
          </div>
          <button class="btn btn-primary" @click="iniciarAccion('aprobar')">✓ Aprobar (Firma Digital)</button>
        </div>
      </div>
    </div>

    <!-- Metadatos -->
    <div class="space-y-4">
      <div class="card-base">
        <div class="section-header mb-3 pb-2">Información del documento</div>
        <div class="space-y-2.5 text-[11.5px] text-slate-600">
          <div class="flex justify-between border-b border-slate-100 pb-2">
            <span class="text-slate-400">Código</span>
            <span class="font-semibold text-slate-700">MAN-LOG-003</span>
          </div>
          <div class="flex justify-between border-b border-slate-100 pb-2">
            <span class="text-slate-400">Versión</span>
            <span class="font-semibold text-slate-700">v01</span>
          </div>
          <div class="flex justify-between border-b border-slate-100 pb-2">
            <span class="text-slate-400">Elaborador</span>
            <span class="font-semibold text-slate-700">Carlos Flores</span>
          </div>
          <div class="flex justify-between border-b border-slate-100 pb-2">
            <span class="text-slate-400">Gerencia</span>
            <span class="font-semibold text-slate-700">Logística</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">Plazo SLA</span>
            <span class="badge badge-amber">7 días restantes</span>
          </div>
        </div>
      </div>
    </div>
  </div>

</div>`
}
