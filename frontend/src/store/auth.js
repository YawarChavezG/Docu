/**
 * auth.js — Alpine store for authentication (con persistencia localStorage)
 *
 * Registered as: Alpine.store('auth', authStore)
 * Access inside Alpine templates: $store.auth.user
 * Access in JS: Alpine.store('auth').login(...)
 *
 * Backend: FastAPI en /api/v1/auth/{login, me, logout, verify-password}.
 * Cookie httpOnly 'user_id' se setea en el backend; el frontend
 * NO maneja el token, solo el objeto user que viene en /me.
 */

import { API_BASE } from '../utils/config.js'
// Antes este archivo usaba una URL absoluta (http://localhost:18000/api/v1)
// que causaba problemas de CORS + cookies cuando el browser estaba en
// localhost:8080 (Nginx proxy). Ahora usamos la misma API_BASE que
// utils/api.js, que es relativa via Nginx.
const _API_BASE = API_BASE

/* ─── Mapeo rol backend -> rol frontend ───
   El backend devuelve roles como ["ADMIN"], ["ETO"], etc.
   El frontend usa roles en minúscula: 'eto', 'user', 'admin', 'visualizador'.
   Esta función los normaliza. */
function mapRolesToFrontend(roles) {
  if (!Array.isArray(roles) || roles.length === 0) return 'user'
  if (roles.includes('ADMIN')) return 'admin'
  if (roles.includes('ETO')) return 'eto'
  if (roles.includes('VISUALIZADOR (CL-EVAL)')) return 'visualizador'
  return 'user' // ELABORADOR - REVISOR, ELABORADOR - REVISOR - APROBADOR
}

export const authStore = {

  /* ─── State ─────────────────────────────────────────────── */
  user: null,
  role: null,
  // isReady = true cuando YA sabemos el estado de la sesion (cache sincrono
  // + /me completado). Hasta entonces, el router NO debe tomar decisiones
  // de redireccion (mostrar loader en su lugar).
  isReady: false,
  // Promesa de la llamada de refresh en curso. La pueden usar main.js
  // y el router para await antes de iniciar la UI.
  _refreshPromise: null,

  /* ─── Persistencia ──────────────────────────────────────── */

  init() {
    // Paso 1 (sincronico): restaurar sesion desde localStorage.
    // Esto evita que el router vea isAuthenticated=false en el primer tick
    // y nos mande a /login cuando en realidad tenemos cookies + cache validos.
    this.isReady = false
    const cached = localStorage.getItem('cofar_session')
    if (cached) {
      try {
        const parsed = JSON.parse(cached)
        if (parsed && parsed.user && parsed.role) {
          this.user = parsed.user
          this.role = parsed.role
          // Con cache sincrono ya podemos declarar listo: el backend
          // validara en background; si las cookies vencieron, _refreshPromise
          // limpiara el estado y disparara isReady=true de nuevo.
          this.isReady = true
        }
      } catch (_) {
        localStorage.removeItem('cofar_session')
      }
    }

    // Paso 2 (async): validar contra el backend. Si falla, limpiar todo.
    this._refreshPromise = this.refreshFromBackend()
      .catch(() => {
        this.user = null
        this.role = null
        localStorage.removeItem('cofar_session')
      })
      .finally(() => {
        this.isReady = true
        this._refreshPromise = null
      })

    // Sesion 17: evento global para terminar impersonate desde el banner
    // del AppLayout (que no tiene acceso directo al store).
    window.addEventListener('sgd-stop-impersonate', () => this.stopImpersonate())
  },

  /**
   * Sesion 17: termina el impersonate llamando al endpoint del backend y
   * refresca el store. Maneja la respuesta del banner sticky.
   */
  async stopImpersonate() {
    if (!this.user?.impersonated_by) return
    try {
      const csrf = ('; ' + document.cookie).split('; csrf_token=').pop().split(';')[0]
      const res = await fetch(`${_API_BASE}/admin/impersonate/stop`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRF-Token': csrf },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        if (window.toast) window.toast(`Error terminando impersonate: ${err.detail || res.status}`, 'error')
        return
      }
      if (window.toast) window.toast('✅ Impersonate terminado. Volvió a su sesión original.', 'success')
      await this.refreshFromBackend()
      // Sesion 27 (Opcion A): navegar a la homeRoute del admin original
      // (no del impersonado) y reload completo para que la sidebar se
      // reconstruya con los links correctos.
      const target = this.homeRoute
      window.location.hash = '#' + target
      window.location.reload()
    } catch (e) {
      if (window.toast) window.toast(`Error de red: ${e.message}`, 'error')
    }
  },

  async refreshFromBackend() {
    try {
      const res = await fetch(`${_API_BASE}/me`, {
        method: 'GET',
        credentials: 'include', // enviar cookies
      })
      if (!res.ok) {
        this.user = null
        this.role = null
        return null
      }
      const data = await res.json()
      if (data.authenticated && data.user) {
        // Mapear campos del backend (snake_case) al formato legacy
        // que el resto del frontend espera (camelCase / nombres cortos).
        this.user = this._mapBackendUserToFrontend(data.user, data.impersonated_by)
        this.role = mapRolesToFrontend(data.user.roles)

        // Chequear delegado en BD (necesario para alerta de sidebar).
        // No bloquea: si falla, mantenemos la heuristica del rol.
        this._checkDelegadoAlerta().catch(() => { /* ignore */ })

        this._persist()
        return this.user
      }
      this.user = null
      this.role = null
      return null
    } catch (e) {
      console.error('[auth] refreshFromBackend error:', e)
      this.user = null
      this.role = null
      return null
    }
  },

  /**
   * Chequea si el usuario actual tiene delegado asignado.
   * Set this.user.hasDelegadoAlert = true si:
   *   - el rol del usuario requiere delegado, Y
   *   - el usuario NO tiene delegado (delegado_id=null)
   * Si falla la consulta a /usuarios, deja el flag como esta.
   */
  async _checkDelegadoAlerta() {
    if (!this.user || !this.user.username) return
    if (!this.user.requiereDelegadoPorRol) {
      this.user.hasDelegadoAlert = false
      return
    }
    try {
      const res = await fetch(
        `${_API_BASE}/usuarios?q=${encodeURIComponent(this.user.username)}&page_size=5`,
        { method: 'GET', credentials: 'include' }
      )
      if (!res.ok) return
      const data = await res.json()
      const me = (data.items || []).find(x => x.username === this.user.username)
      if (me) {
        const tieneDelegado = !!me.delegado_id
        const ausente = !!me.ausente
        this.user.hasDelegadoAlert = !tieneDelegado && !ausente
        // Exponer campos para que Mi Perfil los pueda leer
        this.user.delegado_id = me.delegado_id
        this.user.delegado_nombre = me.delegado_nombre
        this.user.delegado_username = me.delegado_username
        this.user.estado_delegacion = me.estado_delegacion
        this.user.ausente = ausente
        this.user.estado = me.estado
      }
    } catch (_) {
      // ignore - mantener flag como esta
    }
  },

  /**
   * Convierte el user del backend al shape legacy del frontend.
   * El backend devuelve:
   *   { username, nombre_completo, iniciales, email, cargo, area_id,
   *     gerencia_sigla, area_sigla, ad_department, estado, ausente,
   *     es_impersonado, es_usuario_ad, roles }
   * (Sesion 26: modulos eliminado, es_usuario_ad agregado para ProfileModal)
   * El frontend (mock original) espera:
   *   { username, name, roleLabel, initials, area, hasDelegadoAlert }
   */
  _mapBackendUserToFrontend(bu, impersonatedBy) {
    const roleLabels = {
      'ADMIN': 'Administrador del Sistema',
      'ETO': 'Gestor Documental ETO',
      'ELABORADOR - REVISOR': 'Elaborador - Revisor',
      'ELABORADOR - REVISOR - APROBADOR': 'Elaborador - Revisor - Aprobador',
      'VISUALIZADOR (CL-EVAL)': 'Visualizador (CL-EVAL)',
    }
    const roles = bu.roles || []
    const primaryRole = roles[0] || ''

    // Resolucion de area con fallback al AD.
    // Prioridad:
    //  1) area_sigla + gerencia_sigla (match con tabla areas en BD)
    //  2) ad_department (department del AD, ej: "Tecnologia")
    //  3) "Sin area"
    let areaLabel = 'Sin área'
    if (bu.area_sigla) {
      areaLabel = bu.gerencia_sigla
        ? `${bu.gerencia_sigla} / ${bu.area_sigla}`
        : bu.area_sigla
    } else if (bu.gerencia_sigla) {
      areaLabel = bu.gerencia_sigla
    } else if (bu.ad_department) {
      // ad_department viene como "Tecnologia | Tercia SRL" del backend.
      // Para el modal de perfil mostramos el primer componente (gerencia).
      areaLabel = bu.ad_department.split('|')[0].trim()
    }

    // Roles que requieren delegado obligatorio (sesion 2, ver model Rol.requiere_delegado)
    const rolesQueRequierenDelegado = new Set([
      'ETO', 'ELABORADOR - REVISOR', 'ELABORADOR - REVISOR - APROBADOR',
    ])
    // La alerta solo se muestra si:
    //   1) el rol lo requiere
    //   2) el usuario NO tiene delegado (no lo sabemos en /me, hay que cruzar)
    // Por ahora usamos una heuristica conservadora: la alerta se chequea en
    // refreshFromBackend() buscando el usuario en /usuarios?q=<username>.
    const requiereDelegadoPorRol = rolesQueRequierenDelegado.has(primaryRole)

    return {
      // passthrough del backend
      username: bu.username,
      nombre_completo: bu.nombre_completo,
      iniciales: bu.iniciales,
      email: bu.email,
      cargo: bu.cargo,
      area_id: bu.area_id,
      gerencia_sigla: bu.gerencia_sigla,
      area_sigla: bu.area_sigla,
      ad_department: bu.ad_department,
      ad_physical_delivery_office: bu.ad_physical_delivery_office,
      estado: bu.estado,
      ausente: bu.ausente,
      es_impersonado: bu.es_impersonado || !!impersonatedBy,
      es_usuario_ad: bu.es_usuario_ad || false,  // Sesion 26
      roles: roles,
      impersonated_by: impersonatedBy || null,
      // aliases legacy (mock compat)
      name: bu.nombre_completo,
      roleLabel: bu.cargo || roleLabels[primaryRole] || primaryRole,
      initials: bu.iniciales,
      area: areaLabel,
      // hasDelegadoAlert: se setea en refreshFromBackend (chequea BD).
      // Por defecto false; el refresh asincrono lo activa si corresponde.
      hasDelegadoAlert: false,
      requiereDelegadoPorRol,
    }
  },

  _persist() {
    if (this.user && this.role) {
      localStorage.setItem('cofar_session', JSON.stringify({
        user: this.user,
        role: this.role,
      }))
    } else {
      localStorage.removeItem('cofar_session')
    }
  },

  /* ─── Actions ───────────────────────────────────────────── */

  /**
   * Login contra el backend (FastAPI /api/v1/login).
   * Devuelve { ok: true, user } si exitoso, { ok: false, message } si falla.
   * ASYNC — el caller debe await.
   */
  async login(username, password, authSource = 'cofar') {
    try {
      const res = await fetch(`${_API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // recibir y enviar cookies
        body: JSON.stringify({
          username: username.trim(),
          password: password,
          auth_source: authSource,  // 'cofar' (AD) o 'local' (BD seeded)
        }),
      })

      if (!res.ok) {
        let detail = 'Error de autenticación'
        try {
          const err = await res.json()
          detail = err.detail || detail
        } catch (_) {}
        return { ok: false, message: detail }
      }

      const data = await res.json()
      if (data.user) {
        this.user = this._mapBackendUserToFrontend(data.user, data.impersonated_by)
        this.role = mapRolesToFrontend(data.user.roles)
        this._persist()
        return { ok: true, user: this.user }
      }
      return { ok: false, message: 'Respuesta inválida del servidor' }
    } catch (e) {
      console.error('[auth] login error:', e)
      return { ok: false, message: 'No se pudo conectar con el servidor. Verifica tu conexión.' }
    }
  },

  async logout() {
    try {
      await fetch(`${_API_BASE}/logout`, {
        method: 'POST',
        credentials: 'include',
      })
    } catch (_) {}
    this.user = null
    this.role = null
    localStorage.removeItem('cofar_session')
  },

  /* ─── Computed ──────────────────────────────────────────── */

  get isAuthenticated() {
    return this.user !== null
  },

  get homeRoute() {
    const map = {
      eto: '/bandeja',
      user: '/bandeja',
      admin: '/parametrizacion',
      visualizador: '/bandeja',
    }
    return map[this.role] || '/bandeja'
  },

  canAccess(section) {
    const acl = {
      bandeja: ['eto', 'user', 'visualizador'],
      lista: ['eto', 'user', 'visualizador'],
      consulta: ['eto', 'user', 'visualizador'],
      copias: ['eto'],
      publicacion: ['eto'],
      reportes: ['eto'],
      evaluaciones: ['eto', 'user', 'visualizador'],
      flujo: ['eto', 'user'],
      solicitud: ['eto', 'user'],
      chat: ['eto', 'user', 'visualizador'],
      plantillas: ['eto', 'user'],
      parametrizacion: ['eto', 'admin'],
    }
    return (acl[section] ?? []).includes(this.role)
  },

  canAccessRoute(route) {
    const map = {
      '/login': 'login',
      '/bandeja': 'bandeja',
      '/tareas-completas': 'bandeja',
      '/lista': 'lista',
      '/consulta': 'consulta',
      '/biblioteca': 'lista',
      '/evaluaciones': 'evaluaciones',
      '/certificados': 'evaluaciones',
      '/certificado-imprimible': 'evaluaciones',
      '/pre-eval': 'evaluaciones',
      '/tomar-lectura': 'evaluaciones',
      '/plantillas': 'plantillas',
      '/liberacion-detalle': 'flujo',
      '/revision': 'flujo',
      '/aprobacion-final': 'flujo',
      '/correccion': 'flujo',
      '/version-editable': 'solicitud',
      '/aprobacion-documento': 'solicitud',
      '/modulo-copias': 'copias',
      '/copias-cc': 'copias',
      '/copias-cn': 'copias',
      '/publicacion': 'publicacion',
      '/reportes': 'reportes',
      '/chat': 'chat',
      '/parametrizacion': 'parametrizacion',
      '/config-examen': 'parametrizacion',
      '/403': 'login',
      '/404': 'login',
    }
    const section = map[route]
    if (!section) return false
    if (section === 'login') return true
    return this.canAccess(section)
  },
}
