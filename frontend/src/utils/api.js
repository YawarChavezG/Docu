/**
 * src/utils/api.js
 *
 * Wrapper centralizado de fetch() para el backend FastAPI.
 *
 * Caracteristicas:
 *  - credentials: 'include' (envia y recibe cookies de sesion)
 *  - CSRF automatico: lee cookie csrf_token y la envia en header X-CSRF-Token
 *    en metodos no seguros (POST/PUT/PATCH/DELETE). El backend esta preparado
 *    para validar este header en cualquier momento (ver main.py + auth.py).
 *  - 401 -> redirige a /#/login (sesion expirada / cookie invalidada)
 *  - 403 -> toast y loggeo (permisos insuficientes, NO redirige)
 *  - 5xx / network errors -> reintento exponencial (max 2 reintentos)
 *  - AbortController nativo (timeout por defecto 30s)
 *  - Error normalizado: { ok:false, status, code, message, detail }
 *
 * Convenciones:
 *  - path puede empezar con /api/v1 o sin prefijo (se agrega automaticamente)
 *  - body se serializa a JSON salvo que options.body ya sea FormData/Blob
 *  - respuesta se parsea a JSON; si el backend no devuelve JSON, devuelve {ok:false, ...}
 */
import { API_BASE } from './config.js'

const DEFAULT_TIMEOUT_MS = 30_000
const MAX_RETRIES = 2
const RETRYABLE_STATUS = new Set([502, 503, 504, 0]) // 0 = network error

/* ─── Helpers internos ──────────────────────────────────────── */

function getCookie(name) {
  if (typeof document === 'undefined') return null
  const target = `${name}=`
  const parts = document.cookie ? document.cookie.split(';') : []
  for (const raw of parts) {
    const c = raw.trim()
    if (c.startsWith(target)) {
      return decodeURIComponent(c.substring(target.length))
    }
  }
  return null
}

function isUnsafeMethod(method) {
  const m = (method || 'GET').toUpperCase()
  return m === 'POST' || m === 'PUT' || m === 'PATCH' || m === 'DELETE'
}

function isFormData(body) {
  return typeof FormData !== 'undefined' && body instanceof FormData
}

function normalizePath(path) {
  if (!path) return API_BASE
  if (/^https?:\/\//i.test(path)) return path // absoluta, dejar como esta
  if (path.startsWith('/api/')) return path
  // Si el path NO trae el prefijo /api/v1, agregarselo.
  // Convencion del codebase: el caller puede omitir el prefijo y se concatena
  // automaticamente. API_BASE ya termina en /api/v1.
  const base = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE
  return path.startsWith('/') ? `${base}${path}` : `${base}/${path}`
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function buildError({ status, code, message, detail }) {
  return { ok: false, status, code, message, detail }
}

function handleUnauthorized() {
  // Limpia sesion y redirige a login. Usa hash routing (Alpine SPA).
  try {
    if (window.Alpine?.store('auth')?.logout) {
      window.Alpine.store('auth').logout()
    }
  } catch (_) {
    /* noop */
  }
  // Solo redirigir si NO estamos ya en login (evita loop)
  const currentHash = window.location.hash || ''
  if (!currentHash.startsWith('#/login')) {
    window.location.hash = '#/login'
  }
}

function showErrorToast(message) {
  if (typeof window.toast === 'function') {
    window.toast(message, 'error')
  } else {
    // Fallback minimo: console + alert (no deberia pasar, toast deberia existir)
    // eslint-disable-next-line no-console
    console.error('[api]', message)
  }
}

/* ─── Funcion principal ─────────────────────────────────────── */

/**
 * Wrapper de fetch con CSRF, retry, timeout y manejo de errores.
 *
 * @param {string} path          Path del endpoint (con o sin prefijo /api/v1).
 * @param {object} [options]     Opciones de fetch extendidas.
 * @param {string} [options.method]      GET | POST | PUT | PATCH | DELETE
 * @param {object} [options.body]        Objeto JS (se serializa a JSON) o FormData/Blob.
 * @param {object} [options.headers]     Headers extra.
 * @param {object} [options.query]       Query string como objeto {k:v}.
 * @param {number} [options.timeout]     Timeout en ms (default 30000).
 * @param {number} [options.retries]     Reintentos en 5xx (default 2).
 * @param {boolean}[options.raw]         Si true, NO parsea JSON; devuelve Response.
 * @param {boolean}[options.silent]      Si true, NO muestra toast en errores.
 * @param {boolean}[options.noRedirect]  Si true, NO redirige en 401.
 * @returns {Promise<{ok:true, data, status, headers} | {ok:false, status, code, message, detail}>}
 */
export async function apiFetch(path, options = {}) {
  const {
    method = 'GET',
    headers: extraHeaders = {},
    body,
    query,
    timeout = DEFAULT_TIMEOUT_MS,
    retries = MAX_RETRIES,
    raw = false,
    silent = false,
    noRedirect = false,
    ...rest
  } = options

  // ─── URL con query string ───
  let url = normalizePath(path)
  if (query && typeof query === 'object') {
    const usp = new URLSearchParams()
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null) continue
      usp.append(k, String(v))
    }
    const qs = usp.toString()
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }

  // ─── Headers base ───
  const headers = { Accept: 'application/json', ...extraHeaders }
  const upperMethod = method.toUpperCase()

  // Body: serializar JSON salvo FormData/Blob
  let finalBody = body
  if (body && !isFormData(body) && !(body instanceof Blob) && !raw) {
    if (!headers['Content-Type'] && !headers['content-type']) {
      headers['Content-Type'] = 'application/json'
    }
    if (typeof body === 'string') {
      finalBody = body
    } else {
      finalBody = JSON.stringify(body)
    }
  }

  // CSRF en metodos no seguros
  if (isUnsafeMethod(upperMethod)) {
    const csrf = getCookie('csrf_token')
    if (csrf) {
      headers['X-CSRF-Token'] = csrf
    }
  }

  // ─── Loop con reintentos ───
  let lastError = null
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeout)
    try {
      const res = await fetch(url, {
        method: upperMethod,
        credentials: 'include',
        headers,
        body: finalBody,
        signal: controller.signal,
        ...rest,
      })
      clearTimeout(timer)

      // 401: sesion expirada
      if (res.status === 401 && !noRedirect) {
        handleUnauthorized()
        return buildError({
          status: 401,
          code: 'UNAUTHORIZED',
          message: 'Sesion expirada. Por favor, inicia sesion nuevamente.',
          detail: null,
        })
      }

      // 5xx / network -> retry
      if (RETRYABLE_STATUS.has(res.status) && attempt < retries) {
        await sleep(2 ** attempt * 400) // 400, 800 ms
        continue
      }

      // 204 No Content
      if (res.status === 204) {
        return { ok: true, data: null, status: 204, headers: res.headers }
      }

      // raw: devolver Response sin parsear
      if (raw) {
        return { ok: res.ok, data: res, status: res.status, headers: res.headers }
      }

      // Parsear respuesta (JSON o no)
      const contentType = res.headers.get('content-type') || ''
      let data = null
      if (contentType.includes('application/json')) {
        try {
          data = await res.json()
        } catch (_) {
          data = null
        }
      } else {
        try {
          data = await res.text()
        } catch (_) {
          data = null
        }
      }

      if (res.ok) {
        return { ok: true, data, status: res.status, headers: res.headers }
      }

      // Error HTTP: construir mensaje legible
      const detail = (data && typeof data === 'object' && data.detail) || null
      const message =
        (typeof detail === 'string' && detail) ||
        (Array.isArray(detail) && detail[0]?.msg) ||
        (typeof data === 'string' && data) ||
        `Error ${res.status} en ${path}`

      const err = buildError({
        status: res.status,
        code: res.status === 403 ? 'FORBIDDEN' : res.status === 404 ? 'NOT_FOUND' : 'HTTP_ERROR',
        message,
        detail,
      })

      if (!silent && res.status >= 500) {
        showErrorToast(message)
      }
      return err
    } catch (e) {
      clearTimeout(timer)
      // AbortError = timeout
      if (e?.name === 'AbortError') {
        lastError = buildError({
          status: 0,
          code: 'TIMEOUT',
          message: `La peticion a ${path} excedio el tiempo limite (${timeout}ms).`,
          detail: null,
        })
      } else {
        lastError = buildError({
          status: 0,
          code: 'NETWORK',
          message: `No se pudo conectar con el servidor (${path}).`,
          detail: e?.message || String(e),
        })
      }
      // Reintentar en errores de red
      if (attempt < retries) {
        await sleep(2 ** attempt * 400)
        continue
      }
      break
    }
  }

  if (!silent) showErrorToast(lastError.message)
  return lastError
}

/* ─── Atajos ergonomicos ────────────────────────────────────── */

export const apiGet = (path, opts = {}) => apiFetch(path, { ...opts, method: 'GET' })
export const apiPost = (path, body, opts = {}) => apiFetch(path, { ...opts, method: 'POST', body })
export const apiPut = (path, body, opts = {}) => apiFetch(path, { ...opts, method: 'PUT', body })
export const apiPatch = (path, body, opts = {}) => apiFetch(path, { ...opts, method: 'PATCH', body })
export const apiDelete = (path, opts = {}) => apiFetch(path, { ...opts, method: 'DELETE' })

/**
 * Descarga un blob del backend (CSV/XLSX/PDF) respetando cookies.
 * Usar para endpoints como GET /usuarios/export?format=excel.
 *
 * @param {string} path
 * @param {object} [opts]
 * @param {string} [opts.filename]  Nombre sugerido para el download.
 * @returns {Promise<{ok:true, blob, filename} | {ok:false, ...}>}
 */
export async function apiDownload(path, opts = {}) {
  const res = await apiFetch(path, { ...opts, raw: true, silent: true })
  if (!res.ok) {
    showErrorToast(res.message || 'Error al descargar el archivo')
    return res
  }
  const blob = await res.data.blob()
  let filename = opts.filename || 'download'
  // Intentar leer Content-Disposition para nombre sugerido por el server
  const cd = res.headers.get('content-disposition') || ''
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd)
  if (m && m[1]) {
    try {
      filename = decodeURIComponent(m[1])
    } catch (_) {
      filename = m[1]
    }
  }
  // Disparar descarga
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
  return { ok: true, blob, filename }
}

/* ─── Exponer para uso inline en Alpine ─────────────────────── */
if (typeof window !== 'undefined') {
  window.apiFetch = apiFetch
  window.apiGet = apiGet
  window.apiPost = apiPost
  window.apiPut = apiPut
  window.apiPatch = apiPatch
  window.apiDelete = apiDelete
  window.apiDownload = apiDownload
}

export default apiFetch
