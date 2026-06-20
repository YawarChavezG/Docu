/**
 * pages/Placeholder.js — Página temporal para rutas aún no implementadas
 */
export const page = {
  init() {},
  template: /* html */`
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            height:300px;color:#94a3b8;gap:16px;animation:fadeIn 0.35s ease-out both">
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="1.5" opacity="0.4">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
  <div style="text-align:center">
    <p style="font-size:14px;font-weight:600;color:#64748b;margin:0 0 4px">
      Módulo en construcción
    </p>
    <p style="font-size:12px;color:#94a3b8;margin:0">
      Esta sección estará disponible próximamente.
    </p>
  </div>
  <button onclick="window.history.back()"
          class="btn btn-sm"
          style="font-size:12px">
    ← Volver
  </button>
</div>`,
}
