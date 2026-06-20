/**
 * pages/AprobacionDocumento.js — Wizard de aprobación documental (3 pasos)
 *
 * Sesion 22 R2 FASE 2: consume /api/v1/documentos (BD real) + /api/v1/bandeja.
 *
 * Cambios vs version previa:
 *  - Importa de services/documentosApi.js en vez de mocks de data/
 *  - Carga catalogos (tipos, gerencias, areas, usuarios) via API en init()
 *  - codigoAuto: llama a /preview-codigo (no se calcula en cliente)
 *  - areasList: filtrado en cliente sobre la lista de areas de la BD
 *  - firmarEnviar: POST /documentos (paso 1) + POST /enviar (paso 3) con firma 2FA real
 *  - Paso 1: crear doc via POST antes de pasar a paso 2
 */
import { documentos, bandejas, generarNombreCompleto } from '../services/documentosApi.js'
import { tiposDocumento, gerencias as gerenciasApi, areas as areasApi, usuarios as usuariosApi, roles as rolesApi, configGlobal } from '../services/parametrizacionApi.js'

export const page = {
  init() {
    window.Alpine?.data('wizardAprobacion', () => ({
      paso: 1,

      // ─── Catalogos (cargados del backend en init()) ───
      tiposList: [],
      gerenciasList: [],
      areasAll: [],     // todas las areas (para filtrar en cliente por gerencia)
      empleadosList: [],
      analistasEtoList: [],   // solo usuarios con rol ETO (F1)
      revisoresList: [],      // usuarios con capacidad de revisar (F2)
      aprobadoresList: [],    // usuarios con capacidad de aprobar (F2)
      cargandoCatalogos: true,

      // ─── Documento en creacion ───
      documentoId: null,  // id devuelto por POST /documentos
      flujoId: null,
      tipodoc: '',
      gerencia: '',
      area: '',
      tipoSolicitud: '',
      titulo: '',
      justificacion: '',
      // R3 item 0.2: actualizacion documental
      docActualizar: '',          // id del Documento existente que se actualiza
      docsActualizables: [],      // lista de docs filtrados por (area, tipo)
      cargandoDocsActualizables: false,
      inputDocActualizar: '',     // texto de busqueda para dropdown
      mostrarDocsActualizables: false,
      // Issue 11.1: el cliente decidio quitar el campo "Analista ETO asignado"
      // del wizard paso 1. analistasEtoList se mantiene porque el paso 3
      // incluye ETOs como posibles revisores/aprobadores.

      // ─── Limites de archivos (cargados de configuracion_global en init()) ───
      _limitesArchivos: { maxTamanoArchivoMb: 20, maxArchivosPorSolicitud: 20 },

      // ─── Codigo automatico (del backend) ───
      codigoAuto: '---',
      versionAuto: '00',
      cargandoCodigo: false,

      // ─── Paso 1: archivos (drag&drop) ───
      archivoPrincipal: null,
      dropPrincipal: false,
      formulariosAsociados: [],   // [{ id, file, titulo }]
      dropFormularios: false,
      _dragIdx: null,             // indice del elemento siendo arrastrado

      // ─── Paso 2: Difusion ───
      requiereEval: 'si',
      requiereLectura: 'si',
      showTree: false,
      // Arbol de difusion (gerencias con sus areas) - se construye desde BD
      arbol: [],
      tiempoVigenciaAnos: null,  // se carga del tipo de documento (null = Indefinido)

      // ─── Paso 3: Firmas ───
      revisores: [],   // {id, username, nombre_completo}
      aprobadores: [],
      reemplaza: 'no',
      _reemplazoInput: '',
      _reemplazoResults: [],
      _reemplazoOpen: false,
      _reemplazoDebounce: null,
      chipsReemplazo: [],
      submitting: false,  // indica que se esta creando/firmando
      _validandoCaratula: false, // R3 item 0.3: evitar llamadas concurrentes

      // ─── Inicializacion async ───
      async init() {
        this.cargandoCatalogos = true
        try {
          // Cargar catalogos en paralelo
          const [tiposRes, gerRes, areasRes, usersRes, cfgRes] = await Promise.all([
            tiposDocumento.list(),
            gerenciasApi.list('', 1, 200),
            areasApi.list('', ''),
            usuariosApi.listActivos(''),
            configGlobal.list('ARCHIVOS'),
          ])
          if (tiposRes.ok) this.tiposList = tiposRes.data?.items || []
          if (gerRes.ok) this.gerenciasList = gerRes.data?.items || []
          if (areasRes.ok) this.areasAll = areasRes.data?.items || []
          if (usersRes.ok) {
            this.empleadosList = (usersRes.data?.items || []).map(u => ({
              id: u.id,
              username: u.username,
              nombre_completo: u.nombre_completo,
              cargo: u.cargo,
            }))
          }
          // Cargar SOLO usuarios con rol ETO (Sesion 24 / F1)
          // Se mantiene porque el paso 3 los usa como posibles
          // revisores/aprobadores. Issue 11.1 removio el dropdown del paso 1.
          const etosRes = await usuariosApi.listPorRol('ETO')
          if (etosRes.ok) {
            this.analistasEtoList = (etosRes.data?.items || []).map(u => ({
              id: u.id,
              username: u.username,
              nombre_completo: u.nombre_completo,
              ausente: u.ausente,
            }))
          }
          // F2: cargar usuarios con capacidad de revisar y aprobar
          // (revisor = ELABORADOR - REVISOR + ELABORADOR - REVISOR - APROBADOR + ETO)
          // (aprobador = ELABORADOR - REVISOR - APROBADOR + ETO)
          const [revRes, aprRes] = await Promise.all([
            usuariosApi.listPorCualquierRol([
              'ELABORADOR - REVISOR',
              'ELABORADOR - REVISOR - APROBADOR',
              'ETO',
            ]),
            usuariosApi.listPorCualquierRol([
              'ELABORADOR - REVISOR - APROBADOR',
              'ETO',
            ]),
          ])
          if (revRes.ok) {
            this.revisoresList = (revRes.data?.items || []).map(u => ({
              id: u.id,
              username: u.username,
              nombre_completo: u.nombre_completo,
            }))
          }
          if (aprRes.ok) {
            this.aprobadoresList = (aprRes.data?.items || []).map(u => ({
              id: u.id,
              username: u.username,
              nombre_completo: u.nombre_completo,
            }))
          }
          // Cargar limites de archivos desde configuracion_global (categoria=ARCHIVOS)
          if (cfgRes.ok && cfgRes.data?.items) {
            for (const cfg of cfgRes.data.items) {
              if (cfg.clave === 'max_tamano_archivo_mb') {
                const v = parseInt(cfg.valor, 10)
                if (!isNaN(v)) this._limitesArchivos.maxTamanoArchivoMb = v
              } else if (cfg.clave === 'max_archivos_por_solicitud') {
                const v = parseInt(cfg.valor, 10)
                if (!isNaN(v)) this._limitesArchivos.maxArchivosPorSolicitud = v
              }
            }
          }
          // Construir arbol de difusion desde gerencias + areas
          this.arbol = (this.gerenciasList || []).map(g => ({
            id: g.id,
            nombre: g.nombre + ' (' + g.sigla + ')',
            sigla: g.sigla,
            checked: false,
            indeterminate: false,
            subs: (this.areasAll || [])
              .filter(a => a.gerencia_id === g.id)
              .map(a => ({ id: a.id, nombre: a.nombre + ' (' + a.sigla + ')', sigla: a.sigla, checked: false })),
          }))
        } catch (e) {
          window.toast?.('Error al cargar catalogos: ' + (e?.message || e), 'error')
        } finally {
          this.cargandoCatalogos = false
        }

        // R3 item 0.3: validar caratula automaticamente al seleccionar archivo
        this.$watch('archivoPrincipal', async (file) => {
          if (!file || !file.name?.endsWith('.docx')) return
                if (!this.codigoAuto || this.codigoAuto === '---') return
          // Esperar 1.2s para asegurar que el usuario termino de seleccionar
          await new Promise(r => setTimeout(r, 1200))
          if (this.archivoPrincipal !== file) return // usuario cambió de archivo
          if (this._validandoCaratula) return
          this._validandoCaratula = true
          try {
            const codigo = (this.codigoAuto || '').split('/')[0]
            const res = await documentos.validarCaratula(
              file, codigo, this.versionAuto || '00', this.titulo,
            )
            if (res.ok && res.data) {
              if (res.data.coincide) {
                window.toast?.('✅ Caratula del documento verificada correctamente', 'success')
              } else if (res.data.warnings?.length > 0) {
                window.toast?.('⚠️ ' + res.data.warnings.join(' | '), 'warn')
              }
            }
          } catch (e) {
            // Silencio — error de validacion no debe molestar al usuario
          } finally {
            this._validandoCaratula = false
          }
        })
      },

      // ─── Computeds ───
      get areasList() {
        if (!this.gerencia) return []
        // Comparar con coercion numerica: el select devuelve string,
        // pero gerencia_id en BD es number. Sin coercion el filtro falla.
        const gerenciaId = Number(this.gerencia)
        return this.areasAll.filter(a => Number(a.gerencia_id) === gerenciaId)
      },

      get tipoSeleccionado() {
        return this.tiposList.find(t => String(t.id) === String(this.tipodoc))
      },

      get tiempoVigenciaLabel() {
        if (this.tiempoVigenciaAnos === null || this.tiempoVigenciaAnos === undefined) {
          return 'Indefinido'
        }
        return `${this.tiempoVigenciaAnos} anos`
      },

      // R3 item 0.1: nombre completo del documento
      // Formato: {codigo} {TITULO EN MAYUSCULAS} V{version}
      get nombreCompletoAuto() {
        if (!this.codigoAuto || this.codigoAuto === '---' || this.codigoAuto === 'Error al calcular') {
          return ''
        }
        const codigo = (this.codigoAuto || '').split('/')[0]
        const titulo = (this.titulo || '').trim().toUpperCase()
        const version = this.versionAuto || '00'
        if (!titulo) return `${codigo} V${version}`
        return `${codigo} ${titulo} V${version}`
      },

      // Issue 11.1: analistaEtoSeleccionadoAusente removido (ya no hay
      // campo Analista ETO en paso 1).

      // Cuando cambian tipodoc + area + tipoSolicitud, recalcular codigo
      async _recalcularCodigo() {
        if (!this.tipodoc || !this.area) {
          this.codigoAuto = '---'
          return
        }
        this.cargandoCodigo = true
        try {
          const res = await documentos.previewCodigo(this.tipodoc, this.area, this.tipoSolicitud || 'CREACION')
          if (res.ok) {
            this.codigoAuto = res.data.codigo_completo
            this.versionAuto = res.data.version
            // Leer tiempo_vigencia del tipo
            if (this.tipoSeleccionado) {
              if (this.tipoSeleccionado.indefinido) {
                this.tiempoVigenciaAnos = null
              } else {
                this.tiempoVigenciaAnos = this.tipoSeleccionado.periodo_vigencia
              }
            }
          } else {
            this.codigoAuto = 'Error al calcular'
            window.toast?.('No se pudo calcular el codigo', 'warn')
          }
        } catch (e) {
          this.codigoAuto = 'Error'
        } finally {
          this.cargandoCodigo = false
        }
      },

      // R3 item 0.2: cargar docs actualizables (filtrados por area+tipo)
      async _cargarDocsActualizables() {
        this.docsActualizables = []
        this.docActualizar = ''
        if (this.tipoSolicitud !== 'ACTUALIZACION' || !this.tipodoc || !this.area) return
        this.cargandoDocsActualizables = true
        try {
          const res = await documentos.listActualizables(this.area, this.tipodoc)
          if (res.ok) {
            this.docsActualizables = res.data || []
            if (this.docsActualizables.length === 0) {
              window.toast?.('No hay documentos APROBADOS previos para actualizar de este (area, tipo)', 'warn')
            }
          } else {
            window.toast?.('No se pudieron cargar los documentos actualizables', 'error')
          }
        } catch (e) {
          window.toast?.('Error: ' + (e?.message || e), 'error')
        } finally {
          this.cargandoDocsActualizables = false
        }
      },

      // R3 item 0.2: filtro de busqueda para docs actualizables
      get docsActualizablesFiltrados() {
        const q = (this.inputDocActualizar || '').toLowerCase().trim()
        if (!q) return this.docsActualizables
        return this.docsActualizables.filter(d =>
          (d.codigo_completo || '').toLowerCase().includes(q) ||
          (d.titulo || '').toLowerCase().includes(q)
        )
      },

      seleccionarDocActualizar(d) {
        this.docActualizar = d.id
        this.inputDocActualizar = d.codigo_completo + ' — ' + d.titulo
        this.mostrarDocsActualizables = false
        this.onDocActualizarChange()
      },

      // R3 item 0.2: al seleccionar un doc a actualizar, autocompletar campos
      onDocActualizarChange() {
        const d = this.docsActualizables.find(x => String(x.id) === String(this.docActualizar))
        if (d) {
          this.titulo = d.titulo
          // Reutilizar el codigo y version del doc anterior (version_anterior)
          // El backend calcula la version nueva = version_anterior + 1 al firmar.
          this.codigoAuto = d.codigo_completo
          this.versionAuto = this._incrementarVersion(d.version)
        }
      },

      _incrementarVersion(v) {
        const n = parseInt(v || '0', 10)
        if (isNaN(n)) return '01'
        return String(n + 1).padStart(2, '0')
      },

      // ─── Dropdowns custom (estilo searchable) ───
      dropdownOpen: { tipodoc: false, gerencia: false, area: false, solicitud: false, eval: false, lectura: false, reemplazo: false },

      _toggleDropdown(name) {
        this.dropdownOpen[name] = !this.dropdownOpen[name]
      },

      _selectDropdown(name, val) {
        if (name === 'tipodoc') {
          this.tipodoc = val
          this.dropdownOpen.tipodoc = false
          this.onTipodocChange()
        } else if (name === 'gerencia') {
          this.gerencia = val
          this.area = ''
          this.dropdownOpen.gerencia = false
          this.onAreaChange()
        } else if (name === 'area') {
          this.area = val
          this.dropdownOpen.area = false
          this.onAreaChange()
        } else if (name === 'solicitud') {
          this.tipoSolicitud = val
          this.dropdownOpen.solicitud = false
          this.onTipoSolicitudChange()
        } else if (name === 'eval') {
          this.requiereEval = val
          this.dropdownOpen.eval = false
        } else if (name === 'lectura') {
          this.requiereLectura = val
          this.dropdownOpen.lectura = false
        } else if (name === 'reemplazo') {
          this.reemplaza = val
          this.dropdownOpen.reemplazo = false
        }
      },

      _getDisplayVal(name) {
        if (name === 'tipodoc') {
          const t = this.tiposList.find(x => String(x.id) === String(this.tipodoc))
          return t ? `${t.nombre} (${t.codigo})` : 'Seleccionar...'
        } else if (name === 'gerencia') {
          const g = this.gerenciasList.find(x => String(x.id) === String(this.gerencia))
          return g ? `${g.sigla} - ${g.nombre}` : 'Seleccionar...'
        } else if (name === 'area') {
          const a = this.areasList.find(x => String(x.id) === String(this.area))
          return a ? `${a.sigla} - ${a.nombre}` : (!this.gerencia ? 'Seleccione una gerencia primero...' : 'Seleccionar...')
        } else if (name === 'solicitud') {
          const labels = { CREACION: 'Creacion de nuevo documento', ACTUALIZACION: 'Actualizacion de documento' }
          return labels[this.tipoSolicitud] || 'Seleccionar...'
        } else if (name === 'eval') {
          return this.requiereEval === 'si' ? 'Si' : 'No'
        } else if (name === 'lectura') {
          return this.requiereLectura === 'si' ? 'Si - firma de lectura obligatoria' : 'No'
        } else if (name === 'reemplazo') {
          return this.reemplaza === 'si' ? 'Si' : 'No'
        }
        return ''
      },

      _getDropdownOptions(name) {
        if (name === 'tipodoc') return this.tiposList.map(t => ({ id: t.id, label: `${t.nombre} (${t.codigo})` }))
        if (name === 'gerencia') return this.gerenciasList.map(g => ({ id: g.id, label: `${g.sigla} - ${g.nombre}` }))
        if (name === 'area') return this.areasList.map(a => ({ id: a.id, label: `${a.sigla} - ${a.nombre}` }))
        if (name === 'solicitud') return [
          { id: 'CREACION', label: 'Creacion de nuevo documento' },
          { id: 'ACTUALIZACION', label: 'Actualizacion de documento' },
        ]
        if (name === 'eval') return [
          { id: 'si', label: 'Si' },
          { id: 'no', label: 'No' },
        ]
        if (name === 'lectura') return [
          { id: 'si', label: 'Si - firma de lectura obligatoria' },
          { id: 'no', label: 'No' },
        ]
        if (name === 'reemplazo') return [
          { id: 'no', label: 'No' },
          { id: 'si', label: 'Si' },
        ]
        return []
      },

      // ─── Watchers implicitos via metodos ───
      // (Llamados desde el template con @change)
      async onTipodocChange() {
        await this._recalcularCodigo()
        await this._cargarDocsActualizables()
      },
      async onAreaChange() {
        await this._recalcularCodigo()
        await this._cargarDocsActualizables()
      },
      async onTipoSolicitudChange() {
        await this._recalcularCodigo()
        if (this.tipoSolicitud === 'ACTUALIZACION') {
          await this._cargarDocsActualizables()
        } else {
          this.docsActualizables = []
          this.docActualizar = ''
        }
      },

      // ─── Paso 1: drag&drop de archivos ───
      _nextFormId: 1,

      _sanitizarNombre(t) {
        return (t || '').toUpperCase().replace(/[^A-Z0-9ÁÉÍÓÚÑÜ\s]/g, '').trim().replace(/\s+/g, '_')
      },

      _getExtension(name) {
        const i = (name || '').lastIndexOf('.')
        return i > 0 ? name.slice(i) : ''
      },

      get formulariosConNombres() {
        const cod = (this.codigoAuto || '').split('/')[0]
        const ver = this.versionAuto || '00'
        if (!cod || cod === '---') return this.formulariosAsociados.map(f => ({ ...f, nombre_codificado: f.file.name }))
        return this.formulariosAsociados.map((f, i) => {
          const ext = this._getExtension(f.file.name)
          const tituloSanitizado = this._sanitizarNombre(f.titulo || '')
          const corr = String(i + 1).padStart(2, '0')
          const nombre = tituloSanitizado ? `${cod}-F${corr}_${tituloSanitizado}_V${ver}${ext}` : `${cod}-F${corr}_V${ver}${ext}`
          return { ...f, nombre_codificado: nombre, correlativo: corr }
        })
      },

      _extrayendoTitulos: 0,

      agregarFormularios(files) {
        const nuevos = Array.from(files)
        const pendientes = []
        nuevos.forEach(file => {
          const existe = this.formulariosAsociados.some(f => f.file.name === file.name && f.file.size === file.size)
          if (!existe) {
            const id = this._nextFormId++
            this.formulariosAsociados.push({ id, file, titulo: '', _extrayendo: true })
            pendientes.push({ id, file })
          }
        })
        // Extraer titulos de los archivos via API
        if (pendientes.length > 0) {
          this._extrayendoTitulos += pendientes.length
          pendientes.forEach(async ({ id, file }) => {
            try {
              const res = await documentos.extraerTituloFormulario(file)
              const idx = this.formulariosAsociados.findIndex(f => f.id === id)
              if (idx !== -1) {
                if (res.ok && res.data?.titulo) {
                  this.formulariosAsociados[idx].titulo = res.data.titulo
                } else {
                  // Fallback: extraer del nombre del archivo
                  const nameNoExt = file.name.replace(/\.[^.]+$/, '')
                  const sugerido = nameNoExt.replace(/[_-]/g, ' ').replace(/\s+/g, ' ').trim()
                  this.formulariosAsociados[idx].titulo = sugerido
                }
                this.formulariosAsociados[idx]._extrayendo = false
              }
            } catch (e) {
              const idx = this.formulariosAsociados.findIndex(f => f.id === id)
              if (idx !== -1) {
                const nameNoExt = file.name.replace(/\.[^.]+$/, '')
                this.formulariosAsociados[idx].titulo = nameNoExt.replace(/[_-]/g, ' ').replace(/\s+/g, ' ').trim()
                this.formulariosAsociados[idx]._extrayendo = false
              }
            } finally {
              this._extrayendoTitulos--
            }
          })
        }
      },

      removerFormulario(index) {
        this.formulariosAsociados.splice(index, 1)
      },

      actualizarTituloFormulario(idx, titulo) {
        if (this.formulariosAsociados[idx]) {
          this.formulariosAsociados[idx].titulo = titulo
        }
      },

      // Drag & drop reorder
      dragFormularioStart(idx) {
        this._dragIdx = idx
      },

      dragFormularioOver(idx) {
        if (this._dragIdx === null || this._dragIdx === idx) return
        const item = this.formulariosAsociados.splice(this._dragIdx, 1)[0]
        this.formulariosAsociados.splice(idx, 0, item)
        this._dragIdx = idx
      },

      dragFormularioEnd() {
        this._dragIdx = null
      },

      // ─── Paso 2: chips de difusion ───
      togglePadre(grupo) {
        grupo.checked = !grupo.checked
        grupo.indeterminate = false
        grupo.subs.forEach(s => s.checked = grupo.checked)
      },
      toggleHijo(grupo, hijo) {
        hijo.checked = !hijo.checked
        const todos = grupo.subs.every(s => s.checked)
        const algunos = grupo.subs.some(s => s.checked)
        grupo.checked = todos
        grupo.indeterminate = !todos && algunos
      },
      get chipsDifusion() {
        const chips = []
        this.arbol.forEach(g => {
          if (g.checked) {
            chips.push({ id: g.id, nombre: g.nombre, tipo: 'padre', ref: g })
          } else {
            g.subs.forEach(s => {
              if (s.checked) chips.push({ id: s.id, nombre: s.nombre, tipo: 'hijo', refPadre: g, refHijo: s })
            })
          }
        })
        return chips
      },
      removerChip(chip) {
        if (chip.tipo === 'padre') this.togglePadre(chip.ref)
        else this.toggleHijo(chip.refPadre, chip.refHijo)
      },

      // ─── Paso 3: revisores/aprobadores con searchable dropdown ───
      _addSearch: { revisor: '', aprobador: '' },
      _addSearchOpen: { revisor: false, aprobador: false },

      get _revisoresFiltrados() {
        const q = (this._addSearch.revisor || '').toLowerCase().trim()
        if (!q) return this.revisoresList
        return this.revisoresList.filter(u => (u.nombre_completo || '').toLowerCase().includes(q) || (u.username || '').toLowerCase().includes(q))
      },
      get _aprobadoresFiltrados() {
        const q = (this._addSearch.aprobador || '').toLowerCase().trim()
        if (!q) return this.aprobadoresList
        return this.aprobadoresList.filter(u => (u.nombre_completo || '').toLowerCase().includes(q) || (u.username || '').toLowerCase().includes(q))
      },

      addRevisor() {
        if (this.revisoresList.length === 0) return
        this._addSearchOpen.revisor = true
      },
      seleccionarRevisor(emp) {
        if (!this.revisores.some(r => r.user_id === emp.id)) {
          this.revisores.push({ id: Date.now() + Math.random(), user_id: emp.id, username: emp.username, nombre: emp.nombre_completo })
        }
        this._addSearch.revisor = ''
        this._addSearchOpen.revisor = false
      },
      addAprobador() {
        if (this.aprobadoresList.length === 0) return
        this._addSearchOpen.aprobador = true
      },
      seleccionarAprobador(emp) {
        if (!this.aprobadores.some(a => a.user_id === emp.id)) {
          this.aprobadores.push({ id: Date.now() + Math.random(), user_id: emp.id, username: emp.username, nombre: emp.nombre_completo })
        }
        this._addSearch.aprobador = ''
        this._addSearchOpen.aprobador = false
      },
      removerRevisor(idx) { this.revisores.splice(idx, 1) },
      removerAprobador(idx) { this.aprobadores.splice(idx, 1) },

      _onReemplazoInput() {
        const q = this._reemplazoInput.trim()
        if (this._reemplazoDebounce) clearTimeout(this._reemplazoDebounce)
        if (q.length < 2) {
          this._reemplazoResults = []
          this._reemplazoOpen = false
          return
        }
        this._reemplazoDebounce = setTimeout(async () => {
          try {
            const res = await documentos.buscar(q, 8)
            if (res.ok) {
              const items = (res.data?.items || []).filter(d => !this.chipsReemplazo.includes(d.codigo_completo))
              this._reemplazoResults = items
              this._reemplazoOpen = items.length > 0
            }
          } catch (_) { /* ignore */ }
        }, 300)
      },
      _seleccionarReemplazo(doc) {
        const cod = doc.codigo_completo
        if (!this.chipsReemplazo.includes(cod)) this.chipsReemplazo.push(cod)
        this._reemplazoInput = ''
        this._reemplazoResults = []
        this._reemplazoOpen = false
      },
      removeChipReemplazo(chip) {
        this.chipsReemplazo = this.chipsReemplazo.filter(c => c !== chip)
      },

      // ─── Navegacion entre pasos ───
      async nextPaso() {
        // Paso 1 -> 2: solo validar (NO crear documento, eso se hace al firmar)
        if (this.paso === 1) {
          if (!this.tipodoc || !this.gerencia || !this.area || !this.tipoSolicitud || !this.titulo.trim()) {
            window.toast?.('Complete todos los campos obligatorios del paso 1', 'warn')
            return
          }
          // Issue 11.1: validacion de Analista ETO removida (campo ya no existe).
          // Validar tamano y cantidad de archivos contra configuracion_global (A3)
          if (this._limitesArchivos) {
            const maxMB = this._limitesArchivos.maxTamanoArchivoMb || 20
            const maxCant = this._limitesArchivos.maxArchivosPorSolicitud || 20
            const total = (this.archivoPrincipal ? 1 : 0) + this.formulariosAsociados.length
            if (total > maxCant) {
              window.toast?.(`Excede el maximo de ${maxCant} archivos por solicitud (tiene ${total})`, 'warn')
              return
            }
            const allFiles = this.archivoPrincipal ? [this.archivoPrincipal, ...this.formulariosAsociados] : this.formulariosAsociados
            for (const f of allFiles) {
              const sizeMB = f.size / 1024 / 1024
              if (sizeMB > maxMB) {
                window.toast?.(`El archivo "${f.name}" (${sizeMB.toFixed(1)} MB) excede el maximo de ${maxMB} MB`, 'warn')
                return
              }
            }
          }
        }
        if (this.paso < 3) this.paso++
      },
      prevPaso() {
        if (this.paso > 1) this.paso--
      },

      // ─── Paso 3: Firma 2FA real via /enviar ───
      firmarEnviar() {
        if (this.revisores.length === 0) {
          window.toast?.('Debe agregar al menos 1 revisor', 'warn')
          return
        }
        if (this.aprobadores.length === 0) {
          window.toast?.('Debe agregar al menos 1 aprobador', 'warn')
          return
        }
        // Capturar el password via authModal (callback recibe {password, ...})
        window.authModal?.abrir({
          titulo: 'Firmar y enviar a Liberacion',
          icono: 'FIRMA',
          mensaje: 'Va a enviar la solicitud <strong>"' + (this.titulo || 'Nuevo Documento') + '"</strong> al flujo de Liberacion ETO. Esta accion requiere doble autenticacion.',
          onSuccess: async ({ password }) => {
            this.submitting = true
            try {
              // 1) Crear el documento en BD (recien al firmar, no antes)
              const resCreate = await documentos.create({
                gerencia_id: Number(this.gerencia),
                area_id: Number(this.area),
                tipo_documento_id: Number(this.tipodoc),
                titulo: this.titulo.trim(),
                comentarios_eto: null,
                tipo_solicitud: this.tipoSolicitud,
              })
              if (!resCreate.ok) {
                window.toast?.(resCreate.message || 'Error al crear documento', 'error')
                this.submitting = false
                return
              }
              this.documentoId = resCreate.data.documento.id
              this.flujoId = resCreate.data.flujo_id
              // Subir archivo principal
              if (this.archivoPrincipal) {
                await documentos.uploadArchivo(this.documentoId, this.archivoPrincipal, 'PRINCIPAL')
              }
              // Subir formularios
              for (const f of this.formulariosAsociados) {
                const upRes = await documentos.uploadArchivo(this.documentoId, f, 'FORMULARIO')
                if (upRes.ok && upRes.data?.formulario?.codigo_formulario) {
                  window.toast?.('✅ Formulario subido: ' + upRes.data.formulario.codigo_formulario, 'success')
                }
              }
              // 2) Enviar a liberacion con firma 2FA
              const res = await documentos.enviar(this.documentoId, {
                password: password || '',
                revisor_ids: this.revisores.map(r => r.user_id),
                aprobador_ids: this.aprobadores.map(a => a.user_id),
                requiere_evaluacion: this.requiereEval === 'si',
                requiere_control_lectura: this.requiereLectura === 'si',
                alcance_difusion_ids: this.chipsDifusion.map(c => c.id),
                reemplaza_documento_ids: this.chipsReemplazo.length ? this.chipsReemplazo : null,
                justificacion: this.justificacion || null,
                documento_actualizado_id: this.tipoSolicitud === 'ACTUALIZACION' && this.docActualizar
                  ? Number(this.docActualizar)
                  : null,
              })
              this.submitting = false
              if (res.ok) {
                window.toast?.('Solicitud enviada a ETO correctamente.', 'success')
                window.navigate?.('/bandeja')
              } else {
                window.toast?.(res.message || 'Error al enviar', 'error')
              }
            } catch (e) {
              this.submitting = false
              window.toast?.('Error inesperado: ' + (e?.message || e), 'error')
            }
          },
        })
      },

      // ─── Cancelar ───
      cancelar() {
        window.confirmCancelModal?.abrir({
          titulo: 'Cancelar Solicitud',
          mensaje: 'Esta seguro de cancelar? Perdera el progreso.',
          onConfirm: () => window.navigate('/bandeja'),
        })
      },
    }))
  },
  template: /* html */ `
<div x-data="wizardAprobacion" class="max-w-4xl mx-auto animate-fade-in-page">

  <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Aprobacion de Documento</h1>
      <p class="page-subtitle">Flujo completo de creacion o actualizacion documental</p>
    </div>
    <button @click="cancelar()" class="btn btn-danger text-xs">Cancelar solicitud</button>
  </div>

  <!-- Loading catalogos -->
  <div x-show="cargandoCatalogos" class="card-base text-center py-8 text-slate-500">
    <div class="text-sm">Cargando catalogos del sistema...</div>
  </div>

  <div x-show="!cargandoCatalogos">
  <!-- Stepper -->
  <div class="flex items-center mb-3 card-base overflow-x-auto gap-0">
    <template x-for="(s,i) in ['Datos y Carga de Archivo','Difusion y Evaluacion','Flujo y Firmas']" :key="i">
      <div class="flex items-center flex-1 min-w-0">
        <div class="flex items-center gap-2 whitespace-nowrap">
          <div class="w-[26px] h-[26px] rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0"
               :class="paso>i+1 ? 'bg-emerald-600 text-white' : paso===i+1 ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-400'"
               x-text="paso>i+1?'OK':i+1"></div>
          <span class="hidden md:inline text-[11px] font-semibold"
                :class="paso===i+1 ? 'text-brand-500' : paso>i+1 ? 'text-emerald-600' : 'text-slate-400'"
                x-text="s"></span>
        </div>
        <div x-show="i<2" class="flex-1 h-0.5 bg-slate-100 mx-2.5 min-w-[12px]"></div>
      </div>
    </template>
  </div>

  <div x-show="paso===1" class="card-base">
    <div class="section-header">1. Datos del documento y carga de archivo</div>

    <div class="form-grid-2 mb-5">
      <!-- Dropdown Tipo de documento -->
      <div class="relative">
        <label class="form-label">Tipo de documento *</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="tipodoc ? 'text-slate-800' : 'text-slate-400'"
             @click.stop="_toggleDropdown('tipodoc')">
          <span x-text="_getDisplayVal('tipodoc')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.tipodoc ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.tipodoc"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="dropdownOpen.tipodoc ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('tipodoc')" :key="o.id">
            <button @click="_selectDropdown('tipodoc', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="String(tipodoc) === String(o.id) ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.tipodoc" @click="dropdownOpen.tipodoc=false" class="fixed inset-0 z-10"></div>
      </div>

      <!-- Dropdown Gerencia -->
      <div class="relative">
        <label class="form-label">Gerencia responsable *</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="gerencia ? 'text-slate-800' : 'text-slate-400'"
             @click.stop="_toggleDropdown('gerencia')">
          <span x-text="_getDisplayVal('gerencia')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.gerencia ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.gerencia"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="dropdownOpen.gerencia ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('gerencia')" :key="o.id">
            <button @click="_selectDropdown('gerencia', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="String(gerencia) === String(o.id) ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.gerencia" @click="dropdownOpen.gerencia=false" class="fixed inset-0 z-10"></div>
      </div>

      <!-- Dropdown Area -->
      <div class="relative">
        <label class="form-label">Area responsable *</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="!gerencia ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : (area ? 'text-slate-800' : 'text-slate-400')"
             @click.stop="gerencia ? _toggleDropdown('area') : null">
          <span x-text="_getDisplayVal('area')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.area ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.area"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="dropdownOpen.area ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('area')" :key="o.id">
            <button @click="_selectDropdown('area', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="String(area) === String(o.id) ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.area" @click="dropdownOpen.area=false" class="fixed inset-0 z-10"></div>
      </div>

      <!-- Dropdown Tipo de solicitud -->
      <div class="relative">
        <label class="form-label">Tipo de solicitud *</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="tipoSolicitud ? 'text-slate-800' : 'text-slate-400'"
             @click.stop="_toggleDropdown('solicitud')">
          <span x-text="_getDisplayVal('solicitud')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.solicitud ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.solicitud"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="dropdownOpen.solicitud ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('solicitud')" :key="o.id">
            <button @click="_selectDropdown('solicitud', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="tipoSolicitud === o.id ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.solicitud" @click="dropdownOpen.solicitud=false" class="fixed inset-0 z-10"></div>
      </div>
      <!-- R3 item 0.2: selector de documento a actualizar (searchable) -->
      <div class="sm:col-span-2 relative" x-show="tipoSolicitud === 'ACTUALIZACION'">
        <label class="form-label">Documento a actualizar *</label>
        <input type="text" class="form-input text-xs" x-model="inputDocActualizar"
               placeholder="Buscar documento por codigo o titulo..."
               @focus="mostrarDocsActualizables=true"
               @input="mostrarDocsActualizables=true"
               :disabled="!tipodoc || !area || cargandoDocsActualizables"
               @click.stop>
        <div x-show="mostrarDocsActualizables && docsActualizablesFiltrados.length > 0"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="(mostrarDocsActualizables && docsActualizablesFiltrados.length > 0) ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="d in docsActualizablesFiltrados" :key="d.id">
            <button @click="seleccionarDocActualizar(d)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors">
              <div class="text-[11px] font-semibold text-slate-800 truncate" x-text="d.codigo_completo"></div>
              <div class="text-[10px] text-slate-500 truncate" x-text="d.titulo"></div>
            </button>
          </template>
        </div>
        <div x-show="mostrarDocsActualizables && docsActualizablesFiltrados.length === 0 && inputDocActualizar"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-center text-[11px] text-slate-500"
             style="display:none"
             :style="(mostrarDocsActualizables && docsActualizablesFiltrados.length === 0 && inputDocActualizar) ? 'display:block' : 'display:none'">
          Sin resultados.
        </div>
        <span class="form-hint" x-show="docActualizar">
          Version nueva: <span class="font-mono font-semibold" x-text="(docsActualizables.find(x => String(x.id) === String(docActualizar))?.version || '00')"></span> + 1. Campos autocompletados.
        </span>
        <!-- Cerrar dropdown al hacer click fuera -->
        <div x-show="mostrarDocsActualizables" @click="mostrarDocsActualizables=false" class="fixed inset-0 z-10"></div>
      </div>
      <div>
        <label class="form-label">Codigo (automatico)</label>
        <input type="text" :value="codigoAuto" class="form-input bg-slate-50 text-slate-400 font-mono text-xs" readonly>
      </div>
      <div>
        <label class="form-label">Version (automatico)</label>
        <input type="text" :value="versionAuto" class="form-input bg-slate-50 text-slate-400 text-xs" readonly>
      </div>
      <div class="sm:col-span-2" x-show="codigoAuto && codigoAuto !== '---' && codigoAuto !== 'Error al calcular' && titulo.trim()">
        <label class="form-label">Nombre completo del documento</label>
        <input type="text" :value="nombreCompletoAuto" class="form-input bg-slate-50 text-slate-700 text-xs font-semibold" readonly>
        <span class="form-hint">Formato: <span class="font-mono">CODIGO TITULO VXX</span> — usado como nombre del archivo .docx y en bandejas/listas.</span>
      </div>
      <div class="sm:col-span-2">
        <label class="form-label">Titulo del documento *</label>
        <input type="text" class="form-input text-xs" x-model="titulo" placeholder="Ej.: Procedimiento de Control de Documentos del SIG">
      </div>
      <!-- Sesion 23 / Bloque A6: campos read-only del solicitante -->
      <div>
        <label class="form-label">Nombre del solicitante</label>
        <input type="text" :value="$store.auth?.user?.nombre_completo || ''" class="form-input bg-slate-50 text-slate-500 text-xs cursor-not-allowed" readonly tabindex="-1">
      </div>
      <div>
        <label class="form-label">Cargo</label>
        <input type="text" :value="$store.auth?.user?.cargo || ''" class="form-input bg-slate-50 text-slate-500 text-xs cursor-not-allowed" readonly tabindex="-1">
      </div>
      <div>
        <label class="form-label">Fecha</label>
        <input type="text" :value="new Date().toLocaleDateString('es-BO', { year: 'numeric', month: '2-digit', day: '2-digit' })" class="form-input bg-slate-50 text-slate-500 text-xs cursor-not-allowed" readonly tabindex="-1">
      </div>
      <div class="sm:col-span-2">
        <label class="form-label">Justificacion / motivo de la solicitud</label>
        <textarea class="form-input text-xs resize-y" rows="3" x-model="justificacion" placeholder="Describa el motivo de creacion o actualizacion del documento..."></textarea>
      </div>
      <!-- Issue 11.1: campo "Analista ETO asignado" removido del paso 1.
           El cliente decidio que el solicitante no deberia ver esto. -->
    </div>

    <div class="pt-4 border-t border-slate-100">
      <div class="text-[11px] font-bold text-slate-800 mb-3 uppercase tracking-wider">Carga del documento elaborado</div>

      <div class="mb-5">
        <label class="form-label">Documento principal (.docx)</label>
        <div class="border-2 border-dashed rounded-xl p-7 text-center cursor-pointer transition-all duration-150"
             :class="archivoPrincipal ? 'border-emerald-300 bg-emerald-50' : dropPrincipal ? 'border-brand-500 bg-blue-50' : 'border-blue-200 bg-slate-50'"
             @dragover.prevent="dropPrincipal=true"
             @dragleave="dropPrincipal=false"
             @drop.prevent="archivoPrincipal=$event.dataTransfer.files[0];dropPrincipal=false"
             @click="document.querySelector('[x-ref=filePrincipal]')?.click()">
          <template x-if="archivoPrincipal">
            <div>
              <div class="text-2xl mb-1.5">DOC</div>
              <div class="text-xs font-semibold text-emerald-700" x-text="archivoPrincipal.name"></div>
              <div class="text-[10.5px] text-slate-500 mt-0.5" x-text="(archivoPrincipal.size/1024/1024).toFixed(2) + ' MB - click para cambiar'"></div>
            </div>
          </template>
          <template x-if="!archivoPrincipal">
            <div>
              <div class="text-[32px] mb-2">DOC</div>
              <div class="text-xs font-semibold text-brand-600">Cargar documento principal</div>
              <div class="text-[11px] text-slate-400 mt-1">Arrastre su archivo .docx aqui o haga click para seleccionar</div>
            </div>
          </template>
        </div>
        <input type="file" x-ref="filePrincipal" accept=".docx" class="hidden" @change="archivoPrincipal=$event.target.files[0]">
      </div>

      <div class="mb-2">
        <label class="form-label">Formularios asociados y adjuntos adicionales <span class="text-slate-400 font-normal" x-text="'(' + formulariosConNombres.length + ' archivos)'"></span></label>
        <div class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-150 mb-3"
             :class="dropFormularios ? 'border-brand-500 bg-blue-50' : 'border-slate-200 bg-slate-50/50'"
             @dragover.prevent="dropFormularios=true"
             @dragleave="dropFormularios=false"
             @drop.prevent="agregarFormularios($event.dataTransfer.files); dropFormularios=false"
             @click="document.querySelector('[x-ref=fileFormularios]')?.click()">
          <div class="flex flex-col items-center">
            <div class="text-2xl mb-1">DOCS</div>
            <div class="text-[11.5px] font-semibold text-slate-600">Anadir archivos adicionales</div>
            <div class="text-[10px] text-slate-400 mt-0.5 uppercase">PDF, WORD, EXCEL, PPT, DWG, IMAGENES</div>
          </div>
        </div>
        <input type="file" x-ref="fileFormularios" multiple class="hidden"
               accept=".docx,.doc,.xlsx,.xls,.pdf,.pptx,.ppt,.dwg,.png,.jpg,.jpeg"
               @change="agregarFormularios($event.target.files)">

        <!-- Lista de formularios con drag-reorder y titulo editable -->
        <div class="space-y-2" x-show="formulariosConNombres.length > 0">
          <template x-for="(f, idx) in formulariosConNombres" :key="f.id">
            <div class="bg-white border border-slate-200 rounded-lg shadow-sm"
                 :class="{ 'border-brand-400 ring-2 ring-brand-200': _dragIdx === idx }"
                 draggable="true"
                 @dragstart="dragFormularioStart(idx)"
                 @dragover.prevent="dragFormularioOver(idx)"
                 @dragend="dragFormularioEnd()">
              <div class="flex items-start gap-2 p-2.5">
                <!-- Drag handle -->
                <div class="mt-1 text-slate-300 hover:text-slate-500 cursor-grab active:cursor-grabbing select-none text-sm" title="Arrastrar para reordenar">⠿</div>
                <!-- Icono -->
                <div class="w-8 h-8 rounded bg-slate-100 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">DOCS</div>
                <!-- Contenido -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] font-bold text-brand-600 bg-brand-50 px-1.5 py-0.5 rounded font-mono shrink-0" x-show="codigoAuto && codigoAuto !== '---'" x-text="codigoAuto.split('/')[0] + '-F' + f.correlativo"></span>
                    <span x-show="!codigoAuto || codigoAuto === '---'" class="text-[10px] font-bold text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded font-mono shrink-0" x-text="'--F' + f.correlativo"></span>
                    <span x-show="f._extrayendo" class="w-3 h-3 border-2 border-brand-500 border-t-transparent rounded-full animate-spin shrink-0"></span>
                    <span class="text-[10px] text-slate-400 font-mono shrink-0" x-text="'V' + (versionAuto || '00')"></span>
                    <span class="text-[10px] text-slate-400 truncate" x-text="f.file.name"></span>
                    <span class="text-[10px] text-slate-300 ml-auto shrink-0" x-text="(f.file.size/1024).toFixed(0) + 'KB'"></span>
                  </div>
                  <div class="mt-1.5 flex items-center gap-2">
                    <input type="text" class="form-input text-[11px] py-1 flex-1 min-w-0"
                           :value="f.titulo"
                           @input="actualizarTituloFormulario(idx, $event.target.value)"
                           placeholder="Escriba el nombre del formulario...">
                    <button @click="removerFormulario(idx)" class="text-red-400 hover:text-red-600 text-sm shrink-0 px-1 cursor-pointer" title="Eliminar formulario">✕</button>
                  </div>
                  <div x-show="f.titulo" class="mt-1">
                    <span class="text-[9.5px] font-mono text-slate-500 bg-slate-50 px-1.5 py-0.5 rounded truncate block" x-text="f.nombre_codificado"></span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>

  <div x-show="paso===2" class="card-base">
    <div class="section-header">2. Difusion y evaluacion</div>
    <div class="form-grid-2 mb-5">
      <div>
        <label class="form-label">Tiempo de vigencia</label>
        <input type="text" :value="tiempoVigenciaLabel" class="form-input bg-slate-50 text-slate-400 text-xs" readonly>
      </div>
      <!-- Dropdown Requiere evaluacion -->
      <div class="relative">
        <label class="form-label">Requiere evaluacion</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="requiereEval ? 'text-slate-800' : 'text-slate-400'"
             @click.stop="_toggleDropdown('eval')">
          <span x-text="_getDisplayVal('eval')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.eval ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.eval"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
             style="display:none" :style="dropdownOpen.eval ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('eval')" :key="o.id">
            <button @click="_selectDropdown('eval', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="requiereEval === o.id ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.eval" @click="dropdownOpen.eval=false" class="fixed inset-0 z-10"></div>
      </div>
      <!-- Dropdown Requiere control de lectura -->
      <div class="sm:col-span-2 relative">
        <label class="form-label">Requiere control de lectura</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="requiereLectura ? 'text-slate-800' : 'text-slate-400'"
             @click.stop="_toggleDropdown('lectura')">
          <span x-text="_getDisplayVal('lectura')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.lectura ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.lectura"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
             style="display:none" :style="dropdownOpen.lectura ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('lectura')" :key="o.id">
            <button @click="_selectDropdown('lectura', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="requiereLectura === o.id ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.lectura" @click="dropdownOpen.lectura=false" class="fixed inset-0 z-10"></div>
      </div>
    </div>

    <div>
      <label class="form-label">Alcance de difusion (Gerencias / Areas) *</label>
      <div class="relative" @click.outside="showTree=false">
        <div @click="showTree=!showTree" class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="chipsDifusion.length ? 'text-slate-800' : 'text-slate-400'">
          <span x-text="chipsDifusion.length ? chipsDifusion.length + ' grupo(s) seleccionado(s)' : 'Seleccionar grupos...'"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="showTree ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="showTree" @click.stop class="absolute z-[100] left-0 w-full top-[calc(100%+4px)] bg-white border border-slate-200 rounded-lg shadow-xl p-3 max-h-[300px] overflow-y-auto">
          <div class="text-[10px] text-slate-400 mb-2.5 pb-2 border-b border-slate-100">Marcar una Gerencia selecciona todas sus areas automaticamente</div>
          <template x-for="grupo in arbol" :key="grupo.id">
            <div class="mb-2.5">
              <label class="flex items-center gap-2 cursor-pointer px-1.5 py-1 rounded-md text-[11px] font-semibold text-slate-700 hover:bg-slate-50 select-none" @click.stop="togglePadre(grupo)">
                <span class="w-[15px] h-[15px] rounded-[3px] border-2 flex items-center justify-center text-[9px] font-bold transition-all duration-100 shrink-0"
                      :class="grupo.checked ? 'bg-brand-500 border-brand-500 text-white' : (grupo.indeterminate ? 'bg-brand-100 border-brand-300 text-brand-600' : 'bg-white border-slate-300 hover:border-brand-400')">
                  <span x-show="grupo.checked">✓</span>
                  <span x-show="!grupo.checked && grupo.indeterminate">−</span>
                </span>
                <span x-text="grupo.nombre"></span>
              </label>
              <div class="ml-7 mt-0.5">
                <template x-for="hijo in grupo.subs" :key="hijo.id">
                  <label class="flex items-center gap-2 cursor-pointer px-1.5 py-0.5 rounded-md text-[11px] text-slate-600 hover:bg-slate-50 select-none" @click.stop="toggleHijo(grupo, hijo)">
                    <span class="w-[15px] h-[15px] rounded-[3px] border-2 flex items-center justify-center text-[9px] font-bold transition-all duration-100 shrink-0"
                          :class="hijo.checked ? 'bg-brand-500 border-brand-500 text-white' : 'bg-white border-slate-300 hover:border-brand-400'">
                      <span x-show="hijo.checked">✓</span>
                    </span>
                    <span x-text="hijo.nombre"></span>
                  </label>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div class="flex flex-wrap gap-1.5 mt-2.5 px-2.5 py-2 bg-slate-50 rounded-lg border border-slate-200 min-h-[42px] items-center">
        <template x-if="chipsDifusion.length===0">
          <span class="text-[11px] text-slate-300">Ningun grupo seleccionado aun...</span>
        </template>
        <template x-for="chip in chipsDifusion" :key="chip.id">
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span x-text="chip.nombre"></span>
            <button type="button" @click="removerChip(chip)" class="text-red-600 cursor-pointer bg-transparent border-0 p-0 leading-none text-[13px]">X</button>
          </span>
        </template>
      </div>
    </div>
  </div>

  <div x-show="paso===3" class="card-base">
    <div class="section-header">3. Flujo y firmas</div>

    <!-- Revisores con searchable dropdown -->
    <div>
      <label class="form-label">Revisores asignados (Minimo 1)</label>
      <div class="flex flex-col gap-1.5">
        <template x-for="(r,i) in revisores" :key="r.id">
          <div class="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
            <div class="flex-1 min-w-0">
              <div class="text-[12px] font-semibold text-slate-800 truncate" x-text="r.nombre"></div>
              <div class="text-[10px] text-slate-500 font-mono" x-text="'@' + r.username"></div>
            </div>
            <button @click="removerRevisor(i)" class="text-red-400 hover:text-red-600 text-sm cursor-pointer shrink-0" title="Quitar revisor">✕</button>
          </div>
        </template>
      </div>
      <div class="relative mt-2">
        <div class="flex items-center gap-2">
          <input type="text" class="form-input text-xs flex-1" x-model="_addSearch.revisor"
                 placeholder="Buscar revisor por nombre..."
                 @focus="_addSearchOpen.revisor=true"
                 @input="_addSearchOpen.revisor=true"
                 @click.stop>
          <button @click="addRevisor()" class="btn btn-sm text-brand-600 border-brand-500 text-[11px] shrink-0">Buscar</button>
        </div>
        <div x-show="_addSearchOpen.revisor && _revisoresFiltrados.length > 0"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="(_addSearchOpen.revisor && _revisoresFiltrados.length > 0) ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="emp in _revisoresFiltrados" :key="emp.id">
            <button @click="seleccionarRevisor(emp)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors">
              <div class="text-[11px] font-semibold text-slate-800" x-text="emp.nombre_completo"></div>
              <div class="text-[10px] text-slate-500 font-mono" x-text="'@' + emp.username"></div>
            </button>
          </template>
        </div>
        <div x-show="_addSearchOpen.revisor && _revisoresFiltrados.length === 0 && _addSearch.revisor"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-center text-[11px] text-slate-500"
             style="display:none"
             :style="(_addSearchOpen.revisor && _revisoresFiltrados.length === 0 && _addSearch.revisor) ? 'display:block' : 'display:none'">
          Sin resultados.
        </div>
        <div x-show="_addSearchOpen.revisor" @click="_addSearchOpen.revisor=false" class="fixed inset-0 z-10"></div>
      </div>
    </div>

    <!-- Aprobadores con searchable dropdown -->
    <div class="mt-4">
      <label class="form-label">Aprobadores asignados (Minimo 1)</label>
      <div class="flex flex-col gap-1.5">
        <template x-for="(a,i) in aprobadores" :key="a.id">
          <div class="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
            <div class="flex-1 min-w-0">
              <div class="text-[12px] font-semibold text-slate-800 truncate" x-text="a.nombre"></div>
              <div class="text-[10px] text-slate-500 font-mono" x-text="'@' + a.username"></div>
            </div>
            <button @click="removerAprobador(i)" class="text-red-400 hover:text-red-600 text-sm cursor-pointer shrink-0" title="Quitar aprobador">✕</button>
          </div>
        </template>
      </div>
      <div class="relative mt-2">
        <div class="flex items-center gap-2">
          <input type="text" class="form-input text-xs flex-1" x-model="_addSearch.aprobador"
                 placeholder="Buscar aprobador por nombre..."
                 @focus="_addSearchOpen.aprobador=true"
                 @input="_addSearchOpen.aprobador=true"
                 @click.stop>
          <button @click="addAprobador()" class="btn btn-sm text-brand-600 border-brand-500 text-[11px] shrink-0">Buscar</button>
        </div>
        <div x-show="_addSearchOpen.aprobador && _aprobadoresFiltrados.length > 0"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
             style="display:none"
             :style="(_addSearchOpen.aprobador && _aprobadoresFiltrados.length > 0) ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="emp in _aprobadoresFiltrados" :key="emp.id">
            <button @click="seleccionarAprobador(emp)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors">
              <div class="text-[11px] font-semibold text-slate-800" x-text="emp.nombre_completo"></div>
              <div class="text-[10px] text-slate-500 font-mono" x-text="'@' + emp.username"></div>
            </button>
          </template>
        </div>
        <div x-show="_addSearchOpen.aprobador && _aprobadoresFiltrados.length === 0 && _addSearch.aprobador"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-center text-[11px] text-slate-500"
             style="display:none"
             :style="(_addSearchOpen.aprobador && _aprobadoresFiltrados.length === 0 && _addSearch.aprobador) ? 'display:block' : 'display:none'">
          Sin resultados.
        </div>
        <div x-show="_addSearchOpen.aprobador" @click="_addSearchOpen.aprobador=false" class="fixed inset-0 z-10"></div>
      </div>
    </div>

    <!-- Issue 11.2: UI para "Reemplazo o baja de documento" -->
    <div class="mt-4">
      <div class="relative">
        <label class="form-label">Reemplazo o baja de documento</label>
        <div class="form-input text-xs flex items-center justify-between cursor-pointer select-none"
             :class="reemplaza ? 'text-slate-800' : 'text-slate-400'"
             @click.stop="_toggleDropdown('reemplazo')">
          <span x-text="_getDisplayVal('reemplazo')"></span>
          <span class="text-slate-300 text-[10px] transition-transform" :class="dropdownOpen.reemplazo ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="dropdownOpen.reemplazo"
             x-transition:enter="transition ease-out duration-100"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
             style="display:none" :style="dropdownOpen.reemplazo ? 'display:block' : 'display:none'"
             @click.stop>
          <template x-for="o in _getDropdownOptions('reemplazo')" :key="o.id">
            <button @click="_selectDropdown('reemplazo', o.id)" type="button"
                    class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]"
                    :class="reemplaza === o.id ? 'bg-blue-50 font-semibold text-brand-700' : 'text-slate-700'">
              <span x-text="o.label"></span>
            </button>
          </template>
        </div>
        <div x-show="dropdownOpen.reemplazo" @click="dropdownOpen.reemplazo=false" class="fixed inset-0 z-10"></div>
      </div>
      <div x-show="reemplaza==='si'" class="mt-2">
        <label class="form-label">Codigos de documentos a dar de baja</label>
        <div class="relative">
          <input type="text" x-model="_reemplazoInput" @input="_onReemplazoInput()"
                 @keydown.enter.prevent="_seleccionarReemplazo({codigo_completo: _reemplazoInput.trim().toUpperCase()})"
                 @focus="if(_reemplazoResults.length>0) _reemplazoOpen=true"
                 class="form-input text-xs w-full font-mono" placeholder="Escriba el codigo para buscar... CC-3-005/00"
                 autocomplete="off" autocorrect="off" spellcheck="false">
          <div x-show="_reemplazoOpen && _reemplazoResults.length > 0"
               x-transition:enter="transition ease-out duration-100"
               x-transition:enter-start="opacity-0 -translate-y-1"
               x-transition:enter-end="opacity-100 translate-y-0"
               class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[260px] overflow-y-auto"
               style="display:none"
               :style="(_reemplazoOpen && _reemplazoResults.length > 0) ? 'display:block' : 'display:none'"
               @click.stop>
            <template x-for="doc in _reemplazoResults" :key="doc.id">
              <button @click="_seleccionarReemplazo(doc)" type="button"
                      class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors">
                <div class="text-[11px] font-semibold text-slate-800 font-mono" x-text="doc.codigo_completo + ' — ' + (doc.titulo || '')"></div>
                <div class="text-[10px] text-slate-500" x-text="(doc.gerencia?.sigla || '') + ' / ' + (doc.area?.sigla || '') + ' · ' + (doc.tipo?.nombre || '')"></div>
              </button>
            </template>
          </div>
          <div x-show="_reemplazoOpen && _reemplazoResults.length === 0 && _reemplazoInput.trim().length >= 2"
               class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-center text-[11px] text-slate-500"
               style="display:none"
               :style="(_reemplazoOpen && _reemplazoResults.length === 0 && _reemplazoInput.trim().length >= 2) ? 'display:block' : 'display:none'">
            Sin resultados.
          </div>
          <div x-show="_reemplazoOpen" @click="_reemplazoOpen=false" class="fixed inset-0 z-10"></div>
        </div>
        <div class="flex flex-wrap gap-1.5 mt-2">
          <template x-for="chip in chipsReemplazo" :key="chip">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-amber-50 text-amber-700 border border-amber-200">
              <span x-text="chip"></span>
              <button @click="removeChipReemplazo(chip)" class="text-red-600 hover:text-red-800 text-[13px] cursor-pointer leading-none">✕</button>
            </span>
          </template>
          <span x-show="chipsReemplazo.length===0" class="text-[11px] text-slate-400 italic self-center">Sin codigos agregados</span>
        </div>
      </div>
    </div>

    <div class="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3.5 flex items-center justify-between flex-wrap gap-2.5 mt-4">
      <div>
        <div class="text-[11px] font-bold text-emerald-700">Firma Digital Requerida</div>
        <div class="text-[11px] text-emerald-600 mt-0.5">Se solicitara doble autenticacion para enviar al flujo de Liberacion</div>
      </div>
      <button @click="firmarEnviar()" :disabled="submitting" class="btn btn-primary whitespace-nowrap">
        <span x-text="submitting ? 'Enviando...' : 'Firmar y Enviar a Liberacion'"></span>
      </button>
    </div>
  </div>

  <div class="flex justify-between items-center mt-3.5 flex-wrap gap-2">
    <button x-show="paso>1" class="btn" @click="prevPaso()">Anterior</button>
    <div class="flex-1"></div>
    <div x-show="paso<3" class="flex items-center gap-2.5">
      <span class="text-[11px] text-slate-400">El documento se persistira al firmar (paso 3)</span>
      <button class="btn btn-primary" @click="nextPaso()" :disabled="submitting">
        <span x-text="submitting ? 'Creando...' : 'Siguiente'"></span>
      </button>
    </div>
  </div>
  </div>

</div>`
}
