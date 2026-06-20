/**
 * AppLayout.js — Main application shell
 *
 * Renders once and persists across page navigations.
 * The router only swaps #page-content.
 *
 * Exports: { AppLayout: { render(auth), init() } }
 */

import { AuthModalTemplate } from '../components/AuthModal.js'
import { ProfileModalTemplate }   from '../components/ProfileModal.js'
import { TimelineModalTemplate }  from '../components/TimelineModal.js'
import { PdfViewerModalTemplate, CertificadoPdfTemplate } from '../components/PdfViewerModal.js'
import { AlcanceModalTemplate }       from '../components/AlcanceModal.js'
import { ParametrosDifusionModalTemplate } from '../components/ParametrosDifusionModal.js'
import { ConfirmLiberacionModalTemplate }  from '../components/ConfirmLiberacionModal.js'
import { DelegarTareaModalTemplate }        from '../components/DelegarTareaModal.js'
import { AuthRecepcionModalTemplate }       from '../components/AuthRecepcionModal.js'
import { AuthDevolucionModalTemplate }       from '../components/AuthDevolucionModal.js'
import { ExamConfirmModalTemplate }         from '../components/ExamConfirmModal.js'
import { RespuestasExamenModalTemplate }    from '../components/RespuestasExamenModal.js'
import { ConfirmCancelModalTemplate }       from '../components/ConfirmCancelModal.js'
import { ConfirmDeleteModalTemplate }       from '../components/ConfirmDeleteModal.js'
import { EditUserModalTemplate }            from '../components/EditUserModal.js'
import { MoveAreaModalTemplate }            from '../components/MoveAreaModal.js'
import { ObsolescenciaModalTemplate }       from '../components/ObsolescenciaModal.js'
import { LoadingOverlay }                    from '../components/LoadingOverlay.js'

/* ── SVG icon helper ─────────────────────────────────────────── */
const ic = (d, extra = '') =>
  `<svg class="w-3.5 h-3.5 flex-shrink-0 opacity-75 ${extra}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`

const ICONS = {
  bandeja:   ic('<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>'),
  lista:     ic('<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>'),
  search:    ic('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
  copias:    ic('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'),
  chart:     ic('<rect x="2" y="2" width="12" height="12" rx="1.5"/><path d="M5 10l2-3 2 2 2-4"/>'),
  report:    ic('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>'),
  eval:      ic('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>'),
  folder:    ic('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'),
  newDoc:    ic('<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>'),
  ai:        ic('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="10" r="1"/>'),
  settings:  ic('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'),
  chevron:   ic('<polyline points="6 9 12 15 18 9"/>', 'transition-transform duration-200'),
  warn:      ic('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'),
  menu:      ic('<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>'),
  bell:      ic('<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'),
}

/* ── Nav link helper ─────────────────────────────────────────── */
const navLink = (route, icon, label, showBadge = false) => `
  <a href="#${route}"
     data-route="${route}"
     class="nav-item"
     @click="closeSidebar()">
    ${icon}
    <span class="truncate">${label}</span>
    ${showBadge ? `<span class="nav-badge" x-show="$store.notificaciones.total > 0" x-text="$store.notificaciones.total"></span>` : ''}
  </a>`

/* ── Nav submenu helper ──────────────────────────────────────── */
const navGroup = (key, icon, label, children) => `
  <button type="button"
          class="nav-item w-full text-left"
          @click="toggleSubmenu('${key}')">
    ${icon}
    <span class="truncate flex-1">${label}</span>
    <span :class="isSubmenuOpen('${key}') ? 'rotate-180' : ''"
          class="transition-transform duration-200 opacity-60">
      ${ic('<polyline points="6 9 12 15 18 9"/>')}
    </span>
  </button>
  <div class="nav-submenu ml-4 pl-2"
       x-show="isSubmenuOpen('${key}')"
       x-transition:enter="transition-all duration-200 ease-out"
       x-transition:enter-start="opacity-0 -translate-y-2"
       x-transition:enter-end="opacity-100 translate-y-0"
       x-transition:leave="transition-all duration-150 ease-in"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0">
    ${children}
  </div>`

/* ── Role nav configs ────────────────────────────────────────── */
function buildNav(role) {
  const ETO_NAV = `
    <div class="nav-section">Mi Espacio</div>
    ${navLink('/bandeja', ICONS.bandeja, 'Mi Bandeja', true)}

    <div class="nav-section">Documentación</div>
    ${navLink('/lista', ICONS.lista, 'Lista Maestra')}
    ${navLink('/consulta', ICONS.search, 'Consultar Documentos')}

    <div class="nav-section">Consultas</div>
    ${navGroup('/copias', ICONS.copias, 'Monitor de Copias', `
      ${navLink('/copias-cc', '', 'Copias Controladas')}
      ${navLink('/copias-cn', '', 'Copias No Controladas')}
    `)}
    ${navLink('/publicacion', ICONS.chart, 'Monitor de Eval. / Controles')}
    ${navLink('/reportes', ICONS.report, 'Reportes')}
    ${navGroup('/eval', ICONS.eval, 'Mis Evaluaciones', `
      ${navLink('/evaluaciones', '', 'Evaluaciones y Controles de Lectura')}
      ${navLink('/certificados', '', 'Mis Certificados')}
    `)}

    <div class="nav-section">Flujo Documental</div>
    ${navLink('/plantillas', ICONS.folder, 'Plantillas Documentales')}
    ${navGroup('/solicitud', ICONS.newDoc, 'Nueva Solicitud', `
      ${navLink('/version-editable',     '', 'Documento en versión editable')}
      ${navLink('/aprobacion-documento', '', 'Aprobación de un documento')}
    `)}
    ${navLink('/chat', ICONS.ai, 'Asistente IA (BD)')}

    <div class="nav-section mt-2 border-t border-white/10 pt-3">Configuración</div>
    ${navLink('/parametrizacion', ICONS.settings, 'Parametrización General')}
  `

  const USER_NAV = `
    <div class="nav-section">Mi Espacio</div>
    ${navLink('/bandeja', ICONS.bandeja, 'Mi Bandeja', true)}

    <div class="nav-section">Documentación</div>
    ${navLink('/lista', ICONS.lista, 'Lista Maestra')}

    <div class="nav-section">Consultas</div>
    ${navLink('/consulta', ICONS.search, 'Consultar Documentos')}
    ${navGroup('/eval', ICONS.eval, 'Mis Evaluaciones', `
      ${navLink('/evaluaciones', '', 'Evaluaciones y Controles de Lectura')}
      ${navLink('/certificados', '', 'Mis Certificados')}
    `)}

    <div class="nav-section">Flujo Documental</div>
    ${navLink('/plantillas', ICONS.folder, 'Plantillas Documentales')}
    ${navGroup('/solicitud', ICONS.newDoc, 'Nueva Solicitud', `
      ${navLink('/version-editable',     '', 'Documento en versión editable')}
      ${navLink('/aprobacion-documento', '', 'Aprobación de un documento')}
    `)}
    ${navLink('/chat', ICONS.ai, 'Asistente IA (BD)')}
  `

  const ADMIN_NAV = `
    <div class="nav-section">Configuración del Sistema</div>
    ${navLink('/parametrizacion', ICONS.settings, 'Parametrización General')}
  `

  const VIS_NAV = `
    <div class="nav-section">Mi Espacio</div>
    ${navLink('/bandeja', ICONS.bandeja, 'Mi Bandeja')}

    <div class="nav-section">Documentación</div>
    ${navLink('/lista', ICONS.lista, 'Lista Maestra')}

    <div class="nav-section">Consultas</div>
    ${navGroup('/eval', ICONS.eval, 'Mis Evaluaciones', `
      ${navLink('/evaluaciones', '', 'Evaluaciones y Controles de Lectura')}
      ${navLink('/certificados', '', 'Mis Certificados')}
    `)}
    ${navLink('/chat', ICONS.ai, 'Asistente IA (BD)')}
  `

  const navMap = { eto: ETO_NAV, user: USER_NAV, admin: ADMIN_NAV, visualizador: VIS_NAV }
  return navMap[role] ?? USER_NAV
}

/* ── Delegado alert banner ───────────────────────────────────── */
const delegadoAlert = `
  <div x-show="$store.auth.user?.hasDelegadoAlert"
       x-transition:enter="transition-all duration-300"
       x-transition:enter-start="opacity-0 -translate-y-2"
       x-transition:enter-end="opacity-100 translate-y-0"
       class="mx-2 mb-3">
    <button type="button"
            @click="window.dispatchEvent(new CustomEvent('open-profile'))"
            class="w-full flex items-start gap-2.5 bg-orange-900/80 hover:bg-orange-800/90
                   border border-orange-600/50 text-orange-100 rounded-xl px-3 py-2.5
                   text-left transition-all duration-200 cursor-pointer group
                   animate-pulse-ring">
      <span class="flex-shrink-0 mt-0.5 text-orange-400">
        ${ic('<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>')}
      </span>
      <div>
        <p class="text-[11px] font-semibold leading-tight">Sin delegado activo</p>
        <p class="text-[9.5px] text-orange-300/80 mt-0.5 leading-tight">Delegado anterior desvinculado</p>
      </div>
    </button>
  </div>`

/* ── Full layout HTML ────────────────────────────────────────── */
export const AppLayout = {
  init() {
    // Nothing to register here — appLayout data is in main.js
  },

  render(auth) {
    const nav = buildNav(auth.role)
    const roleColors = {
      eto:         'bg-blue-600',
      user:        'bg-emerald-600',
      admin:       'bg-violet-600',
      visualizador:'bg-slate-500',
    }
    const avatarBg = roleColors[auth.role] || 'bg-slate-600'

    return /* html */`
<div class="flex h-full overflow-hidden" x-data="appLayout">

  <!-- ════════════════════════════════════════════════════════
       MOBILE OVERLAY
  ════════════════════════════════════════════════════════ -->
  <div class="fixed inset-0 z-[999] bg-black/60 backdrop-blur-sm lg:hidden"
       x-show="sidebarOpen"
       x-transition:enter="transition-opacity duration-200"
       x-transition:enter-start="opacity-0"
       x-transition:enter-end="opacity-100"
       x-transition:leave="transition-opacity duration-150"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0"
       @click="closeSidebar()"
       style="display:none;">
  </div>

  <!-- ════════════════════════════════════════════════════════
       SIDEBAR
  ════════════════════════════════════════════════════════ -->
  <aside class="fixed lg:static inset-y-0 left-0 z-[1000] flex flex-col w-[220px] flex-shrink-0
                transition-transform duration-300 ease-out
                lg:translate-x-0"
         :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
         style="background: linear-gradient(180deg, #0c1d3d 0%, #0f2244 60%, #0a1628 100%);">

    <!-- Logo -->
    <div class="flex-shrink-0 px-5 py-5 border-b border-white/8">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center flex-shrink-0 shadow-lg">
          <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
        </div>
        <div>
          <div class="text-white font-bold text-[15px] leading-none">COFAR <span class="text-brand-400">·</span> SGD</div>
          <div class="text-white/35 text-[9px] mt-0.5 tracking-wide">Gestión Documental v2.0</div>
        </div>
      </div>
    </div>

    <!-- Navigation scroll area -->
    <nav class="flex-1 overflow-y-auto overflow-x-hidden py-3 scrollbar-hide">
      ${nav}
    </nav>

    <!-- Delegado alert -->
    ${delegadoAlert}

    <!-- User info + actions -->
    <div class="flex-shrink-0 border-t border-white/8 px-3 py-3 space-y-2">
      <div class="flex items-center gap-2.5 px-1">
        <div class="w-7 h-7 rounded-full ${avatarBg} flex items-center justify-center
                    text-[10px] font-bold text-white flex-shrink-0 shadow-inner-glow">
          ${auth.user?.initials ?? '?'}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-white text-[11.5px] font-medium truncate">${auth.user?.name ?? ''}</p>
          <p class="text-white/35 text-[9px] truncate">${auth.user?.roleLabel ?? ''}</p>
        </div>
      </div>

      <button type="button"
              @click="openProfile()"
              class="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg
                     text-white/60 text-[11px] font-medium
                     hover:bg-white/10 hover:text-white transition-colors duration-150 cursor-pointer">
        ${ic('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>')}
        Mi Perfil
      </button>

      <button type="button"
              @click="logout()"
              class="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg
                     bg-red-500/15 text-red-400 text-[11px] font-medium
                     hover:bg-red-500/25 hover:text-red-300 transition-colors duration-150 cursor-pointer">
        ${ic('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>')}
        Cerrar Sesión
      </button>
    </div>
  </aside>

  <!-- ════════════════════════════════════════════════════════
       IMPERSONATE BANNER (Sesion 17)
       Sticky top banner que aparece SOLO cuando el admin/ETO esta
       impersonando a otro usuario. Visible en TODAS las paginas
       autenticadas (porque vive en el AppLayout, fuera del slot
       de page-content). El boton "Terminar" llama al endpoint
       POST /admin/impersonate/stop y refresca el store.
  ════════════════════════════════════════════════════════ -->
  <div x-show="$store.auth.user?.impersonated_by"
       x-cloak
       x-transition:enter="transition-all duration-200 ease-out"
       x-transition:enter-start="opacity-0 -translate-y-2"
       x-transition:enter-end="opacity-100 translate-y-0"
       x-transition:leave="transition-all duration-150 ease-in"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0"
       class="fixed top-0 left-0 right-0 z-[2000] bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 text-white shadow-lg">
    <div class="flex items-center justify-between gap-3 px-4 py-2.5 max-w-screen-2xl mx-auto">
      <div class="flex items-center gap-2.5 min-w-0">
        <span class="text-lg flex-shrink-0">🕵️</span>
        <div class="text-[12.5px] font-medium leading-tight min-w-0">
          <div class="truncate">
            <span class="font-bold">Impersonando a:</span>
            <span class="font-semibold" x-text="$store.auth.user?.nombre_completo"></span>
            <span class="opacity-80 font-mono" x-text="'(' + $store.auth.user?.username + ')'"></span>
          </div>
          <div class="text-[10.5px] opacity-90 truncate">
            <span>Sesión real: </span>
            <span class="font-mono font-semibold" x-text="$store.auth.user?.impersonated_by"></span>
            <span> · Los cambios se ejecutan como el usuario impersonado. Esta acción queda registrada en auditoría.</span>
          </div>
        </div>
      </div>
      <button type="button"
              @click="window.dispatchEvent(new CustomEvent('sgd-stop-impersonate'))"
              class="flex-shrink-0 px-3 py-1.5 rounded-lg bg-white/20 hover:bg-white/30 active:bg-white/40 border border-white/30 text-white text-[11px] font-bold transition-colors cursor-pointer">
        ✕ Terminar Impersonate
      </button>
    </div>
  </div>

  <!-- ════════════════════════════════════════════════════════
       MAIN CONTENT AREA
  ════════════════════════════════════════════════════════ -->
  <div class="flex flex-col flex-1 min-w-0 overflow-hidden"
       :class="$store.auth.user?.impersonated_by ? 'pt-[60px]' : ''">

    <!-- Topbar -->
    <header class="flex-shrink-0 h-14 bg-white border-b border-slate-200 flex items-center gap-3 px-4 lg:px-5 shadow-card">
      <!-- Mobile menu button -->
      <button type="button"
              @click="toggleSidebar()"
              class="lg:hidden p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
              aria-label="Menú">
        ${ic('<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>')}
      </button>

      <!-- Page title (dynamic) -->
      <div class="flex-1 text-sm font-semibold text-slate-800 truncate" id="topbar-title" x-text="$store.app.pageTitle">
        COFAR · Sistema de Gestión Documental
      </div>

      <!-- Right actions -->
      <div class="flex items-center gap-2">
        <!-- Role badge -->
        <span class="hidden sm:inline-flex badge badge-blue">
          ${auth.user?.roleLabel ?? ''}
        </span>

        <!-- Notifications dropdown -->
        <div class="relative" x-data="{ ndOpen: false }" @click.away="ndOpen = false">
          <button type="button"
                  class="relative p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                  @click="ndOpen = !ndOpen"
                  aria-label="Notificaciones">
            ${ICONS.bell}
            <!-- Indicador de notificaciones -->
            <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full ring-1 ring-white"
                  x-show="$store.notificaciones.total > 0 && $store.notificaciones.total < 10"></span>
            <span class="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center ring-1 ring-white"
                  x-show="$store.notificaciones.total > 9"
                  x-text="$store.notificaciones.total"></span>
          </button>

          <!-- Dropdown panel -->
          <div x-show="ndOpen"
               x-transition:enter="transition ease-out duration-150"
               x-transition:enter-start="opacity-0 scale-95 -translate-y-1"
               x-transition:enter-end="opacity-100 scale-100 translate-y-0"
               x-transition:leave="transition ease-in duration-100"
               x-transition:leave-start="opacity-100 scale-100 translate-y-0"
               x-transition:leave-end="opacity-0 scale-95 -translate-y-1"
               class="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-card-hover border border-slate-200/80 overflow-hidden z-[1001]"
               style="display:none;">

            <!-- Estado vacío -->
            <template x-if="$store.notificaciones.total === 0">
              <div class="p-6 text-center">
                <div class="w-10 h-10 mx-auto mb-2 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
                  ${ic('<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>')}
                </div>
                <p class="text-xs text-slate-500 font-medium">No hay notificaciones pendientes</p>
              </div>
            </template>

            <!-- Lista de notificaciones -->
            <template x-if="$store.notificaciones.total > 0">
              <div>
                <!-- Header del dropdown -->
                <div class="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
                  <span class="text-[10.5px] font-bold text-slate-500 uppercase tracking-wider">Notificaciones Pendientes</span>
                  <span class="nav-badge" x-text="$store.notificaciones.total"></span>
                </div>

                <!-- Items scrollables -->
                <div class="max-h-[360px] overflow-y-auto scrollbar-hide">
                  <template x-for="n in $store.notificaciones.items" :key="n.id">
                    <a :href="'#' + n.ruta"
                       @click="ndOpen = false; closeSidebar()"
                       class="flex items-start gap-3 px-4 py-3 hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0 group cursor-pointer">
                      <!-- Indicador de prioridad -->
                      <div class="mt-1.5 flex-shrink-0">
                        <span class="block w-2 h-2 rounded-full"
                              :class="n.dotColor"></span>
                      </div>
                      <!-- Contenido -->
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-0.5">
                          <span class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded"
                                :class="[n.badgeBg, n.badgeText]"
                                x-text="n.tipo"></span>
                        </div>
                        <div class="text-[11px] font-mono font-semibold text-slate-700 leading-tight"
                             x-text="n.codigo"></div>
                        <div class="text-[11px] text-slate-600 truncate leading-tight mt-0.5"
                             x-text="n.nombre"></div>
                        <div class="text-[10px] text-slate-400 mt-0.5 flex items-center gap-1.5">
                          <span x-text="n.categoria"></span>
                          <span class="w-0.5 h-0.5 rounded-full bg-slate-300"></span>
                          <span x-text="n.fecha"></span>
                        </div>
                      </div>
                      <!-- Flecha de acción (hover) -->
                      <div class="flex-shrink-0 self-center opacity-0 group-hover:opacity-100 transition-opacity">
                        ${ic('<polyline points="9 18 15 12 9 6"/>', 'text-slate-400')}
                      </div>
                    </a>
                  </template>
                </div>

                <!-- Footer del dropdown -->
                <div class="px-4 py-2.5 border-t border-slate-100 bg-slate-50/60">
                  <a href="#/bandeja"
                     @click="ndOpen = false; closeSidebar()"
                     class="text-[11px] font-semibold text-brand-600 hover:text-brand-700 transition-colors">
                    Ver todas en Mi Bandeja →
                  </a>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </header>

    <!-- ── Page content slot ── -->
    <main id="page-content"
          class="flex-1 overflow-y-auto overflow-x-hidden p-4 lg:p-5 bg-slate-50 animate-fade-in-page">
      <!-- Router injects page HTML here -->
    </main>
  </div>

  <!-- ════════════════════════════════════════════════════════
       MODALES GLOBALES (fuera del flujo de páginas)
  ════════════════════════════════════════════════════════ -->
  ${AuthModalTemplate}
  ${ProfileModalTemplate}
  ${TimelineModalTemplate}
  ${PdfViewerModalTemplate}
  ${CertificadoPdfTemplate}
  ${AlcanceModalTemplate}
  ${ParametrosDifusionModalTemplate}
  ${ConfirmLiberacionModalTemplate}
  ${DelegarTareaModalTemplate}
  ${AuthRecepcionModalTemplate}
  ${AuthDevolucionModalTemplate}
  ${ExamConfirmModalTemplate}
  ${RespuestasExamenModalTemplate}
  ${ConfirmCancelModalTemplate}
  ${ConfirmDeleteModalTemplate}
  ${EditUserModalTemplate}
  ${MoveAreaModalTemplate}
  ${ObsolescenciaModalTemplate}

  ${LoadingOverlay}

</div>
    `
  },
}
