/**
 * pages/PreEval.js — Pre-evaluación + Examen cronometrado con resultado (US-6.03)
 */
import { examenEjemploDB } from '../data/evaluaciones.js'

export const page = {
  init() {
    window.Alpine?.data('preEvalPage', () => ({
      // Vista: 'pre' | 'examen' | 'resultado'
      vista: 'pre',
      confirmado: false,
      notaMaxima: null,

      // Examen
      examen: examenEjemploDB,
      respuestas: examenEjemploDB.preguntas.map(() => null),
      timerInterval: null,
      minutos: examenEjemploDB.tiempoMinutos,
      segundos: 0,
      tiempoAgotado: false,

      // Resultado
      resultado: null, // { nota, aprobado, correctas, total }

      get timerDisplay() {
        const m = String(this.minutos).padStart(2, '0')
        const s = String(this.segundos).padStart(2, '0')
        return m + ':' + s
      },
      get timerEsCritico() {
        return this.minutos < 5
      },

      iniciarExamen() {
        this.vista = 'examen'
        this.respuestas = this.examen.preguntas.map(() => null)
        this.minutos = this.examen.tiempoMinutos
        this.segundos = 0
        this.tiempoAgotado = false
        this.timerInterval = setInterval(() => {
          if (this.segundos > 0) {
            this.segundos--
          } else if (this.minutos > 0) {
            this.minutos--
            this.segundos = 59
          } else {
            clearInterval(this.timerInterval)
            this.tiempoAgotado = true
            window.toast('⏱️ Tiempo agotado. El examen fue enviado automáticamente.', 'warn')
            this.submitExamen()
          }
        }, 1000)
      },

      submitExamen() {
        if (this.timerInterval) { clearInterval(this.timerInterval); this.timerInterval = null }
        let correctas = 0
        this.examen.preguntas.forEach((p, i) => {
          if (this.respuestas[i] === p.correcta) correctas++
        })
        const total = this.examen.preguntas.length
        const nota = Math.round((correctas / total) * 100)
        const aprobado = nota >= this.examen.notaMinima
        this.resultado = { nota, aprobado, correctas, total }
        if (this.notaMaxima === null || nota > this.notaMaxima) this.notaMaxima = nota
        this.vista = 'resultado'
      },

      confirmarTerminarExamen() {
        window.examConfirmModal?.abrir({
          respondidas: this.respuestas.filter(r => r !== null).length,
          total: this.examen.preguntas.length,
          onConfirm: () => this.submitExamen(),
          onCancel: () => {},
        })
      },

      reintentar() {
        this.resultado = null
        this.vista = 'pre'
        this.confirmado = false
      },
    }))
  },

  template: /* html */`
<div x-data="preEvalPage" style="animation:fadeIn 0.35s ease-out both;max-width:900px;margin:0 auto">

  <!-- ===== VISTA PRE ===== -->
  <div x-show="vista==='pre'">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
      <a href="#/evaluaciones" class="btn btn-sm">← Volver</a>
      <div>
        <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Detalles de Evaluación</h1>
        <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">PRO-RRHH-001 — Política de Asistencia</p>
      </div>
    </div>

    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:16px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px">
        <p style="font-size:12px;color:#475569;max-width:480px;margin:0;line-height:1.6">
          El documento se encuentra vigente desde el <strong>16/04/2026</strong>. A continuación se presentan los detalles y reglas de la evaluación.
        </p>
        <div @click="window.pdfViewer?.abrir({cod:'PRO-RRHH-001',titulo:'Política de Asistencia',tipo:'original',esVencido:false,esObsoleto:false,returnRoute:'/pre-eval'})"
             style="padding:6px 14px;border:1px solid #bfdbfe;background:#eff6ff;color:#1a5fb4;border-radius:6px;cursor:pointer;font-size:11.5px;font-weight:600" @mouseenter="$el.style.background='#dbeafe'" @mouseleave="$el.style.background='#eff6ff'">
          📄 Ver Documento
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px">Tiempo Límite</div>
          <div style="font-size:22px;font-weight:700;color:#1a5fb4">45 Minutos</div>
        </div>
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px">Intentos Permitidos</div>
          <div style="font-size:22px;font-weight:700;color:#1a5fb4">2 <span style="font-size:14px;color:#94a3b8">(1 Restante)</span></div>
        </div>
        <div style="background:#fff5f5;border:1px solid #fecaca;border-radius:10px;padding:20px;text-align:center">
          <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px">Fecha Límite</div>
          <div style="font-size:18px;font-weight:700;color:#dc2626">15/01/2026, 23:59</div>
        </div>
      </div>

      <div x-show="notaMaxima !== null" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 14px;margin-bottom:16px;font-size:12px;color:#166534;font-weight:600">
        🏆 Nota más alta registrada: <span x-text="notaMaxima + '%'"></span>
      </div>

      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 16px;margin-bottom:20px">
        <div style="font-size:11.5px;font-weight:700;color:#1d4ed8;margin-bottom:8px">📋 Instrucciones Importantes</div>
        <ul style="font-size:11.5px;color:#1e40af;padding-left:18px;margin:0;line-height:1.8">
          <li>La evaluación es individual y cronometrada.</li>
          <li>No podrá pausar el examen una vez iniciado.</li>
          <li>El puntaje mínimo de aprobación es <strong>70%</strong>.</li>
          <li>Puede revisar el documento antes de iniciar (botón "Ver Documento").</li>
          <li>En caso de problema técnico, contacte al ETO.</li>
        </ul>
      </div>

      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px 16px;display:flex;align-items:center;gap:12px;margin-bottom:24px">
        <input type="checkbox" id="chk-listo" x-model="confirmado" style="width:18px;height:18px;cursor:pointer;accent-color:#1a5fb4">
        <label for="chk-listo" style="font-size:12px;color:#166534;font-weight:500;cursor:pointer">
          He leído las instrucciones y confirmo que estoy listo para iniciar la evaluación.
        </label>
      </div>

      <div style="display:flex;justify-content:flex-end;gap:10px">
        <a href="#/evaluaciones" class="btn">Cancelar</a>
        <button class="btn btn-primary" :disabled="!confirmado" style="font-size:13px;padding:10px 24px"
                @click="iniciarExamen()">
          🎓 Iniciar Examen Ahora →
        </button>
      </div>
    </div>
  </div>

  <!-- ===== VISTA EXAMEN ===== -->
  <div x-show="vista==='examen'">
    <!-- Header con cronómetro -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
      <div>
        <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Examen en Curso — PRO-RRHH-001</h1>
        <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Política de Asistencia · Responda todas las preguntas</p>
      </div>
      <div :style="'display:flex;align-items:center;gap:8px;padding:8px 16px;border-radius:10px;font-weight:800;font-size:20px;font-family:monospace;'+(timerEsCritico?'background:#fef2f2;color:#dc2626;border:1px solid #fecaca':'background:#f0fdf4;color:#059669;border:1px solid #bbf7d0')" x-text="timerDisplay"></div>
    </div>

    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px">
        <div style="font-size:12px;font-weight:600;color:#475569" x-text="examen.preguntas.length + ' preguntas · Nota mínima: ' + examen.notaMinima + '%'"></div>
        <div style="font-size:11.5px;color:#64748b" x-text="respuestas.filter(r=>r!==null).length + ' de ' + examen.preguntas.length + ' respondidas'"></div>
      </div>

      <template x-for="(preg, pi) in examen.preguntas" :key="pi">
        <div style="margin-bottom:22px;padding-bottom:22px;border-bottom:1px solid #f1f5f9">
          <div style="font-size:13px;font-weight:600;color:#1e293b;margin-bottom:12px">
            <span :style="'display:inline-flex;width:24px;height:24px;border-radius:9999px;align-items:center;justify-content:center;font-size:11px;font-weight:800;background:#1a5fb4;color:#fff;margin-right:8px'" x-text="pi+1"></span>
            <span x-text="preg.pregunta"></span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;padding-left:32px">
            <template x-for="(op, oi) in preg.opciones" :key="oi">
              <label :style="'display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:8px;cursor:pointer;font-size:12px;transition:all 150ms;'+(respuestas[pi]===oi?'background:#eff6ff;border:1px solid #1a5fb4;color:#1a5fb4;font-weight:600':'background:#f8fafc;border:1px solid #e2e8f0;color:#475569')"
                    @mouseenter="if(respuestas[pi]!==oi) $el.style.borderColor='#94a3b8'"
                    @mouseleave="if(respuestas[pi]!==oi) $el.style.borderColor='#e2e8f0'">
                <input type="radio" :name="'preg_'+pi" :value="oi" x-model.number="respuestas[pi]"
                       style="width:16px;height:16px;accent-color:#1a5fb4;cursor:pointer;flex-shrink:0">
                <span x-text="op"></span>
              </label>
            </template>
          </div>
        </div>
      </template>

      <div style="display:flex;justify-content:flex-end;gap:10px;padding-top:8px">
        <button class="btn btn-primary" style="padding:10px 28px;font-size:13px"
                @click="confirmarTerminarExamen()">
          ✓ Terminar y Enviar Examen
        </button>
      </div>
    </div>
  </div>

  <!-- ===== VISTA RESULTADO ===== -->
  <div x-show="vista==='resultado' && resultado">
    <div style="background:#fff;border-radius:16px;padding:40px 32px;box-shadow:0 2px 12px rgba(0,0,0,0.08);text-align:center;max-width:480px;margin:0 auto">
      <div :style="'width:80px;height:80px;border-radius:9999px;display:flex;align-items:center;justify-content:center;font-size:40px;margin:0 auto 18px;'+(resultado?.aprobado?'background:#ecfdf5':'background:#fef2f2')"
           x-text="resultado?.aprobado?'🎓':'😔'"></div>
      <div :style="'font-size:28px;font-weight:900;margin-bottom:4px;'+(resultado?.aprobado?'color:#059669':'color:#dc2626')"
           x-text="resultado?.aprobado?'APROBADO':'REPROBADO'"></div>
      <div :style="'font-size:48px;font-weight:800;margin:12px 0;'+(resultado?.aprobado?'color:#059669':'color:#dc2626')"
           x-text="resultado?.nota+'%'"></div>
      <div style="font-size:12.5px;color:#64748b;margin-bottom:6px" x-text="resultado?.correctas+' de '+resultado?.total+' preguntas correctas'"></div>
      <div style="font-size:11px;color:#94a3b8;margin-bottom:24px" x-text="'Nota mínima de aprobación: '+examen.notaMinima+'%'"></div>

      <div x-show="resultado?.aprobado" style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px;margin-bottom:20px;font-size:11.5px;color:#166534">
        ✅ Su certificado ha sido generado. Puede verlo en la sección <strong>Mis Certificados</strong>.
      </div>
      <div x-show="!resultado?.aprobado" style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:14px;margin-bottom:20px;font-size:11.5px;color:#dc2626">
        ❌ No alcanzó el puntaje mínimo. Revise el documento y vuelva a intentarlo.
      </div>

      <div x-show="notaMaxima !== null" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-bottom:20px;font-size:11.5px;color:#475569">
        🏆 Nota más alta de sus intentos: <strong x-text="notaMaxima+'%'"></strong>
      </div>

      <div style="display:flex;gap:10px;justify-content:center">
        <button class="btn" @click="reintentar()" style="padding:10px 20px">Volver a Intentar</button>
        <a href="#/evaluaciones" class="btn btn-primary" style="padding:10px 20px">Volver a Evaluaciones</a>
      </div>
    </div>
  </div>

</div>`
}
