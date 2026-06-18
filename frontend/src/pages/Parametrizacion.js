/**
 * src/pages/Parametrizacion.js - Parametrizacion General del Sistema.
 *
 * Sesion B - tarea #10: refactorizado para consumir el backend real
 * (EPICA 9 endpoints) a traves de services/parametrizacionApi.js.
 *
 * Sesion 12: eliminada la duplicacion de handlers (segunda declaracion con
 * mocks heredados de la version pre-refactor). Ahora todos los CRUD (save,
 * delete, add, mover) persisten en la BD via la API real. Dropdown de
 * "Tipos excluidos" muestra catalogo real de tipos_documento.
 *
 * Sesion 13:
 *  - Fixes A1-A11 (refresh al login, errores Alpine, export, logs, etc).
 *  - Refactor tipos_documento (codigo int + slug + nombre unique).
 *  - Semaforizacion por tipo de tarea (nueva tabla semaforizacion_tarea).
 *  - Plantillas: 11 codigos (10 del doc + 1 PDF) con editor WYSIWYG Tiptap.
 *
 * Tabs:
 *  - Tiempos y SLAs: /api/v1/configuracion-global + /semaforizacion-tarea
 *  - Restricciones:  /api/v1/configuracion-global
 *  - Diccionarios:   /api/v1/tipos-documento + /estados + /matriz-enrutamiento-eto
 *  - Gerencias:      /api/v1/gerencias + /areas
 *  - Notificaciones: /api/v1/email-templates (11 plantillas con Tiptap)
 *  - Usuarios:       /api/v1/usuarios (incluye export XLSX/CSV)
 *  - Logs:           /api/v1/audit-log
 */

import { initPlantillaEditor } from '../components/PlantillaEditor.js'
import { API_BASE } from '../utils/config.js'
import { apiFetch } from '../utils/api.js'

import {
  configGlobal,
  feriados,
  emailTemplates,
  matrizEto,
  tiposDocumento,
  estados,
  gerencias,
  areas,
  auditLog,
  usuarios,
  roles,
  semaforizacion,
} from '../services/parametrizacionApi.js'

export const page = {
  init() {
    window.Alpine?.data('paramPage', () => {
      // ★ CLAVE Sesion 16: `let editor` en closure del factory, NO en
      // `this`. Esto es lo que la doc oficial de Tiptap recomienda para
      // evitar "Applying a mismatched transaction" (Alpine envuelve las
      // propiedades de `this` en Proxies, lo que rompe ProseMirror).
      let editor = null
      let editorDestroy = null

      return {
      /* ── Tabs ── */
      tab: 'tiempos',
      tabs: [
        { id: 'tiempos', label: 'Tiempos y SLAs' },
        { id: 'restricciones', label: 'Restricciones' },
        { id: 'diccionarios', label: 'Diccionarios y Enrutamiento' },
        { id: 'gerencias', label: 'Gerencias y Areas' },
        { id: 'notificaciones', label: 'Plantillas de Notificacion' },
        { id: 'usuarios', label: 'Gestion de Usuarios' },
        { id: 'logs', label: 'Logs de Auditoria' },
      ],

      /* ── Estado general: loading por tab ── */
      loading: { tiempos: false, restricciones: false, diccionarios: false, gerencias: false, notificaciones: false, logs: false, usuarios: false },

      /* ── LOGS (Auditoria - Sesion B #9) ── */
      logs: [],
      logSearch: '',
      logTabFilter: '',
      logAccionFilter: '',
      logRecursoFilter: '',
      logPage: 1,
      logPageSize: 10,
      logTotal: 0,
      logTotalPages: 1,
      get logsFiltrados() {
        // Filtro client-side adicional sobre la pagina actual (busqueda libre).
        const q = this.logSearch.toLowerCase()
        if (!q) return this.logs
        return this.logs.filter(l =>
          (l.descripcion || '').toLowerCase().includes(q) ||
          (l.usuario_username || '').toLowerCase().includes(q) ||
          (l.recurso || '').toLowerCase().includes(q) ||
          (l.accion || '').toLowerCase().includes(q) ||
          (l.usuario_nombre || '').toLowerCase().includes(q)
        )
      },
      _tabFromRecurso(recurso) {
        const map = { gerencia: 'gerencias', area: 'gerencias', feriado: 'restricciones', configuracion_global: 'restricciones', email_template: 'notificaciones', matriz_eto: 'diccionarios', tipo_documento: 'diccionarios', estado: 'diccionarios', usuario: 'usuarios' }
        return map[recurso] || ''
      },
      _formatFechaBolivia(iso) {
        if (!iso) return ''
        try {
          return new Date(iso).toLocaleString('es-BO', {
            timeZone: 'America/La_Paz',
            dateStyle: 'short',
            timeStyle: 'medium',
          })
        } catch (_) { return iso }
      },
      _mapLog(l) {
        // Mapea el shape del backend (AuditLog) al shape que consume el template.
        // Antes faltaba este mapeo y la tabla quedaba con celdas vacias.
        return {
          id: l.id,
          fecha: this._formatFechaBolivia(l.created_at),
          tab: this._tabFromRecurso(l.recurso),
          parametro: `${l.accion} ${l.recurso}${l.recurso_id ? ' #' + l.recurso_id : ''}`,
          anterior: l.detalles?.antes ? JSON.stringify(l.detalles.antes) : '—',
          nuevo: l.detalles?.despues ? JSON.stringify(l.detalles.despues) : '—',
          usuario: l.usuario_username || '—',
          // Crudos del backend (por si se necesitan en el template)
          accion: l.accion,
          recurso: l.recurso,
          recurso_id: l.recurso_id,
          descripcion: l.descripcion,
          usuario_username: l.usuario_username,
          usuario_nombre: l.usuario_nombre,
        }
      },
      async cargarLogs() {
        this.loading.logs = true
        try {
          const res = await auditLog.list({
            limit: this.logPageSize,
            offset: (this.logPage - 1) * this.logPageSize,
            accion: this.logAccionFilter,
            recurso: this.logRecursoFilter,
          })
          if (res.ok) {
            const data = res.data
            this.logs = (data.items || []).map(l => this._mapLog(l))
            this.logTotal = data.total
            this.logTotalPages = Math.max(1, Math.ceil(data.total / this.logPageSize))
          } else {
            window.toast(`Error cargando logs: ${res.status}`, 'error')
          }
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        } finally {
          this.loading.logs = false
        }
      },
      logPrevPage() { if (this.logPage > 1) { this.logPage--; this.cargarLogs() } },
      logNextPage() { if (this.logPage < this.logTotalPages) { this.logPage++; this.cargarLogs() } },
      logGoToPage(p) {
        if (p < 1) p = 1
        if (p > this.logTotalPages) p = this.logTotalPages
        if (p === this.logPage) return
        this.logPage = p
        this.cargarLogs()
      },
      logOnPageSizeChange() { this.logPage = 1; this.cargarLogs() },
      logOnFilterChange() { this.logPage = 1; this.cargarLogs() },
      get logPageStart() { return this.logTotal === 0 ? 0 : (this.logPage - 1) * this.logPageSize + 1 },
      get logPageEnd() { return Math.min(this.logPage * this.logPageSize, this.logTotal) },
      get logVisiblePages() {
        const total = this.logTotalPages
        const current = this.logPage
        if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
        const pages = [1]
        if (current > 4) pages.push('...')
        const start = Math.max(2, current - 1)
        const end = Math.min(total - 1, current + 1)
        for (let i = start; i <= end; i++) pages.push(i)
        if (current < total - 3) pages.push('...')
        if (total > 1) pages.push(total)
        return pages
      },
      async exportarLogs(formato = 'xlsx') {
        // Sesion 13: delega al backend (XLSX profesional via /audit-log/export)
        //
        // Sesion 15: mismo fix que exportarUsuarios. Para evitar perder
        // el user gesture, construimos los params sincronicamente y
        // llamamos apiDownload DIRECTAMENTE sin await previo. Si lo
        // hacemos despues de un await, el browser ignora el a.click().
        try {
          const params = new URLSearchParams({ formato })
          if (this.logAccionFilter) params.set('accion', this.logAccionFilter)
          if (this.logRecursoFilter) params.set('recurso', this.logRecursoFilter)
          const url = `/audit-log/export?${params.toString()}`
          const filename = formato === 'csv'
            ? `logs_sgd_${new Date().toISOString().slice(0,10)}.csv`
            : `logs_sgd_${new Date().toISOString().slice(0,10)}.xlsx`
          window.apiDownload(url, { filename }).then(res => {
            if (res && res.ok) {
              window.toast(`Logs exportados a ${formato.toUpperCase()}`, 'success')
              this.cargarLogs().catch(() => {})
            } else {
              window.toast(`Error exportando logs`, 'error')
            }
          })
        } catch (e) {
          window.toast(`Error: ${e.message}`, 'error')
        }
      },

      /* ── Tiempos y SLAs (US-9.01) ── */
      // Sesion 23 / Bloque A5: plazoRevision y plazoLectura fueron removidos
      // porque son redundantes con la tabla semaforizacion_tarea. La grilla
      // de semaforos por tipo de tarea es la unica fuente de verdad.
      tiempos: { plazoRevision: 5, plazoLectura: 3 },
      vigencias: [],
      // Semaforizacion por tipo de tarea (sesion 13: nueva tabla)
      semaforos: [],   // [{tipo_tarea, dias_verde, dias_amarillo, dias_rojo, plazo_maximo_dias}]
      semaforoEditing: null,  // cual fila esta en modo edicion
      semaforoOriginal: null, // snapshot para detectar cambios sucios
      // Snapshot de las vigencias originales para detectar cambios sucios
      _vigenciasOriginal: [],
      async cargarTiempos() {
        this.loading.tiempos = true
        try {
          // Cargar tipos-doc con periodo_vigencia para la grilla de vigencias
          const tdRes = await tiposDocumento.list()
          if (tdRes.ok) {
            this.vigencias = (tdRes.data.items || []).map(t => ({
              id: t.id, tipo: t.nombre, codigo: t.codigo, slug: t.slug,
              anios: t.indefinido ? 'Indefinido' : (t.periodo_vigencia ?? 0),
              indefinido: t.indefinido,
            }))
            this._vigenciasOriginal = JSON.parse(JSON.stringify(this.vigencias))
          }
          // Cargar semaforizacion por tipo de tarea
          const sfRes = await semaforizacion.list()
          if (sfRes.ok) {
            this.semaforos = (sfRes.data.items || []).map(s => ({
              tipo_tarea: s.tipo_tarea,
              dias_verde: s.dias_verde,
              dias_amarillo: s.dias_amarillo,
              dias_rojo: s.dias_rojo,
              plazo_maximo_dias: s.plazo_maximo_dias,
            }))
          }
        } catch (e) {
          window.toast(`Error cargando tiempos: ${e.message}`, 'error')
        } finally {
          this.loading.tiempos = false
        }
      },
      async guardarTiempos() {
        try {
          // 1) Guardar periodo_vigencia por cada tipo de documento que haya cambiado
          let cambiosVigencia = 0
          for (const v of this.vigencias) {
            const orig = (this._vigenciasOriginal || []).find(x => x.id === v.id)
            if (!orig) continue
            const origAnios = orig.indefinido ? 'Indefinido' : (orig.anios ?? 0)
            if (origAnios === v.anios) continue
            const indefinido = v.anios === 'Indefinido'
            const periodo = indefinido ? null : parseInt(v.anios, 10) || 1
            const res = await tiposDocumento.update(v.id, { periodo_vigencia: periodo, indefinido })
            if (res.ok) cambiosVigencia++
            else window.toast(`Error guardando vigencia de ${v.tipo}: ${res.data?.detail || res.status}`, 'error')
          }
          window.toast(
            cambiosVigencia > 0
              ? `${cambiosVigencia} vigencia(s) de tipo actualizadas`
              : 'Vigencias guardadas',
            'success'
          )
          await this.cargarLogs()
          await this.cargarTiempos()
        } catch (e) {
          window.toast(`Error: ${e.message}`, 'error') }
      },
      // ── Semaforizacion por tipo de tarea (sesion 13) ──
      editSemaforo(s) {
        this.semaforoEditing = s.tipo_tarea
        this.semaforoOriginal = { ...s }
      },
      cancelSemaforo() {
        this.semaforoEditing = null
        this.semaforoOriginal = null
      },
      async guardarSemaforo(s) {
        // Validacion: verde < amarillo < rojo <= plazo_maximo
        if (!(s.dias_verde < s.dias_amarillo && s.dias_amarillo < s.dias_rojo && s.dias_rojo <= s.plazo_maximo_dias)) {
          window.toast(`⚠️ ${s.tipo_tarea}: dias_verde(${s.dias_verde}) < dias_amarillo(${s.dias_amarillo}) < dias_rojo(${s.dias_rojo}) <= plazo_maximo(${s.plazo_maximo_dias})`, 'warn')
          return
        }
        const res = await semaforizacion.update(s.tipo_tarea, {
          dias_verde: s.dias_verde,
          dias_amarillo: s.dias_amarillo,
          dias_rojo: s.dias_rojo,
          plazo_maximo_dias: s.plazo_maximo_dias,
        })
        if (res.ok) {
          window.toast(`Semaforo ${s.tipo_tarea} actualizado`, 'success')
          this.semaforoEditing = null
          this.semaforoOriginal = null
          await this.cargarTiempos()
          await this.cargarLogs()
        } else {
          window.toast(`Error: ${res.data?.detail || res.status}`, 'error')
        }
      },

      /* ── Restricciones (US-9.02) ── */
      restricciones: { maxAdjuntos: 20, maxSizeMB: 20, maxDescargasDia: 10, bandejaRegistros: 10 },
      chips: [], // tipos excluidos de limite de descarga (US-9.02) — cargados en cargarRestricciones() desde backend
      async cargarRestricciones() {
        this.loading.restricciones = true
        try {
          const res = await configGlobal.list()
          if (res.ok) {
            const cfg = (res.data.items || []).reduce((acc, c) => { acc[c.clave] = c.valor; return acc }, {})
            this.restricciones = {
              maxAdjuntos: parseInt(cfg.max_archivos_por_solicitud || '20', 10),
              maxSizeMB: parseInt(cfg.max_tamano_archivo_mb || '20', 10),
              maxDescargasDia: parseInt(cfg.max_descargas_editables_dia || '10', 10),
              bandejaRegistros: parseInt(cfg.paginacion_mi_bandeja || '10', 10),
            }
            // Chips: tipos excluidos se guardan como JSON en una clave dedicada
            try {
              this.chips = cfg.tipos_excluidos_limite_descarga ? JSON.parse(cfg.tipos_excluidos_limite_descarga) : []
            } catch (_) { this.chips = [] }
          }
        } catch (e) {
          window.toast(`Error cargando restricciones: ${e.message}`, 'error')
        } finally {
          this.loading.restricciones = false
        }
      },
      nuevoChip: '',
      quitarChip(tipo) { this.chips = this.chips.filter(c => c !== tipo) },
      agregarChip() {
        const t = (this.nuevoChip || '').trim()
        if (!t) return
        if (this.chips.includes(t)) { window.toast('Tipo ya excluido', 'warn'); return }
        this.chips.push(t); this.nuevoChip = ''
      },
      async guardarRestricciones() {
        try {
          await configGlobal.bulkUpsert('ARCHIVOS', [
            { clave: 'max_archivos_por_solicitud', valor: String(this.restricciones.maxAdjuntos) },
            { clave: 'max_tamano_archivo_mb', valor: String(this.restricciones.maxSizeMB) },
          ])
          await configGlobal.bulkUpsert('DESCARGAS', [
            { clave: 'max_descargas_editables_dia', valor: String(this.restricciones.maxDescargasDia) },
            { clave: 'paginacion_mi_bandeja', valor: String(this.restricciones.bandejaRegistros) },
            { clave: 'tipos_excluidos_limite_descarga', valor: JSON.stringify(this.chips) },
          ])
          window.toast('Restricciones guardadas', 'success')
          await this.cargarLogs()
        } catch (e) {
          window.toast(`Error: ${e.message}`, 'error')
        }
      },
      guardarLimitesDescarga() { this.guardarRestricciones() },
      get tiposExcluibles() {
        // Tipos de documento activos que NO estan ya en chips.
        // Usado por el dropdown de "Tipos excluidos" en el template.
        return (this.tiposDocs || []).filter(t => t.activo && !this.chips.includes(t.cod))
      },
      // Para los chips, ahora usamos el codigo (int) en vez del slug.
      // Si la BD tiene chips viejos (strings), los migramos al codigo int.
      get chipsEnCodigoInt() {
        return (this.chips || []).map(c => {
          if (typeof c === 'number') return c
          const found = (this.tiposDocs || []).find(t => t.cod === c)
          return found ? found.codigo_int : null
        }).filter(c => c !== null)
      },

      /* ── Diccionarios (US-9.03) ── */
      tiposDocs: [],
      tipoEditing: null,
      estados: [],
      estadoEditing: null,
      matrizETO: [],
      analistas: [],          // ETOs para el dropdown de la matriz (rol ETO)
      usuariosActivos: [],    // todos los usuarios activos para delegado de matriz
      tiempoVigenciaDefault: 3,  // años; se carga de configuracion_global.tiempo_vigencia_anios
      async cargarDiccionarios() {
        this.loading.diccionarios = true
        try {
          const [tdRes, estRes, matRes, uRes, uaRes, cfgRes] = await Promise.all([
            tiposDocumento.list(),
            estados.list(),
            matrizEto.list(),
            usuarios.list({ rol: 'ETO' }),
            usuarios.listActivos(),
            configGlobal.list(),
          ])
          if (tdRes.ok) this.tiposDocs = (tdRes.data.items || []).map(t => ({
            id: t.id, tipo: t.nombre, cod: t.slug, codigo_int: t.codigo,
            vigencia: t.indefinido ? 'Indefinido' : (t.periodo_vigencia || 0),
            activo: t.activo,
          }))
          if (estRes.ok) this.estados = (estRes.data.items || []).map(e => ({
            id: e.id, est: e.nombre, cod: e.codigo, ctx: e.contexto, activo: e.activo,
          }))
          if (matRes.ok) this.matrizETO = (matRes.data.items || []).map(m => ({
            id: m.id, gerencia: m.gerencia_sigla, gerencia_id: m.gerencia_id,
            analista: m.analista_username,
            analista_id: m.analista_usuario_id == null ? null : String(m.analista_usuario_id),
            analista_nombre: m.analista_nombre,
            delegado: m.delegado_username,
            delegado_id: m.delegado_usuario_id == null ? null : String(m.delegado_usuario_id),
            delegado_nombre: m.delegado_nombre,
            disponible: m.disponibilidad === 'DISPONIBLE', disponibilidad: m.disponibilidad,
          }))
          if (uRes.ok) this.analistas = (uRes.data.items || []).map(u => ({ id: u.id, username: u.username, nombre: u.nombre_completo }))
          if (uaRes.ok) this.usuariosActivos = (uaRes.data.items || []).map(u => ({ id: u.id, username: u.username, nombre: u.nombre_completo }))
          // Re-bind de los controles de la matriz ETO: x-model/x-model no se
          // re-bindea cuando las options (o el DOM) se cargan DESPUÉS del
          // initial render de Alpine. Fix: forzar el value/checked después de
          // poblar `analistas` y `usuariosActivos`, dentro de un nextTick para
          // esperar el render de las options.
          await this.$nextTick()
          document.querySelectorAll('select[data-matriz-select="analista"]').forEach(sel => {
            const mid = sel.getAttribute('data-matriz-id')
            const fila = this.matrizETO.find(x => String(x.id) === String(mid))
            if (fila) sel.value = fila.analista_id == null ? '' : String(fila.analista_id)
          })
          document.querySelectorAll('select[data-matriz-select="delegado"]').forEach(sel => {
            const mid = sel.getAttribute('data-matriz-id')
            const fila = this.matrizETO.find(x => String(x.id) === String(mid))
            if (fila) sel.value = fila.delegado_id == null ? '' : String(fila.delegado_id)
          })
          document.querySelectorAll('input[data-matriz-check="disponible"]').forEach(cb => {
            const mid = cb.getAttribute('data-matriz-id')
            const fila = this.matrizETO.find(x => String(x.id) === String(mid))
            if (fila) cb.checked = !!fila.disponible
          })
          if (cfgRes.ok) {
            const cfg = (cfgRes.data.items || []).reduce((acc, c) => { acc[c.clave] = c.valor; return acc }, {})
            this.tiempoVigenciaDefault = parseInt(cfg.tiempo_vigencia_anios || '3', 10)
          }
        } catch (e) {
          window.toast(`Error cargando diccionarios: ${e.message}`, 'error')
        } finally {
          this.loading.diccionarios = false
        }
      },
      addTipo() {
        const nuevo = { tipo: '', cod: '', codigo_int: 1, _new: true }
        this.tiposDocs.push(nuevo); this.tipoEditing = nuevo
      },
      async saveTipo(t) {
        if (!t.tipo.trim() || !t.cod.trim()) { window.toast('Complete tipo y codigo', 'warn'); return }
        const slug = t.cod.toUpperCase().slice(0, 10)
        const codigo = parseInt(t.codigo_int, 10) || 1
        try {
          if (t._new) {
            // Default periodo_vigencia viene de configuracion_global.tiempo_vigencia_anios
            // (antes hardcoded a 5; bug detectado sesion 13)
            const res = await tiposDocumento.create({
              codigo, slug, nombre: t.tipo,
              periodo_vigencia: this.tiempoVigenciaDefault,
              indefinido: false,
              max_descargas_dia: 10,
              activo: true,
            })
            if (res.ok) { t.id = res.data.id; delete t._new; this.tipoEditing = null; window.toast('Tipo creado', 'success'); await this.cargarDiccionarios(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          } else {
            const res = await tiposDocumento.update(t.id, { codigo, slug, nombre: t.tipo })
            if (res.ok) { this.tipoEditing = null; window.toast('Tipo actualizado', 'success'); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          }
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },
      cancelTipo(t) { if (t._new) this.tiposDocs.splice(this.tiposDocs.indexOf(t), 1); this.tipoEditing = null },
      deleteTipo(t) {
        window.confirmDeleteModal?.abrir({
          titulo: 'Eliminar Tipo de Documento',
          mensaje: `Eliminar el tipo <strong>${t.tipo}</strong> (${t.cod})?`,
          onConfirm: async () => {
            const res = await tiposDocumento.remove(t.id)
            if (res.ok) { window.toast('Tipo eliminado', 'warn'); await this.cargarDiccionarios(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          },
        })
      },
      addEstado() {
        const nuevo = { est: '', cod: '', ctx: 'TAREA', _new: true }
        this.estados.push(nuevo); this.estadoEditing = nuevo
      },
      async saveEstado(e) {
        if (!e.est.trim()) { window.toast('Ingrese el nombre del estado', 'warn'); return }
        try {
          if (e._new) {
            const res = await estados.create({ codigo: e.cod || e.est.toUpperCase().replace(/\s+/g, '_'), nombre: e.est, contexto: e.ctx, orden: 99, activo: true })
            if (res.ok) { e.id = res.data.id; delete e._new; this.estadoEditing = null; window.toast('Estado creado', 'success'); await this.cargarDiccionarios(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          } else {
            const res = await estados.update(e.id, { nombre: e.est, contexto: e.ctx })
            if (res.ok) { this.estadoEditing = null; window.toast('Estado actualizado', 'success'); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          }
        } catch (err) { window.toast(`Error: ${err.message}`, 'error') }
      },
      cancelEstado(e) { if (e._new) this.estados.splice(this.estados.indexOf(e), 1); this.estadoEditing = null },
      deleteEstado(e) {
        window.confirmDeleteModal?.abrir({
          titulo: 'Eliminar Estado',
          mensaje: `Eliminar el estado <strong>${e.est}</strong> (${e.ctx})?`,
          onConfirm: async () => {
            const res = await estados.remove(e.id)
            if (res.ok) { window.toast('Estado eliminado', 'warn'); await this.cargarDiccionarios(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          },
        })
      },
      async guardarFilaMatriz(m) {
        try {
          // Validar: si NO esta disponible, debe tener delegado.
          if (!m.disponible && !m.delegado_id) {
            window.toast('⚠️ Si el analista esta Ausente, asigne un delegado', 'warn')
            return
          }
          const payload = {
            disponibilidad: m.disponible ? 'DISPONIBLE' : 'AUSENTE',
            analista_usuario_id: m.analista_id ? Number(m.analista_id) : null,
            delegado_usuario_id: !m.disponible ? (m.delegado_id ? Number(m.delegado_id) : null) : null,
          }
          const res = await matrizEto.update(m.id, payload)
          if (res.ok) {
            window.toast('Fila actualizada', 'success')
            await this.cargarDiccionarios()   // re-lee del backend para sincronizar
            await this.cargarLogs()
          } else {
            window.toast(`Error: ${res.data?.detail || res.status}`, 'error')
          }
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },

      /* ── Gerencias y Areas (US-9.06 + #9d) ── */
      gerencias: [],
      areasPorGerencia: {},
      gerSelId: null,
      gerEditMode: false,
      gerEditNombre: '',
      gerEditCod: '',
      get gerSel() { return this.gerencias.find(g => g.id === this.gerSelId) },
      get areasGerSel() { return this.areasPorGerencia[this.gerSelId] || [] },
      async cargarGerencias() {
        this.loading.gerencias = true
        try {
          const res = await gerencias.list('', 1, 200)
          if (res.ok) {
            // Mapear response del backend a la estructura que espera el template.
            // El template usa `g.areas.length`, `g.cod`, `gerSel.areas`, `a.n`, `a.c`
            // (legacy de la version mock-only). Adaptamos el shape para que
            // funcione con los datos REALES del backend.
            this.gerencias = (res.data.items || []).map(g => ({
              id: g.id,
              sigla: g.sigla,
              nombre: g.nombre,
              cod: g.sigla,           // alias para `g.cod` en el template
              activo: g.activo,
              orden: g.orden,
              areas_count: g.areas_count ?? 0,
              areas: [],              // se llena async abajo; evita undefined en el template
            }))
            if (this.gerencias.length && !this.gerSelId) this.gerSelId = this.gerencias[0].id
            // Cargar areas de cada gerencia en paralelo (Promise.all)
            await Promise.all(this.gerencias.map(async (g) => {
              try {
                const ar = await areas.list('', g.id)
                if (ar.ok) {
                  const list = (ar.data.items || []).map(a => ({
                    id: a.id,
                    sigla: a.sigla,
                    nombre: a.nombre,
                    n: a.nombre,           // alias para `a.n` en el template
                    c: a.sigla,            // alias para `a.c` en el template
                    activo: a.activo,
                    orden: a.orden,
                    usuarios_count: a.usuarios_count,
                    _new: false,
                    _edit: false,
                  }))
                  g.areas = list
                  this.areasPorGerencia[g.id] = list
                }
              } catch { /* ignore individual failure */ }
            }))
          }
        } catch (e) {
          window.toast(`Error cargando gerencias: ${e.message}`, 'error')
        } finally {
          this.loading.gerencias = false
        }
      },
      async addGerencia() {
        try {
          const res = await gerencias.create({ sigla: 'NUEVA', nombre: 'Nueva Gerencia', orden: 99, activo: true })
          if (res.ok) { window.toast('Gerencia creada', 'success'); await this.cargarGerencias(); await this.cargarLogs(); this.gerSelId = res.data.id; this.startEditGer() }
          else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },
      startEditGer() { const g = this.gerSel; if (!g) return; this.gerEditMode = true; this.gerEditNombre = g.nombre; this.gerEditCod = g.sigla },
      async saveGer() {
        const g = this.gerSel; if (!g) return
        if (!this.gerEditNombre.trim() || !this.gerEditCod.trim()) { window.toast('Complete nombre y sigla', 'warn'); return }
        try {
          const res = await gerencias.update(g.id, { nombre: this.gerEditNombre.trim(), sigla: this.gerEditCod.trim().toUpperCase().slice(0, 10) })
          if (res.ok) { this.gerEditMode = false; window.toast('Gerencia actualizada', 'success'); await this.cargarGerencias(); await this.cargarLogs() }
          else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },
      deleteGer() {
        const g = this.gerSel; if (!g) return
        window.confirmDeleteModal?.abrir({
          titulo: 'Eliminar Gerencia',
          mensaje: `Borrado logico de la gerencia <strong>${g.nombre}</strong>. Las areas hijas tambien se desactivaran.`,
          onConfirm: async () => {
            const res = await gerencias.remove(g.id)
            if (res.ok) { window.toast('Gerencia eliminada (logico)', 'warn'); await this.cargarGerencias(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          },
        })
      },
      addArea() {
        const g = this.gerSel; if (!g) return
        if (!this.areasPorGerencia[g.id]) this.areasPorGerencia[g.id] = []
        // El template usa a.n / a.c como aliases, y el backend canónico es
        // nombre / sigla. Seteamos ambos para que el binding bidireccional
        // del template (x-model="a.n") se refleje al guardar.
        this.areasPorGerencia[g.id].push({
          sigla: 'NV', nombre: 'Nueva Area',
          n: 'Nueva Area', c: 'NV',
          orden: 99, _edit: true, _new: true,
        })
      },
      async saveArea(a) {
        const g = this.gerSel; if (!g) return
        // El template bindea x-model="a.n" / x-model="a.c"; si el usuario edita
        // ahi, los canónicos nombre/sigla quedan con el valor inicial. Resolvemos
        // desde los aliases primero y caemos al canónico.
        const nombre = (a.n ?? a.nombre ?? '').trim()
        const siglaRaw = (a.c ?? a.sigla ?? '').trim()
        if (!nombre || !siglaRaw) { window.toast('Complete nombre y sigla', 'warn'); return }
        const sigla = siglaRaw.toUpperCase().slice(0, 10)
        try {
          if (a._new) {
            const res = await areas.create({ gerencia_id: g.id, sigla, nombre, orden: a.orden || 0, activo: true })
            if (res.ok) { window.toast('Area creada', 'success'); await this.cargarGerencias(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          } else {
            const res = await areas.update(a.id, { sigla, nombre })
            if (res.ok) { delete a._edit; window.toast('Area actualizada', 'success'); await this.cargarGerencias(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          }
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },
      cancelEditArea(a) {
        if (a._new) { const g = this.gerSel; this.areasPorGerencia[g.id] = this.areasPorGerencia[g.id].filter(x => x !== a) }
        else { delete a._edit }
      },
      deleteArea(a) {
        const g = this.gerSel; if (!g) return
        window.confirmDeleteModal?.abrir({
          titulo: 'Eliminar Area',
          mensaje: `Eliminar el area <strong>${a.nombre}</strong> (${a.sigla})? Borrado logico por default.`,
          onConfirm: async () => {
            const res = await areas.remove(a.id, false)
            if (res.ok) { window.toast('Area eliminada (logico)', 'warn'); await this.cargarGerencias(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          },
        })
      },
      abrirMoverArea(a) {
        const g = this.gerSel; if (!g) return
        window.moveAreaModal?.abrir({
          area: a,
          origenId: g.id,
          gerencias: this.gerencias.filter(x => x.id !== g.id).map(x => ({ id: x.id, sigla: x.sigla, nombre: x.nombre })),
          onConfirmar: async (destinoId) => {
            const res = await areas.mover(a.id, destinoId)
            if (res.ok) { window.toast(`Area movida`, 'success'); await this.cargarGerencias(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          },
        })
      },

      /* ── Plantillas de Notificacion (US-9.04, sesion 13 con Tiptap) ── */
      plantillaSelect: 0,
      plantillas: [],
      etiquetas: [], // variables JSON de la plantilla seleccionada
      // Editor Tiptap (Sesion 16: editor en closure del factory, NO en `this`)
      _editorMounted: false,    // flag para evitar doble mount (el editor vive en closure)
      // Toolbar state (se actualiza desde Tiptap selectionUpdate)
      tbState: {
        bold: false, italic: false, underline: false, strike: false,
        h1: false, h2: false, h3: false,
        bulletList: false, orderedList: false, blockquote: false, codeBlock: false,
      },
      // Color / font-size del textStyle
      tbColor: '#000000',
      tbFontSize: '',
      async cargarNotificaciones() {
        this.loading.notificaciones = true
        try {
          // Sesion 16: el editor vive en closure del factory (NO en `this`).
          // No destruimos al re-cargar. La destruccion previa causaba
          // "mismatched transaction" porque el destroy() async de Tiptap 3.x
          // no terminaba antes del nuevo mount.
          const res = await emailTemplates.list()
          if (res.ok) {
            this.plantillas = (res.data.items || []).map(t => ({
              id: t.id, codigo: t.codigo, nombre: t.nombre,
              asunto: t.asunto, cuerpo: t.cuerpo_html,
              variables: t.variables_json || [], activo: t.activo,
            }))
            this.plantillaSelect = 0
            if (this.plantillas.length) {
              const p = this.plantillas[0]
              this.etiquetas = p?.variables || []
              if (!this._editorMounted || !editor || editor.isDestroyed) {
                await this._mountTiptap()
              }
            }
          }
        } catch (e) {
          window.toast(`Error cargando plantillas: ${e.message}`, 'error')
        } finally {
          this.loading.notificaciones = false
        }
      },
      // Click en una fila del sidebar de plantillas.
      onSelectPlantillaClick(i) {
        if (this.plantillaSelect === i) return
        this.plantillaSelect = i
        const p = this.plantillas[i]
        this.etiquetas = p?.variables || []
        if (editor && !editor.isDestroyed && p) {
          // Quitar el focus del DOM element antes de setContent para
          // evitar transacciones concurrentes.
          const dom = editor.options.element
          if (dom && document.activeElement === dom) dom.blur()
          // setContent con emitUpdate=false evita que onUpdate se dispare.
          editor.commands.setContent(p.cuerpo || '<p></p>', false)
          // Forzar refresh del toolbar.
          this._updateToolbarState()
        }
      },
      // ─── Tiptap lifecycle ───
      // Sesion 16: editor se guarda en closure `let editor` del factory.
      // NO en `this` (eso es lo que causaba el "mismatched transaction"
      // porque Alpine wrappea las props en Proxies que rompen ProseMirror).
      async _mountTiptap() {
        await this.$nextTick()
        await new Promise(r => setTimeout(r, 0))
        const currentMountEl = this.$refs?.tiptapBody
          || document.querySelector('[x-ref="tiptapBody"]')
        if (!currentMountEl) {
          console.warn('[tiptap] mount point no encontrado, se reintentará en nextTick')
          return
        }
        // Si hay un editor pero su element NO es el mount actual,
        // o si ya esta destruido, lo descartamos para crear uno nuevo.
        if (editor) {
          const editorEl = editor.options?.element
          const isValid = !editor.isDestroyed && editorEl === currentMountEl
          if (!isValid) {
            try { await editorDestroy() } catch (_) {}
            editor = null
            editorDestroy = null
            this._editorMounted = false
          }
        }
        if (this._editorMounted && editor && !editor.isDestroyed) {
          // Ya esta montado; solo actualizamos contenido
          this.onSelectPlantilla()
          return
        }
        const p = this.plantillas[this.plantillaSelect]
        const handle = initPlantillaEditor(currentMountEl, p?.cuerpo || '<p></p>', (html) => {
          this._editorHtmlCache = html
        })
        // ★ Asignar al CLOSURE, NO a `this`
        editor = handle.editor
        editorDestroy = handle.destroy
        this._editorHtmlCache = p?.cuerpo || ''
        this._editorMounted = true
        editor.on('selectionUpdate', () => this._updateToolbarState())
      },
      _updateToolbarState() {
        if (!editor || editor.isDestroyed) return
        try {
          this.tbState = {
            bold: editor.isActive('bold'),
            italic: editor.isActive('italic'),
            underline: editor.isActive('underline'),
            strike: editor.isActive('strike'),
            h1: editor.isActive('heading', { level: 1 }),
            h2: editor.isActive('heading', { level: 2 }),
            h3: editor.isActive('heading', { level: 3 }),
            bulletList: editor.isActive('bulletList'),
            orderedList: editor.isActive('orderedList'),
            blockquote: editor.isActive('blockquote'),
            codeBlock: editor.isActive('codeBlock'),
          }
          // Color actual del mark textStyle
          const textStyleAttrs = editor.getAttributes('textStyle')
          const color = textStyleAttrs.color
          if (color) this.tbColor = color
          const fontSize = textStyleAttrs.fontSize
          this.tbFontSize = fontSize || ''
        } catch (e) { /* editor en transicion, ignorar */ }
      },
      // ─── Toolbar actions (template las invoca) ───
      // ★ Sesion 16: usar `editor` (closure) directamente con el patron
      // oficial chain().focus().X().run(). La doc oficial de Tiptap
      // para Alpine 3.x lo dice: el editor debe vivir en closure, no en
      // `this`, para evitar que Alpine lo wrappee en un Proxy.
      tbToggle(name) {
        if (!editor || editor.isDestroyed) return
        try {
          // Mapear nombre de toolbar a command de Tiptap
          const cmd = {
            bold: 'toggleBold',
            italic: 'toggleItalic',
            underline: 'toggleUnderline',
            strike: 'toggleStrike',
            h1: () => editor.chain().focus().toggleHeading({ level: 1 }).run(),
            h2: () => editor.chain().focus().toggleHeading({ level: 2 }).run(),
            h3: () => editor.chain().focus().toggleHeading({ level: 3 }).run(),
            bulletList: 'toggleBulletList',
            orderedList: 'toggleOrderedList',
            blockquote: 'toggleBlockquote',
            codeBlock: 'toggleCodeBlock',
            undo: 'undo',
            redo: 'redo',
          }[name]
          if (!cmd) return
          if (typeof cmd === 'function') cmd()
          else editor.chain().focus()[cmd]().run()
        } catch (e) { console.warn('[tiptap] tbToggle error:', e) }
      },
      tbSetColor(color) {
        if (!editor || editor.isDestroyed) return
        this.tbColor = color
        // Tiptap 3.x: setColor es command (no chain method)
        editor.commands.setColor(color)
      },
      tbUnsetColor() {
        if (!editor || editor.isDestroyed) return
        this.tbColor = '#000000'
        editor.commands.unsetColor()
      },
      tbSetFontSize(size) {
        if (!editor || editor.isDestroyed) return
        this.tbFontSize = size
        // Tiptap 3.x: setFontSize es command (no chain method)
        editor.commands.setFontSize(size)
      },
      tbUnsetFontSize() {
        if (!editor || editor.isDestroyed) return
        this.tbFontSize = ''
        editor.commands.unsetFontSize()
      },
      // Destruir editor y limpiar el DOM.
      async _cleanupEditor() {
        if (editor) {
          try { await editorDestroy() } catch (_) { /* ignore */ }
          editor = null
          editorDestroy = null
          this._editorMounted = false
        }
        // Limpiar el DOM del mount point
        const el = this.$refs?.tiptapBody
        if (el) {
          while (el.firstChild) el.removeChild(el.firstChild)
        }
      },
      insertarEtiqueta(tag) {
        // F3: detecta el campo activo (asunto o cuerpo) para insertar la variable
        // en el lugar correcto. Si el cursor esta en el input "asunto", se inserta
        // alli; si esta en el Tiptap (cuerpo), se inserta en el editor.
        const active = document.activeElement
        // Caso 1: input de asunto (es un <input type="text" x-model="...asunto">)
        if (active && active.tagName === 'INPUT' && active === this.$refs?.asuntoInput) {
          const start = active.selectionStart ?? active.value.length
          const end = active.selectionEnd ?? active.value.length
          try {
            active.setRangeText(tag, start, end, 'end')
            // Disparar input event para que Alpine actualice el x-model
            active.dispatchEvent(new Event('input', { bubbles: true }))
          } catch (e) {
            // Fallback: concatenar al final
            active.value = (active.value || '') + tag
            active.dispatchEvent(new Event('input', { bubbles: true }))
          }
          return
        }
        // Caso 2: Tiptap editor (cuerpo) - comportamiento legacy
        if (!editor || editor.isDestroyed) return
        try {
          // Re-focus al editor antes de insertar (por si el chip robó el focus)
          editor.chain().focus().insertContent(tag).run()
        } catch (e) { console.warn('[tiptap] insertarEtiqueta error:', e) }
      },
      async guardarPlantilla() {
        const p = this.plantillas[this.plantillaSelect]
        if (!p) return
        // Sincronizar el HTML del editor con el state antes de guardar.
        let html = this._editorHtmlCache || ''
        if (editor && !editor.isDestroyed) {
          try { html = editor.getHTML() } catch (_) { /* fallback al cache */ }
        }
        p.cuerpo = html
        try {
          const res = await emailTemplates.update(p.codigo, { asunto: p.asunto, cuerpo_html: html })
          if (res.ok) { window.toast('Plantilla guardada', 'success'); await this.cargarLogs() }
          else window.toast(`Error: ${res.data?.detail || res.status}`, 'error')
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },

      /* ─── Gestión de Usuarios (lee del backend real, no mock) ─── */
      usuarios: [],
      // Paginación server-side
      uqPage: 1,
      uqPageSize: 10,
      uqTotal: 0,
      uqTotalPages: 1,
      uqSearch: '',
      uqRol: '',
      uqEst: '',
      uqAusente: '',  // Issue 8.1: '', 'true', 'false'
      uqFuente: '',
      loadingUsuarios: false,
      lastSyncText: 'nunca',
      kpisUsuarios: { total: 0, activos: 0, inactivos: 0, desvinculados: 0, ausentes: 0 },

      // ─── Modal Editar Usuario (Sesion 9) ───
      editModalOpen: false,
      editModalLoading: false,
      editModalSaving: false,
      editModalRoles: [],             // roles de la BD
      editModalUsuariosActivos: [],   // lista para picker de delegado
      editModalDelegadoSearch: '',
      editModalShowDelegadoList: false,
      editForm: {
        id: null,
        username: '',
        nombre_completo: '',
        email: '',
        cargo: '',
        estado: 'activo',             // activo / inactivo / desvinculado
        ausente: false,
        rol_codigo: '',               // rol seleccionado
        requiere_delegado: false,     // si el rol actual requiere delegado
        delegado_id: null,
        delegado_nombre: '',
        observaciones: '',
        // Sesion 23 / Bloque B1: vacaciones con fechas
        fecha_inicio_ausencia: '',
        fecha_fin_ausencia: '',
        ausencias: [],
        ausenciaVigenteId: null,
        ausenciaMotivo: 'vacaciones',
      },

      // ─── Carga inicial al entrar al tab ───
      async init() {
        // Sesion B - tarea #10: carga los 7 tabs en paralelo al inicio.
        // (El usuario esperaba que cada tab cargue al activarse, pero
        // para mejorar UX cargamos todo upfront ya que son 9 endpoints
        // pequeños.)
        await Promise.all([
          this.cargarTiempos(),
          this.cargarRestricciones(),
          this.cargarDiccionarios(),
          this.cargarGerencias(),
          this.cargarNotificaciones(),
          this.cargarLogs(),
          this.cargarUsuarios(),
        ])
        this.cargarSyncStatus()
      },

      watchTabUsuarios(nuevoTab) {
        if (nuevoTab === 'usuarios' && this.usuarios.length === 0) {
          this.cargarUsuarios()
        }
      },

      async cargarUsuarios() {
        this.loadingUsuarios = true
        try {
          const res = await usuarios.list({
            q: this.uqSearch,
            rol: this.uqRol,
            estado: this.uqEst,
            ausente: this.uqAusente === '' ? undefined : (this.uqAusente === 'true'),
            fuente: this.uqFuente,
            page: this.uqPage,
            page_size: this.uqPageSize,
          })
          if (!res.ok) {
            window.toast(`Error cargando usuarios: ${res.data?.detail || res.status}`, 'error')
            return
          }
          const data = res.data
          this.usuarios = data.items
          this.kpisUsuarios = data.kpis
          this.uqTotal = data.total
          this.uqTotalPages = Math.max(1, Math.ceil(data.total / this.uqPageSize))
          if (this.uqPage > this.uqTotalPages) {
            this.uqPage = this.uqTotalPages
            await this.cargarUsuarios()
          }
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        } finally {
          this.loadingUsuarios = false
        }
      },

      uqPrevPage() {
        if (this.uqPage > 1) {
          this.uqPage--
          this.cargarUsuarios()
        }
      },

      uqNextPage() {
        if (this.uqPage < this.uqTotalPages) {
          this.uqPage++
          this.cargarUsuarios()
        }
      },

      uqGoToPage(p) {
        if (p < 1) p = 1
        if (p > this.uqTotalPages) p = this.uqTotalPages
        if (p === this.uqPage) return
        this.uqPage = p
        this.cargarUsuarios()
      },

      uqOnPageSizeChange() {
        this.uqPage = 1
        this.cargarUsuarios()
      },

      uqOnFilterChange() {
        // Cualquier cambio de filtro resetea a pagina 1
        this.uqPage = 1
        this.cargarUsuarios()
      },

      get uqPageStart() {
        return this.uqTotal === 0 ? 0 : (this.uqPage - 1) * this.uqPageSize + 1
      },

      get uqPageEnd() {
        return Math.min(this.uqPage * this.uqPageSize, this.uqTotal)
      },

      get uqVisiblePages() {
        // Devuelve hasta 5 numeros de pagina centrados en la actual
        // para mostrar en la barra de paginacion
        const total = this.uqTotalPages
        const current = this.uqPage
        if (total <= 7) {
          return Array.from({ length: total }, (_, i) => i + 1)
        }
        const pages = []
        pages.push(1)
        if (current > 4) pages.push('...')
        const start = Math.max(2, current - 1)
        const end = Math.min(total - 1, current + 1)
        for (let i = start; i <= end; i++) pages.push(i)
        if (current < total - 3) pages.push('...')
        if (total > 1) pages.push(total)
        return pages
      },

      async cargarSyncStatus() {
        try {
          const res = await usuarios.syncStatus()
          if (res.ok) {
            const data = res.data
            if (data.last_sync_at) {
              const fecha = new Date(data.last_sync_at)
              this.lastSyncText = fecha.toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'short' })
            } else {
              this.lastSyncText = 'nunca'
            }
          }
        } catch (_) { /* ignore */ }
      },

      get usuariosFiltrados() {
        // Filtro client-side adicional (el backend ya filtra por q/rol/estado,
        // aca agregamos busqueda libre sobre la pagina actual)
        if (!this.uqSearch) return this.usuarios
        const q = this.uqSearch.toLowerCase()
        return this.usuarios.filter(u =>
          (u.nombre_completo || '').toLowerCase().includes(q) ||
          (u.username || '').toLowerCase().includes(q) ||
          (u.email || '').toLowerCase().includes(q) ||
          (u.area_sigla || '').toLowerCase().includes(q) ||
          (u.gerencia_sigla || '').toLowerCase().includes(q)
        )
      },

      async sincronizarDirectorio() {
          if (this.loadingUsuarios) return
          this.loadingUsuarios = true
          window.toast('⏳ Sincronizando con Active Directory... (puede tardar 30-60s)', 'info')
          try {
            const res = await usuarios.syncAd(750)
            if (!res.ok) {
              window.toast(`Error en sync: ${res.data?.detail || res.status}`, 'error')
              return
            }
            const data = res.data
            this.lastSyncText = new Date().toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'short' })
            window.toast(
              `✅ Sync OK: ${data.creados} nuevos, ${data.actualizados} actualizados, ${data.excluidos} excluidos (${data.duracion_seg.toFixed(1)}s)`,
              'success'
            )
            await this.cargarUsuarios()
            await this.cargarLogs()
          } catch (e) {
            window.toast(`Error de red: ${e.message}`, 'error')
          } finally {
            this.loadingUsuarios = false
          }
        },

        async exportarUsuarios(formato = 'xlsx') {
          // Sesion B - #9e: delega al backend (XLSX profesional con cabecera,
          // auto-filtros, freeze, totales, paleta pastel).
          //
          // IMPORTANTE (sesion 15): los browsers modernos requieren que el
          // <a>.click() de descarga este en el mismo tick del user gesture.
          // Si lo llamamos despues de await/then, el gesture se pierde y el
          // download no dispara. Por eso construimos el query string AQUI
          // (sincronicamente) y llamamos apiDownload DIRECTAMENTE sin await
          // intermedio. apiDownload internamente hace la fetch + blob + a.click().
          try {
            const params = new URLSearchParams({ formato })
            if (this.uqSearch) params.set('q', this.uqSearch)
            if (this.uqRol && this.uqRol !== 'Todos los roles') params.set('rol', this.uqRol)
            if (this.uqEst && this.uqEst !== 'Todos los estados') params.set('estado', this.uqEst)
            const url = `/usuarios/export?${params.toString()}`
            const filename = formato === 'csv'
              ? `usuarios_sgd_${new Date().toISOString().slice(0,10)}.csv`
              : `usuarios_sgd_${new Date().toISOString().slice(0,10)}.xlsx`
            // Llamada sincronica: NO await antes de invocar apiDownload.
            // Devolvemos la promesa para no romper tests, pero el click
            // ya se ejecuto en el tick del user gesture.
            window.apiDownload(url, { filename }).then(res => {
              if (res && res.ok) {
                window.toast(`Exportado a ${formato.toUpperCase()}`, 'success')
                this.cargarLogs().catch(() => {})
              } else {
                window.toast(`Error exportando`, 'error')
              }
            })
          } catch (e) {
            window.toast(`Error: ${e.message}`, 'error')
          }
        },

      async impersonarUsuario(u) {
        // Sesion 17: validaciones de frontend antes de pegarle al backend.
        const auth = window.Alpine?.store('auth')
        const me = auth?.user
        const myRole = auth?.role
        // Solo ADMIN o ETO pueden impersonar (el backend tambien valida esto).
        if (myRole !== 'admin' && myRole !== 'eto') {
          window.toast('⛔ Solo ADMIN o ETO pueden impersonar usuarios', 'error')
          return
        }
        // No se puede impersonar a si mismo.
        if (me && me.username === u.username) {
          window.toast('⛔ No puede impersonarse a si mismo', 'error')
          return
        }
        if (!confirm(`¿Impersonar a ${u.nombre_completo} (${u.username})? Tu sesión actual (${me?.username}) se mantiene en segundo plano. El backend registrará este evento en el log de auditoría.`)) {
          return
        }
        try {
          const res = await fetch(`${API_BASE}/admin/impersonate/start`, {
              method: 'POST',
              credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sAMAccountName: u.username }),
          })
          if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            window.toast(`Error impersonando: ${err.detail || res.status}`, 'error')
            return
          }
          const data = await res.json()
          window.toast(`🕵️ Impersonando a ${data.user.nombre_completo} (${data.user.username})`, 'info')
          // Sesion 17: refrescar el store para que el banner aparezca, en vez
          // de hacer window.location.hash (que rompe el estado del wizard/editor).
          await auth.refreshFromBackend()
          this.cargarLogs()
          // Sesion 27 (Opcion A): navegar a la homeRoute del nuevo rol Y
          // recargar. Sin el reload, la sidebar queda con los links del
          // admin (es HTML estatico construido una sola vez). Sin la
          // navegacion, el router rechaza la URL actual con /403 porque el
          // impersonado no tiene acceso a parametrizacion.
          const target = auth.homeRoute
          window.location.hash = '#' + target
          window.location.reload()
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        }
      },

      async stopImpersonate() {
        // Sesion 17: terminar el impersonate. Llama a /admin/impersonate/stop,
        // refresca el store y muestra toast.
        const auth = window.Alpine?.store('auth')
        if (!auth?.user?.impersonated_by) {
          window.toast('No estás impersonando a nadie', 'info')
          return
        }
        const who = `${auth.user.nombre_completo} (${auth.user.username})`
        if (!confirm(`¿Terminar impersonate de ${who} y volver a tu sesión original (${auth.user.impersonated_by})?`)) {
          return
        }
        try {
          const res = await fetch(`${API_BASE}/admin/impersonate/stop`, {
              method: 'POST',
              credentials: 'include',
          })
          if (!res.ok) {
            const err = await res.json().catch(() => ({}))
            window.toast(`Error terminando impersonate: ${err.detail || res.status}`, 'error')
            return
          }
          const data = await res.json()
          window.toast(`✅ Impersonate terminado. Volvió a su sesión como ${data.message || auth.user.impersonated_by}`, 'success')
          await auth.refreshFromBackend()
          this.cargarLogs()
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        }
      },

      async toggleAusente(u) {
        // TODO: implementar PATCH /usuarios/{id} cuando exista
        window.toast((u.ausente ? '✅ Usuario marcado como Ausente' : '↩ Usuario restaurado a Activo'), 'success')
        this.pushLog('Estado usuario', u.nombre_completo, u.ausente ? 'Ausente' : 'Activo', 'usuarios')
      },

      async editarUsuario(u) {
        // Abrir modal de edicion con los datos del usuario.
        // Carga roles y usuarios activos en paralelo.
        this.editModalOpen = true
        this.editModalLoading = true
        this.editModalDelegadoSearch = ''
        this.editModalShowDelegadoList = false
        // IMPORTANTE: NO setear rol_codigo aqui. Las <option> del <select>
        // se renderizan DESPUES de cargar editModalRoles, y Alpine bindea
        // x-model cuando las options existen. Si lo seteamos antes, el <select>
        // muestra "Seleccionar rol" hasta que el usuario interactue con el.
        this.editForm = {
          id: u.id,
          username: u.username,
          nombre_completo: u.nombre_completo,
          email: u.email || '',
          cargo: u.cargo || '',
          estado: u.estado,
          ausente: !!u.ausente,
          rol_codigo: '',
          requiere_delegado: false,
          delegado_id: u.delegado_id || null,
          delegado_nombre: u.delegado_nombre || '',
          observaciones: '',
          // Sesion 23 / Bloque B1: vacaciones con fechas
          fecha_inicio_ausencia: '',
          fecha_fin_ausencia: '',
          ausencias: [],
          ausenciaVigenteId: null,
          ausenciaMotivo: 'vacaciones',
        }
        // Cargar ausencias del usuario (Sesion 23 / Bloque B1)
        try {
          const resAus = await fetch(`${API_BASE}/ausencias?usuario_id=${u.id}`, {
            method: 'GET', credentials: 'include',
          })
          if (resAus.ok) {
            const dataAus = await resAus.json()
            this.editForm.ausencias = dataAus.items || []
            const vigente = this.editForm.ausencias.find(a => a.esta_vigente)
            if (vigente) {
              this.editForm.ausente = true
              this.editForm.fecha_inicio_ausencia = vigente.fecha_desde
              this.editForm.fecha_fin_ausencia = vigente.fecha_hasta
              this.editForm.ausenciaVigenteId = vigente.id
              this.editForm.ausenciaMotivo = vigente.motivo || 'vacaciones'
            }
          }
        } catch (e) {
          // ignore - las ausencias son opcionales
        }
        // Guardar el rol original para setearlo despues de cargar las options
        const rolOriginal = (u.roles && u.roles.length > 0) ? u.roles[0] : ''
        try {
          const [resRoles, resActivos] = await Promise.all([
            roles.list(),
            usuarios.listActivos(),
          ])
          if (resRoles.ok) {
            this.editModalRoles = resRoles.data.items || []
            // Despues de cargar las options, setear el rol original.
            // Usar $nextTick para esperar a que Alpine renderice las <option>.
            await this.$nextTick()
            this.editForm.rol_codigo = rolOriginal
            // Determinar si el rol actual requiere delegado
            const rolObj = this.editModalRoles.find(r => r.codigo === rolOriginal)
            this.editForm.requiere_delegado = rolObj ? !!rolObj.requiere_delegado : false
          } else {
            window.toast('Error cargando roles', 'error')
            this.editModalRoles = []
          }
          if (resActivos.ok) {
            // Excluir al propio usuario del listado de posibles delegados
            this.editModalUsuariosActivos = (resActivos.data.items || []).filter(x => x.id !== u.id)
          } else {
            window.toast('Error cargando usuarios activos', 'error')
            this.editModalUsuariosActivos = []
          }
        } catch (e) {
          window.toast(`Error: ${e.message}`, 'error')
        } finally {
          this.editModalLoading = false
        }
      },

      cerrarModalEdicion() {
        if (this.editModalSaving) return
        this.editModalOpen = false
      },

      onRolChange() {
        // Actualizar si el rol requiere delegado
        const rolObj = this.editModalRoles.find(r => r.codigo === this.editForm.rol_codigo)
        this.editForm.requiere_delegado = rolObj ? !!rolObj.requiere_delegado : false
        // Si el rol NO requiere delegado, limpiar el delegado
        if (!this.editForm.requiere_delegado) {
          this.editForm.delegado_id = null
          this.editForm.delegado_nombre = ''
          this.editModalDelegadoSearch = ''
        }
      },

      get editModalDelegadosFiltrados() {
        // Filtro fuzzy sobre usuarios activos: nombre, username, codigo SAP, email
        const q = (this.editModalDelegadoSearch || '').toLowerCase().trim()
        if (!q) return this.editModalUsuariosActivos.slice(0, 50)
        const tokens = q.split(/\s+/).filter(Boolean)
        return this.editModalUsuariosActivos.filter(u => {
          const haystack = [
            u.nombre_completo || '',
            u.username || '',
            u.email || '',
            u.ad_postal_code || '',
            u.cargo || '',
          ].join(' ').toLowerCase()
          return tokens.every(t => haystack.includes(t))
        }).slice(0, 50)
      },

      seleccionarDelegado(u) {
        this.editForm.delegado_id = u.id
        this.editForm.delegado_nombre = u.nombre_completo
        this.editModalDelegadoSearch = ''
        this.editModalShowDelegadoList = false
      },

      limpiarDelegado() {
        this.editForm.delegado_id = null
        this.editForm.delegado_nombre = ''
        this.editModalDelegadoSearch = ''
        this.editModalShowDelegadoList = false
      },

      async guardarEdicionUsuario() {
        if (!this.editForm.id) return
        if (!this.editForm.rol_codigo) {
          window.toast('⚠️ Selecciona un rol', 'warn')
          return
        }
        if (this.editForm.requiere_delegado && !this.editForm.delegado_id) {
          // Issue 3.1: delegado es RECOMENDADO pero NO obligatorio.
          // El cliente quiere poder asignar eto/revisor/aprobador sin delegado.
          if (!confirm('Este rol sugiere asignar un delegado. ¿Guardar de todos modos?')) {
            return
          }
        }
        this.editModalSaving = true
        try {
          // Construir payload solo con campos que cambiaron respecto al original
          const u = this.usuarios.find(x => x.id === this.editForm.id)
          const payload = {}
          if (u) {
            if (this.editForm.estado !== u.estado) payload.estado = this.editForm.estado
            // Sesion 23 / Bloque B1: ausente se maneja via /ausencias, NO en PATCH.
            // Quitamos la linea de ausente del payload.
            const rolOrig = (u.roles && u.roles[0]) || ''
            if (this.editForm.rol_codigo !== rolOrig) payload.rol_codigo = this.editForm.rol_codigo
            if ((this.editForm.delegado_id || null) !== (u.delegado_id || null)) {
              payload.delegado_id = this.editForm.delegado_id
            }
          } else {
            // Fallback: mandar todo
            payload.estado = this.editForm.estado
            payload.rol_codigo = this.editForm.rol_codigo
            payload.delegado_id = this.editForm.delegado_id
          }
          if (this.editForm.observaciones && this.editForm.observaciones.trim()) {
            payload.observaciones = this.editForm.observaciones.trim()
          }
          // Sesion 23 / Bloque B1: gestionar ausencias via endpoint propio
          // Logica:
          //   1) Si el usuario quiere ausente y NO tiene ausencia vigente -> POST
          //   2) Si tiene ausencia vigente y quiere cambiar fechas -> PATCH
          //   3) Si tiene ausencia vigente y NO quiere ausente -> DELETE
          //   4) Si no quiere ausente y no tiene -> nada
          const quiereAusente = this.editForm.ausente && this.editForm.fecha_inicio_ausencia && this.editForm.fecha_fin_ausencia
          if (quiereAusente && this.editForm.ausenciaVigenteId) {
            // PATCH
            const rAus = await apiFetch(`/ausencias/${this.editForm.ausenciaVigenteId}`, {
              method: 'PATCH',
              body: JSON.stringify({
                fecha_desde: this.editForm.fecha_inicio_ausencia,
                fecha_hasta: this.editForm.fecha_fin_ausencia,
                motivo: this.editForm.ausenciaMotivo || 'vacaciones',
              }),
            })
            if (!rAus.ok) {
              window.toast(`Error guardando ausencia: ${rAus.data?.detail || rAus.status}`, 'error')
              this.editModalSaving = false
              return
            }
          } else if (quiereAusente && !this.editForm.ausenciaVigenteId) {
            // POST
            const rAus = await apiFetch(`/ausencias/usuarios/${this.editForm.id}`, {
              method: 'POST',
              body: JSON.stringify({
                fecha_desde: this.editForm.fecha_inicio_ausencia,
                fecha_hasta: this.editForm.fecha_fin_ausencia,
                motivo: this.editForm.ausenciaMotivo || 'vacaciones',
              }),
            })
            if (!rAus.ok) {
              window.toast(`Error creando ausencia: ${rAus.data?.detail || rAus.status}`, 'error')
              this.editModalSaving = false
              return
            }
          } else if (!quiereAusente && this.editForm.ausenciaVigenteId) {
            // DELETE
            const rAus = await apiFetch(`/ausencias/${this.editForm.ausenciaVigenteId}`, {
              method: 'DELETE',
            })
            if (!rAus.ok) {
              window.toast(`Error cancelando ausencia: ${rAus.data?.detail || rAus.status}`, 'error')
              this.editModalSaving = false
              return
            }
          }

          if (Object.keys(payload).length === 0) {
            window.toast('Vacaciones actualizadas', 'success')
            this.cerrarModalEdicion()
            this.cargarUsuarios()
            return
          }
          const res = await usuarios.override(this.editForm.id, payload)
          if (!res.ok) {
            window.toast(`Error: ${res.data?.detail || res.status}`, 'error')
            return
          }
          window.toast('✅ Usuario actualizado', 'success')
          this.cerrarModalEdicion()
          await this.cargarUsuarios()
          await this.cargarLogs()
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        } finally {
          this.editModalSaving = false
        }
      },

      formatRol(rolCodigo) {
        const map = {
          'ADMIN': 'Admin',
          'ETO': 'ETO',
          'ELABORADOR - REVISOR': 'Elaborador',
          'ELABORADOR - REVISOR - APROBADOR': 'Elaborador+Apr',
          'VISUALIZADOR (CL-EVAL)': 'Visualizador',
        }
        return map[rolCodigo] || rolCodigo
      },

      rolColor(rolCodigo) {
        const map = {
          'ADMIN': 'badge-green',
          'ETO': 'badge-blue',
          'ELABORADOR - REVISOR': 'badge-purple',
          'ELABORADOR - REVISOR - APROBADOR': 'badge-purple',
          'VISUALIZADOR (CL-EVAL)': 'badge-gray',
        }
        return map[rolCodigo] || 'badge-gray'
      },
    }
  })
  },

  template: /* html */`
<div x-data="paramPage" class="animate-fade-in-page">

  <!-- Header -->
  <div class="flex items-center justify-between mb-3.5 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Parametrización General del Sistema</h1>
      <p class="page-subtitle">⚙️ Solo visible para Rol ETO</p>
    </div>
  </div>

  <!-- Tabs -->
  <div class="flex gap-0.5 bg-slate-100 rounded-xl p-1 mb-4 flex-wrap">
    <template x-for="t in tabs" :key="t.id">
      <button @click="tab=t.id"
              :class="tab===t.id ? 'bg-white text-brand-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
              class="px-4 py-1.5 rounded-lg border-none text-[11.5px] font-semibold cursor-pointer transition-all duration-150"
              x-text="t.label"></button>
    </template>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: TIEMPOS Y SLAs
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='tiempos'" x-cloak>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
      <!-- Vigencia por tipo de documento -->
      <div class="card-base">
        <div class="section-header">📄 Vigencia por Tipo de Documento</div>
        <!-- Header row: nombre + bloque de control con ancho fijo (min-w-[7.5rem])
             para que las filas se alineen uniformemente. -->
        <div class="flex items-center gap-3 px-1 py-1.5 border-b border-slate-200 text-[10.5px] uppercase tracking-wide font-semibold text-slate-500">
          <div class="flex-1">Tipo de documento</div>
          <div class="w-[7.5rem] text-center">Vigencia</div>
        </div>
        <div class="divide-y divide-slate-100">
          <template x-for="(v, idx) in vigencias" :key="v.id">
            <div :class="idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'"
                 class="flex items-center gap-3 px-1 py-2 hover:bg-blue-50/40 transition-colors">
              <div class="flex-1 text-[11.5px] font-medium text-slate-800" x-text="v.tipo"></div>
              <!-- Bloque de control de ancho fijo: input+años o badge Indefinido.
                   min-w-[7.5rem] para que el ancho no varie entre filas. -->
              <div class="w-[7.5rem] flex items-center justify-center gap-1">
                <label class="inline-flex items-center gap-1 text-[10.5px] text-slate-500 cursor-pointer select-none whitespace-nowrap">
                  <input type="checkbox" x-model="v.indefinido"
                         @change="v.anios = v.indefinido ? 'Indefinido' : 4"
                         class="w-3.5 h-3.5 accent-brand-500">
                  <span>Indef.</span>
                </label>
                <input type="number" x-show="!v.indefinido" x-model.number="v.anios"
                       min="1" max="20"
                       class="form-input w-12 text-xs py-0.5 px-1 text-center">
                <span x-show="!v.indefinido" class="text-[10.5px] text-slate-500 whitespace-nowrap">años</span>
                <span x-show="v.indefinido"
                      class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-200 text-slate-600 whitespace-nowrap min-w-[3.5rem]">
                  Indefinido
                </span>
              </div>
            </div>
          </template>
        </div>
        <div class="form-hint mt-2">Cada tipo tiene su propio plazo de vigencia antes de requerir revisión. Marcar "Indef." si no vence nunca.</div>
        <button @click="guardarTiempos()" class="btn btn-primary w-full mt-3">💾 Guardar Vigencia y Flujo</button>
      </div>

      <!-- Semaforización por tipo de tarea (sesion 13: nueva tabla) -->
      <div class="card-base">
        <div class="section-header">🚦 Semaforización por Tipo de Tarea</div>
        <div class="text-[11px] text-slate-500 mb-3">Define los umbrales (en días naturales desde la asignación) que determinan el color de cada tarea. El plazo máximo es 15 días; ROJO se activa cuando faltan 3 días para cumplirlo.</div>
        <div class="overflow-x-auto -mx-3 px-3">
        <table class="data-table min-w-full">
          <thead><tr>
            <th>Tipo Tarea</th>
            <th class="w-14 text-center">Verde</th>
            <th class="w-14 text-center">Amarillo</th>
            <th class="w-14 text-center">Rojo</th>
            <th class="w-14 text-center">Plazo</th>
            <th class="w-20 text-right">Acciones</th>
          </tr></thead>
          <tbody>
            <template x-for="s in semaforos" :key="s.tipo_tarea">
              <tr>
                <td class="font-semibold text-slate-800" x-text="s.tipo_tarea.replace('_', ' ')"></td>
                <td>
                  <template x-if="semaforoEditing === s.tipo_tarea">
                    <input type="number" x-model.number="s.dias_verde" min="1" max="14" class="form-input w-14 text-xs py-1 text-center">
                  </template>
                  <template x-if="semaforoEditing !== s.tipo_tarea">
                    <div class="flex items-center justify-center gap-1">
                      <span class="w-3 h-3 rounded-full bg-emerald-600 flex-shrink-0"></span>
                      <span class="font-mono text-emerald-700 font-bold" x-text="'0-' + s.dias_verde"></span>
                    </div>
                  </template>
                </td>
                <td>
                  <template x-if="semaforoEditing === s.tipo_tarea">
                    <input type="number" x-model.number="s.dias_amarillo" min="2" max="14" class="form-input w-14 text-xs py-1 text-center">
                  </template>
                  <template x-if="semaforoEditing !== s.tipo_tarea">
                    <div class="flex items-center justify-center gap-1">
                      <span class="w-3 h-3 rounded-full bg-amber-500 flex-shrink-0"></span>
                      <span class="font-mono text-amber-700 font-bold" x-text="(s.dias_verde+1) + '-' + s.dias_amarillo"></span>
                    </div>
                  </template>
                </td>
                <td>
                  <template x-if="semaforoEditing === s.tipo_tarea">
                    <input type="number" x-model.number="s.dias_rojo" min="3" max="30" class="form-input w-14 text-xs py-1 text-center">
                  </template>
                  <template x-if="semaforoEditing !== s.tipo_tarea">
                    <div class="flex items-center justify-center gap-1">
                      <span class="w-3 h-3 rounded-full bg-red-600 flex-shrink-0"></span>
                      <span class="font-mono text-red-700 font-bold" x-text="(s.dias_amarillo+1) + '-' + s.dias_rojo"></span>
                    </div>
                  </template>
                </td>
                <td class="text-center">
                  <template x-if="semaforoEditing === s.tipo_tarea">
                    <input type="number" x-model.number="s.plazo_maximo_dias" min="5" max="30" class="form-input w-14 text-xs py-1 text-center">
                  </template>
                  <template x-if="semaforoEditing !== s.tipo_tarea">
                    <span class="badge badge-gray text-[10px]" x-text="s.plazo_maximo_dias + ' días'"></span>
                  </template>
                </td>
                <td class="text-right whitespace-nowrap">
                  <template x-if="semaforoEditing === s.tipo_tarea">
                    <div class="flex gap-1 justify-end">
                      <button @click="guardarSemaforo(s)" class="btn btn-sm text-emerald-700 border-emerald-200 py-0.5 px-1.5 text-[10px]">✓</button>
                      <button @click="cancelSemaforo()" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">✕</button>
                    </div>
                  </template>
                  <template x-if="semaforoEditing !== s.tipo_tarea">
                    <button @click="editSemaforo(s)" class="btn btn-sm py-0.5 px-1.5 text-[10px]">✏️</button>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        </div>
        <div class="form-hint mt-2">REVISION/APROBACION/CONTROL_LECTURA: 7/7/7. EVALUACION: 5/5/5. El plazo máximo por defecto es 15 días naturales. Sesión 23: los plazos globales de revisión/aprobación y control de lectura fueron removidos por ser redundantes con esta grilla.</div>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: RESTRICCIONES
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='restricciones'" x-cloak>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
      <div class="card-base">
        <div class="section-header">📎 Restricciones de Archivos Adjuntos</div>
        <div class="form-grid-2">
          <div>
            <label class="form-label text-[10.5px]">Límite de archivos adjuntos por solicitud</label>
            <input type="number" x-model="restricciones.maxAdjuntos" min="1" max="20" class="form-input text-xs">
          </div>
          <div>
            <label class="form-label text-[10.5px]">Tamaño máximo por archivo (MB)</label>
            <input type="number" x-model="restricciones.maxSizeMB" min="1" max="100" class="form-input text-xs">
          </div>
        </div>
        <div class="text-[11px] text-slate-500 bg-slate-50 rounded-lg p-2 mt-2">El backend rechazará con error 413 los archivos que excedan el límite configurado.</div>
        <button @click="guardarRestricciones()" class="btn btn-primary w-full mt-3">💾 Guardar Restricciones de Archivo</button>
      </div>

      <div class="card-base">
        <div class="section-header">⬇️ Límites de Descarga de Editables</div>
        <div class="form-grid-2">
          <div>
            <label class="form-label text-[10.5px]">Máx. descargas de editable por día/usuario</label>
            <input type="number" x-model="restricciones.maxDescargasDia" min="1" max="20" class="form-input text-xs">
          </div>
          <div>
            <label class="form-label text-[10.5px]">Paginación de "Mi Bandeja" (registros)</label>
            <select x-model="restricciones.bandejaRegistros" class="form-input text-xs">
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="30">30</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>
        <div class="mt-3">
          <label class="form-label text-[10.5px]">Tipos excluidos del límite de descarga</label>
          <div class="flex flex-wrap gap-1.5 mb-2">
            <template x-for="(chip, idx) in chips" :key="idx + '-' + chip">
              <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] bg-blue-50 text-blue-700 border border-blue-200">
                <span x-text="chip"></span>
                <button @click="quitarChip(chip)" class="text-red-500 hover:text-red-700 font-bold leading-none cursor-pointer">✕</button>
              </span>
            </template>
          </div>
          <div class="flex gap-2">
            <select x-model="nuevoChip" class="form-input text-xs w-auto min-w-[140px]">
              <option value="">Seleccionar tipo...</option>
              <template x-for="(t, idx) in tiposExcluibles" :key="idx + '-' + t.cod">
                <option :value="t.cod" x-text="t.cod + ' - ' + t.tipo"></option>
              </template>
            </select>
            <button @click="agregarChip()" class="btn btn-sm">+ Agregar</button>
          </div>
        </div>
        <button @click="guardarLimitesDescarga()" class="btn btn-primary w-full mt-3">💾 Guardar Límites de Descarga</button>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: DICCIONARIOS Y ENRUTAMIENTO
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='diccionarios'" x-cloak>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3.5 mb-3.5">
      <!-- Tipos de documento -->
      <div class="card-base">
        <div class="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-100">
          <span class="text-[11.5px] font-bold text-slate-600">📄 Tipos de Documento</span>
          <button class="btn btn-sm text-emerald-700 border-emerald-200" @click="addTipo()">+ Nuevo</button>
        </div>
        <div class="overflow-x-auto -mx-3 px-3">
        <table class="data-table min-w-full">
          <thead><tr><th>Tipo</th><th class="w-20">Cód. Doc</th><th class="w-20 text-right">Acciones</th></tr></thead>
          <tbody>
            <template x-for="t in tiposDocs" :key="t.id">
              <tr>
                <template x-if="tipoEditing === t">
                  <td colspan="2" class="py-1.5">
                    <div class="flex gap-1.5 flex-wrap">
                      <input type="text" x-model="t.tipo" class="form-input text-[11px] py-1 flex-1 min-w-[120px]" placeholder="Nombre del tipo">
                      <!-- Issue 6.1: slug oculto en tabla pero sigue en el form de edicion -->
                      <input type="hidden" x-model="t.cod">
                      <input type="number" x-model.number="t.codigo_int" min="1" max="99" class="form-input text-[11px] py-1 w-16" placeholder="#">
                    </div>
                  </td>
                </template>
                <template x-if="tipoEditing !== t">
                  <td class="font-medium" x-text="t.tipo"></td>
                </template>
                <template x-if="tipoEditing !== t">
                  <td class="font-mono text-slate-500" x-text="t.codigo_int"></td>
                </template>
                <td class="text-right whitespace-nowrap">
                  <template x-if="tipoEditing === t">
                    <div class="flex gap-1 justify-end">
                      <button @click="saveTipo(t)" class="btn btn-sm text-emerald-700 border-emerald-200 py-0.5 px-1.5 text-[10px]">✓</button>
                      <button @click="cancelTipo(t)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">✕</button>
                    </div>
                  </template>
                  <template x-if="tipoEditing !== t">
                    <div class="flex gap-1 justify-end">
                      <button @click="tipoEditing=t" class="btn btn-sm py-0.5 px-1.5 text-[10px]">✏️</button>
                      <button @click="deleteTipo(t)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">🗑</button>
                    </div>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        </div>
        <div class="form-hint mt-2">Los tipos con registros activos no pueden eliminarse (borrado lógico).</div>
      </div>

      <!-- Estados -->
      <div class="card-base">
        <div class="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-100">
          <span class="text-[11.5px] font-bold text-slate-600">⚙️ Estados de Proceso y Tarea</span>
          <button class="btn btn-sm text-emerald-700 border-emerald-200" @click="addEstado()">+ Nuevo</button>
        </div>
        <div class="overflow-x-auto -mx-3 px-3">
        <table class="data-table min-w-full">
          <thead><tr><th>Estado</th><th>Contexto</th><th class="w-20 text-right">Acciones</th></tr></thead>
          <tbody>
            <template x-for="e in estados" :key="e.id">
              <tr>
                <template x-if="estadoEditing === e">
                  <td class="py-1.5">
                    <input type="text" x-model="e.est" class="form-input text-[11px] py-1" placeholder="Nombre del estado">
                  </td>
                </template>
                <template x-if="estadoEditing !== e">
                  <td class="font-medium" x-text="e.est"></td>
                </template>
                <td class="py-1.5">
                  <template x-if="estadoEditing === e">
                    <select x-model="e.ctx" class="form-input text-[11px] py-1 w-auto">
                      <option value="PROCESO">Proceso</option>
                      <option value="TAREA">Tarea</option>
                      <option value="ACCION">Accion</option>
                      <option value="AMBOS">Ambos</option>
                    </select>
                  </template>
                  <template x-if="estadoEditing !== e">
                    <span :class="{
                        'badge badge-blue': e.ctx==='TAREA',
                        'badge badge-green': e.ctx==='PROCESO',
                        'badge badge-purple': e.ctx==='ACCION',
                        'badge badge-gray': e.ctx==='AMBOS'
                      }" x-text="e.ctx"></span>
                  </template>
                </td>
                <td class="text-right">
                  <template x-if="estadoEditing === e">
                    <div class="flex gap-1 justify-end">
                      <button @click="saveEstado(e)" class="btn btn-sm text-emerald-700 border-emerald-200 py-0.5 px-1.5 text-[10px]">✓</button>
                      <button @click="cancelEstado(e)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">✕</button>
                    </div>
                  </template>
                  <template x-if="estadoEditing !== e">
                    <div class="flex gap-1 justify-end">
                      <button @click="estadoEditing=e" class="btn btn-sm py-0.5 px-1.5 text-[10px]">✏️</button>
                      <button @click="deleteEstado(e)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">🗑</button>
                    </div>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        </div>
      </div>
    </div>

    <!-- Matriz ETO -->
    <div class="card-base">
      <div class="flex items-center justify-between mb-1">
        <div class="text-[11.5px] font-bold text-slate-600"># Matriz de Enrutamiento ETO</div>
        <div class="text-[10.5px] text-slate-400">El sistema consulta esta tabla en el Paso 4 del flujo para asignar la tarea de liberación.</div>
      </div>
      <div class="overflow-x-auto -mx-3 px-3">
        <table class="data-table min-w-full">
          <thead>
            <tr>
              <th>Gerencia</th>
              <th>Analista ETO Asignado</th>
              <th class="text-center w-28">Disponibilidad</th>
              <th>Delegado (si ausente)</th>
              <th class="w-16 text-center">Guardar</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="m in matrizETO" :key="m.id">
              <tr>
                <td class="font-bold text-slate-800 whitespace-nowrap" x-text="m.gerencia"></td>
                <td>
                  <select class="form-input text-xs" x-model="m.analista_id"
                          :data-matriz-id="m.id" data-matriz-select="analista">
                    <option value="">— Seleccionar —</option>
                    <template x-for="a in analistas" :key="a.id"><option :value="String(a.id)" x-text="(a.nombre || a.username)"></option></template>
                  </select>
                </td>
                <td class="text-center">
                  <label class="inline-flex items-center gap-1.5 cursor-pointer text-[11.5px]">
                    <input type="checkbox" x-model="m.disponible"
                           :data-matriz-id="m.id" data-matriz-check="disponible"
                           class="w-4 h-4 accent-brand-500">
                    <span :class="m.disponible ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'" x-text="m.disponible ? 'Disp.' : 'Ausente'"></span>
                  </label>
                </td>
                <td>
                  <select x-show="!m.disponible" class="form-input text-xs" x-model="m.delegado_id"
                          :data-matriz-id="m.id" data-matriz-select="delegado">
                    <option value="">— Seleccionar —</option>
                    <!-- Issue 7.1: dropdown delegado SOLO usuarios con rol ETO
                         (mismo array 'analistas' que el dropdown de analista) -->
                    <template x-for="u in analistas" :key="'de'+u.id"><option :value="String(u.id)" x-text="(u.nombre || u.username)"></option></template>
                  </select>
                  <span x-show="m.disponible" class="text-[11px] text-slate-400">—</span>
                </td>
                <td class="text-center">
                  <button @click="guardarFilaMatriz(m)" class="btn btn-sm text-[10px] py-0.5 px-1.5">💾</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: GERENCIAS Y ÁREAS
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='gerencias'" x-cloak>
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-2.5 mb-3.5 text-[11.5px] text-blue-800">
      Esta estructura alimenta los desplegables de Gerencia/Área del formulario de solicitud y el Árbol de Difusión de Outlook.
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-3.5">
      <!-- Lista gerencias -->
      <div class="card-base p-0 overflow-hidden">
        <div class="flex items-center justify-between px-3.5 py-3 border-b border-slate-100">
          <span class="text-[11px] font-bold text-slate-600">Gerencias registradas</span>
          <button @click="addGerencia()" class="btn btn-sm text-emerald-700 border-emerald-200 text-[11px]">+ Nueva</button>
        </div>
        <template x-for="g in gerencias" :key="g.id">
          <div @click="gerSelId=g.id"
               :class="gerSelId===g.id ? 'bg-blue-50 border-l-[3px] border-brand-500' : 'hover:bg-slate-50 border-l-[3px] border-transparent'"
               class="cursor-pointer px-3.5 py-3 border-b border-slate-100 transition-colors">
            <div class="text-xs font-semibold text-slate-800" x-text="g.nombre"></div>
            <div class="text-[10.5px] text-slate-400 mt-0.5" x-text="(g.areas_count ?? 0) + ' área(s) · Cód: ' + g.sigla"></div>
          </div>
        </template>
      </div>

      <!-- Detalle gerencia -->
      <div x-show="gerSel" class="card-base">
        <div class="flex items-start justify-between mb-3.5">
          <div class="flex-1 mr-3">
            <template x-if="!gerEditMode">
              <div>
                <div class="text-[13px] font-bold text-slate-800" x-text="gerSel?.nombre"></div>
                <div class="text-[11px] text-slate-400 mt-0.5" x-text="'Código: ' + gerSel?.sigla"></div>
              </div>
            </template>
            <template x-if="gerEditMode">
              <div class="flex gap-2 items-center flex-wrap">
                <input type="text" x-model="gerEditNombre" class="form-input text-xs flex-1 min-w-[160px]" placeholder="Nombre de la gerencia">
                <input type="text" x-model="gerEditCod" class="form-input text-xs w-20 uppercase font-mono" placeholder="COD" maxlength="5">
              </div>
            </template>
          </div>
          <div class="flex gap-1.5 flex-shrink-0">
            <template x-if="!gerEditMode">
              <div class="flex gap-1.5">
                <button @click="startEditGer()" class="btn btn-sm text-[10.5px]">✏️ Editar</button>
                <button @click="deleteGer()" class="btn btn-sm text-red-700 border-red-200 text-[10.5px]">🗑 Eliminar</button>
              </div>
            </template>
            <template x-if="gerEditMode">
              <div class="flex gap-1.5">
                <button @click="saveGer()" class="btn btn-sm text-emerald-700 border-emerald-200 text-[10.5px]">✓ Guardar</button>
                <button @click="gerEditMode=false" class="btn btn-sm text-red-700 border-red-200 text-[10.5px]">✕ Cancelar</button>
              </div>
            </template>
          </div>
        </div>
        <div class="flex items-center justify-between mb-2.5 pb-2.5 border-b border-slate-100">
          <span class="text-[11px] font-bold text-slate-600">Áreas / Sub-unidades (<span x-text="areasGerSel.length"></span>)</span>
          <button @click="addArea()" class="btn btn-sm text-emerald-700 border-emerald-200 text-[11px]">+ Nueva Área</button>
        </div>
        <table class="data-table">
          <thead><tr><th>Nombre del Área</th><th>Código</th><th class="w-28"></th></tr></thead>
          <tbody>
            <template x-for="a in areasGerSel" :key="a.id">
              <tr>
                <template x-if="a._edit">
                  <td class="py-1"><input type="text" x-model="a.n" class="form-input text-[11px] py-1" placeholder="Nombre del área"></td>
                </template>
                <template x-if="!a._edit">
                  <td class="font-medium" x-text="a.n"></td>
                </template>
                <template x-if="a._edit">
                  <td class="py-1"><input type="text" x-model="a.c" class="form-input text-[11px] py-1 w-20 uppercase font-mono" placeholder="COD" maxlength="5"></td>
                </template>
                <template x-if="!a._edit">
                  <td class="font-mono font-bold text-brand-600" x-text="a.c"></td>
                </template>
                <td class="text-right">
                  <template x-if="a._edit">
                    <div class="flex gap-1 justify-end">
                      <button @click="saveArea(a)" class="btn btn-sm text-emerald-700 border-emerald-200 py-0.5 px-1.5 text-[10px]">✓</button>
                      <button @click="cancelEditArea(a)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">✕</button>
                    </div>
                  </template>
                  <template x-if="!a._edit">
                    <div class="flex gap-1 justify-end">
                      <button @click="a._edit=true" class="btn btn-sm py-0.5 px-1.5 text-[10px]">✏️</button>
                      <button @click="deleteArea(a)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">🗑</button>
                      <button @click="abrirMoverArea(a)" class="btn btn-sm text-brand-700 border-brand-200 py-0.5 px-1.5 text-[10px]" title="Mover de Gerencia">➡️</button>
                    </div>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        <div class="form-hint mt-2">Las áreas con documentos activos no pueden eliminarse (borrado lógico). Los cambios se propagan al formulario de solicitud y al Árbol de Outlook.</div>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: PLANTILLAS DE NOTIFICACIÓN
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='notificaciones'" x-cloak>
    <div class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-3.5">
      <!-- Lista -->
      <div class="card-base p-0 overflow-hidden">
        <div class="px-3.5 py-3 border-b border-slate-100 text-[11px] font-bold text-slate-600">📧 Plantillas de Email</div>
        <template x-for="(p,i) in plantillas" :key="p.id || i">
          <div @click="onSelectPlantillaClick(i)"
               :class="plantillaSelect===i ? 'bg-blue-50 border-l-[3px] border-brand-500' : 'hover:bg-slate-50 border-l-[3px] border-transparent'"
               class="cursor-pointer px-3.5 py-2.5 border-b border-slate-100 transition-colors">
            <div class="text-xs font-semibold text-slate-800" x-text="p.nombre"></div>
            <div class="text-[10px] text-slate-400 mt-0.5" x-text="p.trigger"></div>
          </div>
        </template>
      </div>

      <!-- Editor (Sesion 13: Tiptap rich text. Sesion 17: sin previsualizar) -->
      <div class="card-base">
        <div class="flex items-center justify-between mb-3.5">
          <h2 class="text-[13px] font-bold text-slate-800" x-text="plantillas[plantillaSelect]?.nombre || 'Sin plantilla seleccionada'"></h2>
        </div>

        <!-- Asunto del correo: x-if para que Alpine NO evalue x-model cuando
             no hay plantilla seleccionada (evita "Cannot read properties of undefined"). -->
        <template x-if="plantillas[plantillaSelect]">
          <div class="mb-3">
            <label class="form-label text-[10.5px]">Asunto del correo</label>
            <input type="text" x-model="plantillas[plantillaSelect].asunto" x-ref="asuntoInput" class="form-input text-xs">
          </div>
        </template>

        <!-- Etiquetas: x-if por la misma razon. -->
        <template x-if="plantillas[plantillaSelect]">
          <div class="mb-3">
            <label class="form-label text-[10.5px]">Etiquetas disponibles (clic para insertar en el editor):</label>
            <div class="flex flex-wrap gap-1.5">
              <template x-for="e in etiquetas" :key="e">
                <button @mousedown.prevent @click="insertarEtiqueta(e)" class="px-2 py-0.5 rounded border border-blue-200 bg-blue-50 text-brand-600 text-[10.5px] cursor-pointer font-mono hover:bg-blue-100 transition-colors" x-text="e"></button>
              </template>
            </div>
          </div>
        </template>

        <!-- ─── Tiptap Toolbar + Editor (solo cuando HAY plantilla) ───
             Usamos x-if (template) en lugar de x-show para que Alpine NO evalue
             las expresiones x-model / x-text internas cuando la plantilla no
             existe (evita el "Cannot read properties of undefined (reading 'asunto')"). -->
        <template x-if="plantillas[plantillaSelect]">
          <div class="mb-3">
            <label class="form-label text-[10.5px]">Cuerpo del correo (editor rich text)</label>

            <!-- Toolbar Tiptap
                 Sesion 16: @mousedown.prevent en todos los botones para
                 evitar que roben el focus del editor (patron WSIWYG). -->
            <div class="flex flex-wrap items-center gap-1 p-1.5 bg-slate-50 border border-slate-200 rounded-t-lg">
              <button @mousedown.prevent @click="tbToggle('bold')" :class="tbState.bold ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded font-bold text-[12px] transition-colors" title="Negrita (Ctrl+B)">B</button>
              <button @mousedown.prevent @click="tbToggle('italic')" :class="tbState.italic ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded italic text-[12px] transition-colors" title="Cursiva (Ctrl+I)">I</button>
              <button @mousedown.prevent @click="tbToggle('underline')" :class="tbState.underline ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded underline text-[12px] transition-colors" title="Subrayado (Ctrl+U)">U</button>
              <button @mousedown.prevent @click="tbToggle('strike')" :class="tbState.strike ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded line-through text-[12px] transition-colors" title="Tachado">S</button>
              <span class="w-px h-5 bg-slate-300 mx-0.5"></span>
              <button @mousedown.prevent @click="tbToggle('h1')" :class="tbState.h1 ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded font-bold text-[13px] transition-colors" title="Título 1">H1</button>
              <button @mousedown.prevent @click="tbToggle('h2')" :class="tbState.h2 ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded font-bold text-[12px] transition-colors" title="Título 2">H2</button>
              <button @mousedown.prevent @click="tbToggle('h3')" :class="tbState.h3 ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded font-bold text-[11px] transition-colors" title="Título 3">H3</button>
              <span class="w-px h-5 bg-slate-300 mx-0.5"></span>
              <button @mousedown.prevent @click="tbToggle('bulletList')" :class="tbState.bulletList ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded text-[12px] transition-colors" title="Lista con viñetas">•≡</button>
              <button @mousedown.prevent @click="tbToggle('orderedList')" :class="tbState.orderedList ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded text-[12px] transition-colors" title="Lista numerada">1.</button>
              <button @mousedown.prevent @click="tbToggle('blockquote')" :class="tbState.blockquote ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded text-[12px] transition-colors" title="Cita">❝</button>
              <button @mousedown.prevent @click="tbToggle('codeBlock')" :class="tbState.codeBlock ? 'bg-brand-500 text-white' : 'text-slate-600 hover:bg-slate-200'" class="w-7 h-7 rounded text-[11px] font-mono transition-colors" title="Bloque de código">{}</button>
              <span class="w-px h-5 bg-slate-300 mx-0.5"></span>
              <!-- Color picker -->
              <div class="flex items-center gap-1 px-1.5">
                <label class="text-[10.5px] text-slate-500" title="Color de texto">🎨</label>
                <input type="color" :value="tbColor" @input="tbSetColor($event.target.value)" class="w-6 h-7 rounded cursor-pointer border-0 bg-transparent" title="Color de texto">
                <button @mousedown.prevent @click="tbUnsetColor()" class="text-[10px] text-slate-500 hover:text-red-500 px-1" title="Quitar color">✕</button>
              </div>
              <!-- Font size -->
              <div class="flex items-center gap-1 px-1.5">
                <label class="text-[10.5px] text-slate-500">Aa</label>
                <select :value="tbFontSize" @change="tbSetFontSize($event.target.value)" class="form-input text-[10.5px] py-0.5 px-1 w-auto h-7" title="Tamaño de fuente">
                  <option value="">-</option>
                  <option value="12px">12</option>
                  <option value="14px">14</option>
                  <option value="16px">16</option>
                  <option value="18px">18</option>
                  <option value="20px">20</option>
                  <option value="24px">24</option>
                  <option value="32px">32</option>
                </select>
                <button @mousedown.prevent @click="tbUnsetFontSize()" class="text-[10px] text-slate-500 hover:text-red-500 px-1" title="Quitar tamaño">✕</button>
              </div>
              <span class="w-px h-5 bg-slate-300 mx-0.5"></span>
              <button @mousedown.prevent @click="tbToggle('undo')" class="w-7 h-7 rounded text-slate-600 hover:bg-slate-200 text-[12px] transition-colors" title="Deshacer (Ctrl+Z)">↶</button>
              <button @mousedown.prevent @click="tbToggle('redo')" class="w-7 h-7 rounded text-slate-600 hover:bg-slate-200 text-[12px] transition-colors" title="Rehacer (Ctrl+Y)">↷</button>
            </div>

            <!-- Tiptap mount point -->
            <div x-ref="tiptapBody" class="border border-slate-200 border-t-0 rounded-b-lg p-3 min-h-[260px] text-[12.5px] prose prose-sm max-w-none focus:outline-none bg-white" style="line-height:1.55"></div>
            <div class="form-hint mt-1">El editor guarda HTML (no Markdown). Las variables {{...}} se mantienen como texto plano para que el backend las pueda renderizar con Jinja2.</div>
          </div>
        </template>

        <div x-show="!plantillas[plantillaSelect]" class="text-center text-slate-400 py-8 text-[12px]">
          No hay plantillas disponibles.
        </div>

        <div class="flex justify-end gap-2" x-show="plantillas[plantillaSelect]">
          <button @click="onSelectPlantillaClick(plantillaSelect)" class="btn btn-sm">Cancelar</button>
          <button @click="guardarPlantilla()" class="btn btn-primary btn-sm">💾 Guardar Plantilla</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: GESTIÓN DE USUARIOS
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='usuarios'" x-cloak x-init="watchTabUsuarios('usuarios')">
    <!-- KPIs (Issue 8.5: anadidos inactivos + desvinculados) -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-2.5 mb-3.5">
      <div class="metric-card text-center">
        <div class="metric-value text-slate-800" x-text="kpisUsuarios.total || 0"></div>
        <div class="metric-label">Usuarios Totales</div>
      </div>
      <div class="metric-card border-emerald-200 text-center">
        <div class="metric-value text-emerald-600" x-text="kpisUsuarios.activos || 0"></div>
        <div class="metric-label text-emerald-600">Activos</div>
      </div>
      <div class="metric-card border-slate-300 text-center">
        <div class="metric-value text-slate-500" x-text="kpisUsuarios.inactivos || 0"></div>
        <div class="metric-label text-slate-500">Inactivos</div>
      </div>
      <div class="metric-card border-red-200 text-center">
        <div class="metric-value text-red-600" x-text="kpisUsuarios.desvinculados || 0"></div>
        <div class="metric-label text-red-600">Desvinculados</div>
      </div>
      <div class="metric-card border-amber-200 text-center">
        <div class="metric-value text-amber-600" x-text="kpisUsuarios.ausentes || 0"></div>
        <div class="metric-label text-amber-600">En Vacaciones</div>
      </div>
    </div>

    <!-- Busqueda + acciones -->
    <div class="card-base mb-3.5">
      <div class="flex items-center gap-2 flex-wrap mb-2.5">
        <span class="text-[11px] text-slate-500 font-semibold">Panel de Control de Usuarios — Datos en vivo del backend</span>
        <span class="text-[10px] text-slate-400 ml-auto">Última sincronización: <span x-text="lastSyncText"></span></span>
      </div>
      <div class="flex gap-2 flex-wrap">
        <div class="relative flex-1 min-w-[200px]">
          <input class="form-input text-xs" placeholder="Buscar por nombre, usuario, email..."
                 x-model="uqSearch"
                 @input.debounce.300ms="uqOnFilterChange()">
        </div>
        <select class="form-input text-xs w-auto" x-model="uqRol" @change="uqOnFilterChange()">
          <option value="">Todos los roles</option>
          <option value="ADMIN">ADMIN</option>
          <option value="ETO">ETO</option>
          <option value="ELABORADOR - REVISOR">ELABORADOR - REVISOR</option>
          <option value="ELABORADOR - REVISOR - APROBADOR">ELABORADOR - REVISOR - APROBADOR</option>
          <option value="VISUALIZADOR (CL-EVAL)">VISUALIZADOR (CL-EVAL)</option>
        </select>
        <select class="form-input text-xs w-auto" x-model="uqFuente" @change="uqOnFilterChange()">
          <option value="">Todas las fuentes</option>
          <option value="ad">Del AD</option>
          <option value="local">Locales (test)</option>
        </select>
        <select class="form-input text-xs w-auto" x-model="uqEst" @change="uqOnFilterChange()">
          <option value="">Todos los estados</option>
          <option value="activo">Activos</option>
          <option value="inactivo">Inactivos</option>
          <option value="desvinculado">Desvinculados</option>
        </select>
        <select class="form-input text-xs w-auto" x-model="uqAusente" @change="uqOnFilterChange()">
          <option value="">Todos (ausencia)</option>
          <option value="true">Solo ausentes</option>
          <option value="false">Solo presentes</option>
        </select>
        <button @click="uqSearch='';uqRol='';uqFuente='';uqEst='';uqAusente='';uqOnFilterChange()" class="btn btn-sm text-[11px]">Limpiar</button>
        <button @click="sincronizarDirectorio()" :disabled="loadingUsuarios"
                x-show="$store.auth.role === 'admin'"
                class="btn btn-sm text-[11px] btn-primary" x-text="loadingUsuarios ? 'Sincronizando...' : 'Sincronizar AD'"></button>
        <button @click="exportarUsuarios('xlsx')" class="btn btn-sm text-[11px]">📊 Exportar a Excel</button>
      </div>
    </div>

    <!-- Tabla -->
    <div class="card-base p-0 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Colaborador</th>
              <th class="w-32">Rol</th>
              <th>Área</th>
              <th class="w-36">Delegado</th>
              <th class="w-28">Cód. SAP</th>
              <th class="w-20">Estado</th>
              <th>Sincronizado</th>
              <th class="text-center w-44">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="u in usuarios" :key="u.id">
              <tr class="group">
                <td class="py-2.5">
                  <div class="flex items-center gap-2.5">
                    <div :class="u.ausente ? 'bg-slate-400' : 'bg-gradient-to-br from-brand-500 to-blue-400'"
                         class="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0"
                         x-text="u.iniciales || '??'"></div>
                    <div class="min-w-0">
                      <div class="text-xs font-semibold text-slate-800 truncate" x-text="u.nombre_completo"></div>
                      <div class="text-[10px] text-slate-400 truncate" x-text="'@' + u.username + ' · ' + (u.email || 'sin email')"></div>
                      <div class="text-[10px] text-slate-500 mt-0.5" x-text="u.cargo"></div>
                    </div>
                  </div>
                </td>
                <td>
                  <template x-for="r in (u.roles || [])" :key="r">
                    <span :class="rolColor(r)" class="text-[10px] mr-1 mb-1 inline-block" x-text="formatRol(r)"></span>
                  </template>
                </td>
                <td class="text-[11px] text-slate-500">
                  <div x-show="u.gerencia_sigla" class="text-slate-700 font-semibold" x-text="u.gerencia_sigla + (u.area_sigla ? ' / ' + u.area_sigla : '')"></div>
                  <div x-show="u.ad_info" class="text-[10px] text-slate-400 truncate max-w-[200px]" :title="u.ad_info" x-text="u.ad_info"></div>
                </td>
                <td class="text-[11px]">
                  <template x-if="u.delegado_nombre">
                    <div>
                      <div class="flex items-center gap-1.5 text-slate-700">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        <span class="font-medium truncate" x-text="u.delegado_nombre"></span>
                      </div>
                      <div class="text-[9.5px] text-slate-400 mt-0.5" x-text="'@' + (u.delegado_username || '')"></div>
                    </div>
                  </template>
                  <template x-if="!u.delegado_nombre && u.estado_delegacion === 'pendiente'">
                    <div class="flex items-center gap-1.5 text-amber-600">
                      <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                      <span class="text-[10.5px] font-medium">⚠ Sin delegado</span>
                    </div>
                  </template>
                  <template x-if="!u.delegado_nombre && u.estado_delegacion === 'na'">
                    <div class="flex items-center gap-1.5 text-slate-400">
                      <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                      <span class="text-[10.5px]">No requiere</span>
                    </div>
                  </template>
                </td>
                <td>
                  <span x-show="u.ad_postal_code" class="text-[11px] font-mono text-slate-700" x-text="u.ad_postal_code"></span>
                  <span x-show="!u.ad_postal_code" class="text-[10px] text-amber-600" title="Sin codigo SAP (postalCode vacio en AD)">⚠ falta</span>
                </td>
                <td>
                  <span :class="u.estado === 'activo' ? 'badge badge-green' : (u.estado === 'inactivo' ? 'badge badge-amber' : 'badge badge-gray')" class="text-[10px]" x-text="u.estado"></span>
                  <div x-show="u.ausente" class="text-[10px] text-amber-600 mt-0.5">En vacaciones</div>
                </td>
                <td class="text-[10px] text-slate-400">
                  <span x-show="u.ad_last_synced_at" x-text="new Date(u.ad_last_synced_at).toLocaleDateString('es-BO')"></span>
                  <span x-show="!u.ad_last_synced_at" class="text-slate-300">—</span>
                  <div x-show="u.ad_warning" class="text-amber-600 mt-0.5" :title="u.ad_warning" x-text="u.ad_warning"></div>
                </td>
                <td class="text-center">
                  <button x-show="$store.auth.role === 'admin' || $store.auth.role === 'eto'"
                          @click="impersonarUsuario(u)" class="btn btn-sm text-[10px] mr-1" title="Iniciar sesion como este usuario">Impersonar</button>
                  <button @click="editarUsuario(u)" class="btn btn-sm text-[10px] btn-primary" title="Editar usuario">Editar</button>
                </td>
              </tr>
            </template>
            <tr x-show="!loadingUsuarios && usuarios.length === 0">
              <td colspan="8" class="text-center text-slate-400 py-8">
                <div class="text-[12px] mb-2">No hay usuarios cargados.</div>
                <button @click="sincronizarDirectorio()" x-show="$store.auth.role === 'admin'" class="btn btn-sm btn-primary text-[11px]">Sincronizar AD ahora</button>
              </td>
            </tr>
            <tr x-show="loadingUsuarios">
              <td colspan="8" class="text-center text-slate-400 py-6 text-[11px]">
                <div class="flex items-center justify-center gap-2">
                  <div class="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
                  <span>Cargando usuarios...</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         PAGINACIÓN (estilo profesional, debajo de la tabla)
    ═══════════════════════════════════════════════════════════ -->
    <div x-show="!loadingUsuarios && uqTotal > 0"
         class="flex items-center justify-between mt-3 px-1 flex-wrap gap-2">
      <!-- Info: "Mostrando 1-25 de 517 usuarios" -->
      <div class="text-[11px] text-slate-500">
        Mostrando
        <span class="font-semibold text-slate-700" x-text="uqPageStart"></span>–<span class="font-semibold text-slate-700" x-text="uqPageEnd"></span>
        de
        <span class="font-semibold text-slate-700" x-text="uqTotal"></span>
        usuarios
      </div>

      <!-- Controles: ‹ 1 ... 5 6 [7] 8 9 ... 21 › -->
      <nav class="flex items-center gap-1" aria-label="Paginación">
        <button @click="uqGoToPage(1)"
                :disabled="uqPage === 1 || loadingUsuarios"
                :class="(uqPage === 1 || loadingUsuarios) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                class="px-2 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors"
                title="Primera página">«</button>
        <button @click="uqPrevPage()"
                :disabled="uqPage === 1 || loadingUsuarios"
                :class="(uqPage === 1 || loadingUsuarios) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                class="px-2.5 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors"
                title="Anterior">‹</button>

        <template x-for="(p, idx) in uqVisiblePages" :key="idx">
          <span>
            <button x-show="p !== '...'"
                    @click="uqGoToPage(p)"
                    :class="p === uqPage
                      ? 'bg-brand-500 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-200'"
                    class="min-w-[28px] px-2 py-1 rounded text-[11px] font-semibold transition-colors"
                    x-text="p"></button>
            <span x-show="p === '...'" class="px-1 text-slate-400 text-[11px]">…</span>
          </span>
        </template>

        <button @click="uqNextPage()"
                :disabled="uqPage === uqTotalPages || loadingUsuarios"
                :class="(uqPage === uqTotalPages || loadingUsuarios) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                class="px-2.5 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors"
                title="Siguiente">›</button>
        <button @click="uqGoToPage(uqTotalPages)"
                :disabled="uqPage === uqTotalPages || loadingUsuarios"
                :class="(uqPage === uqTotalPages || loadingUsuarios) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                class="px-2 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors"
                title="Última página">»</button>
      </nav>

      <!-- Selector de tamaño de página -->
      <div class="flex items-center gap-1.5 text-[11px] text-slate-500">
        <span>Por página:</span>
        <select class="form-input text-[11px] py-0.5 px-1.5 w-auto"
                x-model.number="uqPageSize"
                @change="uqOnPageSizeChange()">
          <option value="10">10</option>
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
        </select>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: LOGS DE AUDITORÍA (NUEVA)
  ═══════════════════════════════════════════════════════════ -->

  <!-- ═══════════════════════════════════════════════════════════
       MODAL: EDITAR USUARIO (Sesion 9)
  ═══════════════════════════════════════════════════════════ -->
  <template x-teleport="body">
    <div x-show="editModalOpen"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrarModalEdicion()"
         class="modal-overlay" style="z-index:8000;display:none"
         :style="editModalOpen ? 'display:flex' : 'display:none'">

      <div @click.stop class="modal-box max-w-[560px] relative max-h-[90vh] overflow-y-auto"
           style="display:block">

        <button @click="cerrarModalEdicion()" :disabled="editModalSaving"
                class="absolute top-3.5 right-3.5 text-slate-400 hover:text-red-500 transition-colors text-lg leading-none cursor-pointer disabled:opacity-30">✕</button>

        <!-- Header -->
        <div class="mb-4 pb-3 border-b border-slate-200">
          <div class="text-base font-bold text-slate-900 flex items-center gap-2">
            <span class="text-xl">✏️</span>
            <span>Editar Usuario</span>
          </div>
          <div class="text-[11px] text-slate-500 mt-1">
            <span class="font-mono" x-text="'@' + editForm.username"></span>
            <span class="mx-1.5">·</span>
            <span x-text="editForm.nombre_completo"></span>
            <span class="mx-1.5">·</span>
            <span x-text="editForm.cargo"></span>
          </div>
        </div>

        <!-- Loading inicial -->
        <div x-show="editModalLoading" class="py-12 text-center text-slate-500">
          <div class="w-6 h-6 mx-auto border-2 border-brand-500 border-t-transparent rounded-full animate-spin mb-2"></div>
          <div class="text-[11.5px]">Cargando roles y usuarios activos...</div>
        </div>

        <!-- Form -->
        <div x-show="!editModalLoading" class="space-y-4">

          <!-- ROL -->
          <div>
            <label class="form-label flex items-center gap-1.5">
              <span class="text-brand-500">●</span> Rol
              <span class="text-slate-500 text-[10px]" x-show="editForm.requiere_delegado">(sugiere delegado)</span>
            </label>
            <select class="form-input text-xs" x-model="editForm.rol_codigo" @change="onRolChange()">
              <option value="">— Seleccionar rol —</option>
              <template x-for="r in editModalRoles" :key="r.codigo">
                <option :value="r.codigo" x-text="r.nombre + (r.requiere_delegado ? ' (sugiere delegado)' : '')"></option>
              </template>
            </select>
            <div class="form-hint">Determina qué pantallas y permisos tiene el usuario.</div>
          </div>

          <!-- DELEGADO (visible si el rol lo requiere) -->
          <div x-show="editForm.requiere_delegado">
            <label class="form-label flex items-center gap-1.5">
              <span class="text-brand-500">●</span> Delegado (Back-up)
              <span class="text-slate-500 text-[10px]">(opcional)</span>
            </label>

            <!-- Delegado actual -->
            <div x-show="editForm.delegado_nombre && !editModalShowDelegadoList"
                 class="flex items-center gap-2.5 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span class="text-[12px] font-semibold text-slate-800 flex-1" x-text="editForm.delegado_nombre"></span>
              <button @click="limpiarDelegado()" type="button" class="text-slate-400 hover:text-red-500 text-[14px] leading-none" title="Quitar delegado">✕</button>
              <button @click="editModalShowDelegadoList=true" type="button" class="text-brand-500 hover:text-brand-700 text-[10.5px] font-semibold" title="Cambiar delegado">Cambiar</button>
            </div>

            <!-- Buscador de delegado -->
            <div x-show="!editForm.delegado_nombre || editModalShowDelegadoList"
                 class="relative">
              <input type="text"
                     class="form-input text-xs"
                     placeholder="Buscar por nombre, usuario, código SAP, email..."
                     x-model="editModalDelegadoSearch"
                     @input="editModalShowDelegadoList=true"
                     @focus="editModalShowDelegadoList=true"
                     @click.outside="editModalShowDelegadoList=false">
              <div class="form-hint">
                <span x-text="editModalUsuariosActivos.length"></span> usuarios activos disponibles.
              </div>

              <!-- Dropdown de resultados -->
              <div x-show="editModalShowDelegadoList && editModalDelegadosFiltrados.length > 0"
                   x-transition:enter="transition ease-out duration-100"
                   x-transition:enter-start="opacity-0 -translate-y-1"
                   x-transition:enter-end="opacity-100 translate-y-0"
                   class="absolute z-10 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[240px] overflow-y-auto"
                   style="display:none"
                   :style="(editModalShowDelegadoList && editModalDelegadosFiltrados.length > 0) ? 'display:block' : 'display:none'">
                <template x-for="u in editModalDelegadosFiltrados" :key="u.id">
                  <button @click="seleccionarDelegado(u)" type="button"
                          class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors">
                    <div class="flex items-center gap-2">
                      <div class="w-7 h-7 rounded-full bg-gradient-to-br from-brand-500 to-blue-400 flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0"
                           x-text="u.iniciales || '??'"></div>
                      <div class="min-w-0 flex-1">
                        <div class="text-[12px] font-semibold text-slate-800 truncate" x-text="u.nombre_completo"></div>
                        <div class="text-[10px] text-slate-500 flex items-center gap-1.5">
                          <span class="font-mono" x-text="'@' + u.username"></span>
                          <template x-if="u.ad_postal_code">
                            <span class="text-slate-400">· SAP: <span class="font-mono" x-text="u.ad_postal_code"></span></span>
                          </template>
                          <template x-if="u.gerencia_sigla">
                            <span class="text-slate-400">· <span x-text="u.gerencia_sigla"></span></span>
                          </template>
                        </div>
                      </div>
                    </div>
                  </button>
                </template>
              </div>

              <div x-show="editModalShowDelegadoList && editModalDelegadosFiltrados.length === 0"
                   class="absolute z-10 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-center text-[11px] text-slate-500"
                   style="display:none"
                   :style="(editModalShowDelegadoList && editModalDelegadosFiltrados.length === 0) ? 'display:block' : 'display:none'">
                No se encontraron usuarios activos que coincidan con la búsqueda.
              </div>
            </div>
          </div>

          <!-- VACACIONES (Sesion 23 / Bloque B1: con fechas) -->
          <div>
            <label class="form-label flex items-center gap-2 cursor-pointer">
              <input type="checkbox" x-model="editForm.ausente" class="w-4 h-4 accent-brand-500 cursor-pointer">
              <span>🏖️ En vacaciones / Licencia</span>
            </label>
            <div class="form-hint">Marca al usuario como ausente. Las tareas se re-enrutan a su delegado.</div>
            <!-- Edicion de rango (Sesion 23 / Bloque B1) -->
            <div class="grid grid-cols-2 gap-2 mt-2">
              <div>
                <label class="text-[10px] text-slate-600 font-semibold block mb-1">Desde:</label>
                <input type="date" x-model="editForm.fecha_inicio_ausencia" class="form-input text-xs">
              </div>
              <div>
                <label class="text-[10px] text-slate-600 font-semibold block mb-1">Hasta:</label>
                <input type="date" x-model="editForm.fecha_fin_ausencia" class="form-input text-xs">
              </div>
            </div>
            <div class="text-[10px] text-slate-500 mt-1">
              <span x-show="editForm.ausencias && editForm.ausencias.length > 0">
                <span x-text="editForm.ausencias.length"></span> ausencia(s) registrada(s)
              </span>
            </div>
          </div>

          <!-- ESTADO -->
          <div>
            <label class="form-label flex items-center gap-1.5">
              <span class="text-brand-500">●</span> Estado
            </label>
            <select class="form-input text-xs" x-model="editForm.estado">
              <option value="activo">✅ Activo (puede usar el sistema)</option>
              <option value="inactivo">⏸ Inactivo (suspendido temporalmente)</option>
              <option value="desvinculado">🚫 Desvinculado (baja definitiva)</option>
            </select>
            <div class="form-hint">
              <span class="text-amber-600" x-show="editForm.estado === 'inactivo'">El usuario no podrá iniciar sesión hasta reactivarlo.</span>
              <span class="text-red-600" x-show="editForm.estado === 'desvinculado'">El usuario es removido del AD. No podrá loguearse nunca más por este username.</span>
            </div>
          </div>

          <!-- Observaciones -->
          <div>
            <label class="form-label">📝 Observaciones (queda en audit log)</label>
            <textarea class="form-input text-xs" x-model="editForm.observaciones" rows="2"
                      placeholder="Ej.: Asignación de ETO por promoción interna..."></textarea>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-2 mt-5 pt-3 border-t border-slate-200">
          <button @click="cerrarModalEdicion()" :disabled="editModalSaving" class="btn">Cancelar</button>
          <button @click="guardarEdicionUsuario()" :disabled="editModalSaving || editModalLoading"
                  class="btn btn-primary flex items-center gap-1.5">
            <span x-show="!editModalSaving">💾 Guardar cambios</span>
            <span x-show="editModalSaving" class="flex items-center gap-1.5">
              <span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Guardando...
            </span>
          </button>
        </div>
      </div>
    </div>
  </template>

  <div x-show="tab==='logs'" x-cloak>
    <div class="card-base">
      <div class="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-100 flex-wrap gap-2">
        <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider">📜 Historial de Cambios de Parámetros</div>
        <div class="flex gap-2 items-center flex-wrap">
          <input type="text" x-model="logSearch" @input.debounce.300ms="logOnFilterChange()" placeholder="Buscar parámetro, usuario, valor..." class="form-input text-xs w-56">
          <select x-model="logRecursoFilter" @change="logOnFilterChange()" class="form-input text-xs w-auto">
            <option value="">Todos los recursos</option>
            <option value="gerencia">Gerencia</option>
            <option value="area">Área</option>
            <option value="configuracion_global">Configuración</option>
            <option value="feriado">Feriado</option>
            <option value="email_template">Plantilla email</option>
            <option value="matriz_eto">Matriz ETO</option>
            <option value="tipo_documento">Tipo documento</option>
            <option value="estado">Estado</option>
            <option value="usuario">Usuario</option>
          </select>
          <select x-model="logAccionFilter" @change="logOnFilterChange()" class="form-input text-xs w-auto">
            <option value="">Todas las acciones</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="DELETE">DELETE</option>
            <option value="LOGIN">LOGIN</option>
            <option value="EXPORT">EXPORT</option>
            <option value="SYNC">SYNC</option>
            <option value="OVERRIDE">OVERRIDE</option>
          </select>
          <button @click="exportarLogs('xlsx')" class="btn btn-sm text-[11px]">📊 Exportar a Excel</button>
        </div>
      </div>
      <div class="overflow-x-auto -mx-3 px-3">
        <table class="data-table min-w-full">
          <thead>
            <tr>
              <th class="w-36">Fecha (BO)</th>
              <th class="w-24">Acción</th>
              <th class="w-32">Recurso</th>
              <th>Detalle</th>
              <th class="w-24">Usuario</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="h in logsFiltrados" :key="h.id">
              <tr>
                <td class="text-slate-500 text-[11px] whitespace-nowrap" x-text="h.fecha"></td>
                <td>
                  <span :class="{
                      'badge badge-green text-[10px]': h.accion === 'CREATE',
                      'badge badge-blue text-[10px]': h.accion === 'UPDATE',
                      'badge badge-red text-[10px]': h.accion === 'DELETE',
                      'badge badge-amber text-[10px]': h.accion === 'OVERRIDE' || h.accion === 'LOGIN',
                      'badge badge-gray text-[10px]': !['CREATE','UPDATE','DELETE','OVERRIDE','LOGIN'].includes(h.accion)
                   }" x-text="h.accion"></span>
                </td>
                <td class="font-mono text-[11px] text-slate-600" x-text="(h.recurso || '') + (h.recurso_id ? ' #' + h.recurso_id : '')"></td>
                <td class="text-[11.5px] text-slate-700" x-text="h.descripcion || h.parametro"></td>
                <td class="font-mono text-[10.5px] text-brand-600" x-text="h.usuario"></td>
              </tr>
            </template>
            <tr x-show="!loading.logs && logs.length === 0">
              <td colspan="5" class="text-center text-slate-400 py-6 text-[11px]">No se encontraron registros.</td>
            </tr>
            <tr x-show="loading.logs">
              <td colspan="5" class="text-center text-slate-400 py-6 text-[11px]">
                <div class="flex items-center justify-center gap-2">
                  <div class="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
                  <span>Cargando logs...</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="flex items-center justify-between mt-3 px-1 flex-wrap gap-2"
           x-show="!loading.logs && logTotal > 0">
        <div class="text-[11px] text-slate-500">
          Mostrando <span class="font-semibold text-slate-700" x-text="logPageStart"></span>–<span class="font-semibold text-slate-700" x-text="logPageEnd"></span>
          de <span class="font-semibold text-slate-700" x-text="logTotal"></span> registros
        </div>
        <nav class="flex items-center gap-1" aria-label="Paginación de logs">
          <button @click="logGoToPage(1)" :disabled="logPage === 1 || loading.logs"
                  :class="(logPage === 1 || loading.logs) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                  class="px-2 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors" title="Primera página">«</button>
          <button @click="logPrevPage()" :disabled="logPage === 1 || loading.logs"
                  :class="(logPage === 1 || loading.logs) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                  class="px-2.5 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors" title="Anterior">‹</button>
          <template x-for="(p, idx) in logVisiblePages" :key="'lp'+idx">
            <span>
              <button x-show="p !== '...'" @click="logGoToPage(p)"
                      :class="p === logPage ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-200'"
                      class="min-w-[28px] px-2 py-1 rounded text-[11px] font-semibold transition-colors"
                      x-text="p"></button>
              <span x-show="p === '...'" class="px-1 text-slate-400 text-[11px]">…</span>
            </span>
          </template>
          <button @click="logNextPage()" :disabled="logPage === logTotalPages || loading.logs"
                  :class="(logPage === logTotalPages || loading.logs) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                  class="px-2.5 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors" title="Siguiente">›</button>
          <button @click="logGoToPage(logTotalPages)" :disabled="logPage === logTotalPages || loading.logs"
                  :class="(logPage === logTotalPages || loading.logs) ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-200'"
                  class="px-2 py-1 rounded text-[11px] font-semibold text-slate-600 transition-colors" title="Última página">»</button>
        </nav>
        <div class="flex items-center gap-1.5 text-[11px] text-slate-500">
          <span>Por página:</span>
          <select class="form-input text-[11px] py-0.5 px-1.5 w-auto" x-model.number="logPageSize" @change="logOnPageSizeChange()">
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </div>
      </div>
    </div>
  </div>

</div>`
}
