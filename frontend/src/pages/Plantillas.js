/**
 * pages/Plantillas.js — Plantillas Documentales
 *
 * Sesion 24 / Bloque E: consume /api/v1/plantillas-documentales (BD + filesystem).
 * Reemplaza el mock legacy `plantillasDocDB` de data/plantillas.js.
 */
import { plantillas } from '../services/plantillasApi.js'

// ─── Helpers de UI ─────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const TIPO_META = {
  word:  { bg: '#eff6ff', color: '#1a5fb4', border: '#bfdbfe', emoji: '📄', label: 'Word' },
  excel: { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0', emoji: '📊', label: 'Excel' },
  ppt:   { bg: '#fffbeb', color: '#92400e', border: '#fde68a', emoji: '📑', label: 'PPT' },
  otro:  { bg: '#f8fafc', color: '#64748b', border: '#e2e8f0', emoji: '📁', label: 'Otro' },
}

function tipoMeta(cat) {
  return TIPO_META[cat] || TIPO_META.otro
}

export const page = {
  init() {
    window.Alpine?.data('plantillasPage', () => ({
      plantillas: [],
      loading: true,
      filterTipo: '',
      errorMsg: '',

      async init() {
        await this.cargar()
      },

      async cargar() {
        this.loading = true
        this.errorMsg = ''
        const res = await plantillas.list()
        if (res.ok && res.data?.items) {
          this.plantillas = res.data.items
        } else {
          this.plantillas = []
          this.errorMsg = res.message || 'No se pudieron cargar las plantillas'
          window.toast?.(this.errorMsg, 'error')
        }
        this.loading = false
      },

      get filtered() {
        return this.filterTipo
          ? this.plantillas.filter(p => p.categoria === this.filterTipo)
          : this.plantillas
      },

      tipoMeta(cat) { return tipoMeta(cat) },

      formatBytes(b) { return formatBytes(b) },

      async descargar(p) {
        const toastId = window.toast?.('⬇️ Descargando: ' + p.nombre_display + '...', 'info')
        const res = await plantillas.download(p.nombre_archivo)
        if (res.ok) {
          window.toast?.('✅ Plantilla "' + p.nombre_display + '" descargada', 'success')
        } else {
          window.toast?.(res.message || 'Error al descargar', 'error')
        }
      },
    }))
  },
  template: /* html */`
<div x-data="plantillasPage" style="animation:fadeIn 0.35s ease-out both">

  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Plantillas Documentales</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Descargue la plantilla oficial para elaborar su documento</p>
    </div>
    <div style="display:flex;gap:8px">
      <button @click="filterTipo=''" :style="!filterTipo?'background:#1a5fb4;color:#fff;border-color:#1a5fb4':''" class="btn btn-sm">Todas</button>
      <button @click="filterTipo='word'" :style="filterTipo==='word'?'background:#1a5fb4;color:#fff;border-color:#1a5fb4':''" class="btn btn-sm">📄 Word</button>
      <button @click="filterTipo='excel'" :style="filterTipo==='excel'?'background:#166534;color:#fff;border-color:#166534':''" class="btn btn-sm">📊 Excel</button>
      <button @click="filterTipo='ppt'" :style="filterTipo==='ppt'?'background:#92400e;color:#fff;border-color:#92400e':''" class="btn btn-sm">📑 PPT</button>
      <button @click="cargar()" :disabled="loading" :title="loading ? 'Cargando...' : 'Refrescar'" class="btn btn-sm" style="display:inline-flex;align-items:center;gap:4px">
        <span :style="loading ? 'display:inline-block;animation:spin 0.8s linear infinite' : ''">↻</span> Refrescar
      </button>
    </div>
  </div>

  <!-- IA -->
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px 14px;margin-bottom:20px">
    <div style="font-size:10px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px">✦ IA — Recomendación</div>
    <div style="font-size:11.5px;color:#1e3a8a;line-height:1.5">Para documentos de tipo <strong>Procedimiento (SOP)</strong>, utilice la plantilla v3 actualizada con la estructura BPM-2024. Recuerde activar el <em>Control de Cambios</em> en Word antes de editar.</div>
  </div>

  <!-- Loading -->
  <div x-show="loading" style="text-align:center;padding:60px;color:#94a3b8">
    <div style="width:24px;height:24px;border:3px solid #cbd5e1;border-top-color:#1a5fb4;border-radius:50%;margin:0 auto 8px;animation:spin 0.8s linear infinite"></div>
    <div style="font-size:11.5px">Cargando plantillas...</div>
  </div>

  <!-- Cards de plantillas -->
  <div x-show="!loading" style="display:grid;grid-template-columns:repeat(2,1fr);gap:14px" class="lg:grid-cols-3">
    <template x-for="p in filtered" :key="p.nombre_archivo">
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05);transition:all 200ms"
           @mouseenter="$el.style.boxShadow='0 6px 20px rgba(0,0,0,0.08)';$el.style.transform='translateY(-2px)'"
           @mouseleave="$el.style.boxShadow='0 1px 3px rgba(0,0,0,0.05)';$el.style.transform=''">
        <!-- Icono -->
        <div :style="'width:48px;height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;background:'+tipoMeta(p.categoria).bg+';border:1px solid '+tipoMeta(p.categoria).border">
          <span x-text="tipoMeta(p.categoria).emoji"></span>
        </div>
        <!-- Info -->
        <div style="flex:1">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
            <span :style="'display:inline-flex;align-items:center;padding:2px 7px;border-radius:9999px;font-size:10px;font-weight:700;background:'+tipoMeta(p.categoria).bg+';color:'+tipoMeta(p.categoria).color+';border:1px solid '+tipoMeta(p.categoria).border" x-text="tipoMeta(p.categoria).label"></span>
            <span style="font-size:10px;color:#94a3b8;background:#f8fafc;padding:2px 6px;border-radius:4px;border:1px solid #e2e8f0" x-text="p.version"></span>
          </div>
          <h3 style="font-size:13px;font-weight:600;color:#1e293b;margin:0 0 6px;line-height:1.3" x-text="p.nombre_display"></h3>
          <p style="font-size:11px;color:#64748b;margin:0;line-height:1.4" x-text="p.descripcion || 'Plantilla oficial COFAR'"></p>
        </div>
        <!-- Footer -->
        <div style="border-top:1px solid #f1f5f9;padding-top:12px">
          <div style="font-size:10px;color:#94a3b8;margin-bottom:8px">
            <span x-text="'Tamaño: ' + formatBytes(p.tamano_bytes)"></span>
            <span style="margin:0 6px">·</span>
            <span x-text="p.nombre_archivo"></span>
          </div>
          <button @click="descargar(p)"
                  :style="'width:100%;padding:8px 12px;border-radius:8px;border:1px solid '+tipoMeta(p.categoria).border+';background:'+tipoMeta(p.categoria).bg+';color:'+tipoMeta(p.categoria).color+';font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;display:flex;align-items:center;justify-content:center;gap:6px;transition:opacity 150ms'"
                  @mouseenter="$el.style.opacity='0.8'" @mouseleave="$el.style.opacity='1'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Descargar editable
          </button>
        </div>
      </div>
    </template>
    <div x-show="filtered.length===0 && !loading" style="grid-column:1/-1;text-align:center;padding:60px;color:#94a3b8">
      <div style="font-size:32px;margin-bottom:8px">📭</div>
      <div style="font-size:12px" x-text="errorMsg || 'No hay plantillas disponibles para el tipo seleccionado.'"></div>
    </div>
  </div>

  <!-- Nota informativa -->
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px;margin-top:20px;display:flex;align-items:start;gap:10px">
    <svg width="16" height="16" viewBox="0 0 20 20" fill="#64748b" style="flex-shrink:0;margin-top:1px"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>
    <p style="font-size:11.5px;color:#64748b;margin:0;line-height:1.5">
      Las plantillas son gestionadas y actualizadas desde <strong>Parametrización General → Plantillas Documentales</strong>.
      Para solicitar una nueva plantilla o reportar un problema, contacte al Gestor Documental (ETO).
      Cada descarga queda registrada en auditoría.
    </p>
  </div>
</div>`
}
