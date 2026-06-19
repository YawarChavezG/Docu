/**
 * src/services/documentosApi.js
 *
 * Capa de API para la pantalla AprobacionDocumento.js y VersionEditable.js.
 * Sesion 22 R2 FASE 2 - Tarea 2.8.
 *
 * Endpoints consumidos (backend en /api/v1):
 *  - /documentos/buscar?q=              (GET)  autocomplete para /version-editable
 *  - /documentos/preview-codigo?        (GET)  codigo sin persistir
 *  - /documentos?                       (GET)  lista paginada con filtros
 *  - /documentos/{id}                   (GET)  detalle
 *  - /documentos                        (POST) crea doc + flujo inicial
 *  - /documentos/{id}                   (PATCH) edita doc
 *  - /documentos/{id}/archivos          (POST) upload archivo (multipart)
 *  - /documentos/{id}/enviar            (POST) firma 2FA + envio
 *  - /bandeja?tipo=                     (GET)  bandejas
 */
import { apiGet, apiPost, apiPatch, apiDelete } from '../utils/api.js'

// ─── Documentos ───
export const documentos = {
  // ─── Lectura ───
  buscar: (q, limit = 10) => {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    params.set('limit', String(limit))
    return apiGet(`/documentos/buscar?${params.toString()}`)
  },
  previewCodigo: (tipoId, areaId, tipoSolicitud = 'CREACION') => {
    const params = new URLSearchParams({
      tipo_id: String(tipoId),
      area_id: String(areaId),
      tipo_solicitud: tipoSolicitud,
    })
    return apiGet(`/documentos/preview-codigo?${params.toString()}`)
  },
  get: (id) => apiGet(`/documentos/${id}`),
  list: (filtros = {}) => {
    const params = new URLSearchParams()
    Object.entries(filtros).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') params.set(k, v)
    })
    return apiGet(`/documentos?${params.toString()}`)
  },

  // ─── Mutaciones ───
  create: (payload) => apiPost('/documentos', payload),
  update: (id, payload) => apiPatch(`/documentos/${id}`, payload),
  uploadArchivo: (id, file, tipoAdjunto = 'FORMULARIO') => {
    const formData = new FormData()
    formData.append('archivo', file)
    formData.append('tipo_adjunto', tipoAdjunto)
    return apiPost(`/documentos/${id}/archivos`, formData)
  },
  enviar: (id, body) => apiPost(`/documentos/${id}/enviar`, body),
  // R3 item 0.6
  liberar: (id, body) => apiPost(`/documentos/${id}/liberar`, body),
  // R3 item 0.2
  listActualizables: (areaId, tipoDocumentoId) => {
    const params = new URLSearchParams({
      area_id: String(areaId),
      tipo_documento_id: String(tipoDocumentoId),
    })
    return apiGet(`/documentos/actualizables?${params.toString()}`)
  },
}

// ─── Bandejas ───
export const bandejas = {
  elaboracion: (page = 1, pageSize = 10) =>
    apiGet(`/bandeja?tipo=elaboracion&page=${page}&page_size=${pageSize}`),
  revision: (page = 1, pageSize = 10) =>
    apiGet(`/bandeja?tipo=revision&page=${page}&page_size=${pageSize}`),
  aprobacion: (page = 1, pageSize = 10) =>
    apiGet(`/bandeja?tipo=aprobacion&page=${page}&page_size=${pageSize}`),
  liberacion: (page = 1, pageSize = 10) =>
    apiGet(`/bandeja?tipo=liberacion&page=${page}&page_size=${pageSize}`),
}

// ─── Helpers (R3 item 0.1) ───
export function generarNombreCompleto(codigo, titulo, version) {
  if (!codigo) return ''
  const cod = String(codigo).split('/')[0]
  const tit = (titulo || '').trim().toUpperCase()
  const ver = version || '00'
  if (!tit) return `${cod} V${ver}`
  return `${cod} ${tit} V${ver}`
}

export default documentos
