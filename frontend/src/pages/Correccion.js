/**
 * pages/Correccion.js — Corrección de observaciones (US-3.05)
 */
export const page = {
  init() {
    window.Alpine?.data('correccionPage', () => ({
      abriendo: false,
      docAbierto: false,
      confirmado: false,
      tarea: {
        origen: 'Revisores',
        codigo: 'PRO-CAL-045',
        titulo: 'Procedimiento de Muestreo de Control de Calidad'
      },
      observacion: {
        de: 'Revisor 1 (Jasiel Sanjinés)',
        texto: 'Estimado, favor revisar el punto 4.2. Falta incluir la tabla de referencias cruzadas con la norma ISO aplicable. Corregir y volver a enviar.'
      },

      abrirDoc() {
        this.abriendo = true
        setTimeout(() => {
          this.abriendo = false
          this.docAbierto = true
          window.toast('✅ Documento abierto en Office 365 con Control de Cambios habilitado.', 'success')
        }, 2000)
      },

      confirmarYReenviar() {
        if (!this.confirmado) return
        window.authModal?.abrir({
          titulo: 'Firmar Corrección',
          icono: '✓',
          mensaje: `Va a firmar digitalmente la corrección de <strong>${this.tarea.codigo}</strong>. Esta acción queda registrada en la bitácora del sistema.`,
          onSuccess: () => {
            window.toast('✅ Corrección confirmada y reenviada al revisor observador.', 'success')
            window.navigate('/bandeja')
          }
        })
      }
    }))
  },

  template: /* html */`
<div x-data="correccionPage" class="animate-fade-in-page">

  <div class="flex items-center justify-between mb-3.5 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Corregir observaciones de la tarea de <span x-text="tarea.origen"></span> — <span x-text="tarea.codigo"></span> <span x-text="tarea.titulo"></span></h1>
    </div>
    <a href="#/bandeja" class="btn btn-sm">← Volver a Bandeja</a>
  </div>

  <!-- Observación del revisor -->
  <div class="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4 mb-4">
    <div class="flex items-center gap-1.5 font-bold text-[11.5px] text-amber-800 mb-2">⚠️ Documento devuelto por: <span x-text="observacion.de"></span></div>
    <div class="bg-white border border-amber-200 rounded-lg p-3 text-xs text-amber-900 leading-relaxed italic" x-text="observacion.texto"></div>
  </div>

  <!-- Zona de edición -->
  <div class="card-base mb-4">
    <div class="section-header mb-4 pb-2">Edición del Documento Observado</div>

    <div class="flex gap-4 flex-wrap">
      <div class="flex items-start gap-3 flex-1 min-w-[200px]">
        <div class="w-14 h-14 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-center text-[28px] shrink-0">📄</div>
        <div>
          <div class="text-[13px] font-bold text-slate-800" x-text="tarea.codigo + '_v01.docx'"></div>
          <div class="text-[11px] text-slate-500 mt-1">Documento Principal — Última modificación: Hoy, 10:30 a.m.</div>
        </div>
      </div>
      <div>
        <p class="text-[11.5px] text-slate-600 mb-2.5 leading-relaxed max-w-md">
          El documento se encuentra alojado en la nube corporativa de COFAR. Para realizar las correcciones solicitadas, haga clic en el siguiente botón. El documento se abrirá en una nueva pestaña utilizando <strong>Office 365 con el Control de Cambios habilitado</strong> automáticamente.
        </p>
        <button @click="abrirDoc()" :disabled="docAbierto" class="btn btn-primary inline-flex items-center gap-2">
          <span x-text="abriendo ? '⏳ Abriendo...' : docAbierto ? '✅ Documento abierto' : '✏️ Abrir en Office 365 (Edición en línea)'"></span>
        </button>
      </div>
    </div>

    <!-- Visor simulado -->
    <div class="mt-4 bg-slate-700 rounded-xl h-72 flex items-center justify-center transition-opacity duration-300"
         :class="docAbierto ? 'opacity-100' : 'opacity-40 pointer-events-none'">
      <div class="bg-white w-11/12 max-w-2xl h-60 rounded shadow-xl flex items-center justify-center text-[13px] text-slate-400 italic">
        <span x-show="!docAbierto">[ Visor bloqueado — abra el documento primero ]</span>
        <div x-show="docAbierto" class="text-center p-5">
          <div class="text-xs font-bold text-slate-800 mb-2" x-text="tarea.codigo + ' · ' + tarea.titulo"></div>
          <div class="text-[10.5px] text-slate-500 leading-relaxed">[ Word Online — Control de Cambios activado — Editando ]<br>Los cambios se guardan automáticamente en la nube.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Confirmación y envío -->
  <div class="card-base">
    <div :class="docAbierto ? 'opacity-100' : 'opacity-40 pointer-events-none'">
      <div class="flex items-start gap-3 bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-5">
        <input type="checkbox" id="chk-correc" x-model="confirmado" :disabled="!docAbierto" class="w-[18px] h-[18px] cursor-pointer accent-brand-500 shrink-0 mt-0.5">
        <label for="chk-correc" class="text-xs text-emerald-800 font-medium cursor-pointer leading-relaxed">
          Confirmo que he revisado y realizado todas las modificaciones solicitadas en Office 365. El documento está listo para reenvío al revisor que realizó la observación.
        </label>
      </div>
      <div class="flex justify-end gap-2.5">
        <a href="#/bandeja" class="btn">Cancelar</a>
        <button class="btn btn-primary px-6" :disabled="!confirmado" @click="confirmarYReenviar()">✅ Confirmar y Reenviar →</button>
      </div>
    </div>
  </div>

</div>`
}
