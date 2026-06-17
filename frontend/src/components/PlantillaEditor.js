/**
 * src/components/PlantillaEditor.js
 *
 * Editor WYSIWYG de plantillas de notificacion (US-9.04).
 * Usa Tiptap 3.x (https://tiptap.dev) con StarterKit + Color + TextStyle.
 *
 * API:
 *   initEditor(el, initialHtml, onUpdate)  ->  { editor, destroy() }
 *
 *   el: HTMLElement donde se monta el editor (debe ser un <div>)
 *   initialHtml: HTML inicial (de la BD)
 *   onUpdate: callback(html) que se llama en cada cambio
 *
 * Toolbar expuesta:
 *   - Bold, Italic, Underline, Strike
 *   - H1, H2, H3
 *   - BulletList, OrderedList
 *   - Blockquote, CodeBlock
 *   - Color picker (textStyle + color)
 *   - Font size (textStyle)
 *   - Undo, Redo
 *   - Insert variable (callback externo)
 */
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { TextStyle } from '@tiptap/extension-text-style'
import { Color } from '@tiptap/extension-color'

/**
 * Crea e inicializa un editor Tiptap dentro de `el`.
 * @param {HTMLElement} el
 * @param {string} initialHtml
 * @param {(html: string) => void} onUpdate
 * @returns {{ editor: Editor, destroy: () => void }}
 */
export function initPlantillaEditor(el, initialHtml, onUpdate) {
  const editor = new Editor({
    element: el,
    extensions: [
      // Tiptap 3.x StarterKit ya incluye Bold, Italic, Strike, Underline,
      // Headings (H1-H6), BulletList, OrderedList, Blockquote, CodeBlock,
      // History (undo/redo), Document, Paragraph, Text, etc.
      // No hay que importar Underline aparte.
      StarterKit,
      TextStyle,
      Color,
    ],
    content: initialHtml || '<p></p>',
    onUpdate: ({ editor }) => {
      if (typeof onUpdate === 'function') onUpdate(editor.getHTML())
    },
  })
  return {
    editor,
    destroy: () => editor.destroy(),
  }
}

/**
 * Toolbar actions: funciones helper para el template.
 * Sesion 15: usar commands.X() en vez de chain().X().run() para
 * evitar "Applying a mismatched transaction" cuando el editor
 * tiene state stale (despues de setContent o Vite HMR). chain()
 * mantiene una referencia al state inicial; si el state cambia
 * entre chain() y run(), falla. commands.X() aplica directo.
 */
export const toolbarActions = {
  bold:      (e) => { e.commands.focus(); e.commands.toggleBold() },
  italic:    (e) => { e.commands.focus(); e.commands.toggleItalic() },
  underline: (e) => { e.commands.focus(); e.commands.toggleUnderline() },
  strike:    (e) => { e.commands.focus(); e.commands.toggleStrike() },
  h1:        (e) => { e.commands.focus(); e.commands.toggleHeading({ level: 1 }) },
  h2:        (e) => { e.commands.focus(); e.commands.toggleHeading({ level: 2 }) },
  h3:        (e) => { e.commands.focus(); e.commands.toggleHeading({ level: 3 }) },
  bulletList: (e) => { e.commands.focus(); e.commands.toggleBulletList() },
  orderedList: (e) => { e.commands.focus(); e.commands.toggleOrderedList() },
  blockquote: (e) => { e.commands.focus(); e.commands.toggleBlockquote() },
  codeBlock: (e) => { e.commands.focus(); e.commands.toggleCodeBlock() },
  undo:      (e) => { e.commands.focus(); e.commands.undo() },
  redo:      (e) => { e.commands.focus(); e.commands.redo() },
  setColor:  (e, color) => { e.commands.focus(); e.commands.setColor(color) },
  unsetColor: (e) => { e.commands.focus(); e.commands.unsetColor() },
  setFontSize: (e, size) => {
    e.commands.focus()
    // TipTap no tiene setFontSize por defecto. Usamos mark 'textStyle'
    // con estilo inline font-size via updateAttributes.
    return e.commands.updateMark('textStyle', { fontSize: size })
  },
  unsetFontSize: (e) => {
    e.commands.focus()
    return e.commands.updateMark('textStyle', { fontSize: null })
  },
  isActive: (e, name, attrs) => e.isActive(name, attrs),
  /**
   * Inserta un texto en la posicion del cursor.
   */
  insertText: (e, text) => { e.commands.focus(); e.commands.insertContent(text) },
  /**
   * Inserta una variable en la posicion del cursor.
   * Se inserta como texto plano {{CODIGO}} (no como HTML)
   * para que el backend pueda renderizarlo con Jinja2.
   */
  insertVariable: (e, variable) => { e.commands.focus(); e.commands.insertContent(variable) },
}

export default initPlantillaEditor
