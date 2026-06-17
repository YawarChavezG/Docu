/**
 * DebugSession.js — Página debug para aislar el bug de persistencia de sesión.
 *
 * Ruta: /_debug/session  (bypass auth + bypass AppLayout, igual que /login)
 *
 * Permite:
 *  1. Ver el estado actual de la sesión (user, role, isAuthenticated, localStorage, cookies)
 *  2. Simular un login "fake" seteando localStorage directamente (sin tocar backend)
 *  3. Simular un F5 (window.location.reload) para ver a dónde redirige
 *  4. Limpiar la sesión
 *  5. Auto-test: set fake session + F5 (REPRO del bug del usuario)
 *
 * No toca el backend. No requiere auth. Pensada para uso con Chrome DevTools.
 */

import { API_BASE } from '../utils/config.js'

const LOG_LIMIT = 80
const fmt = (v) => {
  if (v === null) return 'null'
  if (v === undefined) return 'undefined'
  if (typeof v === 'string') return v
  try { return JSON.stringify(v, null, 2) } catch (_) { return String(v) }
}

function getAllCookies() {
  if (typeof document === 'undefined') return {}
  const out = {}
  for (const raw of (document.cookie || '').split(';')) {
    const c = raw.trim()
    if (!c) continue
    const eq = c.indexOf('=')
    if (eq < 0) {
      out[c] = ''
    } else {
      out[c.slice(0, eq)] = decodeURIComponent(c.slice(eq + 1))
    }
  }
  return out
}

async function callMeEndpoint() {
  try {
    const res = await fetch(`${API_BASE}/me`, {
      method: 'GET',
      credentials: 'include',
    })
    const status = res.status
    const body = await res.json().catch(() => null)
    return { ok: res.ok, status, body }
  } catch (e) {
    return { ok: false, status: 0, error: e.message || String(e) }
  }
}

export const page = {

  init() {
    window.Alpine?.data('debugSessionPage', () => ({
      // ── Estado observable ──
      user: null,
      role: null,
      isAuthenticated: false,
      isReady: false, // NO existe en auth store; lo seteamos manualmente
      currentHash: '',
      localStorageValue: null,
      cookies: {},
      meProbe: null,
      // ── Log interno ──
      logs: [],
      // ── Indicador de fase del test ──
      testPhase: 'idle', // idle | setting_fake | reloading | observing

      init() {
        this.snapshot()
        this.log('init() debug page')
        // Escuchar hashchange para detectar redirects automáticos
        window.addEventListener('hashchange', (e) => {
          this.log(`hashchange → #${window.location.hash}`)
          this.snapshot()
        })
      },

      snapshot() {
        const auth = window.Alpine?.store('auth')
        this.user = auth?.user ?? null
        this.role = auth?.role ?? null
        this.isAuthenticated = !!auth?.isAuthenticated
        this.isReady = auth?.isReady ?? null  // null si no existe la flag
        this.currentHash = window.location.hash || ''
        const raw = localStorage.getItem('cofar_session')
        this.localStorageValue = raw
        this.cookies = getAllCookies()
      },

      log(msg, data = null) {
        const ts = new Date().toISOString().slice(11, 23)
        const entry = data !== null ? `[${ts}] ${msg} ${fmt(data)}` : `[${ts}] ${msg}`
        this.logs = [entry, ...this.logs].slice(0, LOG_LIMIT)
        console.log('[DebugSession]', msg, data ?? '')
      },

      // ── Acción 1: set fake session (sin backend) ──
      setFakeSession() {
        const fakeUser = {
          username: 'aromero',
          nombre_completo: 'Aracely Romero Plata (DEBUG)',
          iniciales: 'AR',
          email: 'aromero@cofar.com',
          cargo: 'ETO (DEBUG)',
          area_id: 1,
          gerencia_sigla: 'ETO',
          area_sigla: 'ETO',
          ad_department: 'ETO',
          ad_physical_delivery_office: null,
          estado: 'activo',
          ausente: false,
          es_impersonado: false,
          modulos: ['TODOS'],
          roles: ['ETO'],
          impersonated_by: null,
          name: 'Aracely Romero Plata (DEBUG)',
          roleLabel: 'ETO (DEBUG)',
          initials: 'AR',
          area: 'ETO',
          hasDelegadoAlert: false,
          requiereDelegadoPorRol: false,
        }
        const fakeRole = 'eto'

        // 1) Setear localStorage
        localStorage.setItem('cofar_session', JSON.stringify({ user: fakeUser, role: fakeRole }))
        this.log('SET localStorage.cofar_session (fake)')

        // 2) Setear el store directamente (sin esperar backend)
        const auth = window.Alpine?.store('auth')
        if (auth) {
          auth.user = fakeUser
          auth.role = fakeRole
          if ('isReady' in auth) auth.isReady = true
        }
        this.log('SET auth.user/role (fake) — isAuthenticated=', auth?.isAuthenticated)

        this.snapshot()
      },

      // ── Acción 2: hard reload (F5) ──
      hardReload() {
        this.log('HARD RELOAD (window.location.reload)')
        window.location.reload()
      },

      // ── Acción 3: limpiar sesión ──
      clearSession() {
        localStorage.removeItem('cofar_session')
        const auth = window.Alpine?.store('auth')
        if (auth) {
          auth.user = null
          auth.role = null
        }
        // Borrar cookies HttpOnly NO se puede desde JS. Solo documentamos.
        this.log('CLEAR localStorage + auth.user (cookies HttpOnly solo via backend /logout)')
        this.snapshot()
      },

      // ── Acción 4: probe directo a /me ──
      async probeMe() {
        this.log('PROBE /me ...')
        const r = await callMeEndpoint()
        this.log('PROBE /me result', r)
        this.meProbe = r
      },

      // ── Acción 5: AUTO-TEST (simula el bug del usuario) ──
      //   1) Set fake session
      //   2) Hard reload (F5)
      //   3) Al volver, esta misma página se re-monta
      //   4) Lo que veamos en `user/role/isAuthenticated` post-reload es el resultado
      async runAutoTest() {
        if (this.testPhase !== 'idle') {
          this.log('AUTO-TEST ya en curso, fase=' + this.testPhase)
          return
        }
        this.testPhase = 'setting_fake'
        this.log('═══ AUTO-TEST START ═══')
        this.setFakeSession()
        this.log('Esperando 500ms antes de recargar...')
        await new Promise(r => setTimeout(r, 500))
        this.testPhase = 'reloading'
        this.log('Recargando...')
        this.hardReload()
        // Después de esto, la página se destruye y se vuelve a montar
      },

      // ── Acción 6: navegar manualmente a una ruta protegida ──
      goTo(route) {
        this.log('NAVIGATE → ' + route)
        window.location.hash = '#' + route
      },

      // ── Acción 7: cambiar hash SIN reload (caso edge) ──
      changeHash() {
        const h = prompt('Nuevo hash (ej: /bandeja):', '/bandeja')
        if (h) {
          this.log('CHANGE HASH → ' + h)
          window.location.hash = '#' + h
        }
      },
    }))
  },

  template: /* html */`
<div x-data="debugSessionPage" class="min-h-screen bg-slate-900 text-slate-100 p-6 font-mono text-sm">
  <div class="max-w-6xl mx-auto space-y-4">

    <!-- Header -->
    <div class="border-b border-slate-700 pb-3 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-amber-400">🧪 Debug Session</h1>
        <p class="text-slate-400 text-xs mt-1">
          Aisla el bug "F5 me bota al login" · Ruta: <code class="text-emerald-400">/_debug/session</code>
        </p>
      </div>
      <button @click="goTo('/login')" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-xs">
        Ir a /login
      </button>
    </div>

    <!-- Estado actual -->
    <section class="grid grid-cols-2 gap-4">
      <div class="bg-slate-800 rounded p-4">
        <h2 class="text-amber-400 font-bold mb-2">📊 Estado del auth store</h2>
        <div class="space-y-1 text-xs">
          <div>hash: <span class="text-cyan-300" x-text="currentHash || '(vacío)'"></span></div>
          <div>isAuthenticated:
            <span :class="isAuthenticated ? 'text-emerald-400' : 'text-red-400'" class="font-bold"
                  x-text="isAuthenticated ? 'TRUE ✓' : 'FALSE ✗'"></span>
          </div>
          <div>isReady (si existe en store):
            <span :class="isReady === true ? 'text-emerald-400' : isReady === false ? 'text-red-400' : 'text-slate-500'"
                  x-text="isReady === null ? '(no existe)' : (isReady ? 'TRUE' : 'FALSE')"></span>
          </div>
          <div>role: <span class="text-cyan-300" x-text="role || 'null'"></span></div>
          <div>user.username: <span class="text-cyan-300" x-text="user?.username || 'null'"></span></div>
          <div>user.nombre_completo: <span class="text-cyan-300" x-text="user?.nombre_completo || 'null'"></span></div>
        </div>
      </div>

      <div class="bg-slate-800 rounded p-4">
        <h2 class="text-amber-400 font-bold mb-2">🍪 Cookies (NO HttpOnly)</h2>
        <div class="text-xs space-y-1">
          <div>csrf_token:
            <span class="text-cyan-300" x-text="cookies.csrf_token ? cookies.csrf_token.substring(0, 40) + '…' : '(ausente)'"></span>
          </div>
          <div class="text-slate-500 italic">session/user_id son HttpOnly — no se ven desde JS</div>
        </div>
      </div>
    </section>

    <!-- localStorage -->
    <section class="bg-slate-800 rounded p-4">
      <h2 class="text-amber-400 font-bold mb-2">💾 localStorage['cofar_session']</h2>
      <pre class="text-xs whitespace-pre-wrap break-all max-h-40 overflow-auto"
           x-text="localStorageValue || '(vacío)'"></pre>
    </section>

    <!-- Acciones -->
    <section class="bg-slate-800 rounded p-4">
      <h2 class="text-amber-400 font-bold mb-3">🎬 Acciones</h2>
      <div class="flex flex-wrap gap-2">
        <button @click="setFakeSession"
                class="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-xs font-bold">
          1. Set fake session (sin backend)
        </button>
        <button @click="hardReload"
                class="px-3 py-2 bg-amber-600 hover:bg-amber-500 rounded text-xs font-bold">
          2. Hard Reload (F5)
        </button>
        <button @click="clearSession"
                class="px-3 py-2 bg-red-600 hover:bg-red-500 rounded text-xs font-bold">
          3. Clear session
        </button>
        <button @click="probeMe"
                class="px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs font-bold">
          4. Probe /me
        </button>
        <button @click="runAutoTest"
                :disabled="testPhase !== 'idle'"
                :class="testPhase !== 'idle' ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-500'"
                class="px-3 py-2 bg-purple-600 rounded text-xs font-bold">
          5. 🚀 AUTO-TEST (set + reload)
          <span x-show="testPhase !== 'idle'" class="ml-1" x-text="'['+testPhase+']'"></span>
        </button>
        <button @click="changeHash"
                class="px-3 py-2 bg-slate-600 hover:bg-slate-500 rounded text-xs">
          6. Change hash (manual)
        </button>
        <button @click="goTo('/bandeja')"
                class="px-3 py-2 bg-cyan-700 hover:bg-cyan-600 rounded text-xs">
          Ir a /bandeja
        </button>
        <button @click="goTo('/parametrizacion')"
                class="px-3 py-2 bg-cyan-700 hover:bg-cyan-600 rounded text-xs">
          Ir a /parametrizacion
        </button>
      </div>
    </section>

    <!-- Resultado probe /me -->
    <section x-show="meProbe" class="bg-slate-800 rounded p-4">
      <h2 class="text-amber-400 font-bold mb-2">🔍 Último probe /me</h2>
      <pre class="text-xs whitespace-pre-wrap break-all max-h-40 overflow-auto"
           x-text="JSON.stringify(meProbe, null, 2)"></pre>
    </section>

    <!-- Log -->
    <section class="bg-slate-800 rounded p-4">
      <h2 class="text-amber-400 font-bold mb-2">📜 Log (más reciente arriba)</h2>
      <div class="text-xs space-y-0.5 max-h-96 overflow-auto font-mono">
        <template x-for="(line, i) in logs" :key="i">
          <div class="text-slate-300" x-text="line"></div>
        </template>
        <div x-show="logs.length === 0" class="text-slate-500 italic">Sin eventos aún.</div>
      </div>
    </section>

    <!-- Instrucciones -->
    <section class="bg-slate-800 rounded p-4 text-xs text-slate-300 space-y-2">
      <h2 class="text-amber-400 font-bold">📖 Cómo reproducir el bug</h2>
      <ol class="list-decimal list-inside space-y-1">
        <li>Ir a <a href="#/login" class="text-cyan-400">#/login</a> y hacer login con BD Local (aromero/cofar.2026).</li>
        <li>Una vez logueado, navegar a cualquier página (ej: /bandeja).</li>
        <li>Volver a <a href="#/_debug/session" class="text-cyan-400">/_debug/session</a>.</li>
        <li>Verificar que <strong>isAuthenticated = TRUE</strong> y localStorage tiene datos.</li>
        <li>Click en "🚀 AUTO-TEST" (setea fake session + F5).</li>
        <li>Al volver la página: observar si la URL cambió a <code class="text-red-400">#/login</code>
            o se mantuvo en <code class="text-emerald-400">/#/_debug/session</code>.</li>
        <li>Si redirige a <code class="text-red-400">#/login</code> → BUG CONFIRMADO.</li>
        <li>Para comparar: click "2. Hard Reload" manual y observar comportamiento idéntico.</li>
      </ol>
      <p class="text-slate-400 italic mt-2">
        Capturar con DevTools → Network tab para ver el orden de las requests a /me, y
        Console tab para ver los logs de <code class="text-emerald-400">[DebugSession]</code>.
      </p>
    </section>

  </div>
</div>
`,
}
