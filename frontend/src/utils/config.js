/**
 * src/utils/config.js
 *
 * Constantes de configuracion del frontend.
 *
 * IMPORTANTE (sesion 13): API_BASE ahora es RELATIVA (`/api/v1`) en lugar de
 * absoluta. Eso fuerza a que el browser use la misma ORIGIN (el host del
 * frontend: localhost:8080 en dev, sgdqas.cofar.com.bo en QAS), lo cual
 * garantiza que las cookies de sesion se envien correctamente via Nginx.
 *
 * Antes:  'http://localhost:18000/api/v1' (cross-origin, sin cookies)
 * Ahora:  '/api/v1' (mismo origin via Nginx, cookies OK)
 */
export const API_BASE = '/api/v1'

export const APP_VERSION = '2.0'

export const ROLES = {
  ADMIN: 'admin',
  ETO: 'eto',
  USER: 'user',
  VISUALIZADOR: 'visualizador',
}
