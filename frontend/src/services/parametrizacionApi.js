/**
 * src/services/parametrizacionApi.js
 *
 * Capa de API para la pantalla Parametrizacion.js.
 * Envoltorio sobre apiFetch (frontend/src/utils/api.js) con funciones
 * especificas para cada recurso de la EPICA 9.
 *
 * Sesion B - tarea #10: reemplaza a data/parametrosSistema.js (mock legacy).
 *
 * Recursos:
 *  - /api/v1/configuracion-global   (US-9.01, 9.02)
 *  - /api/v1/feriados               (US-9.01 calendario)
 *  - /api/v1/email-templates        (US-9.04)
 *  - /api/v1/matriz-enrutamiento-eto (US-9.03)
 *  - /api/v1/tipos-documento        (US-9.03)
 *  - /api/v1/estados                (US-9.03)
 *  - /api/v1/gerencias              (US-9.06)
 *  - /api/v1/areas                  (US-9.06 + #9d)
 *  - /api/v1/audit-log              (Sesion B #9)
 *  - /api/v1/usuarios               (Sesion B #9e)
 */
import { apiGet, apiPost, apiPut, apiPatch, apiDelete, apiDownload } from '../utils/api.js'

// ─── Configuracion global (clave-valor) ───
export const configGlobal = {
  list: (categoria) => apiGet(`/configuracion-global${categoria ? `?categoria=${categoria}` : ''}`),
  get: (clave) => apiGet(`/configuracion-global/${clave}`),
  upsert: (payload) => apiPost('/configuracion-global', payload),
  update: (clave, payload) => apiPatch(`/configuracion-global/${clave}`, payload),
  bulkUpsert: (categoria, items) => apiPost('/configuracion-global/bulk', { categoria, items }),
}

// ─── Feriados ───
export const feriados = {
  list: (anio) => apiGet(`/feriados${anio ? `?anio=${anio}` : ''}`),
  get: (id) => apiGet(`/feriados/${id}`),
  create: (payload) => apiPost('/feriados', payload),
  update: (id, payload) => apiPatch(`/feriados/${id}`, payload),
  remove: (id) => apiDelete(`/feriados/${id}`),
}

// ─── Plantillas de email ───
export const emailTemplates = {
  list: () => apiGet('/email-templates'),
  get: (codigo) => apiGet(`/email-templates/${codigo}`),
  update: (codigo, payload) => apiPatch(`/email-templates/${codigo}`, payload),
  preview: (codigo, vars) => apiPost(`/email-templates/${codigo}/preview`, { vars }),
}

// ─── Matriz ETO ───
export const matrizEto = {
  list: (soloDisponibles) => apiGet(`/matriz-enrutamiento-eto${soloDisponibles ? '?solo_disponibles=true' : ''}`),
  byGerencia: (gerenciaId) => apiGet(`/matriz-enrutamiento-eto/gerencia/${gerenciaId}`),
  get: (id) => apiGet(`/matriz-enrutamiento-eto/${id}`),
  create: (payload) => apiPost('/matriz-enrutamiento-eto', payload),
  update: (id, payload) => apiPatch(`/matriz-enrutamiento-eto/${id}`, payload),
  remove: (id) => apiDelete(`/matriz-enrutamiento-eto/${id}`),
}

// ─── Tipos de documento ───
export const tiposDocumento = {
  list: (q) => apiGet(`/tipos-documento${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  get: (id) => apiGet(`/tipos-documento/${id}`),
  create: (payload) => apiPost('/tipos-documento', payload),
  update: (id, payload) => apiPatch(`/tipos-documento/${id}`, payload),
  remove: (id) => apiDelete(`/tipos-documento/${id}`),
}

// ─── Estados (catalogo cerrado) ───
export const estados = {
  list: (contexto) => apiGet(`/estados${contexto ? `?contexto=${contexto}` : ''}`),
  get: (id) => apiGet(`/estados/${id}`),
  create: (payload) => apiPost('/estados', payload),
  update: (id, payload) => apiPatch(`/estados/${id}`, payload),
  remove: (id) => apiDelete(`/estados/${id}`),
}

// ─── Gerencias ───
export const gerencias = {
  list: (q, page = 1, pageSize = 200) => apiGet(`/gerencias?q=${q || ''}&page=${page}&page_size=${pageSize}`),
  get: (id) => apiGet(`/gerencias/${id}`),
  create: (payload) => apiPost('/gerencias', payload),
  update: (id, payload) => apiPatch(`/gerencias/${id}`, payload),
  remove: (id) => apiDelete(`/gerencias/${id}`),
}

// ─── Areas (incluye operaciones jerarquicas Sesion B - #9d) ───
export const areas = {
  list: (q, gerenciaId) => {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    if (gerenciaId) params.set('gerencia_id', gerenciaId)
    return apiGet(`/areas?${params.toString()}`)
  },
  get: (id) => apiGet(`/areas/${id}`),
  create: (payload) => apiPost('/areas', payload),
  update: (id, payload) => apiPatch(`/areas/${id}`, payload),
  remove: (id, fisico = false) => apiDelete(`/areas/${id}${fisico ? '?fisico=true' : ''}`),
  mover: (id, gerenciaIdDestino) => apiPost(`/areas/${id}/mover`, { gerencia_id_destino: gerenciaIdDestino }),
  promoverAGerencia: (id, siglaGerencia, nombreGerencia) =>
    apiPost(`/areas/${id}/promover-a-gerencia`, { sigla_gerencia: siglaGerencia, nombre_gerencia: nombreGerencia }),
}

// ─── Audit log (Sesion B - #9) ───
export const auditLog = {
  list: (filtros = {}) => {
    const params = new URLSearchParams()
    Object.entries(filtros).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') params.set(k, v)
    })
    return apiGet(`/audit-log?${params.toString()}`)
  },
  export: (formato = 'xlsx', filtros = {}) => {
    const params = new URLSearchParams({ formato })
    Object.entries(filtros).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') params.set(k, v)
    })
    return apiDownload(`/audit-log/export?${params.toString()}`)
  },
}

// ─── Usuarios (Sesion B - #9e) ───
export const usuarios = {
  list: (filtros = {}) => {
    const params = new URLSearchParams()
    Object.entries(filtros).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') params.set(k, v)
    })
    return apiGet(`/usuarios?${params.toString()}`)
  },
  get: (id) => apiGet(`/usuarios/${id}`),
  override: (id, payload) => apiPatch(`/usuarios/${id}`, payload),
  syncStatus: () => apiGet('/usuarios/sync-status'),
  syncAd: (maxResults = 5000) => apiPost('/usuarios/sync-ad', { max_results: maxResults }),
  export: (formato = 'xlsx', filtros = {}) => {
    const params = new URLSearchParams({ formato })
    Object.entries(filtros).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') params.set(k, v)
    })
    return apiDownload(`/usuarios/export?${params.toString()}`)
  },
  // Listar usuarios activos para el picker de delegado (modal editar)
  listActivos: (q = '') => apiGet(`/usuarios?estado=activo&page_size=200&q=${encodeURIComponent(q)}`),
}

// ─── Roles (Sesion 9 - Gestion de Usuarios edit) ───
export const roles = {
  list: () => apiGet('/roles'),
}

// ─── Semaforizacion por tipo de tarea (Sesion 13) ───
export const semaforizacion = {
  list: () => apiGet('/semaforizacion-tarea'),
  get: (tipo) => apiGet(`/semaforizacion-tarea/${tipo}`),
  update: (tipo, payload) => apiPatch(`/semaforizacion-tarea/${tipo}`, payload),
  calcular: (tipoTarea, dias) => apiPost('/semaforizacion-tarea/calcular', { tipo_tarea: tipoTarea, dias_transcurridos: dias }),
}
