/**
 * pages/Error404.js — Página no encontrada
 */
export const page = {
  init() {},
  template: /* html */`
<div class="animate-fade-in-page flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
  <!-- Doodle: Página no encontrada -->
  <svg class="w-56 h-56 text-slate-300 mb-6" viewBox="0 0 240 240" fill="none">
    <circle cx="120" cy="120" r="100" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
    <rect x="70" y="50" width="90" height="120" rx="6" stroke="currentColor" stroke-width="2"/>
    <path d="M70 80 H160" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
    <path d="M70 100 H160" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
    <path d="M70 120 H140" stroke="currentColor" stroke-width="1.5" opacity="0.4"/>
    <path d="M130 170 L145 185 L160 170" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="165" cy="165" r="30" class="text-brand-500" stroke="currentColor" stroke-width="2"/>
    <line x1="187" y1="187" x2="210" y2="210" class="text-brand-500" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
    <line x1="155" y1="165" x2="175" y2="165" class="text-brand-500" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="165" y1="155" x2="165" y2="175" class="text-brand-500" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
  <h1 class="text-3xl font-extrabold text-slate-800 mb-2">404</h1>
  <p class="text-sm font-semibold text-slate-600 mb-1">Página no encontrada</p>
  <p class="text-xs text-slate-400 max-w-xs mb-6 leading-relaxed">
    La ruta solicitada no existe en el sistema.<br>
    Verifica la URL o regresa al inicio.
  </p>
  <a href="#/bandeja" class="btn btn-primary">
    ← Volver a Inicio
  </a>
</div>`,
}
