/**
 * src/pages/Parametrizacion.js - Parametrizacion General del Sistema.
 *
 * Sesion B - tarea #10: refactorizado para consumir el backend real
 * (EPICA 9 endpoints) a traves de services/parametrizacionApi.js.
 * Ya NO importa de data/parametrosSistema.js.
 *
 * Tabs:
 *  - Tiempos y SLAs: /api/v1/configuracion-global
 *  - Restricciones:  /api/v1/configuracion-global
 *  - Diccionarios:   /api/v1/tipos-documento + /estados + /matriz-enrutamiento-eto
 *  - Gerencias:      /api/v1/gerencias + /areas
 *  - Notificaciones: /api/v1/email-templates
 *  - Usuarios:       /api/v1/usuarios (incluye export XLSX/CSV)
 *  - Logs:           /api/v1/audit-log
 */

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
} from '../services/parametrizacionApi.js'
import {
  ParametrosGlobalesDB,
  exclusionTiposDB,
  tiposExcluiblesDB,
  analistasETODB,
  estadosProcesoParamDB,
  etiquetasPlantillaDB,
  gerenciasParamDB,
  matrizETOParamDB,
  plantillasNotificacionParamDB,
  tiposDocParamDB,
} from '../data/parametrosSistema.js'

export const page = {
  init() {
    window.Alpine?.data('paramPage', () => ({
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
      logLimit: 200,
      logOffset: 0,
      logTotal: 0,
      get logsFiltrados() {
        const q = this.logSearch.toLowerCase()
        return this.logs.filter(l =>
          (!q ||
            (l.descripcion || '').toLowerCase().includes(q) ||
            (l.usuario_username || '').toLowerCase().includes(q) ||
            (l.recurso || '').toLowerCase().includes(q) ||
            (l.accion || '').toLowerCase().includes(q)
          ) &&
          (!this.logTabFilter || this._tabFromRecurso(l.recurso) === this.logTabFilter) &&
          (!this.logAccionFilter || l.accion === this.logAccionFilter) &&
          (!this.logRecursoFilter || l.recurso === this.logRecursoFilter)
        )
      },
      _tabFromRecurso(recurso) {
        const map = { gerencia: 'gerencias', area: 'gerencias', feriado: 'restricciones', configuracion_global: 'restricciones', email_template: 'notificaciones', matriz_eto: 'diccionarios', tipo_documento: 'diccionarios', estado: 'diccionarios', usuario: 'usuarios' }
        return map[recurso] || ''
      },
      async cargarLogs() {
        this.loading.logs = true
        try {
          const res = await auditLog.list({
            limit: this.logLimit,
            offset: this.logOffset,
            accion: this.logAccionFilter,
            recurso: this.logRecursoFilter,
          })
          if (res.ok) {
            const data = await res.data
            this.logs = data.items
            this.logTotal = data.total
          } else {
            window.toast(`Error cargando logs: ${res.status}`, 'error')
          }
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        } finally {
          this.loading.logs = false
        }
      },
      async exportarLogs(formato = 'xlsx') {
        // Reutiliza el helper build_excel del backend via /audit-log?formato=
        // Por simplicidad: descarga un XLSX via CSV (el backend no tiene export
        // de audit aun, asi que el frontend arma un CSV a partir de this.logs).
        const headers = ['Fecha', 'Usuario', 'Accion', 'Recurso', 'Recurso ID', 'Descripcion', 'IP', 'Exitoso']
        const rows = this.logs.map(l => [
          l.created_at, l.usuario_username || '', l.accion, l.recurso, l.recurso_id || '',
          (l.descripcion || '').replace(/[;,]/g, ' '), l.ip || '', l.exitoso ? 'SI' : 'NO',
        ])
        let csv = headers.join(';') + '\n'
        rows.forEach(r => { csv += r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(';') + '\n' })
        const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `audit_log_${new Date().toISOString().slice(0,10)}.csv`
        a.click()
        URL.revokeObjectURL(url)
        window.toast('Logs exportados a CSV', 'success')
      },

      /* ── Tiempos y SLAs (US-9.01) ── */
      tiempos: { plazoRevision: 5, plazoLectura: 3, slaVerde: 5, slaAmarillo: 10 },
      vigencias: [],
      async cargarTiempos() {
        this.loading.tiempos = true
        try {
          // Traer TODAS las claves de configuracion (no filtrar por categoria)
          // porque en la BD 'plazo_revision_aprobacion_dias' esta en FLUJO
          // y 'plazo_control_lectura_dias' en VIGENCIA. Mejor mergear todo.
          const res = await configGlobal.list()
          if (res.ok) {
            const cfg = (res.data.items || []).reduce((acc, c) => { acc[c.clave] = c.valor; return acc }, {})
            this.tiempos = {
              plazoRevision: parseInt(cfg.plazo_revision_aprobacion_dias || '5', 10),
              plazoLectura: parseInt(cfg.plazo_control_lectura_dias || '3', 10),
              slaVerde: parseInt(cfg.semaforo_verde_dias || '5', 10),
              slaAmarillo: parseInt(cfg.semaforo_amarillo_dias || '10', 10),
            }
          }
          // Cargar tipos-doc con periodo_vigencia para la grilla de vigencias
          const tdRes = await tiposDocumento.list()
          if (tdRes.ok) {
            this.vigencias = (tdRes.data.items || []).map(t => ({
              id: t.id, tipo: t.nombre, codigo: t.codigo, codigo_doc: t.codigo_doc,
              anios: t.indefinido ? 'Indefinido' : (t.periodo_vigencia || 0),
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
          await configGlobal.bulkUpsert('VIGENCIA', [
            { clave: 'plazo_revision_aprobacion_dias', valor: String(this.tiempos.plazoRevision) },
            { clave: 'plazo_control_lectura_dias', valor: String(this.tiempos.plazoLectura) },
            { clave: 'semaforo_verde_dias', valor: String(this.tiempos.slaVerde) },
            { clave: 'semaforo_amarillo_dias', valor: String(this.tiempos.slaAmarillo) },
          ])
          window.toast('Parametros de tiempos actualizados', 'success')
          await this.cargarLogs()
        } catch (e) {
          window.toast(`Error: ${e.message}`, 'error')
        }
      },
      guardarSemaforizacion() { this.guardarTiempos() },

      /* ── Restricciones (US-9.02) ── */
      restricciones: { maxAdjuntos: 20, maxSizeMB: 20, maxDescargasDia: 10, bandejaRegistros: 10 },
      chips: [...exclusionTiposDB], // tipos excluidos de limite de descarga (US-9.02) — fallback del mock hasta que cargueRestricciones() sobreescriba con datos del backend
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

      /* ── Diccionarios (US-9.03) ── */
      tiposDocs: [],
      tipoEditing: null,
      estados: [],
      estadoEditing: null,
      matrizETO: [],
      analistas: [], // lista de usuarios con rol ETO (cargada al entrar al tab)
      async cargarDiccionarios() {
        this.loading.diccionarios = true
        try {
          const [tdRes, estRes, matRes, uRes] = await Promise.all([
            tiposDocumento.list(),
            estados.list(),
            matrizEto.list(),
            usuarios.list({ rol: 'ETO' }),
          ])
          if (tdRes.ok) this.tiposDocs = (tdRes.data.items || []).map(t => ({
            id: t.id, tipo: t.nombre, cod: t.codigo, codigo_doc: t.codigo_doc,
            vigencia: t.indefinido ? 'Indefinido' : (t.periodo_vigencia || 0),
            activo: t.activo,
          }))
          if (estRes.ok) this.estados = (estRes.data.items || []).map(e => ({
            id: e.id, est: e.nombre, cod: e.codigo, ctx: e.contexto, activo: e.activo,
          }))
          if (matRes.ok) this.matrizETO = (matRes.data.items || []).map(m => ({
            id: m.id, gerencia: m.gerencia_sigla, gerencia_id: m.gerencia_id,
            analista: m.analista_username, analista_id: m.analista_usuario_id,
            disponible: m.disponibilidad === 'DISPONIBLE', disponibilidad: m.disponibilidad,
          }))
          if (uRes.ok) this.analistas = (uRes.data.items || []).map(u => ({ id: u.id, username: u.username, nombre: u.nombre_completo }))
        } catch (e) {
          window.toast(`Error cargando diccionarios: ${e.message}`, 'error')
        } finally {
          this.loading.diccionarios = false
        }
      },
      addTipo() {
        const nuevo = { tipo: '', cod: '', codigo_doc: 1, _new: true }
        this.tiposDocs.push(nuevo); this.tipoEditing = nuevo
      },
      async saveTipo(t) {
        if (!t.tipo.trim() || !t.cod.trim()) { window.toast('Complete tipo y codigo', 'warn'); return }
        const codigo = t.cod.toUpperCase().slice(0, 10)
        const codigo_doc = parseInt(t.codigo_doc, 10) || 1
        try {
          if (t._new) {
            const res = await tiposDocumento.create({ codigo, nombre: t.tipo, codigo_doc, periodo_vigencia: 5, indefinido: false, max_descargas_dia: 10, activo: true })
            if (res.ok) { t.id = res.data.id; delete t._new; this.tipoEditing = null; window.toast('Tipo creado', 'success'); await this.cargarDiccionarios(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          } else {
            const res = await tiposDocumento.update(t.id, { codigo, nombre: t.tipo, codigo_doc })
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
          const res = await matrizEto.update(m.id, { disponibilidad: m.disponible ? 'DISPONIBLE' : 'AUSENTE' })
          if (res.ok) { window.toast('Fila actualizada', 'success'); await this.cargarDiccionarios(); await this.cargarLogs() }
          else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },

      /* ── Gerencias y Areas (US-9.06 + #9d) ── */
      gerencias: [],
      areasPorGerencia: {},
      gerSelId: null,
      gerEditMode: false,
      gerEditNombre: '',
      gerEditSigla: '',
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
      startEditGer() { const g = this.gerSel; if (!g) return; this.gerEditMode = true; this.gerEditNombre = g.nombre; this.gerEditSigla = g.sigla },
      async saveGer() {
        const g = this.gerSel; if (!g) return
        if (!this.gerEditNombre.trim() || !this.gerEditSigla.trim()) { window.toast('Complete nombre y sigla', 'warn'); return }
        try {
          const res = await gerencias.update(g.id, { nombre: this.gerEditNombre.trim(), sigla: this.gerEditSigla.trim().toUpperCase().slice(0, 10) })
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
        this.areasPorGerencia[g.id].push({ sigla: 'NV', nombre: 'Nueva Area', orden: 99, _edit: true, _new: true })
      },
      async saveArea(a) {
        const g = this.gerSel; if (!g) return
        if (!a.nombre.trim() || !a.sigla.trim()) { window.toast('Complete nombre y sigla', 'warn'); return }
        const sigla = a.sigla.toUpperCase().slice(0, 10)
        try {
          if (a._new) {
            const res = await areas.create({ gerencia_id: g.id, sigla, nombre: a.nombre, orden: a.orden || 0, activo: true })
            if (res.ok) { window.toast('Area creada', 'success'); await this.cargarGerencias(); await this.cargarLogs() }
            else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
          } else {
            const res = await areas.update(a.id, { sigla, nombre: a.nombre })
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

      /* ── Plantillas de Notificacion (US-9.04) ── */
      plantillaSelect: 0,
      plantillas: [],
      etiquetas: [], // variables JSON de la plantilla seleccionada
      previewMode: false,
      previewHtml: '',
      async cargarNotificaciones() {
        this.loading.notificaciones = true
        try {
          const res = await emailTemplates.list()
          if (res.ok) {
            this.plantillas = (res.data.items || []).map(t => ({
              id: t.id, codigo: t.codigo, nombre: t.nombre, asunto: t.asunto, cuerpo: t.cuerpo_html, variables: t.variables_json || [], activo: t.activo,
            }))
            if (this.plantillas.length) this.onSelectPlantilla()
          }
        } catch (e) {
          window.toast(`Error cargando plantillas: ${e.message}`, 'error')
        } finally {
          this.loading.notificaciones = false
        }
      },
      onSelectPlantilla() {
        const p = this.plantillas[this.plantillaSelect]
        this.etiquetas = p?.variables || []
      },
      insertarEtiqueta(tag) {
        const ta = this.$refs.editorBody
        if (!ta) return
        const start = ta.selectionStart; const end = ta.selectionEnd
        const cuerpo = this.plantillas[this.plantillaSelect]?.cuerpo || ''
        this.plantillas[this.plantillaSelect].cuerpo = cuerpo.slice(0, start) + tag + cuerpo.slice(end)
        this.$nextTick(() => { ta.focus(); ta.setSelectionRange(start + tag.length, start + tag.length) })
      },
      async guardarPlantilla() {
        const p = this.plantillas[this.plantillaSelect]
        if (!p) return
        try {
          const res = await emailTemplates.update(p.codigo, { asunto: p.asunto, cuerpo_html: p.cuerpo })
          if (res.ok) { window.toast('Plantilla guardada', 'success'); await this.cargarLogs() }
          else window.toast(`Error: ${res.data.detail || res.status}`, 'error')
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },
      async previsualizarPlantilla() {
        const p = this.plantillas[this.plantillaSelect]
        if (!p) return
        const mock = { '{{CODIGO}}': 'PRO-CAL-045', '{{TITULO}}': 'Procedimiento de Calibracion de Balanzas', '{{USUARIO}}': 'Aracely Romero', '{{FECHA_LIMITE}}': '15/05/2026', '{{ETAPA}}': 'Revision Paralela', '{{LINK}}': 'https://sgd.cofar.com/bandeja', '{{GERENCIA}}': 'Calidad', '{{OBSERVACION}}': 'Sin observaciones' }
        try {
          const res = await emailTemplates.preview(p.codigo, mock)
          if (res.ok) {
            const r = res.data
            this.previewHtml = `<div class="text-xs text-slate-500 mb-1">Asunto:</div><div class="font-semibold text-slate-800 mb-3 text-sm">${r.asunto_rendered}</div><div class="text-xs text-slate-500 mb-1">Cuerpo:</div><div class="text-slate-700 text-sm leading-relaxed">${r.cuerpo_html_rendered}</div>`
            if (r.vars_faltantes?.length) window.toast(`Variables faltantes: ${r.vars_faltantes.join(', ')}`, 'warn')
            this.previewMode = true
          }
        } catch (e) { window.toast(`Error: ${e.message}`, 'error') }
      },
      cerrarPreview() { this.previewMode = false },

      /* ── Gestion de Usuarios (consume API real) ── */
      guardarTiempos() {
        window.toast('✅ Parámetros de tiempos actualizados correctamente', 'success')
      },
      guardarSemaforizacion() {
        this.guardarTiempos()
      },

      /* ─── Restricciones ─── */
      restricciones: {
        maxAdjuntos: ParametrosGlobalesDB.restriccionesArchivo.maxAdjuntos,
        maxSizeMB: ParametrosGlobalesDB.restriccionesArchivo.maxSizeMB,
        maxDescargasDia: ParametrosGlobalesDB.limitesDescarga.maxDescargasDia,
        bandejaRegistros: ParametrosGlobalesDB.paginacion.bandejaRegistros,
      },
      chips: [...exclusionTiposDB],
      nuevoChip: '',
      quitarChip(tipo) {
        this.chips = this.chips.filter(c => c !== tipo)
        this.pushLog('Tipos excluidos límite descarga', tipo, 'Eliminado', 'restricciones')
      },
      agregarChip() {
        const t = this.nuevoChip.trim()
        if (!t) return
        if (this.chips.includes(t)) { window.toast('⚠️ El tipo ya está excluido', 'warn'); return }
        this.chips.push(t)
        this.nuevoChip = ''
        this.pushLog('Tipos excluidos límite descarga', '—', t, 'restricciones')
      },
      guardarRestricciones() {
        const r = this.restricciones
        if (r.maxAdjuntos !== ParametrosGlobalesDB.restriccionesArchivo.maxAdjuntos) this.pushLog('Límite adjuntos', ParametrosGlobalesDB.restriccionesArchivo.maxAdjuntos + '', r.maxAdjuntos + '', 'restricciones')
        if (r.maxSizeMB !== ParametrosGlobalesDB.restriccionesArchivo.maxSizeMB) this.pushLog('Tamaño máx. archivo', ParametrosGlobalesDB.restriccionesArchivo.maxSizeMB + ' MB', r.maxSizeMB + ' MB', 'restricciones')
        if (r.maxDescargasDia !== ParametrosGlobalesDB.limitesDescarga.maxDescargasDia) this.pushLog('Máx. descargas/día', ParametrosGlobalesDB.limitesDescarga.maxDescargasDia + '', r.maxDescargasDia + '', 'restricciones')
        if (r.bandejaRegistros !== ParametrosGlobalesDB.paginacion.bandejaRegistros) this.pushLog('Paginación bandeja', ParametrosGlobalesDB.paginacion.bandejaRegistros + '', r.bandejaRegistros + '', 'restricciones')
        ParametrosGlobalesDB.restriccionesArchivo.maxAdjuntos = r.maxAdjuntos
        ParametrosGlobalesDB.restriccionesArchivo.maxSizeMB = r.maxSizeMB
        ParametrosGlobalesDB.limitesDescarga.maxDescargasDia = r.maxDescargasDia
        ParametrosGlobalesDB.paginacion.bandejaRegistros = r.bandejaRegistros
        window.toast('✅ Restricciones guardadas correctamente', 'success')
      },
      guardarLimitesDescarga() {
        this.guardarRestricciones()
      },

      /* ─── Diccionarios ─── */
      tiposDocs: JSON.parse(JSON.stringify(tiposDocParamDB)),
      tipoEditing: null,
      addTipo() {
        const nuevo = { tipo: '', cod: '', _new: true }
        this.tiposDocs.push(nuevo)
        this.tipoEditing = nuevo
      },
      saveTipo(t) {
        if (!t.tipo.trim() || !t.cod.trim()) { window.toast('⚠️ Complete tipo y código', 'warn'); return }
        const ant = t._new ? '(nuevo)' : tiposDocParamDB.find(x => x.cod === t.cod)?.tipo || ''
        t.cod = t.cod.toUpperCase().slice(0, 5)
        delete t._new
        this.tipoEditing = null
        this.pushLog('Tipo de documento', ant, t.tipo + ' (' + t.cod + ')', 'diccionarios')
        window.toast('✅ Tipo guardado', 'success')
      },
      cancelTipo(t) {
        if (t._new) this.tiposDocs.splice(this.tiposDocs.indexOf(t), 1)
        this.tipoEditing = null
      },
      deleteTipo(t) {
        window.confirmDeleteModal?.abrir({
          titulo: '🗑 Eliminar Tipo de Documento',
          mensaje: `¿Eliminar el tipo <strong>${t.tipo}</strong> (${t.cod})?`,
          onConfirm: () => {
            this.tiposDocs.splice(this.tiposDocs.indexOf(t), 1)
            this.pushLog('Eliminación tipo documento', t.tipo + ' (' + t.cod + ')', 'Eliminado', 'diccionarios')
            window.toast('✅ Tipo eliminado', 'warn')
          }
        })
      },

      estados: JSON.parse(JSON.stringify(estadosProcesoParamDB)),
      estadoEditing: null,
      addEstado() {
        const nuevo = { est: '', ctx: 'Tarea', _new: true }
        this.estados.push(nuevo)
        this.estadoEditing = nuevo
      },
      saveEstado(e) {
        if (!e.est.trim()) { window.toast('⚠️ Ingrese el nombre del estado', 'warn'); return }
        const ant = e._new ? '(nuevo)' : estadosProcesoParamDB.find(x => x.est === e.est)?.est || ''
        delete e._new
        this.estadoEditing = null
        this.pushLog('Estado de proceso/tarea', ant, e.est + ' · ' + e.ctx, 'diccionarios')
        window.toast('✅ Estado guardado', 'success')
      },
      cancelEstado(e) {
        if (e._new) this.estados.splice(this.estados.indexOf(e), 1)
        this.estadoEditing = null
      },
      deleteEstado(e) {
        window.confirmDeleteModal?.abrir({
          titulo: '🗑 Eliminar Estado',
          mensaje: `¿Eliminar el estado <strong>${e.est}</strong> (${e.ctx})?`,
          onConfirm: () => {
            this.estados.splice(this.estados.indexOf(e), 1)
            this.pushLog('Eliminación estado', e.est + ' (' + e.ctx + ')', 'Eliminado', 'diccionarios')
            window.toast('✅ Estado eliminado', 'warn')
          }
        })
      },

      matrizETO: JSON.parse(JSON.stringify(matrizETOParamDB)),
      analistas: [...analistasETODB],
      guardarFilaMatriz(m) {
        this.pushLog('Matriz ETO', m.gerencia, `Analista: ${m.analista} · Disp: ${m.disponible ? 'Sí' : 'No'}`, 'diccionarios')
        window.toast('✅ Fila actualizada', 'success')
      },

      /* ─── Gerencias y Áreas ─── */
      gerencias: JSON.parse(JSON.stringify(gerenciasParamDB)),
      gerSelId: 1,
      gerEditMode: false,
      gerEditNombre: '',
      gerEditCod: '',
      get gerSel() { return this.gerencias.find(g => g.id === this.gerSelId) },
      addGerencia() {
        const id = Date.now()
        const nuevo = { id, nombre: 'Nueva Gerencia', cod: 'GER', areas: [] }
        this.gerencias.push(nuevo)
        this.gerSelId = id
        this.gerEditMode = true
        this.gerEditNombre = nuevo.nombre
        this.gerEditCod = nuevo.cod
      },
      startEditGer() {
        const g = this.gerSel
        if (!g) return
        this.gerEditMode = true
        this.gerEditNombre = g.nombre
        this.gerEditCod = g.cod
      },
      saveGer() {
        const g = this.gerSel
        if (!g) return
        if (!this.gerEditNombre.trim() || !this.gerEditCod.trim()) { window.toast('⚠️ Complete nombre y código', 'warn'); return }
        const ant = g.nombre + ' (' + g.cod + ')'
        g.nombre = this.gerEditNombre.trim()
        g.cod = this.gerEditCod.trim().toUpperCase().slice(0, 5)
        this.gerEditMode = false
        this.pushLog('Gerencia', ant, g.nombre + ' (' + g.cod + ')', 'gerencias')
        window.toast('✅ Gerencia actualizada', 'success')
      },
      deleteGer() {
        const g = this.gerSel
        if (!g) return
        window.confirmDeleteModal?.abrir({
          titulo: '🗑 Eliminar Gerencia',
          mensaje: `⚠️ Esta estructura tiene documentos vinculados. Se aplicará <strong>borrado lógico</strong> en la gerencia <strong>${g.nombre}</strong>.`,
          onConfirm: () => {
            this.gerencias.splice(this.gerencias.indexOf(g), 1)
            this.gerSelId = this.gerencias[0]?.id || null
            this.pushLog('Eliminación gerencia', g.nombre, 'Borrado lógico', 'gerencias')
            window.toast('⚠️ Gerencia eliminada (borrado lógico)', 'warn')
          }
        })
      },
      addArea() {
        const g = this.gerSel
        if (!g) return
        g.areas.push({ n: 'Nueva Área', c: 'COD', _edit: true })
      },
      saveArea(a) {
        if (!a.n.trim() || !a.c.trim()) { window.toast('⚠️ Complete nombre y código del área', 'warn'); return }
        a.c = a.c.toUpperCase().slice(0, 5)
        delete a._edit
        this.pushLog('Área', '(nueva)', a.n + ' (' + a.c + ')', 'gerencias')
        window.toast('✅ Área guardada', 'success')
      },
      deleteArea(a) {
        const g = this.gerSel
        if (!g) return
        window.confirmDeleteModal?.abrir({
          titulo: 'Eliminar Área',
          mensaje: `¿Eliminar el área <strong>${a.n}</strong>? Borrado lógico — se desvinculará de nuevas solicitudes.`,
          onConfirm: () => {
            g.areas.splice(g.areas.indexOf(a), 1)
            this.pushLog('Eliminación área', a.n + ' (' + a.c + ')', 'Borrado lógico', 'gerencias')
            window.toast('⚠️ Área eliminada', 'warn')
          }
        })
      },
      abrirMoverArea(a) {
        const g = this.gerSel
        if (!g) return
        window.moveAreaModal?.abrir({
          area: a,
          origenId: g.id,
          gerencias: this.gerencias,
          onConfirmar: (destinoId) => {
            const destino = this.gerencias.find(x => x.id === destinoId)
            if (!destino) return
            g.areas.splice(g.areas.indexOf(a), 1)
            destino.areas.push({ n: a.n, c: a.c })
            this.pushLog('Mover área', `${a.n} de ${g.nombre}`, `A ${destino.nombre}`, 'gerencias')
            window.toast(`✅ Área ${a.n} movida a ${destino.nombre}`, 'success')
          }
        })
      },

      /* ─── Plantillas de Notificación ─── */
      plantillaSelect: 0,
      plantillas: JSON.parse(JSON.stringify(plantillasNotificacionParamDB)),
      etiquetas: [...etiquetasPlantillaDB],
      previewMode: false,
      previewHtml: '',
      insertarEtiqueta(tag) {
        const ta = this.$refs.editorBody
        const start = ta.selectionStart
        const end = ta.selectionEnd
        const cuerpo = this.plantillas[this.plantillaSelect].cuerpo || ''
        this.plantillas[this.plantillaSelect].cuerpo = cuerpo.slice(0, start) + tag + cuerpo.slice(end)
        this.$nextTick(() => { ta.focus(); ta.setSelectionRange(start + tag.length, start + tag.length) })
      },
      guardarPlantilla() {
        const p = this.plantillas[this.plantillaSelect]
        this.pushLog('Plantilla notificación', '(editada)', p.nombre, 'notificaciones')
        window.toast('✅ Plantilla "' + p.nombre + '" guardada correctamente', 'success')
      },
      previsualizarPlantilla() {
        const p = this.plantillas[this.plantillaSelect]
        const mock = {
          '{{CODIGO}}': 'PRO-CAL-045',
          '{{TITULO}}': 'Procedimiento de Calibración de Balanzas',
          '{{USUARIO}}': 'Aracely Romero',
          '{{FECHA_LIMITE}}': '15/05/2026',
          '{{ETAPA}}': 'Revisión Paralela',
          '{{LINK}}': 'https://sgd.cofar.com/bandeja',
          '{{GERENCIA}}': 'Calidad',
          '{{OBSERVACION}}': 'Sin observaciones',
        }
        let asunto = p.asunto
        let cuerpo = (p.cuerpo || '').replace(/\n/g, '<br>')
        Object.entries(mock).forEach(([k, v]) => {
          asunto = asunto.replace(new RegExp(k.replace(/[{}]/g, '\\\\$&'), 'g'), v)
          cuerpo = cuerpo.replace(new RegExp(k.replace(/[{}]/g, '\\\\$&'), 'g'), `<strong class="text-brand-600">${v}</strong>`)
        })
        this.previewHtml = `<div class="text-xs text-slate-500 mb-1">Asunto:</div><div class="font-semibold text-slate-800 mb-3 text-sm">${asunto}</div><div class="text-xs text-slate-500 mb-1">Cuerpo:</div><div class="text-slate-700 text-sm leading-relaxed">${cuerpo}</div>`
        this.previewMode = true
      },
      cerrarPreview() { this.previewMode = false },

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
      uqFuente: '',
      loadingUsuarios: false,
      lastSyncText: 'nunca',
      kpisUsuarios: { total: 0, activos: 0, ausentes: 0 },

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
          // apiDownload dispara la descarga automaticamente desde Content-Disposition.
          try {
            const res = await usuarios.export(formato, {
              q: this.uqSearch,
              rol: this.uqRol,
              estado: this.uqEst,
            })
            if (res.ok) {
              window.toast(`Exportado a ${formato.toUpperCase()}`, 'success')
              await this.cargarLogs()
            } else {
              window.toast(`Error exportando: ${res.status}`, 'error')
            }
          } catch (e) {
            window.toast(`Error: ${e.message}`, 'error')
          }
        },

      async impersonarUsuario(u) {
        if (!confirm(`¿Impersonar a ${u.nombre_completo} (${u.username})? Tu sesión actual se mantiene en segundo plano.`)) {
          return
        }
        try {
          const res = await fetch(`${this.API_BASE}/admin/impersonate/start`, {
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
          this.pushLog('Impersonate', 'admin_local', data.user.username, 'usuarios')
          // Recargar la pagina para que el router detecte el cambio de sesion
          setTimeout(() => window.location.hash = '#/bandeja', 800)
        } catch (e) {
          window.toast(`Error de red: ${e.message}`, 'error')
        }
      },

      async toggleAusente(u) {
        // TODO: implementar PATCH /usuarios/{id} cuando exista
        window.toast((u.ausente ? '✅ Usuario marcado como Ausente' : '↩ Usuario restaurado a Activo'), 'success')
        this.pushLog('Estado usuario', u.nombre_completo, u.ausente ? 'Ausente' : 'Activo', 'usuarios')
      },

      editarUsuario(u) {
        // TODO: cuando exista el modal de edicion, abrirlo
        window.toast(`Edición de ${u.username} - en construcción`, 'info')
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
    }))
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
        <div class="space-y-2.5">
          <template x-for="v in vigencias" :key="v.tipo">
            <div class="flex items-center gap-3">
              <div class="flex-1 text-[11.5px] font-medium text-slate-700" x-text="v.tipo"></div>
              <div class="flex items-center gap-1.5">
                <input type="number" x-model.number="v.años" min="1" max="20" class="form-input w-16 text-xs py-1 text-center">
                <span class="text-[11px] text-slate-500">años</span>
              </div>
            </div>
          </template>
        </div>
        <div class="form-hint mt-2">Cada tipo tiene su propio plazo de vigencia antes de requerir revisión.</div>
        <button @click="guardarTiempos()" class="btn btn-primary w-full mt-3">💾 Guardar Vigencia y Flujo</button>
      </div>

      <!-- Semaforización -->
      <div class="card-base">
        <div class="section-header">🚦 Semaforización de Bandejas</div>
        <div class="text-[11px] text-slate-500 mb-3">Define los umbrales (en días) que determinan el color de alerta en las tareas pendientes.</div>
        <div class="flex flex-col gap-2.5">
          <div class="flex items-center gap-3">
            <div class="w-4 h-4 rounded-full bg-emerald-600 flex-shrink-0"></div>
            <div class="flex-1 text-[11.5px] font-semibold text-slate-800">Verde — A tiempo</div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] text-slate-500">Más de</span>
              <input type="number" x-model="tiempos.slaVerde" min="1" max="10" class="form-input w-14 text-xs py-1 text-center">
              <span class="text-[11px] text-slate-500">días restantes</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-4 h-4 rounded-full bg-amber-500 flex-shrink-0"></div>
            <div class="flex-1 text-[11.5px] font-semibold text-slate-800">Amarillo — Próximo a vencer</div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] text-slate-500">Entre</span>
              <input type="number" x-model="tiempos.slaAmarillo" min="1" max="5" class="form-input w-14 text-xs py-1 text-center">
              <span class="text-[11px] text-slate-500">y 5 días</span>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-4 h-4 rounded-full bg-red-600 flex-shrink-0"></div>
            <div class="flex-1 text-[11.5px] font-semibold text-slate-800">Rojo — Vencido o crítico</div>
            <div class="text-[11px] text-slate-400 font-semibold">Menos de 1 día o vencido</div>
          </div>
        </div>
        <div class="form-grid-2 mt-3">
          <div>
            <label class="form-label text-[10.5px]">Plazo máx. revisión/aprobación (días)</label>
            <input type="number" x-model="tiempos.plazoRevision" min="1" max="30" class="form-input text-xs">
          </div>
          <div>
            <label class="form-label text-[10.5px]">Plazo máx. control de lectura (días)</label>
            <input type="number" x-model="tiempos.plazoLectura" min="15" max="60" class="form-input text-xs">
          </div>
        </div>
        <button @click="guardarSemaforizacion()" class="btn btn-primary w-full mt-3">💾 Guardar Semaforización</button>
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
              <template x-for="(t, idx) in chips" :key="idx + '-' + t">
                <option :value="t" x-text="t"></option>
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
        <table class="data-table">
          <thead><tr><th>Tipo</th><th>Código</th><th class="w-20"></th></tr></thead>
          <tbody>
            <template x-for="t in tiposDocs" :key="t.id">
              <tr>
                <template x-if="tipoEditing === t">
                  <td colspan="2" class="py-1.5">
                    <div class="flex gap-1.5">
                      <input type="text" x-model="t.tipo" class="form-input text-[11px] py-1 flex-1" placeholder="Nombre del tipo">
                      <input type="text" x-model="t.cod" class="form-input text-[11px] py-1 w-20 uppercase font-mono" placeholder="COD" maxlength="5">
                    </div>
                  </td>
                </template>
                <template x-if="tipoEditing !== t">
                  <td class="font-medium" x-text="t.tipo"></td>
                </template>
                <template x-if="tipoEditing !== t">
                  <td class="font-mono text-brand-600 font-bold" x-text="t.cod"></td>
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
        <div class="form-hint mt-2">Los tipos con registros activos no pueden eliminarse (borrado lógico).</div>
      </div>

      <!-- Estados -->
      <div class="card-base">
        <div class="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-100">
          <span class="text-[11.5px] font-bold text-slate-600">⚙️ Estados de Proceso y Tarea</span>
          <button class="btn btn-sm text-emerald-700 border-emerald-200" @click="addEstado()">+ Nuevo</button>
        </div>
        <table class="data-table">
          <thead><tr><th>Estado</th><th>Contexto</th><th class="w-20"></th></tr></thead>
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
                      <option value="Tarea">Tarea</option>
                      <option value="Proceso">Proceso</option>
                    </select>
                  </template>
                  <template x-if="estadoEditing !== e">
                    <span :class="e.ctx==='Tarea' ? 'badge badge-blue' : 'badge badge-green'" x-text="e.ctx"></span>
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

    <!-- Matriz ETO -->
    <div class="card-base">
      <div class="flex items-center justify-between mb-1">
        <div class="text-[11.5px] font-bold text-slate-600"># Matriz de Enrutamiento ETO</div>
        <div class="text-[10.5px] text-slate-400">El sistema consulta esta tabla en el Paso 4 del flujo para asignar la tarea de liberación.</div>
      </div>
      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Gerencia / Área</th>
              <th>Analista ETO Asignado</th>
              <th class="text-center">Disponibilidad</th>
              <th>Delegado (si ausente)</th>
              <th class="w-14"></th>
            </tr>
          </thead>
          <tbody>
            <template x-for="m in matrizETO" :key="m.id">
              <tr>
                <td class="font-bold text-slate-800" x-text="m.gerencia"></td>
                <td>
                  <select class="form-input text-xs" x-model="m.analista">
                    <template x-for="a in analistas" :key="a.id || a.username"><option :value="a.username" x-text="a.nombre || a.username"></option></template>
                  </select>
                </td>
                <td class="text-center">
                  <label class="inline-flex items-center gap-1.5 cursor-pointer text-[11.5px]">
                    <input type="checkbox" x-model="m.disponible" class="w-4 h-4 accent-brand-500">
                    <span :class="m.disponible ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'" x-text="m.disponible ? 'Disponible' : 'Ausente'"></span>
                  </label>
                </td>
                <td>
                  <select x-show="!m.disponible" class="form-input text-xs" x-model="m.delegado">
                    <option value="">— Seleccionar —</option>
                    <template x-for="a in analistas" :key="a.id || a.username"><option :value="a.username" x-text="a.nombre || a.username"></option></template>
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
                      <button @click="gerSel.areas.splice(gerSel.areas.indexOf(a),1)" class="btn btn-sm text-red-700 border-red-200 py-0.5 px-1.5 text-[10px]">✕</button>
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
          <div @click="plantillaSelect=i; previewMode=false"
               :class="plantillaSelect===i ? 'bg-blue-50 border-l-[3px] border-brand-500' : 'hover:bg-slate-50 border-l-[3px] border-transparent'"
               class="cursor-pointer px-3.5 py-2.5 border-b border-slate-100 transition-colors">
            <div class="text-xs font-semibold text-slate-800" x-text="p.nombre"></div>
            <div class="text-[10px] text-slate-400 mt-0.5" x-text="p.trigger"></div>
          </div>
        </template>
      </div>

      <!-- Editor / Preview -->
      <div class="card-base">
        <div class="flex items-center justify-between mb-3.5">
          <h2 class="text-[13px] font-bold text-slate-800" x-text="plantillas[plantillaSelect].nombre"></h2>
          <button @click="previsualizarPlantilla()" class="btn btn-sm text-[11px]">✉️ Previsualizar</button>
        </div>

        <!-- Preview overlay -->
        <div x-show="previewMode" class="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-3.5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10.5px] font-bold text-slate-500 uppercase tracking-wider">Vista previa del correo</span>
            <button @click="cerrarPreview()" class="text-slate-400 hover:text-red-500 text-sm leading-none cursor-pointer">✕</button>
          </div>
          <div class="bg-white border border-slate-200 rounded-lg p-4 shadow-sm" x-html="$sanitize(previewHtml)"></div>
        </div>

        <div x-show="!previewMode" class="mb-3">
          <label class="form-label text-[10.5px]">Asunto del correo</label>
          <input type="text" x-model="plantillas[plantillaSelect].asunto" class="form-input text-xs">
        </div>

        <div x-show="!previewMode" class="mb-3">
          <label class="form-label text-[10.5px]">Etiquetas disponibles (clic para insertar):</label>
          <div class="flex flex-wrap gap-1.5">
            <template x-for="e in etiquetas" :key="e">
              <button @click="insertarEtiqueta(e)" class="px-2 py-0.5 rounded border border-blue-200 bg-blue-50 text-brand-600 text-[10.5px] cursor-pointer font-mono hover:bg-blue-100 transition-colors">\${e}</button>
            </template>
          </div>
        </div>

        <div x-show="!previewMode" class="mb-3">
          <label class="form-label text-[10.5px]">Cuerpo del correo</label>
          <textarea class="form-input text-xs font-mono leading-relaxed" rows="10" x-model="plantillas[plantillaSelect].cuerpo" x-ref="editorBody" placeholder="(Plantilla en configuración — haga clic en Previsualizar)"></textarea>
        </div>

        <div class="flex justify-end gap-2">
          <button @click="window.toast('Cambios cancelados','warn')" class="btn btn-sm">Cancelar</button>
          <button @click="guardarPlantilla()" class="btn btn-primary btn-sm">💾 Guardar Plantilla</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ═══════════════════════════════════════════════════════════
       TAB: GESTIÓN DE USUARIOS
  ═══════════════════════════════════════════════════════════ -->
  <div x-show="tab==='usuarios'" x-cloak x-init="watchTabUsuarios('usuarios')">
    <!-- KPIs -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mb-3.5">
      <div class="metric-card text-center">
        <div class="metric-value text-slate-800" x-text="kpisUsuarios.total || 0"></div>
        <div class="metric-label">Usuarios Totales</div>
      </div>
      <div class="metric-card border-emerald-200 text-center">
        <div class="metric-value text-emerald-600" x-text="kpisUsuarios.activos || 0"></div>
        <div class="metric-label text-emerald-600">Activos</div>
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
        <button @click="uqSearch='';uqRol='';uqFuente='';uqOnFilterChange()" class="btn btn-sm text-[11px]">Limpiar</button>
        <button @click="sincronizarDirectorio()" :disabled="loadingUsuarios"
                class="btn btn-sm text-[11px] btn-primary" x-text="loadingUsuarios ? 'Sincronizando...' : 'Sincronizar AD'"></button>
        <button @click="exportarUsuarios()" class="btn btn-sm text-[11px]">Exportar CSV</button>
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
              <th>Área / Gerencia</th>
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
                <td>
                  <span x-show="u.ad_postal_code" class="text-[11px] font-mono text-slate-700" x-text="u.ad_postal_code"></span>
                  <span x-show="!u.ad_postal_code" class="text-[10px] text-amber-600" title="Sin codigo SAP (postalCode vacio en AD)">⚠ falta</span>
                </td>
                <td>
                  <span :class="u.estado === 'activo' ? 'badge badge-green' : 'badge badge-gray'" class="text-[10px]" x-text="u.estado"></span>
                  <div x-show="u.ausente" class="text-[10px] text-amber-600 mt-0.5">En vacaciones</div>
                </td>
                <td class="text-[10px] text-slate-400">
                  <span x-show="u.ad_last_synced_at" x-text="new Date(u.ad_last_synced_at).toLocaleDateString('es-BO')"></span>
                  <span x-show="!u.ad_last_synced_at" class="text-slate-300">—</span>
                  <div x-show="u.ad_warning" class="text-amber-600 mt-0.5" :title="u.ad_warning" x-text="u.ad_warning"></div>
                </td>
                <td class="text-center">
                  <button @click="impersonarUsuario(u)" class="btn btn-sm text-[10px] mr-1" title="Iniciar sesion como este usuario">Impersonar</button>
                  <button @click="editarUsuario(u)" class="btn btn-sm text-[10px]" title="Editar usuario">Editar</button>
                </td>
              </tr>
            </template>
            <tr x-show="!loadingUsuarios && usuarios.length === 0">
              <td colspan="7" class="text-center text-slate-400 py-8">
                <div class="text-[12px] mb-2">No hay usuarios cargados.</div>
                <button @click="sincronizarDirectorio()" class="btn btn-sm btn-primary text-[11px]">Sincronizar AD ahora</button>
              </td>
            </tr>
            <tr x-show="loadingUsuarios">
              <td colspan="7" class="text-center text-slate-400 py-6 text-[11px]">
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
  <div x-show="tab==='logs'" x-cloak>
    <div class="card-base">
      <div class="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-100 flex-wrap gap-2">
        <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider">📜 Historial de Cambios de Parámetros</div>
        <div class="flex gap-2 items-center">
          <input type="text" x-model="logSearch" placeholder="Buscar parámetro, usuario, valor..." class="form-input text-xs w-56">
          <select x-model="logTabFilter" class="form-input text-xs w-auto">
            <option value="">Todas las pestañas</option>
            <option value="tiempos">Tiempos</option>
            <option value="restricciones">Restricciones</option>
            <option value="diccionarios">Diccionarios</option>
            <option value="gerencias">Gerencias</option>
            <option value="notificaciones">Notificaciones</option>
            <option value="usuarios">Usuarios</option>
          </select>
          <button @click="exportarLogs()" class="btn btn-sm text-[11px]">📊 Exportar a Excel</button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th class="w-32">Fecha</th>
              <th>Pestaña</th>
              <th>Parámetro</th>
              <th>Valor Anterior</th>
              <th>Valor Nuevo</th>
              <th class="w-24">Usuario</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="h in logsFiltrados" :key="h.id">
              <tr>
                <td class="text-slate-500" x-text="h.fecha"></td>
                <td>
                  <span class="badge badge-gray text-[10px]" x-text="h.tab || '—'"></span>
                </td>
                <td class="font-semibold text-slate-800" x-text="h.parametro"></td>
                <td class="text-red-600 font-mono text-[11px]" x-text="h.anterior"></td>
                <td class="text-emerald-600 font-mono font-bold text-[11px]" x-text="h.nuevo"></td>
                <td class="text-brand-600 font-mono text-[11px]" x-text="h.usuario"></td>
              </tr>
            </template>
            <tr x-show="logsFiltrados.length === 0">
              <td colspan="6" class="text-center text-slate-400 py-6 text-[11px]">No se encontraron registros.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="form-hint mt-2">Los cambios en plazos no afectan flujos en curso (no retroactivo).</div>
    </div>
  </div>

</div>`
}
