/**
 * Toast.js — Global notification system
 *
 * Usage (anywhere in JS):    toast('Mensaje guardado', 'success')
 * Usage (Alpine templates):  @click="$toast('Operación exitosa')"
 */

const ICONS = {
  success: `<svg class="w-4 h-4 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
  </svg>`,
  error: `<svg class="w-4 h-4 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
  </svg>`,
  warn: `<svg class="w-4 h-4 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
  </svg>`,
  info: `<svg class="w-4 h-4 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
  </svg>`,
}

const TYPE_CLASS = {
  success: 'toast-success',
  error:   'toast-error',
  warn:    'toast-warn',
  info:    'toast-info',
}

/**
 * Shows a toast notification.
 * @param {string} message  — The notification message
 * @param {'success'|'error'|'warn'|'info'} [type='info']
 * @param {number} [duration=2500]  — Auto-dismiss ms (0 = manual)
 */
export function toast(message, type = 'info', duration = 2500) {
  const container = document.getElementById('toast-container')
  if (!container) return

  const el = document.createElement('div')
  el.className = `toast ${TYPE_CLASS[type] ?? TYPE_CLASS.info}`
  el.setAttribute('x-data', '{ open: true }')
  el.setAttribute('x-show', 'open')
  el.setAttribute('x-transition:leave', 'transition ease-in duration-300')
  el.setAttribute('x-transition:leave-end', 'opacity-0 translate-x-full')
  el.innerHTML = `
    ${ICONS[type] ?? ICONS.info}
    <span class="flex-1 leading-snug">${message}</span>
    <button
      class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity ml-1 mt-0.5"
      onclick="const t = this.closest('.toast'); if(t._x_dataStack) t._x_dataStack[0].open = false; setTimeout(()=>t.remove(),350)"
      aria-label="Cerrar"
    >
      <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
      </svg>
    </button>
  `

  container.prepend(el)

  // Initialize Alpine on this dynamic node so x-show / x-transition work
  if (window.Alpine) {
    window.Alpine.initTree(el)
  }

  if (duration > 0) {
    setTimeout(() => {
      const data = el._x_dataStack?.[0]
      if (data) {
        data.open = false
        setTimeout(() => el.remove(), 350)
      } else {
        el.style.animation = 'toastOut 0.25s ease-in both'
        setTimeout(() => el.remove(), 300)
      }
    }, duration)
  }
}

/**
 * Initializes toast system:
 * - Exposes window.toast() for non-Alpine code
 * - Registers $toast Alpine magic helper
 */
export function initToast() {
  // Global shorthand
  window.toast = toast

  // Alpine magic: $toast('msg') or $toast('msg', 'success')
  if (window.Alpine) {
    window.Alpine.magic('toast', () => toast)
  }
}
