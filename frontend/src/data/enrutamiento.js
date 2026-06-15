/**
 * src/data/enrutamiento.js
 * Extraído del HTML: ptab-diccionario (US-9.03) — Matriz de Enrutamiento ETO
 * Contiene: MatrizEnrutamiento[], delegadosPorGerencia[]
 */

export const MatrizEnrutamientoDB = [
  {
    gerencia: 'Calidad',
    analistaAsignado: 'aromero',
    disponible: true,
    delegado: null,
  },
  {
    gerencia: 'Producción',
    analistaAsignado: 'jmamani',
    disponible: true,
    delegado: null,
  },
  {
    gerencia: 'Logística',
    analistaAsignado: 'cflores',
    disponible: false,
    delegado: 'jmamani',
  },
  {
    gerencia: 'RRHH',
    analistaAsignado: 'aromero',
    disponible: true,
    delegado: null,
  },
  {
    gerencia: 'Gerencia',
    analistaAsignado: 'jmamani',
    disponible: true,
    delegado: null,
  },
  {
    gerencia: 'Administración',
    analistaAsignado: 'aromero',
    disponible: true,
    delegado: null,
  },
  {
    gerencia: 'Comercial',
    analistaAsignado: 'cflores',
    disponible: true,
    delegado: null,
  },
]

export const delegadosPorGerenciaDB = [
  { gerencia: 'Calidad',       delegadosPosibles: ['aromero', 'jmamani', 'cflores'] },
  { gerencia: 'Producción',    delegadosPosibles: ['aromero', 'jmamani', 'cflores'] },
  { gerencia: 'Logística',     delegadosPosibles: ['aromero', 'jmamani', 'cflores'] },
  { gerencia: 'RRHH',          delegadosPosibles: ['aromero', 'jmamani', 'cflores'] },
  { gerencia: 'Gerencia',      delegadosPosibles: ['aromero', 'jmamani'] },
  { gerencia: 'Administración',delegadosPosibles: ['aromero', 'cflores'] },
  { gerencia: 'Comercial',     delegadosPosibles: ['jmamani', 'cflores'] },
]

export function getAnalistaPorGerencia(gerencia) {
  const entry = MatrizEnrutamientoDB.find(m => m.gerencia.toLowerCase() === gerencia.toLowerCase())
  if (!entry) return null
  return entry.disponible ? entry.analistaAsignado : entry.delegado
}

export function getDelegadoPorGerencia(gerencia) {
  const entry = MatrizEnrutamientoDB.find(m => m.gerencia.toLowerCase() === gerencia.toLowerCase())
  return entry?.delegado || null
}

export function actualizarDisponibilidad(gerencia, disponible, delegado = null) {
  const entry = MatrizEnrutamientoDB.find(m => m.gerencia === gerencia)
  if (entry) {
    entry.disponible = disponible
    entry.delegado = disponible ? null : delegado
  }
}

export const gruposOutlook = [
  'Gerencia de Calidad',
  'Garantía de Calidad',
  'Validaciones',
  'Dirección Técnica',
  'Administración y Finanzas',
  'Contabilidad',
  'Finanzas',
  'Tesorería',
  'Gerencia de Producción',
  'Planta Líquidos',
  'Planta Sólidos',
]