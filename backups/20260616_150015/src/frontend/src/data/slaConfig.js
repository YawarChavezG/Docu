/**
 * src/data/slaConfig.js
 * Extraído del HTML: ptab-sla (US-9.01) — Tiempos y SLAs
 * Contiene: ConfiguracionSLA{ vigenciaAnios, plazoRevision, autoDelegacionDias, plazosSemColor }
 */

export const ConfiguracionSLA = {
  vigenciaAnios: 3,
  plazoRevision: 15,
  esperaDelegacion: 3,
  plazoLectura: 30,
}

export const plazosSemColor = {
  verde: 5,
  amarillo: 1,
  rojo: 0,
}

export const historialCambiosSLA = [
  { fecha: '10/04/2026 09:12', parametro: 'Tiempo de vigencia', anterior: '2 años',    nuevo: '3 años',  usuario: 'aromero' },
  { fecha: '05/02/2026 14:30', parametro: 'Plazo máx. revisión', anterior: '10 días',  nuevo: '15 días', usuario: 'aromero' },
  { fecha: '01/01/2026 08:00', parametro: 'Auto-delegación',     anterior: '5 días',   nuevo: '3 días',  usuario: 'aromero' },
]

export function getSlaColor(dias) {
  if (dias > 5) return { color: '#22c55e', label: 'Verde', badge: 'badge-green' }
  if (dias >= 1) return { color: '#eab308', label: 'Amarillo', badge: 'badge-amber' }
  return { color: '#ef4444', label: 'Rojo', badge: 'badge-red' }
}

export function getSlaEmoji(dias) {
  if (dias > 5) return '🟢'
  if (dias >= 1) return '🟡'
  return '🔴'
}

export function guardarSLA(config) {
  ConfiguracionSLA.vigenciaAnios = config.vigenciaAnios ?? ConfiguracionSLA.vigenciaAnios
  ConfiguracionSLA.plazoRevision = config.plazoRevision ?? ConfiguracionSLA.plazoRevision
  ConfiguracionSLA.esperaDelegacion = config.esperaDelegacion ?? ConfiguracionSLA.esperaDelegacion
  ConfiguracionSLA.plazoLectura = config.plazoLectura ?? ConfiguracionSLA.plazoLectura
}

export function guardarSemaforizacion(config) {
  plazosSemColor.verde = config.verde ?? plazosSemColor.verde
  plazosSemColor.amarillo = config.amarillo ?? plazosSemColor.amarillo
}