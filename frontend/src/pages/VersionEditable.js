/**
 * pages/VersionEditable.js — Descarga de documento en versión editable
 * Sesion 22 R2 FASE 2: consume /api/v1/documentos/buscar (BD real).
 */
import { documentos } from '../services/documentosApi.js'

export const page = {
  init() {
    window.Alpine?.data('versionEditable', () => ({
      codBuscar: '',
      cargando: false,
      resultadoEditable: null,
      descargado: false,
      resultados: [], // para mostrar lista de matches

      async buscarEditable() {
        if (!this.codBuscar.trim()) {
          window.toast?.('Ingrese un codigo de documento', 'warn')
          return
        }
        this.cargando = true
        this.resultadoEditable = null
        this.descargado = false
        this.resultados = []
        try {
          const res = await documentos.buscar(this.codBuscar.trim(), 10)
          if (!res.ok) {
            window.toast?.(res.message || 'Error al buscar documentos', 'error')
            return
          }
          const items = res.data?.items || []
          this.resultados = items
          if (items.length === 0) {
            window.toast?.('No se encontraron documentos con ese codigo', 'warn')
            return
          }
          // Buscar match exacto por codigo_completo; si no, tomar el primero
          const match = items.find(d => d.codigo_completo === this.codBuscar.trim().toUpperCase()) || items[0]
          this.resultadoEditable = {
            archivo: match.codigo_completo + '.docx',
            nombre: match.titulo,
            tipo: match.tipo?.nombre || '',
            area: match.gerencia?.sigla + ' / ' + match.area?.sigla,
            vigencia: match.vigencia,
            estatus: match.estatus,
            limite: match.tipo?.max_descargas_dia ?? 1,
          }
        } catch (e) {
          window.toast?.('Error inesperado: ' + (e?.message || e), 'error')
        } finally {
          this.cargando = false
        }
      },

      descargarEditable() {
        this.descargado = true
        window.toast?.('Descargando ' + this.resultadoEditable.archivo + '...', 'success')
      },

      // Mostrar el detalle cuando eligen uno de los resultados
      seleccionarResultado(match) {
        this.resultadoEditable = {
          archivo: match.codigo_completo + '.docx',
          nombre: match.titulo,
          tipo: match.tipo?.nombre || '',
          area: match.gerencia?.sigla + ' / ' + match.area?.sigla,
          vigencia: match.vigencia,
          estatus: match.estatus,
          limite: match.tipo?.max_descargas_dia ?? 1,
        }
        this.codBuscar = match.codigo_completo
        this.resultados = []
      },
    }))
  },
  template: /* html */`
<div x-data="versionEditable" style="animation:fadeIn 0.35s ease-out both">

  <!-- Header -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Documento en Version Editable</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Descargue el archivo Word/Excel original para modificar o actualizar</p>
    </div>
    <a href="#/bandeja" class="btn btn-sm">Bandeja</a>
  </div>

  <!-- Policy banner -->
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 14px;margin-bottom:16px;display:flex;align-items:start;gap:8px">
    <span style="font-size:16px;flex-shrink:0">INFO</span>
    <div style="font-size:11.5px;color:#1e3a8a;line-height:1.5">
      <strong>Politica de Descargas:</strong> Se puede descargar <strong>1 documento por dia</strong>, a excepcion de los documentos tipo <strong>METODOLOGIAS Y ESPECIFICACIONES</strong> (CC-1, CC-7), de los cuales se pueden descargar hasta <strong>10 por dia</strong>.
    </div>
  </div>

  <!-- Search card -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.05);max-width:640px">
    <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:16px">Buscar documento</div>
    <div style="margin-bottom:14px">
      <label style="font-size:10.5px;font-weight:600;color:#64748b;display:block;margin-bottom:5px">Codigo del documento requerido</label>
      <div style="display:flex;gap:8px">
        <input type="text" class="form-input"
               style="flex:1;font-family:monospace;font-weight:600;text-transform:uppercase;font-size:12px"
               placeholder="EJ: CC-3-005/01"
               x-model="codBuscar"
               @input="$el.value=$el.value.toUpperCase();codBuscar=$el.value"
               @keydown.enter="buscarEditable()">
        <button class="btn btn-primary" @click="buscarEditable()" :disabled="cargando" style="white-space:nowrap;display:flex;align-items:center;gap:6px">
          <svg x-show="cargando" style="width:13px;height:13px;animation:spin 1s linear infinite" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-opacity="0.25"/><path d="M3 12a9 9 0 019-9" stroke-linecap="round"/>
          </svg>
          <span x-text="cargando ? 'Buscando...' : 'Buscar'"></span>
        </button>
      </div>
    </div>

    <!-- Lista de resultados (autocomplete) -->
    <div x-show="resultados.length > 0 && !resultadoEditable"
         x-transition:enter="transition-opacity duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         style="margin-bottom:14px;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden">
      <div style="font-size:10.5px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.06em;padding:8px 12px;background:#f8fafc;border-bottom:1px solid #e2e8f0"
           x-text="resultados.length + ' resultado(s). Click para seleccionar:'"></div>
      <template x-for="r in resultados" :key="r.id">
        <div @click="seleccionarResultado(r)"
             style="padding:10px 12px;cursor:pointer;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;gap:8px"
             @mouseenter="$el.style.background='#f0f9ff'"
             @mouseleave="$el.style.background='transparent'">
          <div style="min-width:0;flex:1">
            <div style="font-size:11.5px;font-weight:700;color:#1e293b;font-family:monospace" x-text="r.codigo_completo"></div>
            <div style="font-size:10.5px;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" x-text="r.titulo"></div>
          </div>
          <div style="display:flex;gap:6px;align-items:center;flex-shrink:0">
            <span style="font-size:9.5px;padding:2px 6px;border-radius:4px;background:#e0e7ff;color:#3730a3"
                  x-text="r.tipo?.nombre || ''"></span>
            <span style="font-size:9.5px;padding:2px 6px;border-radius:4px"
                  :class="r.vigencia === 'VIGENTE' ? 'background:#dcfce7;color:#166534' : (r.vigencia === 'VENCIDO' ? 'background:#fee2e2;color:#991b1b' : 'background:#fef3c7;color:#92400e')"
                  x-text="r.vigencia"></span>
          </div>
        </div>
      </template>
    </div>

    <!-- Resultado seleccionado -->
    <div x-show="resultadoEditable"
         x-transition:enter="transition-opacity duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100">
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px 16px">
        <div style="font-size:10.5px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px">Resultado encontrado</div>
        <div style="display:flex;align-items:center;gap:10px;justify-content:space-between;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:10px;min-width:0;flex:1">
            <span style="font-size:24px;flex-shrink:0">DOC</span>
            <div style="min-width:0;flex:1">
              <div style="font-size:12px;font-weight:700;color:#1e293b;font-family:monospace" x-text="resultadoEditable?.archivo"></div>
              <div style="font-size:11px;color:#64748b;overflow:hidden;text-overflow:ellipsis" x-text="resultadoEditable?.nombre"></div>
              <div style="font-size:10.5px;color:#059669;margin-top:2px" x-text="resultadoEditable ? 'Tipo: ' + resultadoEditable.tipo + ' | Area: ' + resultadoEditable.area + ' | Limite: ' + resultadoEditable.limite + ' descarga(s)/dia' : ''"></div>
            </div>
          </div>
          <button @click="descargarEditable()" :disabled="descargado" class="btn btn-primary" style="display:flex;align-items:center;gap:6px;flex-shrink:0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span x-text="descargado ? 'Descargado' : 'Descargar Editable'"></span>
          </button>
        </div>
      </div>
    </div>
  </div>

</div>`
}
