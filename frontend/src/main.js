/**
 * main.js — Application bootstrap
 *
 * Order matters:
 *  1. Import Alpine
 *  2. Register stores (MUST be before Alpine.start())
 *  3. Register global Alpine.data components
 *  4. Inject modal templates that live outside AppLayout
 *  5. Expose Alpine globally (for initTree in router)
 *  6. Start Alpine
 *  7. Init toast magic + router
 */

import Alpine from 'alpinejs'
import DOMPurify from 'dompurify'
import { authStore }       from './store/auth.js'
import { flowStore }       from './store/flow.js'
import { notificacionesStore } from './store/notificaciones.js'
import { appStore }        from './store/app.js'
import { icons }           from './utils/icons.js'
import { initToast }       from './components/Toast.js'
import { initRouter }      from './router/index.js'
import { initAuthModal }           from './components/AuthModal.js'
import { initProfileModal }       from './components/ProfileModal.js'
import { initTimelineModal }       from './components/TimelineModal.js'
import { initPdfViewerModal }      from './components/PdfViewerModal.js'
import { initAlcanceModal }        from './components/AlcanceModal.js'
import { initParametrosDifusionModal } from './components/ParametrosDifusionModal.js'
import { initConfirmLiberacionModal }  from './components/ConfirmLiberacionModal.js'
import { initDelegarTareaModal }       from './components/DelegarTareaModal.js'
import { initAuthRecepcionModal }      from './components/AuthRecepcionModal.js'
import { initAuthDevolucionModal }      from './components/AuthDevolucionModal.js'
import { initExamConfirmModal }         from './components/ExamConfirmModal.js'
import { initRespuestasExamenModal }    from './components/RespuestasExamenModal.js'
import { initObsolescenciaModal, ObsolescenciaModalTemplate } from './components/ObsolescenciaModal.js'
import { initConfirmCancelModal, ConfirmCancelModalTemplate } from './components/ConfirmCancelModal.js'
import { initConfirmDeleteModal } from './components/ConfirmDeleteModal.js'
import { initEditUserModal } from './components/EditUserModal.js'
import { initMoveAreaModal } from './components/MoveAreaModal.js'

/* ── 1. Register Alpine stores ──────────────────────────────── */
Alpine.store('app', appStore)
Alpine.store('auth', authStore)
Alpine.store('flow', flowStore)
Alpine.store('notificaciones', notificacionesStore)
Alpine.store('auth').init()

/* ── 2. Register global Alpine.data components ───────────────
   Lightweight components that are used across multiple pages.
   Page-specific components are registered in each page's init().
──────────────────────────────────────────────────────────────── */

// Sidebar/layout component (used by AppLayout)
Alpine.data('appLayout', () => ({
  sidebarOpen: false,           // mobile drawer toggle
  openSubmenus: {},             // { '/copias': true }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen
  },

  closeSidebar() {
    this.sidebarOpen = false
  },

  toggleSubmenu(key) {
    this.openSubmenus[key] = !this.openSubmenus[key]
  },

  isSubmenuOpen(key) {
    return !!this.openSubmenus[key]
  },

  async logout() {
    // Esperar a que el backend borre las cookies HttpOnly ANTES de
    // cambiar el hash. Si no, Alpine puede volver a renderizar con
    // la sesion aun "viva" y el router no se reinicia limpio.
    await Alpine.store('auth').logout()
    window.location.hash = '#/login'
    // Re-render from scratch — router wipes the layout
    document.getElementById('app').innerHTML = ''
    window.dispatchEvent(new HashChangeEvent('hashchange'))
  },

  openProfile() {
    window.profileModal?.abrir()
  },
}))

/* ── 3. Expose Alpine globally (¡ESTO DEBE IR PRIMERO!) ──────── */
window.Alpine = Alpine

/* ── 3.5 Register global XSS sanitizer magic property ────────── */
Alpine.magic('sanitize', () => (dirtyHtml) => DOMPurify.sanitize(dirtyHtml || ''))

/* ── 3.6 Register icon dictionary magic property ─────────────── */
Alpine.magic('icon', () => (name) => icons[name] || '')

/* ── 4. Register standalone modal data ───────────────────────── */
  initObsolescenciaModal()
  initConfirmCancelModal()
  initConfirmDeleteModal()
  initEditUserModal()
  initMoveAreaModal()

/* ── 5. Inject standalone modal templates ────────────────────── */
// document.body.insertAdjacentHTML('beforeend', ObsolescenciaModalTemplate)
// document.body.insertAdjacentHTML('beforeend', ConfirmCancelModalTemplate)

/* ── 6. Start Alpine ─────────────────────────────────────────── */
Alpine.start()

/* ── 7. Init Toast magic + Router ────────────────────────────── */
Promise.resolve().then(() => {
  initToast()              
  initAuthModal()          
  initProfileModal()       
  initTimelineModal()      
  initPdfViewerModal()     
  initAlcanceModal()       
  initParametrosDifusionModal() 
  initConfirmLiberacionModal()  
  initDelegarTareaModal()       
  initAuthRecepcionModal()      
  initAuthDevolucionModal()      
  initExamConfirmModal()         
  initRespuestasExamenModal()    
  
  initRouter()             
})