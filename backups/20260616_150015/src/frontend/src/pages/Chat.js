/**
 * pages/Chat.js — Asistente IA BD (US-8.04)
 * Refactorizado Fase 3 - Lote 8
 */
import { obtenerRespuestaIA } from '../data/iaRespuestas.js'

export const page = {
  init() {
    window.Alpine?.data('chatPage', () => ({
      msgs: [
        {
          bot: true,
          txt: `¡Hola! Soy la IA integrada al Sistema de Gestión Documental de COFAR.<br><br>Puedo realizar consultas complejas en tiempo real. Prueba preguntándome:<br><em>"¿Cuáles son los documentos próximos a vencer?"</em> o <em>"¿Qué documentos están pendientes hace más de 3 meses?"</em>`,
          btns: []
        }
      ],
      input: '',
      loading: false,

      get isETO() {
        return window.Alpine?.store('auth')?.role === 'eto'
      },

      async enviar(txt) {
        const msg = txt || this.input.trim()
        if (!msg) return
        this.msgs.push({ bot: false, txt: msg, btns: [] })
        this.input = ''
        this.loading = true
        this.scrollToBottom()

        await new Promise(r => setTimeout(r, 1800))
        this.loading = false
        const resp = obtenerRespuestaIA(msg)
        this.msgs.push({ bot: true, txt: resp.msg, btns: resp.btns || [] })
        this.scrollToBottom()
      },

      scrollToBottom() {
        this.$nextTick(() => {
          const h = document.getElementById('chat-hist')
          if (h) h.scrollTop = h.scrollHeight
        })
      }
    }))
  },

  template: /* html */`
<div x-data="chatPage" class="flex flex-col h-[calc(100vh-100px)] animate-fade-in-page">

  <!-- Header -->
  <div class="shrink-0 py-3 mb-1">
    <h1 class="page-header flex items-center gap-2">
      <span class="text-lg">✨</span>
      Asistente IA — Conectado a BD Documental
    </h1>
    <p class="page-subtitle" x-text="isETO ? 'Acceso completo a todos los datos del sistema' : 'Consultas limitadas a documentos aprobados en Lista Maestra'"></p>
  </div>

  <!-- Historial -->
  <div id="chat-hist" class="flex-1 overflow-y-auto bg-slate-50/80 border border-slate-200 rounded-xl p-4 flex flex-col gap-3 mb-2.5">
    <div class="text-center text-[11px] text-slate-400 tracking-wide">
      Conexión segura establecida con SAP y SQL Server
    </div>

    <template x-for="(m,i) in msgs" :key="i">
      <div class="flex gap-2.5" :class="m.bot ? 'items-end' : 'items-end flex-row-reverse'">
        <!-- Avatar IA -->
        <div x-show="m.bot" class="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm shrink-0 text-base ring-1 ring-slate-100">
          ✨
        </div>

        <div class="max-w-[75%] flex flex-col" :class="m.bot ? 'items-start' : 'items-end'">
          <!-- Burbuja -->
          <div class="px-4 py-2.5 text-[12.5px] leading-relaxed shadow-sm"
               :class="m.bot
                 ? 'bg-white text-slate-800 rounded-2xl rounded-bl-sm border border-slate-100'
                 : 'bg-brand-500 text-white rounded-2xl rounded-br-sm'"
               x-html="$sanitize(m.txt)">
          </div>

          <!-- Botones de acción -->
          <div x-show="m.btns && m.btns.length" class="flex flex-wrap gap-1.5 mt-1.5">
            <template x-for="b in m.btns" :key="b">
              <button @click="$toast('▶ Ejecutando: ' + b, 'info')"
                      class="btn btn-sm text-[11px] border-blue-200 text-brand-600 bg-blue-50 hover:bg-blue-100 hover:border-blue-300"
                      x-text="b">
              </button>
            </template>
          </div>
        </div>
      </div>
    </template>

    <!-- Estado de carga -->
    <div x-show="loading" x-transition class="flex gap-2.5 items-end">
      <div class="w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-sm shrink-0 text-base ring-1 ring-slate-100">
        ✨
      </div>
      <div class="bg-white border border-slate-100 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div class="flex items-center gap-2">
          <div class="flex gap-1">
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay:0ms"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay:150ms"></span>
            <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay:300ms"></span>
          </div>
          <span class="text-[12px] text-slate-500 italic">La IA está pensando...</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Sugerencias rápidas -->
  <div class="flex gap-1.5 flex-wrap mb-2 shrink-0">
    <button @click="enviar('¿Cuáles son los documentos próximos a vencer?')" class="btn btn-sm text-[11px]">
      📅 Próximos a vencer
    </button>
    <button @click="enviar('¿Qué documentos están pendientes hace más de 3 meses?')" class="btn btn-sm text-[11px]">
      ⏳ Pendientes > 3 meses
    </button>
    <button x-show="isETO" @click="enviar('¿Cuántos documentos están en estado obsoleto?')" class="btn btn-sm text-[11px]">
      📁 Documentos obsoletos
    </button>
  </div>

  <!-- Input -->
  <div class="flex gap-2.5 bg-white border border-slate-200 rounded-xl p-2.5 shrink-0 items-center shadow-sm">
    <input type="text"
           x-model="input"
           @keydown.enter.prevent="enviar()"
           placeholder="Escribe tu consulta en lenguaje natural..."
           class="flex-1 bg-transparent border-0 outline-none text-[13px] text-slate-800 placeholder:text-slate-400">
    <button @click="enviar()"
            :disabled="loading || !input.trim()"
            class="btn btn-primary rounded-lg px-5 py-2 text-[12px] h-auto">
      Enviar
    </button>
  </div>
</div>`
}
