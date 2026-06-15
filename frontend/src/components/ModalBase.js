/**
 * ModalBase.js — Generic modal shell using .modal-overlay & .modal-box
 *
 * Provides:
 *   - modalOverlayClass / modalBoxClass   (CSS class strings for reference)
 *   - ModalBaseTemplate({ dataName, content, size, extraOverlayClass, extraBoxClass })
 *   - initModalBase(name)                 (registers a bare-bones Alpine.data)
 *
 * Usage in a concrete modal:
 *   import { ModalBaseTemplate } from './ModalBase.js'
 *   export const MyModalTemplate = ModalBaseTemplate({
 *     dataName: 'myModalData',
 *     size: 'md',
 *     content: `...your inner HTML...`
 *   })
 */

export const modalOverlayClass = 'modal-overlay'
export const modalBoxClass = 'modal-box'

/** Register a minimal Alpine data object for simple modals. */
export function initModalBase(name = 'modalBaseData') {
  window.Alpine?.data(name, () => ({
    open: false,
    abrir() { this.open = true },
    cerrar() { this.open = false },
  }))
}

/**
 * Returns an HTML template string wrapped in the standard modal overlay/box.
 * @param {object} opts
 * @param {string} opts.dataName                — Alpine x-data name
 * @param {string} opts.content                 — Inner HTML (the modal body)
 * @param {'sm'|'md'|'lg'} [opts.size='md']     — Box width variant
 * @param {string} [opts.extraOverlayClass='']  — Additional classes on overlay
 * @param {string} [opts.extraBoxClass='']      — Additional classes on box
 */
export function ModalBaseTemplate({ dataName, content, size = 'md', extraOverlayClass = '', extraBoxClass = '' }) {
  const sizeClass = size === 'sm' ? 'modal-box-sm' : size === 'lg' ? 'modal-box-lg' : 'modal-box'
  return /* html */`
<div x-data="${dataName}"
     x-show="open"
     @keydown.escape.window="typeof cerrar === 'function' ? cerrar() : (open = false)"
     class="${modalOverlayClass} ${extraOverlayClass}"
     style="display:none;"
     :style="open ? 'display:flex' : 'display:none'">
  <div @click.stop class="${sizeClass} ${extraBoxClass} max-h-[90vh] overflow-y-auto">
    ${content}
  </div>
</div>`
}
