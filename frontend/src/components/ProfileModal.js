/**
 * src/components/ProfileModal.js
 * Modal "Mi Perfil" + Delegación + Ausencias
 *
 * Sesion 9: lee la info del backend (rol, delegado, ausente, estado)
 * en vez del mock legacy `data/users.js`.
 */
import { apiGet, apiPatch, apiPost, apiDelete } from '../utils/api.js'
import { usuarios } from '../services/parametrizacionApi.js'

export function initProfileModal() {
  window.Alpine?.data('profileModalData', () => ({
    open: false,
    delegarOpen: false,
    loading: false,
    saving: false,

    // Datos del usuario (leidos del backend)
    username: '',
    nombre: '',
    cargo: '',
    area: '',
    iniciales: '',
    rolPrincipal: '',
    rolRequiereDelegado: false,
    estado: '',
    ausente: false,
    estadoDelegacion: '',

    // Delegado actual
    delegadoId: null,
    delegadoNombre: '',
    delegadoUsername: '',
    delegadoAlerta: false,

    // Picker de delegado
    inputDelegado: '',
    usuariosActivos: [],
    mostrarListaDelegado: false,
    delegarNombre: '',
    delegarCargo: '',

    // Fechas ausencia
    fechaInicio: '',
    fechaFin: '',
    observaciones: '',
    ausencias: [],  // historial de ausencias (Sesion 23 / Bloque B1)
    ausenciaVigenteId: null,
    ausenciaMotivo: 'vacaciones',

    async abrir() {
      this.loading = true
      this.open = true
      this.inputDelegado = ''
      this.mostrarListaDelegado = false
      try {
        // Issue 2.1: las 5 requests se hacen en PARALELO con Promise.all
        // (antes eran en serie, ~5 round-trips). El orden de procesamiento
        // es independiente: el state se setea a partir de cada response.
        // Solo /me debe completarse ANTES de las otras para tener username
        // (necesario para filtrar usuariosActivos por username).
        const resMe = await apiGet('/me')
        if (resMe.ok && resMe.data.authenticated && resMe.data.user) {
          const u = resMe.data.user
          this.username = u.username
          this.nombre = u.nombre_completo || 'Usuario'
          this.iniciales = u.iniciales || '??'
          this.cargo = u.cargo || 'Sin cargo'
          // Sesion 26: la logica ahora discrimina entre usuarios AD y locales.
          // - AD users (es_usuario_ad=true): SI O SI mostrar el department del AD
          //   (ad_department o fallback a ad_info), porque siempre nos loguearemos
          //   con nuestros usuarios del AD. Los usuarios locales que creamos son
          //   solo para hacer pruebas.
          // - Usuarios NO AD: mostrar gerencia/area (con fallback a ad_info si estan vacios).
          if (u.es_usuario_ad) {
            this.area = (u.ad_department || u.ad_info || 'Sin área (AD)').split('|')[0].trim()
          } else {
            this.area = (u.gerencia_sigla && u.area_sigla)
              ? `${u.gerencia_sigla} / ${u.area_sigla}`
              : (u.gerencia_sigla || u.area_sigla || u.ad_info || 'Sin área')
          }
          this.estado = u.estado || ''
          this.ausente = !!u.ausente
          this.rolPrincipal = (u.roles && u.roles[0]) || ''
          this.estadoDelegacion = ''
        }

        // 4 requests en paralelo: usuarios (mi info), roles, delegados, ausencias
        // (ausencias requiere miId, lo resolvemos al final con la primera response)
        const username = this.username
        const requests = [
          // 1) mi info completa (incluye delegado)
          username ? apiGet(`/usuarios?q=${encodeURIComponent(username)}&page_size=5`) : Promise.resolve({ ok: false }),
          // 2) roles (saber si requiere delegado)
          apiGet('/roles'),
          // 3) lista de usuarios elegibles como delegado
          usuarios.listPorCualquierRol(
            ['ELABORADOR - REVISOR', 'ELABORADOR - REVISOR - APROBADOR', 'ETO'],
            '',
          ).catch(() => ({ ok: false, data: { items: [] } })),
        ]

        const [resList, resRoles, resDelegados] = await Promise.all(requests)

        // Procesar response 1: mi info
        let miId = null
        if (resList.ok && resList.data.items) {
          const me = resList.data.items.find(x => x.username === this.username)
          if (me) {
            miId = me.id
            this.delegadoId = me.delegado_id || null
            this.delegadoNombre = me.delegado_nombre || ''
            this.delegadoUsername = me.delegado_username || ''
            this.estadoDelegacion = me.estado_delegacion || ''
          }
        }

        // Procesar response 2: roles
        if (resRoles.ok) {
          const rol = (resRoles.data.items || []).find(r => r.codigo === this.rolPrincipal)
          this.rolRequiereDelegado = rol ? !!rol.requiere_delegado : false
        }
        // delegated alerta depende de rolRequiereDelegado (calculado arriba) y delegadoId
        this.delegadoAlerta = (this.rolRequiereDelegado && !this.delegadoId)

        // Procesar response 3: usuarios elegibles delegado
        if (resDelegados.ok) {
          this.usuariosActivos = (resDelegados.data.items || []).filter(u => u.username !== this.username)
        } else {
          // Fallback al metodo anterior si el helper falla
          const resActivos = await apiGet('/usuarios?estado=activo&page_size=500')
          if (resActivos.ok) {
            this.usuariosActivos = (resActivos.data.items || []).filter(u => u.username !== this.username)
          }
        }

        // 4) Sesion 23 / Bloque B1: cargar ausencias (necesita miId, asi que
        // espera a la primera response)
        if (miId) {
          await this._cargarAusencias(miId)
        }
      } catch (e) {
        console.error('[ProfileModal] abrir error:', e)
      } finally {
        this.loading = false
      }
    },

    async _cargarAusencias(usuarioId) {
      try {
        const res = await apiGet(`/ausencias?usuario_id=${usuarioId}`)
        if (res.ok) {
          this.ausencias = res.data.items || []
          // Si hay una vigente, pre-llenar el formulario con sus fechas
          const vigente = this.ausencias.find(a => a.esta_vigente)
          if (vigente) {
            this.ausente = true
            this.fechaInicio = vigente.fecha_desde
            this.fechaFin = vigente.fecha_hasta
            this.ausenciaVigenteId = vigente.id
            this.ausenciaMotivo = vigente.motivo || 'vacaciones'
          } else {
            this.ausenciaVigenteId = null
            this.ausenciaMotivo = 'vacaciones'
          }
        }
      } catch (e) {
        console.error('[ProfileModal] _cargarAusencias error:', e)
      }
    },

    async guardarAusencia() {
      if (!this.fechaInicio || !this.fechaFin) {
        window.toast('⚠️ Indica fecha de inicio y fin.', 'warn')
        return
      }
      if (this.fechaInicio > this.fechaFin) {
        window.toast('⚠️ La fecha de inicio no puede ser mayor al fin.', 'warn')
        return
      }
      // Necesito el id del usuario actual. Issue 1.2: ya no filtramos por
      // username (confundia con delegacion). Buscamos por username exacto.
      const resList = await apiGet(`/usuarios?q=${encodeURIComponent(this.username)}&page_size=5`)
      if (!resList.ok) return
      const me = (resList.data.items || []).find(x => x.username === this.username)
      if (!me) return
      const resActivos = await apiGet('/usuarios?estado=activo&page_size=500')
      const myId = me.id
      let res
      if (this.ausenciaVigenteId) {
        // Actualizar
        res = await apiPatch(`/ausencias/${this.ausenciaVigenteId}`, {
          fecha_desde: this.fechaInicio,
          fecha_hasta: this.fechaFin,
          motivo: this.ausenciaMotivo || 'vacaciones',
          notas: this.observaciones || null,
        })
      } else {
        // Crear
        res = await apiPost(`/ausencias/usuarios/${myId}`, {
          fecha_desde: this.fechaInicio,
          fecha_hasta: this.fechaFin,
          motivo: this.ausenciaMotivo || 'vacaciones',
          notas: this.observaciones || null,
        })
      }
      if (res.ok) {
        window.toast('✅ Vacaciones registradas.', 'success')
        await this._cargarAusencias(myId)
        // Refrescar auth store para actualizar el flag ausente
        const auth = window.Alpine?.store('auth')
        if (auth && auth.refreshFromBackend) await auth.refreshFromBackend()
      } else {
        window.toast('❌ Error: ' + (res.data?.detail || res.status), 'error')
      }
    },

    async cancelarAusencia() {
      if (!this.ausenciaVigenteId) {
        // Si no hay ausencia activa, solo desmarca el checkbox
        this.ausente = false
        this.fechaInicio = ''
        this.fechaFin = ''
        return
      }
      if (!confirm('¿Cancelar tus vacaciones registradas?')) return
      const res = await apiDelete(`/ausencias/${this.ausenciaVigenteId}`)
      if (res.ok) {
        window.toast('✅ Vacaciones canceladas.', 'success')
      const resList = await apiGet(`/usuarios?q=${encodeURIComponent(this.username)}&page_size=5`)
      const me = (resList.data.items || []).find(x => x.username === this.username)
      if (me) await this._cargarAusencias(me.id)
      // (Issue 1.2: page_size no afecta esta query porque ya busca por username)
        const auth = window.Alpine?.store('auth')
        if (auth && auth.refreshFromBackend) await auth.refreshFromBackend()
        this.ausente = false
        this.fechaInicio = ''
        this.fechaFin = ''
      } else {
        window.toast('❌ Error: ' + (res.data?.detail || res.status), 'error')
      }
    },

    cerrar() {
      if (this.saving) return
      this.open = false
    },

    get usuariosFiltrados() {
      const q = (this.inputDelegado || '').toLowerCase().trim()
      const maxInicial = 100
      if (!q) return this.usuariosActivos.slice(0, maxInicial)
      const tokens = q.split(/\s+/).filter(Boolean)
      return this.usuariosActivos.filter(u => {
        const haystack = [
          u.nombre_completo || '',
          u.username || '',
          u.email || '',
          u.ad_postal_code || '',
          u.cargo || '',
        ].join(' ').toLowerCase()
        return tokens.every(t => haystack.includes(t))
      }).slice(0, maxInicial)
    },

    seleccionarDelegado(u) {
      this.delegadoId = u.id
      this.delegadoNombre = u.nombre_completo
      this.delegadoUsername = u.username
      this.inputDelegado = ''
      this.mostrarListaDelegado = false
      this.delegadoAlerta = false
    },

    limpiarDelegado() {
      this.delegadoId = null
      this.delegadoNombre = ''
      this.delegadoUsername = ''
      this.inputDelegado = ''
      this.mostrarListaDelegado = false
    },

    async guardar() {
      if (this.rolRequiereDelegado && !this.delegadoId) {
        window.toast('⚠️ Tu rol requiere delegado. Asigna uno antes de guardar.', 'warn')
        return
      }
      this.saving = true
      try {
        // 1) Necesito el ID del usuario actual
        const resList = await apiGet(`/usuarios?q=${encodeURIComponent(this.username)}&page_size=5`)
        if (!resList.ok || !resList.data.items) {
          window.toast('Error: no se encontro el usuario actual', 'error')
          return
        }
        const me = resList.data.items.find(x => x.username === this.username)
        if (!me) {
          window.toast('Error: usuario no encontrado', 'error')
          return
        }
        // 2) PATCH con los cambios (Sesion 23 / Bloque B1: ausente se maneja
        //    via /ausencias, NO en PATCH /usuarios/{id}).
        const payload = {
          delegado_id: this.delegadoId,
        }
        if (this.observaciones && this.observaciones.trim()) {
          payload.observaciones = this.observaciones.trim()
        }
        const res = await apiPatch(`/usuarios/${me.id}`, payload)
        if (!res.ok) {
          window.toast(`Error: ${res.data?.detail || res.status}`, 'error')
          return
        }
        window.toast('✅ Mi Perfil actualizado. Sus tareas se re-enrutan al delegado.', 'success')
        // 3) Refrescar auth store para que el badge de alerta desaparezca
        const auth = window.Alpine?.store('auth')
        if (auth && auth.refreshFromBackend) {
          await auth.refreshFromBackend()
        }
        this.delegadoAlerta = (this.rolRequiereDelegado && !this.delegadoId)
        this.observaciones = ''
      } catch (e) {
        window.toast(`Error: ${e.message}`, 'error')
      } finally {
        this.saving = false
      }
    },

    abrirDelegar(nombre, cargo) {
      this.delegarNombre = nombre
      this.delegarCargo = cargo
      this.delegarOpen = true
    },
    confirmarDelegacion() {
      this.delegarOpen = false
      window.toast('Responsabilidad delegada exitosamente. Se ha notificado al sucesor.', 'success')
      setTimeout(() => window.navigate('/bandeja'), 1200)
    },
  }))

  window.profileModal = {
    abrir() {
      const el = document.querySelector('[x-data="profileModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir()
      else setTimeout(() => window.profileModal.abrir(), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="profileModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
    abrirDelegar(nombre, cargo) {
      const el = document.querySelector('[x-data="profileModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrirDelegar(nombre, cargo)
    },
  }

  window.addEventListener('open-profile', () => {
    window.profileModal?.abrir()
  })
}

export const ProfileModalTemplate = /* html */`
<div x-data="profileModalData">
  <template x-teleport="body">

    <!-- Modal Mi Perfil -->
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrar()"
         class="modal-overlay" style="z-index:8000;display:none"
         :style="open ? 'display:flex' : 'display:none'">

      <div @click.stop
           class="modal-box max-w-[440px] relative max-h-[90vh] overflow-y-auto">

        <button @click="cerrar()" :disabled="saving"
                class="absolute top-3.5 right-3.5 text-slate-400 hover:text-red-500 transition-colors text-lg leading-none cursor-pointer disabled:opacity-30">✕</button>

        <!-- Loading inicial -->
        <div x-show="loading" class="py-12 text-center text-slate-500">
          <div class="w-6 h-6 mx-auto border-2 border-brand-500 border-t-transparent rounded-full animate-spin mb-2"></div>
          <div class="text-[11.5px]">Cargando tu perfil...</div>
        </div>

        <!-- Contenido -->
        <div x-show="!loading">
          <!-- Avatar + Datos -->
          <div class="text-center mb-5">
            <div class="w-[90px] h-[90px] rounded-full bg-gradient-to-br from-brand-500 to-blue-400 mx-auto mb-3.5 flex items-center justify-center text-3xl font-extrabold text-white border-[3px] border-blue-200 shadow-lg" x-text="iniciales"></div>
            <div class="text-xl font-bold text-slate-900 -tracking-wide" x-text="nombre"></div>
            <div class="text-[13px] text-brand-500 font-semibold mt-0.5" x-text="cargo"></div>
            <div class="text-[11.5px] text-slate-500 mt-1.5 inline-flex items-center gap-1 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-200">
              🏢 <span class="font-semibold text-slate-700" x-text="area"></span>
            </div>
            <div class="text-[10.5px] text-slate-400 mt-1.5">
              <span class="font-mono" x-text="'@' + username"></span>
              <span class="mx-1.5">·</span>
              <span x-text="rolPrincipal || 'Sin rol'"></span>
              <span class="mx-1.5">·</span>
              <span :class="estado === 'activo' ? 'text-emerald-600' : 'text-amber-600'" x-text="estado"></span>
            </div>
          </div>

          <!-- Banner alertas -->
          <div x-show="delegadoAlerta"
               class="bg-amber-50 border border-amber-300 rounded-xl p-3 mb-4 flex items-start gap-2.5"
               style="display:none"
               :style="delegadoAlerta ? 'display:flex' : 'display:none'">
            <span class="text-xl flex-shrink-0">⚠️</span>
            <div>
              <div class="text-xs font-bold text-amber-700 mb-0.5">Tu rol requiere delegado</div>
              <div class="text-[11px] text-amber-800 leading-snug">Asigna una persona como back-up para que pueda recibir tus tareas en vacaciones o licencias.</div>
            </div>
          </div>

          <!-- Banner vacaciones -->
          <div x-show="ausente"
               class="bg-blue-50 border border-blue-300 rounded-xl p-3 mb-4 flex items-start gap-2.5"
               style="display:none"
               :style="ausente ? 'display:flex' : 'display:none'">
            <span class="text-xl flex-shrink-0">🏖️</span>
            <div>
              <div class="text-xs font-bold text-blue-700 mb-0.5">Estas en vacaciones / Licencia</div>
              <div class="text-[11px] text-blue-800 leading-snug">Tus tareas se enrutan automáticamente a tu delegado.</div>
            </div>
          </div>

          <!-- Seccion Delegado (F4: oculta para visualizadores/admin) -->
          <div class="bg-slate-50 border border-slate-200 rounded-xl p-4"
               x-show="rolRequiereDelegado"
               style="display:none"
               :style="rolRequiereDelegado ? '' : 'display:none'">
            <div class="text-[13px] font-bold text-slate-700 mb-1.5 flex items-center gap-1.5">🤝 Delegado (Back-up) y Ausencias</div>
            <p class="text-[11px] text-slate-500 mb-3.5 leading-snug" x-show="rolRequiereDelegado">
              Tu rol requiere delegado obligatorio. Selecciona una persona.
            </p>
            <p class="text-[11px] text-slate-500 mb-3.5 leading-snug" x-show="!rolRequiereDelegado">
              Opcional: asigna un delegado para vacaciones o licencias.
            </p>

            <!-- Delegado actual -->
            <div x-show="delegadoNombre"
                 class="mb-3 flex items-center gap-2.5 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              <span class="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0"></span>
              <div class="min-w-0 flex-1">
                <div class="text-[12px] font-semibold text-slate-800 truncate" x-text="delegadoNombre"></div>
                <div class="text-[10px] text-slate-500 font-mono" x-text="'@' + delegadoUsername"></div>
              </div>
              <button @click="limpiarDelegado()" type="button" class="text-slate-400 hover:text-red-500 text-[14px] leading-none" title="Quitar delegado">✕</button>
            </div>

            <!-- Buscador -->
            <div class="relative mb-3">
              <input type="text"
                     class="form-input text-xs"
                     placeholder="Buscar delegado por nombre, usuario o SAP..."
                     x-model="inputDelegado"
                     @input="mostrarListaDelegado=true"
                     @focus="mostrarListaDelegado=true"
                     @click.outside="mostrarListaDelegado=false">
              <div x-show="mostrarListaDelegado && usuariosFiltrados.length > 0"
                   x-transition:enter="transition ease-out duration-100"
                   x-transition:enter-start="opacity-0 -translate-y-1"
                   x-transition:enter-end="opacity-100 translate-y-0"
                   class="absolute z-10 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
                   style="display:none"
                   :style="(mostrarListaDelegado && usuariosFiltrados.length > 0) ? 'display:block' : 'display:none'">
                <template x-for="u in usuariosFiltrados" :key="u.id">
                  <button @click="seleccionarDelegado(u)" type="button"
                          class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors">
                    <div class="flex items-center gap-2">
                      <div class="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-blue-400 flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0"
                           x-text="u.iniciales || '??'"></div>
                      <div class="min-w-0 flex-1">
                        <div class="text-[11.5px] font-semibold text-slate-800 truncate" x-text="u.nombre_completo"></div>
                        <div class="text-[10px] text-slate-500">
                          <span class="font-mono" x-text="'@' + u.username"></span>
                          <template x-if="u.ad_postal_code">
                            <span class="text-slate-400"> · SAP <span class="font-mono" x-text="u.ad_postal_code"></span></span>
                          </template>
                        </div>
                      </div>
                    </div>
                  </button>
                </template>
              </div>
              <div x-show="mostrarListaDelegado && usuariosFiltrados.length === 0 && inputDelegado"
                   class="absolute z-10 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl p-3 text-center text-[11px] text-slate-500"
                   style="display:none"
                   :style="(mostrarListaDelegado && usuariosFiltrados.length === 0 && inputDelegado) ? 'display:block' : 'display:none'">
                Sin resultados.
              </div>
            </div>

            <!-- Checkbox ausencia (Sesion 23 / Bloque B1) -->
            <div class="border-t border-slate-200 pt-3 mt-3.5">
              <label class="flex items-center gap-2 text-xs font-semibold cursor-pointer text-slate-800">
                <input type="checkbox" x-model="ausente" @change="ausente && !ausenciaVigenteId ? null : null" class="w-4 h-4 accent-brand-500 cursor-pointer">
                🏖️ Marcarme como ausente (Vacaciones / Licencia)
              </label>
            </div>

            <!-- Fechas ausencia (Sesion 23 / Bloque B1) -->
            <div class="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div class="text-[10.5px] text-blue-700 mb-2.5 leading-snug">
                <template x-if="ausenciaVigenteId">
                  <span>✅ Tienes vacaciones registradas. Edita el rango o cancela.</span>
                </template>
                <template x-if="!ausenciaVigenteId">
                  <span>Indica el rango de fechas. El sistema marcará ausente=true automáticamente y desactivará al llegar la fecha fin.</span>
                </template>
              </div>
              <div class="grid grid-cols-2 gap-2.5">
                <div>
                  <label class="text-[10.5px] text-blue-700 font-semibold block mb-1">Desde:</label>
                  <input type="date" x-model="fechaInicio" class="form-input text-[11px] py-1.5">
                </div>
                <div>
                  <label class="text-[10.5px] text-blue-700 font-semibold block mb-1">Hasta:</label>
                  <input type="date" x-model="fechaFin" class="form-input text-[11px] py-1.5">
                </div>
              </div>
              <div class="mt-2">
                <label class="text-[10.5px] text-blue-700 font-semibold block mb-1">Motivo:</label>
                <select x-model="ausenciaMotivo" class="form-input text-[11px] py-1.5">
                  <option value="vacaciones">🏖️ Vacaciones</option>
                  <option value="licencia">🏥 Licencia medica</option>
                  <option value="capacitacion">📚 Capacitacion</option>
                  <option value="otro">📌 Otro</option>
                </select>
              </div>
              <div class="flex gap-2 mt-3">
                <button @click="guardarAusencia()" class="btn btn-primary text-[11px] flex-1">
                  <span x-text="ausenciaVigenteId ? 'Actualizar vacaciones' : 'Registrar vacaciones'"></span>
                </button>
                <template x-if="ausenciaVigenteId">
                  <button @click="cancelarAusencia()" class="btn btn-danger text-[11px] flex-1">Cancelar vacaciones</button>
                </template>
              </div>
            </div>

            <!-- Historial de ausencias -->
            <template x-if="ausencias.length > 0">
              <div class="border-t border-slate-200 pt-3 mt-3.5">
                <label class="text-[10.5px] text-slate-600 font-semibold block mb-1.5">📅 Historial de ausencias</label>
                <div class="space-y-1 max-h-[100px] overflow-y-auto">
                  <template x-for="a in ausencias" :key="a.id">
                    <div class="text-[10.5px] text-slate-600 flex items-center gap-2 px-2 py-1 bg-slate-50 rounded">
                      <span x-text="a.fecha_desde + ' → ' + a.fecha_hasta"></span>
                      <span class="text-slate-400" x-text="a.motivo"></span>
                      <span x-show="a.esta_vigente" class="text-emerald-600 font-semibold">VIGENTE</span>
                      <span x-show="!a.activo" class="text-amber-600">cancelada</span>
                    </div>
                  </template>
                </div>
              </div>
            </template>

            <!-- Observaciones -->
            <div class="border-t border-slate-200 pt-3 mt-3.5">
              <label class="text-[10.5px] text-slate-600 font-semibold block mb-1">📝 Observaciones (opcional, queda en audit log)</label>
              <textarea class="form-input text-[11px]" x-model="observaciones" rows="1.5" placeholder="Ej.: Vacaciones programadas del 15 al 30..."></textarea>
            </div>

            <!-- Footer -->
            <div class="flex justify-end items-center mt-4 border-t border-dashed border-slate-300 pt-3">
              <button @click="guardar()" :disabled="saving" class="btn btn-primary rounded-full px-5 flex items-center gap-1.5">
                <span x-show="!saving">Guardar</span>
                <span x-show="saving" class="flex items-center gap-1.5">
                  <span class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Guardando...
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Delegar Tarea (sin cambios) -->
    <div x-show="delegarOpen"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="delegarOpen=false"
         class="modal-overlay" style="z-index:8500;display:none">

      <div @click.stop class="modal-box max-w-[360px] text-center max-h-[90vh] overflow-y-auto">
        <div class="text-4xl mb-2.5">👤➡️👤</div>
        <div class="text-base font-bold text-slate-900 mb-2.5">Delegar Responsabilidad</div>
        <div class="text-[13px] text-slate-600 mb-5 leading-relaxed">
          Usted va a delegar la revisión/aprobación de este documento a su reemplazo configurado en el sistema:
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div class="text-[15px] font-bold text-blue-700 mb-1" x-text="delegarNombre"></div>
          <div class="text-xs text-brand-500" x-text="delegarCargo"></div>
        </div>
        <div class="flex gap-2.5">
          <button @click="delegarOpen=false" class="btn flex-1">Cancelar</button>
          <button @click="confirmarDelegacion()" class="btn btn-primary flex-1">Confirmar Delegación</button>
        </div>
      </div>
    </div>

  </template>
</div>`
