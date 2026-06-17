/**
 * pages/VersionEditable.js — Descarga de documento en versión editable
 */
export const page = {
  init() {
    window.Alpine?.data('versionEditable', () => ({
      codBuscar: '', cargando: false, resultadoEditable: null, descargado: false,
      buscarEditable() {
        if (!this.codBuscar.trim()) { window.toast?.('⚠️ Ingrese un código de documento', 'warn'); return }
        this.cargando = true; this.resultadoEditable = null; this.descargado = false
        setTimeout(() => {
          this.cargando = false
          this.resultadoEditable = {
            archivo: this.codBuscar + '_v01.docx',
            nombre: 'Documento Principal + Formularios adjuntos',
            limite: (this.codBuscar.startsWith('CC-1') || this.codBuscar.startsWith('CC-7')) ? 10 : 1
          }
        }, 1200)
      },
      descargarEditable() {
        this.descargado = true
        window.toast?.('⬇️ Descargando ' + this.resultadoEditable.archivo + '...', 'success')
      },
    }))
  },
  template: /* html */`
<div x-data="versionEditable" style="animation:fadeIn 0.35s ease-out both">

  <!-- Header -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Documento en Versión Editable</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Descargue el archivo Word/Excel original para modificar o actualizar</p>
    </div>
    <a href="#/bandeja" class="btn btn-sm">← Bandeja</a>
  </div>

  <!-- Policy banner -->
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 14px;margin-bottom:16px;display:flex;align-items:start;gap:8px">
    <span style="font-size:16px;flex-shrink:0">ℹ️</span>
    <div style="font-size:11.5px;color:#1e3a8a;line-height:1.5">
      <strong>Política de Descargas:</strong> Se puede descargar <strong>1 documento por día</strong>, a excepción de los documentos tipo <strong>METODOLOGÍAS Y ESPECIFICACIONES</strong> (CC-1, CC-7), de los cuales se pueden descargar hasta <strong>10 por día</strong>.
    </div>
  </div>

  <!-- Search card -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.05);max-width:640px">
    <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:16px">Buscar documento</div>
    <div style="margin-bottom:14px">
      <label style="font-size:10.5px;font-weight:600;color:#64748b;display:block;margin-bottom:5px">Código del documento requerido</label>
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
          <span x-text="cargando ? 'Buscando...' : '🔍 Buscar'"></span>
        </button>
      </div>
    </div>

    <!-- Result -->
    <div x-show="resultadoEditable"
         x-transition:enter="transition-opacity duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100">
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px 16px">
        <div style="font-size:10.5px;font-weight:700;color:#166534;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px">Resultado encontrado</div>
        <div style="display:flex;align-items:center;gap:10px;justify-content:space-between;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:10px">
            <span style="font-size:24px">📄</span>
            <div>
              <div style="font-size:12px;font-weight:700;color:#1e293b" x-text="resultadoEditable?.archivo"></div>
              <div style="font-size:11px;color:#64748b" x-text="resultadoEditable?.nombre"></div>
              <div style="font-size:10.5px;color:#059669;margin-top:2px" x-text="resultadoEditable ? 'Límite: ' + resultadoEditable.limite + ' descarga(s) por día para este tipo' : ''"></div>
            </div>
          </div>
          <button @click="descargarEditable()" :disabled="descargado" class="btn btn-primary" style="display:flex;align-items:center;gap:6px">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span x-text="descargado ? '✅ Descargado' : '⬇ Descargar Editable'"></span>
          </button>
        </div>
      </div>
    </div>
  </div>

</div>`
}
