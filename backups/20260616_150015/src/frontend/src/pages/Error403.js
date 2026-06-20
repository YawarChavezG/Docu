/**
 * pages/Error403.js — Acceso Denegado
 */
export const page = {
  init() {},
  template: /* html */`
<div class="animate-fade-in-page flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
  <!-- Doodle: Acceso Denegado -->
  <svg class="w-56 h-56 text-slate-300 mb-6" viewBox="0 0 240 240" fill="none">
    <circle cx="120" cy="120" r="100" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
    <rect x="80" y="50" width="80" height="140" rx="4" stroke="currentColor" stroke-width="2"/>
    <rect x="88" y="58" width="64" height="124" rx="2" class="text-brand-500" stroke="currentColor" stroke-width="2" opacity="0.2" fill="currentColor"/>
    <circle cx="120" cy="110" r="16" class="text-brand-500" stroke="currentColor" stroke-width="2"/>
    <rect x="114" y="118" width="12" height="10" rx="1" class="text-brand-500" stroke="currentColor" stroke-width="2"/>
    <line x1="70" y1="70" x2="170" y2="170" class="text-brand-500" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  </svg>
  <h1 class="text-3xl font-extrabold text-slate-800 mb-2">403</h1>
  <p class="text-sm font-semibold text-slate-600 mb-1">Acceso Denegado</p>
  <p class="text-xs text-slate-400 max-w-xs mb-6 leading-relaxed">
    No tienes permisos para acceder a esta sección.<br>
    Si crees que esto es un error, contacta al administrador del sistema.
  </p>
  <a href="#/bandeja" class="btn btn-primary">
    ← Volver a Inicio
  </a>
</div>`,
}
