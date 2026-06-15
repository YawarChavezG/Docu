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

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:18000/api/v1'

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

  /* ─── Persistencia ──────────────────────────────────────── */

  init() {
    // Intentar restaurar sesión llamando a /me (que lee la cookie)
    this.refreshFromBackend().catch(() => {
      // Si falla, limpiar storage local
      this.user = null
      this.role = null
      localStorage.removeItem('cofar_session')
    })
  },

  async refreshFromBackend() {
    try {
      const res = await fetch(`${API_BASE}/me`, {
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
   * Convierte el user del backend al shape legacy del frontend.
   * El backend devuelve:
   *   { username, nombre_completo, iniciales, email, cargo, area_id,
   *     gerencia_sigla, area_sigla, estado, ausente, es_impersonado,
   *     modulos, roles }
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
      modulos: bu.modulos || [],
      roles: roles,
      impersonated_by: impersonatedBy || null,
      // aliases legacy (mock compat)
      name: bu.nombre_completo,
      roleLabel: bu.cargo || roleLabels[primaryRole] || primaryRole,
      initials: bu.iniciales,
      area: areaLabel,
      hasDelegadoAlert: false, // TODO: cruzar con tabla delegaciones
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
      const res = await fetch(`${API_BASE}/login`, {
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
      await fetch(`${API_BASE}/logout`, {
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
