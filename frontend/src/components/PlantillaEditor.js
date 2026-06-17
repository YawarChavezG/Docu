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
 */
export const toolbarActions = {
  bold:      (e) => e.chain().focus().toggleBold().run(),
  italic:    (e) => e.chain().focus().toggleItalic().run(),
  underline: (e) => e.chain().focus().toggleUnderline().run(),
  strike:    (e) => e.chain().focus().toggleStrike().run(),
  h1:        (e) => e.chain().focus().toggleHeading({ level: 1 }).run(),
  h2:        (e) => e.chain().focus().toggleHeading({ level: 2 }).run(),
  h3:        (e) => e.chain().focus().toggleHeading({ level: 3 }).run(),
  bulletList: (e) => e.chain().focus().toggleBulletList().run(),
  orderedList: (e) => e.chain().focus().toggleOrderedList().run(),
  blockquote: (e) => e.chain().focus().toggleBlockquote().run(),
  codeBlock: (e) => e.chain().focus().toggleCodeBlock().run(),
  undo:      (e) => e.chain().focus().undo().run(),
  redo:      (e) => e.chain().focus().redo().run(),
  setColor:  (e, color) => e.chain().focus().setColor(color).run(),
  unsetColor: (e) => e.chain().focus().unsetColor().run(),
  setFontSize: (e, size) => {
    // TipTap no tiene setFontSize por defecto. Usamos mark 'textStyle'
    // con estilo inline font-size via updateAttributes.
    return e.chain().focus().updateMark('textStyle', { fontSize: size }).run()
  },
  unsetFontSize: (e) => {
    return e.chain().focus().updateMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run()
  },
  isActive: (e, name, attrs) => e.isActive(name, attrs),
  /**
   * Inserta un texto en la posicion del cursor.
   */
  insertText: (e, text) => e.chain().focus().insertContent(text).run(),
  /**
   * Inserta una variable en la posicion del cursor.
   * Se inserta como texto plano {{CODIGO}} (no como HTML)
   * para que el backend pueda renderizarlo con Jinja2.
   */
  insertVariable: (e, variable) => e.chain().focus().insertContent(variable).run(),
}

export default initPlantillaEditor
