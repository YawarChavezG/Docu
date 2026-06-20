/**
 * src/components/TimelineModal.js
 * Modal de Timeline / Bitácora de Trazabilidad
 */

import { TIMELINE_CONFIG } from '../data/documents.js'

function getNodeConfig(acc, etapa) {
  const cfg = TIMELINE_CONFIG[acc]
  if (cfg) {
    if (acc === 'Liberado' && !etapa.includes('ETO')) {
      return { ...cfg, icon: '✓' }
    }
    return cfg
  }
  return { cls: 'icon-gray', icon: 'O', color: '#6b7280', msgClass: 'msg-gray', title: 'Mensaje:' }
}

export function renderTimelineNode(l, isETO = false, showReasignar = false, onReasignar = null) {
  const cfg = getNodeConfig(l.acc, l.etapa || '')
  const obsHtml = (l.obs && l.obs !== '-')
    ? `<div class="mt-1.5 p-2 rounded-md text-[11px]" style="background:${getNodeBg(cfg.color)};border:1px solid ${cfg.color}33;color:${cfg.color}dd">
         <strong>${cfg.title}</strong><br>${l.obs}
       </div>`
    : ''

  const btnReasignar = (isETO && showReasignar && l.acc === 'Pendiente')
    ? `<button class="btn btn-sm !text-[10px] !px-2.5 !py-0.5 ml-1.5" onclick="${onReasignar ? onReasignar : 'void(0)'}">Reasignar</button>`
    : ''

  return `
    <div class="flex gap-3 relative">
      <div class="flex flex-col items-center w-7 flex-shrink-0">
        <div class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-extrabold" style="background:${getNodeBg(cfg.color)};border:2px solid ${cfg.color};color:${cfg.color}">${cfg.icon}</div>
        <div class="w-0.5 flex-1 bg-slate-200 min-h-[20px] my-0.5"></div>
      </div>
      <div class="pb-4 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <div class="text-[11.5px]">
            <span class="font-semibold text-slate-800">${l.etapa || ''}</span>
            <span class="text-slate-400"> | Acción: </span>
            <span class="font-bold" style="color:${cfg.color}">${l.acc}</span>
          </div>
          <span class="text-[10px] text-slate-400 ml-auto whitespace-nowrap">📅 ${l.fecha} ⏱️ ${l.hora}</span>
          ${btnReasignar}
        </div>
        <div class="text-[11px] text-slate-600 mt-0.5">👤 <strong>Responsable:</strong> ${l.user}</div>
        ${obsHtml}
      </div>
    </div>`
}

function getNodeBg(color) {
  const map = {
    '#3b82f6': '#eff6ff',
    '#10b981': '#ecfdf5',
    '#ef4444': '#fef2f2',
    '#d97706': '#fffbeb',
    '#6b7280': '#f8fafc',
  }
  return map[color] || '#f8fafc'
}

export function initTimelineModal() {
  window.Alpine?.data('timelineModalData', () => ({
    open: false,
    cod: '',
    titulo: '',
    log: [],
    isETO: false,

    abrir({ cod = '', titulo = '', log = [] } = {}) {
      this.cod    = cod
      this.titulo = titulo
      this.log    = log
      this.isETO  = window.Alpine?.store('auth')?.role === 'eto'
      this.open   = true
    },

    cerrar() { this.open = false },

    getNodeStyle(acc, etapa = '') {
      const cfg = getNodeConfig(acc, etapa)
      return { bg: getNodeBg(cfg.color), border: cfg.color, color: cfg.color, icon: cfg.icon, title: cfg.title }
    },

    getMsgBg(acc, etapa = '') { return getNodeBg(getNodeConfig(acc, etapa).color) },
    getMsgBorder(acc, etapa = '') { return getNodeConfig(acc, etapa).color + '33' },
    getMsgColor(acc, etapa = '') { return getNodeConfig(acc, etapa).color + 'dd' },
    getMsgTitle(acc, etapa = '') { return getNodeConfig(acc, etapa).title },
    getIcon(acc, etapa = '') { return getNodeConfig(acc, etapa).icon },
    getColor(acc, etapa = '') { return getNodeConfig(acc, etapa).color },

    reasignar(user) {
      window.toast(`→ Abriendo modal de reasignación para ${user}...`, 'info')
    },
  }))

  window.timelineModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="timelineModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.timelineModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="timelineModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const TimelineModalTemplate = /* html */`
<div x-data="timelineModalData">
  <template x-teleport="body">
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrar()"
         class="modal-overlay" style="z-index:7000;display:none"
         :style="open ? 'display:flex' : 'display:none'">

      <div @click.stop
           class="modal-box max-w-[640px] max-h-[90vh] flex flex-col p-0 overflow-hidden">

        <!-- Header -->
        <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center flex-shrink-0">
          <div>
            <div class="text-sm font-bold text-slate-800">Historial del Proceso</div>
            <div class="text-[11px] text-brand-500 font-mono font-bold mt-0.5" x-text="cod"></div>
          </div>
          <button @click="cerrar()" class="btn btn-sm">✕ Cerrar</button>
        </div>

        <!-- Timeline scroll area -->
        <div class="flex-1 overflow-y-auto p-5">
          <template x-for="(l, idx) in log" :key="idx">
            <div class="flex gap-3 relative">
              <div class="flex flex-col items-center w-7 flex-shrink-0">
                <div :style="'width:28px;height:28px;border-radius:9999px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;background:'+getMsgBg(l.acc, l.etapa)+';border:2px solid '+getColor(l.acc, l.etapa)+';color:'+getColor(l.acc, l.etapa)"
                     x-text="getIcon(l.acc, l.etapa)"></div>
                <div x-show="idx < log.length - 1"
                     class="w-0.5 flex-1 bg-slate-200 min-h-[20px] my-0.5"></div>
              </div>
              <div class="pb-4 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <div class="text-[11.5px]">
                    <span class="font-semibold text-slate-800" x-text="l.etapa"></span>
                    <span class="text-slate-400"> | Acción: </span>
                    <span class="font-bold" :style="'color:'+getColor(l.acc, l.etapa)" x-text="l.acc"></span>
                  </div>
                  <span class="text-[10px] text-slate-400 ml-auto whitespace-nowrap"
                        x-text="'📅 '+l.fecha+' ⏱️ '+l.hora"></span>
                  <button x-show="isETO && l.acc === 'Pendiente'"
                          @click="reasignar(l.user)"
                          class="btn btn-sm !text-[10px] !px-2.5 !py-0.5">Reasignar</button>
                </div>
                <div class="text-[11px] text-slate-600 mt-0.5">
                  👤 <strong>Responsable:</strong> <span x-text="l.user"></span>
                </div>
                <div x-show="l.obs && l.obs !== '-'"
                     class="mt-1.5 p-2 rounded-md text-[11px]"
                     :style="'background:'+getMsgBg(l.acc,l.etapa)+';border:1px solid '+getMsgBorder(l.acc,l.etapa)+';color:'+getMsgColor(l.acc,l.etapa)">
                  <strong x-text="getMsgTitle(l.acc, l.etapa)"></strong><br>
                  <span x-text="l.obs"></span>
                </div>
              </div>
            </div>
          </template>

          <div x-show="!log || log.length === 0"
               class="text-center py-10 text-slate-400 italic">
            No hay historial disponible para este proceso.
          </div>
        </div>
      </div>
    </div>
  </template>
</div>`