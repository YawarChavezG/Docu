/**
 * src/services/plantillasApi.js
 *
 * Capa de API para la pantalla Plantillas.js.
 * Sesion 24 / Bloque E: consume /api/v1/plantillas-documentales.
 *
 * Endpoints backend:
 *   GET  /api/v1/plantillas-documentales              -> { total, items: [...] }
 *   GET  /api/v1/plantillas-documentales/{file}/download  -> file blob (auth + audit)
 */
import { apiGet, apiDownload } from '../utils/api.js'

export const plantillas = {
  /**
   * Lista todas las plantillas disponibles desde el backend.
   * Devuelve { ok, data: { total, items }, message }.
   */
  list: () => apiGet('/plantillas-documentales'),

  /**
   * Descarga una plantilla (genera un download en el browser).
   * Devuelve { ok, blob, filename } o { ok: false, message }.
   * El backend registra la descarga en audit_log automaticamente.
   */
  download: (nombreArchivo) => apiDownload(`/plantillas-documentales/${encodeURIComponent(nombreArchivo)}/download`),
}
