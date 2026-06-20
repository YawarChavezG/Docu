/**
 * pages/TomarLectura.js — Confirmar Control de Lectura
 */
export const page = {
  init() {
    window.Alpine?.data('tomarLecturaPage', () => ({
      leyendo: false, leido: false, confirmado: false,
      iniciarLectura() {
        this.leyendo = true
        setTimeout(() => {
          this.leido = true
          window.toast('✅ Documento leído. Ahora puede confirmar la lectura.', 'success')
        }, 5000)
      },
      confirmarLectura() {
        window.authModal?.abrir({
          titulo: '✍️ Confirmar Lectura',
          icono: '📄',
          mensaje: 'Al confirmar, su <strong>firma digital</strong> quedará registrada en el sistema para el documento <strong>POL-GER-002 v04</strong>. Esta acción no puede deshacerse.',
          onSuccess: () => {
            window.toast('✅ Control de lectura confirmado. Firma digital registrada.', 'success')
            window.navigate('/bandeja')
          },
        })
      },
    }))
  },
  template: /* html */`
<div x-data="tomarLecturaPage" style="animation:fadeIn 0.35s ease-out both">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
    <a href="#/evaluaciones" class="btn btn-sm">← Volver</a>
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Control de Lectura</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">POL-GER-002 — Política de Seguridad y Medio Ambiente</p>
    </div>
  </div>

  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
    <!-- Info del documento -->
    <div style="display:flex;align-items:start;gap:16px;padding-bottom:20px;margin-bottom:20px;border-bottom:1px solid #f1f5f9;flex-wrap:wrap">
      <div style="width:64px;height:64px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:32px;flex-shrink:0">📄</div>
      <div style="flex:1">
        <div style="font-family:monospace;font-size:11px;font-weight:700;color:#1a5fb4;margin-bottom:4px">POL-GER-002 · Versión 04</div>
        <h2 style="font-size:14px;font-weight:700;color:#1e293b;margin:0 0 6px">Política de Seguridad y Medio Ambiente</h2>
        <div style="font-size:11px;color:#64748b">Publicado: 20/09/2023 · Elaborador: Fernanda Loza · Área: Calidad</div>
        <div style="margin-top:6px;font-size:11px;color:#dc2626;font-weight:500">⏰ Plazo máximo para confirmar: <strong>10/02/2026</strong></div>
      </div>
    </div>

    <!-- Instrucciones -->
    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:14px 16px;margin-bottom:20px">
      <div style="font-size:11.5px;font-weight:700;color:#92400e;margin-bottom:6px">⚠️ Instrucciones</div>
      <p style="font-size:11.5px;color:#78350f;margin:0;line-height:1.5">Debe leer el documento completo antes de confirmar. Al confirmar la lectura, su firma digital quedará registrada en el sistema. Esta acción <strong>no puede deshacerse</strong>.</p>
    </div>

    <!-- Paso 1: Ver documento -->
    <div style="background:#f8fafc;border-radius:12px;padding:16px;margin-bottom:16px">
      <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:12px">Paso 1 — Leer el documento</div>
      <button @click="iniciarLectura()"
              :disabled="leido"
              style="display:flex;align-items:center;gap:10px;width:100%;padding:12px 16px;background:#fff;border:1px solid #bfdbfe;border-radius:10px;cursor:pointer;font-family:inherit;transition:all 150ms"
              @mouseenter="!leido && ($el.style.borderColor='#1a5fb4')" @mouseleave="$el.style.borderColor='#bfdbfe'">
        <span style="font-size:24px">📖</span>
        <div style="text-align:left;flex:1">
          <div style="font-size:12px;font-weight:600;color:#1e293b" x-text="leido ? '✅ Documento leído' : leyendo ? '⌛ Cargando documento…' : 'Abrir en Visor (Office 365 Web)'"></div>
          <div style="font-size:10.5px;color:#64748b;margin-top:2px">POL-GER-002_v04.docx · 12 páginas</div>
        </div>
        <span x-show="leido" style="color:#059669;font-size:22px">✓</span>
      </button>
    </div>

    <!-- Paso 2: Confirmar -->
    <div style="background:#f8fafc;border-radius:12px;padding:16px;margin-bottom:24px" :style="leido?'':'opacity:0.5;pointer-events:none'">
      <div style="font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:12px">Paso 2 — Confirmar la lectura</div>
      <div style="display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px">
        <input type="checkbox" id="chk-lectura" x-model="confirmado" :disabled="!leido" style="width:18px;height:18px;cursor:pointer;accent-color:#1a5fb4">
        <label for="chk-lectura" style="font-size:12px;color:#1e293b;font-weight:500;cursor:pointer;line-height:1.4">
          Confirmo que he leído y comprendido el contenido completo del documento <strong>POL-GER-002 v04</strong>.
        </label>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;gap:10px">
      <a href="#/evaluaciones" class="btn">Cancelar</a>
      <button class="btn btn-primary" :disabled="!confirmado" style="padding:10px 24px;font-size:13px"
              @click="confirmarLectura()">
        ✍️ Firmar y Confirmar Lectura
      </button>
    </div>
  </div>
</div>`
}
