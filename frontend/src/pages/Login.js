/**
 * Login.js — Full-screen login page
 *
 * Design: dark navy background with animated blobs + glassmorphism card
 * Features:
 *   - Quick-fill demo user chips
 *   - Password show/hide toggle
 *   - Loading spinner on submit
 *   - Error message with animation
 *   - Responsive (mobile-first)
 */

export const page = {

  init() {
    window.Alpine?.data('loginPage', () => ({
      username: '',
      password: '',
      showPassword: false,
      loading: false,
      error: '',
      // Fuente de autenticacion: "cofar" (AD real) o "local" (BD local seeded).
      // Por defecto "cofar" — el backend respeta este campo.
      authSource: 'cofar',

      // Pre-fill demo user
      fillDemo(user) {
        this.username = user
        // admin_local usa admin.2026, los demas usan cofar.2026
        this.password = user === 'admin_local' ? 'admin.2026' : 'cofar.2026'
        // Si el usuario es uno de los locales, cambiamos el modo a "local"
        const localUsers = ['admin_local', 'eto_test', 'elaborador_revisor', 'elaborador_revisor_aprobador', 'visualizador_cl']
        if (localUsers.includes(user)) {
          this.authSource = 'local'
        }
        this.error = ''
        this.$nextTick(() => {
          document.getElementById('login-submit')?.focus()
        })
      },

      async submit() {
        this.error = ''

        if (!this.username.trim() || !this.password) {
          this.error = 'Por favor, completa todos los campos.'
          return
        }

        this.loading = true

        // Llamada real al backend (FastAPI /api/v1/login)
        const result = await window.Alpine.store('auth').login(
          this.username.trim(),
          this.password,
          this.authSource
        )

        if (result.ok) {
          const home = window.Alpine.store('auth').homeRoute
          window.location.hash = '#' + home
        } else {
          this.error = result.message || 'Usuario o contraseña incorrectos. Verifica tus credenciales.'
          this.loading = false
          this.$nextTick(() => {
            document.getElementById('login-password')?.focus()
          })
        }
      },
    }))
  },

  template: /* html */`
<div class="min-h-screen flex flex-col items-center justify-center relative overflow-hidden"
     style="background: radial-gradient(ellipse at 25% 40%, rgba(29,78,216,0.18) 0%, transparent 55%),
                        radial-gradient(ellipse at 75% 15%, rgba(99,102,241,0.15) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 85%, rgba(14,165,233,0.12) 0%, transparent 50%),
                        linear-gradient(145deg, #060d1a 0%, #0f2244 50%, #111827 100%);">

  <!-- ══ Animated ambient blobs ══════════════════════════════ -->
  <div aria-hidden="true" class="pointer-events-none select-none absolute inset-0 overflow-hidden">
    <!-- Blob 1 — blue, top-left -->
    <div class="absolute -top-20 -left-20 w-[500px] h-[500px] rounded-full opacity-[0.22] animate-blob"
         style="background: radial-gradient(circle, #3b82f6, #1d4ed8); filter: blur(72px); animation-duration: 14s;">
    </div>
    <!-- Blob 2 — indigo, top-right -->
    <div class="absolute top-10 right-0 w-[420px] h-[420px] rounded-full opacity-[0.18] animate-blob"
         style="background: radial-gradient(circle, #818cf8, #4f46e5); filter: blur(80px); animation-duration: 18s; animation-delay: -5s;">
    </div>
    <!-- Blob 3 — cyan, bottom-center -->
    <div class="absolute -bottom-24 left-1/3 w-[380px] h-[380px] rounded-full opacity-[0.14] animate-blob-slow"
         style="background: radial-gradient(circle, #22d3ee, #0284c7); filter: blur(90px); animation-delay: -9s;">
    </div>
  </div>

  <!-- ══ Dot-grid overlay ═════════════════════════════════════ -->
  <div aria-hidden="true"
       class="pointer-events-none absolute inset-0 bg-grid-dot bg-grid-md opacity-100">
  </div>

  <!-- ══ Login card ══════════════════════════════════════════ -->
  <div class="relative z-10 w-full max-w-[400px] mx-4 animate-slide-up"
       x-data="loginPage">

    <div class="glass-card rounded-3xl p-9 shadow-glass-card border border-white/60"
         style="box-shadow: 0 24px 64px -8px rgba(7,17,30,0.6), 0 8px 24px -4px rgba(7,17,30,0.4), inset 0 1px 0 rgba(255,255,255,0.9);">

      <!-- ── Logo ─────────────────────────────────────────── -->
      <div class="text-center mb-7">
        <img src="/src/assets/logo-cofar.png" class="w-48 mx-auto mb-6 object-contain" alt="COFAR" />

        <h1 class="text-[22px] font-extrabold text-brand-900 leading-none tracking-tight">
          COFAR <span class="text-brand-500">·</span> SGD
        </h1>
        <p class="text-slate-400 text-[12px] mt-1.5 font-medium tracking-wide">
          Sistema de Gestión Documental v2.0
        </p>
      </div>

      <!-- ── Selector de fuente de autenticacion ──────────────── -->
      <div class="mb-5">
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
          Fuente de autenticación
        </p>
        <div class="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
          <label class="cursor-pointer">
            <input type="radio" x-model="authSource" value="cofar" class="peer sr-only">
            <div class="text-center py-2 px-2 rounded-lg text-[11px] font-semibold
                        text-slate-500 peer-checked:bg-white peer-checked:text-blue-700
                        peer-checked:shadow-sm transition-all duration-150
                        peer-checked:[&>span]:text-blue-600">
              <span class="block text-base">🌐</span>
              <span>COFAR AD</span>
              <span class="block text-[9px] font-normal text-slate-400 peer-checked:text-blue-500">usuarios reales</span>
            </div>
          </label>
          <label class="cursor-pointer">
            <input type="radio" x-model="authSource" value="local" class="peer sr-only">
            <div class="text-center py-2 px-2 rounded-lg text-[11px] font-semibold
                        text-slate-500 peer-checked:bg-white peer-checked:text-emerald-700
                        peer-checked:shadow-sm transition-all duration-150">
              <span class="block text-base">🧪</span>
              <span>BD Local</span>
              <span class="block text-[9px] font-normal text-slate-400">5 usuarios de test</span>
            </div>
          </label>
        </div>
      </div>

      <!-- ── Demo quick-fill chips ─────────────────────────── -->
      <div class="mb-6" x-show="authSource === 'local'">
        <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2.5">
          Acceso rápido · 5 usuarios locales
        </p>
        <div class="grid grid-cols-2 gap-2">

          <!-- admin_local (ADMIN) -->
          <button type="button"
                  @click="fillDemo('admin_local')"
                  class="group flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200
                         bg-slate-50 hover:bg-violet-50 hover:border-violet-200
                         transition-all duration-150 text-left cursor-pointer">
            <span class="w-5 h-5 rounded-full bg-violet-600 flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0">CM</span>
            <div class="min-w-0">
              <p class="text-[11px] font-semibold text-slate-700 group-hover:text-violet-700 truncate leading-tight">admin_local</p>
              <p class="text-[9.5px] text-slate-400 leading-tight">Admin</p>
            </div>
          </button>

          <!-- eto_test (ETO) -->
          <button type="button"
                  @click="fillDemo('eto_test')"
                  class="group flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200
                         bg-slate-50 hover:bg-blue-50 hover:border-blue-200
                         transition-all duration-150 text-left cursor-pointer">
            <span class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0">PV</span>
            <div class="min-w-0">
              <p class="text-[11px] font-semibold text-slate-700 group-hover:text-blue-700 truncate leading-tight">eto_test</p>
              <p class="text-[9.5px] text-slate-400 leading-tight">ETO</p>
            </div>
          </button>

          <!-- elaborador_revisor -->
          <button type="button"
                  @click="fillDemo('elaborador_revisor')"
                  class="group flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200
                         bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200
                         transition-all duration-150 text-left cursor-pointer">
            <span class="w-5 h-5 rounded-full bg-emerald-600 flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0">RS</span>
            <div class="min-w-0">
              <p class="text-[11px] font-semibold text-slate-700 group-hover:text-emerald-700 truncate leading-tight">elaborador_revisor</p>
              <p class="text-[9.5px] text-slate-400 leading-tight">Elaborador</p>
            </div>
          </button>

          <!-- elaborador_revisor_aprobador -->
          <button type="button"
                  @click="fillDemo('elaborador_revisor_aprobador')"
                  class="group flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200
                         bg-slate-50 hover:bg-amber-50 hover:border-amber-200
                         transition-all duration-150 text-left cursor-pointer">
            <span class="w-5 h-5 rounded-full bg-amber-600 flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0">MF</span>
            <div class="min-w-0">
              <p class="text-[11px] font-semibold text-slate-700 group-hover:text-amber-700 truncate leading-tight">elab._revisor_aprob.</p>
              <p class="text-[9.5px] text-slate-400 leading-tight">Elaborador+Aprobador</p>
            </div>
          </button>

          <!-- visualizador_cl -->
          <button type="button"
                  @click="fillDemo('visualizador_cl')"
                  class="group flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200
                         bg-slate-50 hover:bg-slate-100 hover:border-slate-300
                         transition-all duration-150 text-left cursor-pointer">
            <span class="w-5 h-5 rounded-full bg-slate-500 flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0">DQ</span>
            <div class="min-w-0">
              <p class="text-[11px] font-semibold text-slate-700 group-hover:text-slate-800 truncate leading-tight">visualizador_cl</p>
              <p class="text-[9.5px] text-slate-400 leading-tight">Visualizador</p>
            </div>
          </button>

        </div>
      </div>

      <!-- ── Form ──────────────────────────────────────────── -->
      <form @submit.prevent="submit" novalidate class="space-y-4">

        <!-- Username -->
        <div>
          <label for="login-username" class="form-label">Usuario</label>
          <div class="relative">
            <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <div class="w-4 h-4 text-slate-400" x-html="$icon('user')"></div>
            </div>
            <input
              id="login-username"
              type="text"
              class="form-input form-input-icon"
              placeholder="aromero, admin, solicitante…"
              x-model="username"
              :disabled="loading"
              autocomplete="username"
              autocapitalize="off"
              spellcheck="false"
              @keydown.enter.prevent="submit"
            />
          </div>
        </div>

        <!-- Password -->
        <div>
          <label for="login-password" class="form-label">Contraseña</label>
          <div class="relative">
            <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <div class="w-4 h-4 text-slate-400" x-html="$icon('lock')"></div>
            </div>
            <input
              id="login-password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input form-input-icon pr-10"
              placeholder="••••••••"
              x-model="password"
              :disabled="loading"
              autocomplete="current-password"
              @keydown.enter.prevent="submit"
            />
            <!-- Eye toggle -->
            <button type="button"
                    @click="showPassword = !showPassword"
                    class="absolute inset-y-0 right-0 flex items-center pr-3
                           text-slate-400 hover:text-slate-600 transition-colors duration-150"
                    :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'">
              <!-- Eye open -->
              <div x-show="!showPassword" class="w-4 h-4" x-html="$icon('eye')"></div>
              <!-- Eye slash -->
              <div x-show="showPassword" class="w-4 h-4" x-html="$icon('eye-off')" style="display:none;"></div>
            </button>
          </div>
          <p class="form-hint" x-show="authSource === 'local'">
            Demo: <code class="font-mono bg-slate-100 px-1.5 py-px rounded-md text-[10px] text-slate-600">cofar.2026</code>
            (admin_local: <code class="font-mono bg-slate-100 px-1.5 py-px rounded-md text-[10px] text-slate-600">admin.2026</code>)
          </p>
          <p class="form-hint" x-show="authSource === 'cofar'">
            Usá tu usuario y contraseña del AD corporativo.
          </p>
        </div>

        <!-- Error message -->
        <div x-show="error"
             x-transition:enter="transition-all duration-200"
             x-transition:enter-start="opacity-0 -translate-y-1"
             x-transition:enter-end="opacity-100 translate-y-0"
             class="flex items-start gap-2.5 bg-red-50 border border-red-200 rounded-xl px-3.5 py-2.5"
             style="display:none;">
          <svg class="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
          </svg>
          <p class="text-[11.5px] text-red-700 font-medium leading-snug" x-text="error"></p>
        </div>

        <!-- Submit button -->
        <button
          id="login-submit"
          type="submit"
          :disabled="loading"
          class="w-full btn btn-xl btn-primary justify-center gap-3 mt-2
                 disabled:opacity-70 disabled:cursor-not-allowed"
          style="background: linear-gradient(135deg, #1a5fb4 0%, #1d4ed8 100%);
                 border-color: transparent;
                 box-shadow: 0 4px 14px rgba(26,95,180,0.4);">

          <!-- Spinner -->
          <svg x-show="loading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" style="display:none;">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="white" stroke-width="4"/>
            <path class="opacity-75" fill="white" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>

          <!-- Arrow icon -->
          <svg x-show="!loading" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 11-2 0V4a1 1 0 011-1zm7.707 3.293a1 1 0 010 1.414L9.414 9H17a1 1 0 110 2H9.414l1.293 1.293a1 1 0 01-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" clip-rule="evenodd"/>
          </svg>

          <span x-text="loading ? 'Verificando…' : 'Iniciar Sesión'">Iniciar Sesión</span>
        </button>

      </form>

    </div><!-- /glass-card -->

    <!-- Footer below card -->
    <p class="text-center text-white/25 text-[11px] mt-6 font-medium tracking-wide">
      © 2026 COFAR · Sistema de Gestión Documental
      <span class="mx-1.5 opacity-50">·</span>
      <span class="text-white/20">v2.0</span>
    </p>

  </div><!-- /card wrapper -->

</div><!-- /full-screen -->
  `,
}
