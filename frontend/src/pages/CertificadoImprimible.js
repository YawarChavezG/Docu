/**
 * pages/CertificadoImprimible.js — Diploma / Certificado Formal
 */
import { certificadosDB } from '../data/evaluaciones.js'

function getQueryParam(name) {
  const hash = window.location.hash.replace(/^#/, '')
  const query = hash.includes('?') ? hash.split('?')[1] : ''
  return new URLSearchParams(query).get(name)
}

export const page = {
  init() {
    window.Alpine?.data('certPrintPage', () => ({
      certId: getQueryParam('id') || '',
      cert: null,
      userName: 'Usuario',

      initData() {
        // Seguro: obtener nombre del usuario autenticado
        const auth = window.Alpine?.store('auth')
        this.userName = auth?.user?.name || auth?.user?.username || 'Usuario'

        // Buscar certificado
        if (this.certId) {
          this.cert = certificadosDB.find(c => c.id === this.certId) || null
        }

        // Si no hay certificado, mostrar toast y redirigir
        if (!this.cert) {
          this.$nextTick(() => {
            window.toast && window.toast('Certificado no encontrado. Redirigiendo...', 'warn')
            setTimeout(() => { window.location.hash = '#/certificados' }, 1200)
          })
        }
      },

      volver() {
        window.location.hash = '#/certificados'
      },

      imprimir() {
        window.print()
      },
    }))
  },

  template: /* html */`
<div x-data="certPrintPage" x-init="initData" class="animate-fade-in-page">

  <!-- Controles UI (se ocultan al imprimir) -->
  <div class="print:hidden flex items-center justify-between mb-5">
    <div>
      <h1 class="page-header">Vista de Certificado</h1>
      <p class="page-subtitle">Previsualización del diploma oficial</p>
    </div>
    <div class="flex items-center gap-2">
      <button @click="volver" class="btn">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
        Volver
      </button>
      <button @click="imprimir" class="btn btn-primary">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        Imprimir
      </button>
    </div>
  </div>

  <!-- Área imprimible del Diploma -->
  <div class="max-w-3xl mx-auto bg-white">
    <div class="relative p-10 md:p-14 border-[6px] border-double border-brand-200 rounded-sm">

      <!-- Decoración de esquinas -->
      <div class="absolute top-3 left-3 w-8 h-8 border-t-2 border-l-2 border-brand-300"></div>
      <div class="absolute top-3 right-3 w-8 h-8 border-t-2 border-r-2 border-brand-300"></div>
      <div class="absolute bottom-3 left-3 w-8 h-8 border-b-2 border-l-2 border-brand-300"></div>
      <div class="absolute bottom-3 right-3 w-8 h-8 border-b-2 border-r-2 border-brand-300"></div>

      <!-- Encabezado institucional -->
      <div class="text-center mb-8">
        <div class="text-[11px] font-bold uppercase tracking-[0.25em] text-slate-400 mb-1">COFAR S.A. — Sistema de Gestión Documental</div>
        <div class="h-px w-24 bg-brand-200 mx-auto"></div>
      </div>

      <!-- Título del diploma -->
      <div class="text-center mb-10">
        <h2 class="font-serif text-[34px] md:text-[42px] font-bold text-slate-800 leading-tight tracking-tight">
          Certificado de Aprobación
        </h2>
        <div class="mt-3 h-0.5 w-32 bg-gradient-to-r from-transparent via-brand-400 to-transparent mx-auto"></div>
      </div>

      <!-- Cuerpo -->
      <div class="text-center space-y-6">
        <p class="text-[13px] text-slate-500 leading-relaxed">
          El Sistema de Gestión Documental de <strong class="text-slate-700">COFAR S.A.</strong> certifica que:
        </p>

        <p class="font-serif text-[24px] md:text-[28px] font-bold text-brand-600 leading-snug" x-text="userName"></p>

        <p class="text-[13px] text-slate-500 leading-relaxed">
          Ha completado satisfactoriamente el proceso de evaluación correspondiente al documento:
        </p>

        <p class="text-[16px] md:text-[18px] font-bold text-slate-800 leading-snug px-4 md:px-12" x-text="cert?.documento || '—'"></p>

        <!-- Nota y tipo -->
        <div class="flex items-center justify-center gap-4 mt-4">
          <div class="text-center">
            <div class="text-[10px] uppercase tracking-widest text-slate-400 font-semibold mb-1">Tipo</div>
            <span class="badge"
              :class="cert?.tipo === 'Evaluación' ? 'badge-blue' : 'badge-purple'"
              x-text="cert?.tipo || '—'"></span>
          </div>
          <div class="w-px h-8 bg-slate-200"></div>
          <div class="text-center" x-show="cert?.nota !== null && cert?.nota !== undefined">
            <div class="text-[10px] uppercase tracking-widest text-slate-400 font-semibold mb-1">Nota Obtenida</div>
            <div class="text-[22px] font-extrabold leading-none"
              :class="cert?.nota >= 70 ? 'text-emerald-600' : 'text-red-600'"
              x-text="cert?.nota + '%'"></div>
          </div>
        </div>

        <!-- Fecha -->
        <p class="text-[12px] text-slate-400 mt-6">
          Fecha de obtención:
          <span class="font-semibold text-slate-600" x-text="cert?.fechaObtencion || '—'"></span>
        </p>
      </div>

      <!-- Firmas -->
      <div class="mt-14 grid grid-cols-2 gap-10 max-w-md mx-auto">
        <div class="text-center">
          <div class="h-px bg-slate-300 mb-2"></div>
          <p class="text-[10.5px] text-slate-500 font-medium">Firma del Evaluador</p>
        </div>
        <div class="text-center">
          <div class="h-px bg-slate-300 mb-2"></div>
          <p class="text-[10.5px] text-slate-500 font-medium">Firma del Participante</p>
        </div>
      </div>

      <!-- Pie -->
      <div class="mt-10 text-center">
        <p class="text-[10px] text-slate-300 tracking-wide">
          Este certificado es válido mientras el documento asociado se encuentre vigente.
        </p>
      </div>
    </div>
  </div>

</div>`
}
