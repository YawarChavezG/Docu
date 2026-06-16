/**
 * src/utils/config.js
 *
 * Constantes de configuracion del frontend.
 * VITE_API_URL se inyecta en build por Vite (default: http://localhost:18000/api/v1).
 * En QAS/PRD se sobreescribe con la URL del backend real.
 */
export const API_BASE =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) ||
  'http://localhost:18000/api/v1'

export const APP_VERSION = '2.0'

export const ROLES = {
  ADMIN: 'admin',
  ETO: 'eto',
  USER: 'user',
  VISUALIZADOR: 'visualizador',
}
