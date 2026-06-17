/**
 * src/components/PlantillaEditor.js
 *
 * Editor WYSIWYG de plantillas de notificacion (US-9.04).
 * Tiptap 3.x + Alpine 3.x, patron oficial de:
 *   https://tiptap.dev/docs/editor/getting-started/install/alpine
 *
 * ★ REGLA CRITICA (de la doc oficial, verbatim):
 *   "Alpine's reactive engine automatically wraps component properties in
 *    proxy objects. If you attempt to use a proxied editor instance to
 *    apply a transaction, it will cause a Range Error: Applying a
 *    mismatched transaction, so be sure to unwrap it using Alpine.raw(),
 *    or simply avoid storing your editor as a component property."
 *
 * POR LO TANTO: este modulo retorna {editor, destroy}. El CALLER
 * (Parametrizacion.js) debe guardar el `editor` en un CLOSURE LOCAL,
 * NO en `this` (el state reactivo de Alpine). Si lo guarda en `this`,
 * Alpine lo envuelve en un Proxy y los commands fallan.
 *
 * Para evitar esto, el factory de Alpine en el caller debe verse asi:
 *
 *   Alpine.data('miComponente', () => {
 *     let editor  // <-- closure local, NUNCA en `this`
 *     return {
 *       init() { editor = initPlantillaEditor(el, html, () => {}) },
 *       toggleBold() { editor.chain().focus().toggleBold().run() }
 *     }
 *   })
 */

import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { TextStyleKit } from '@tiptap/extension-text-style'
// TextStyleKit incluye: TextStyle, Color, FontSize, FontFamily,
// BackgroundColor, LineHeight + command removeEmptyTextStyle.

export function initPlantillaEditor(el, initialHtml, onUpdate) {
  const editor = new Editor({
    element: el,
    extensions: [
      StarterKit,
      TextStyleKit,
    ],
    content: initialHtml || '<p></p>',
    onUpdate: ({ editor }) => {
      if (typeof onUpdate === 'function') onUpdate(editor.getHTML())
    },
  })

  return {
    editor,
    async destroy() {
      if (editor && !editor.isDestroyed) {
        try { await editor.destroy() } catch (_) { /* ignore */ }
      }
    },
  }
}

export default initPlantillaEditor
