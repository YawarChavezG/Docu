/**
 * pages/VersionEditable.js — Descarga de documento en versión editable
 * Sesion 22 R2 FASE 2: consume /api/v1/documentos/buscar (BD real).
 * Sesion 22 (fix 2): autocomplete EN VIVO mientras el usuario escribe.
 * Sesion 25 / Issue 10.1: política de descargas desde BD (no hardcodeada).
 */
import { documentos } from '../services/documentosApi.js'
import { configGlobal, tiposDocumento } from '../services/parametrizacionApi.js'

export const page = {
  init() {
    window.Alpine?.data('versionEditable', () => ({
      codBuscar: '',
      cargando: false,
      resultadoEditable: null,
      descargado: false,
      resultados: [], // para mostrar lista de matches
      mostrarLista: false, // mostrar el dropdown de sugerencias

      // Politica de descargas (Issue 10.1: viene de BD, no hardcodeada)
      politicaDescargas: {
        max: 1,
        excepciones: [],
        excepcionMax: 10,
        texto: 'Se puede descargar 1 documento(s) por dia',
      },

      _debounceTimer: null,

      async init() {
        // Cargar politica desde BD (Issue 10.1)
        try {
          const [cfgRes, tiposRes] = await Promise.all([
            configGlobal.list('DESCARGAS'),
            tiposDocumento.list(),
          ])
          if (cfgRes.ok) {
            const items = cfgRes.data?.items || cfgRes.data || []
            const maxKey = items.find(i => i.clave === 'max_descargas_editables_dia')
            if (maxKey) this.politicaDescargas.max = Number(maxKey.valor)
            const exKey = items.find(i => i.clave === 'tipos_excluidos_limite_descarga')
            if (exKey) {
              // valor puede ser JSON string o array
              let ex = exKey.valor
              if (typeof ex === 'string') {
                try { ex = JSON.parse(ex) } catch { ex = ex.split(',').map(s => s.trim()) }
              }
              this.politicaDescargas.excepciones = ex || []
            }
          }
          if (tiposRes.ok) {
            const tipos = tiposRes.data?.items || tiposRes.data || []
            const excludidos = tipos.filter(t =>
              this.politicaDescargas.excepciones.some(e =>
                e.toUpperCase() === t.codigo?.toUpperCase() ||
                e.toUpperCase() === t.nombre?.toUpperCase() ||
                e.toUpperCase() === t.slug?.toUpperCase()
              )
            )
            if (excludidos.length > 0) {
              this.politicaDescargas.excepcionMax = Math.max(
                ...excludidos.map(t => t.max_descargas_dia || 0)
              )
            }
          }
          this._armarTextoPolitica()
        } catch (e) {
          let txt = 'Se puede descargar ' + this.politicaDescargas.max + ' documento(s) por dia'
          if (this.politicaDescargas.excepciones.length > 0) {
            txt += ', a excepcion de los documentos tipo ' + this.politicaDescargas.excepciones.join(' Y ')
            txt += ', de los cuales se pueden descargar hasta ' + this.politicaDescargas.excepcionMax + ' por dia'
          }
          this.politicaDescargas.texto = txt
        }
      },

      _armarTextoPolitica() {
        const p = this.politicaDescargas
        let txt = 'Se puede descargar ' + p.max + ' documento(s) por dia'
        if (p.excepciones.length > 0) {
          txt += ', a excepcion de los documentos tipo ' + p.excepciones.join(' Y ')
          txt += ', de los cuales se pueden descargar hasta ' + p.excepcionMax + ' por dia'
        }
        Alpine.nextTick(() => { p.texto = txt })
      },

      // ─── Buscar con debounce (autocomplete en vivo) ───
      onInputChange() {
        // Cancelar timer previo
        if (this._debounceTimer) clearTimeout(this._debounceTimer)
        const q = this.codBuscar.trim()
        if (q.length < 1) {
          this.resultados = []
          this.mostrarLista = false
          this.resultadoEditable = null
          return
        }
        // Debounce 250ms para no saturar la API
        this._debounceTimer = setTimeout(() => this._buscar(q), 250)
      },

      async _buscar(q) {
        this.cargando = true
        try {
          const res = await documentos.buscar(q, 10)
          if (!res.ok) {
            window.toast?.(res.message || 'Error al buscar documentos', 'error')
            return
          }
          const items = res.data?.items || []
          this.resultados = items
          this.mostrarLista = items.length > 0
          if (items.length === 0) {
            // No mostrar toast en cada keystroke — solo cuando el usuario hace Enter
          }
        } catch (e) {
          // Silenciar errores de red durante typing
          this.resultados = []
          this.mostrarLista = false
        } finally {
          this.cargando = false
        }
      },

      // Buscar al hacer click en el boton (mantiene compatibilidad)
      async buscarEditable() {
        const q = this.codBuscar.trim()
        if (!q) {
          window.toast?.('Ingrese un codigo de documento', 'warn')
          return
        }
        // Cancelar el debounce pendiente
        if (this._debounceTimer) clearTimeout(this._debounceTimer)
        await this._buscar(q)
        this.mostrarLista = this.resultados.length > 0
        if (this.resultados.length === 0) {
          window.toast?.('No se encontraron documentos con ese codigo', 'warn')
        }
      },

      // Seleccionar uno de los resultados del dropdown
      seleccionarResultado(match) {
        this.resultadoEditable = {
          archivo: match.codigo_completo + '.docx',
          nombre: match.titulo,
          tipo: match.tipo?.nombre || '',
          area: (match.gerencia?.sigla || '') + ' / ' + (match.area?.sigla || ''),
          vigencia: match.vigencia,
          estatus: match.estatus,
          limite: match.tipo?.max_descargas_dia ?? 1,
        }
        this.codBuscar = match.codigo_completo
        this.mostrarLista = false
        this.resultados = []
      },

      // Descargar
      descargarEditable() {
        this.descargado = true
        window.toast?.('Descargando ' + this.resultadoEditable.archivo + '...', 'success')
      },

      // Cerrar la lista al hacer click fuera
      cerrarLista() {
        this.mostrarLista = false
      },
    }))
  },
  template: /* html */`
<div x-data="versionEditable" style="animation:fadeIn 0.35s ease-out both" @click.outside="cerrarLista()">

  <!-- Header -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Documento en Version Editable</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Descargue el archivo Word/Excel original para modificar o actualizar</p>
    </div>
    <a href="#/bandeja" class="btn btn-sm">Bandeja</a>
  </div>

  <!-- Policy banner (Issue 10.1: texto desde BD) -->
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 14px;margin-bottom:16px">
    <div style="font-size:11.5px;color:#1e3a8a;line-height:1.5">
      <strong>Politica de Descargas:</strong>
      <span x-text="politicaDescargas.texto"></span>
    </div>
  </div>

  <!-- Search card -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.05);max-width:640px">
    <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:16px">Buscar documento</div>
    <div style="margin-bottom:14px;position:relative">
      <label style="font-size:10.5px;font-weight:600;color:#64748b;display:block;margin-bottom:5px">Codigo del documento requerido (escriba y la lista se actualiza automaticamente)</label>
      <div style="display:flex;gap:8px;position:relative">
        <input type="text" class="form-input"
               style="flex:1;font-family:monospace;font-weight:600;text-transform:uppercase;font-size:12px"
               placeholder="EJ: CC-3-005/01"
               x-model="codBuscar"
               @input="$el.value=$el.value.toUpperCase();codBuscar=$el.value;onInputChange()"
               @keydown.enter.prevent="buscarEditable()"
               @focus="if(resultados.length>0) mostrarLista=true"
               autocomplete="off"
               autocorrect="off"
               spellcheck="false">
        <button class="btn btn-primary" @click="buscarEditable()" :disabled="cargando" style="white-space:nowrap;display:flex;align-items:center;gap:6px">
          <svg x-show="cargando" style="width:13px;height:13px;animation:spin 1s linear infinite" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-opacity="0.25"/><path d="M3 12a9 9 0 019-9" stroke-linecap="round"/>
          </svg>
          <span x-text="cargando ? '...' : 'Buscar'"></span>
        </button>

        <!-- Lista desplegable de sugerencias (autocomplete en vivo) -->
        <div x-show="mostrarLista && resultados.length > 0"
             x-transition:enter="transition-opacity duration-150"
             x-transition:enter-start="opacity-0"
             x-transition:enter-end="opacity-100"
             @click.stop
             style="position:absolute;left:0;right:80px;top:calc(100% + 4px);z-index:50;background:#fff;border:1px solid #cbd5e1;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.12);max-height:360px;overflow-y:auto">
          <div style="font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.06em;padding:8px 12px;background:#f8fafc;border-bottom:1px solid #e2e8f0;position:sticky;top:0;z-index:1"
               x-text="resultados.length + ' resultado(s). Click para seleccionar:'"></div>
          <template x-for="r in resultados" :key="r.id">
            <div @click="seleccionarResultado(r)"
                 style="padding:10px 12px;cursor:pointer;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;gap:8px;transition:background 0.1s"
                 @mouseenter="$el.style.background='#f0f9ff'"
                 @mouseleave="$el.style.background='transparent'">
              <div style="min-width:0;flex:1">
                <div style="font-size:11.5px;font-weight:700;color:#1e293b;font-family:monospace" x-text="r.codigo_completo"></div>
                <div style="font-size:10.5px;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" x-text="r.titulo"></div>
              </div>
              <div style="display:flex;gap:4px;align-items:center;flex-shrink:0">
                <span style="font-size:9px;padding:2px 5px;border-radius:4px;background:#e0e7ff;color:#3730a3"
                      x-text="r.tipo?.nombre || ''"></span>
                <span style="font-size:9px;padding:2px 5px;border-radius:4px"
                      :class="r.vigencia === 'VIGENTE' ? 'background:#dcfce7;color:#166534' : (r.vigencia === 'VENCIDO' ? 'background:#fee2e2;color:#991b1b' : 'background:#fef3c7;color:#92400e')"
                      x-text="r.vigencia"></span>
              </div>
            </div>
          </template>
        </div>
      </div>
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
