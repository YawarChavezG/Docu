/**
 * components/LoadingOverlay.js — Overlay global de carga
 *
 * Se monta dentro del layout y se controla mediante $store.app.isLoading
 */
export const LoadingOverlay = /* html */`
<div x-data="{ show: false }"
     x-show="$store.app.isLoading"
     x-transition:enter="transition-opacity duration-200 ease-out"
     x-transition:enter-start="opacity-0"
     x-transition:enter-end="opacity-100"
     x-transition:leave="transition-opacity duration-150 ease-in"
     x-transition:leave-start="opacity-100"
     x-transition:leave-end="opacity-0"
     class="fixed inset-0 z-[9998] bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center"
     style="display:none;">
  <div class="bg-white rounded-2xl shadow-card-hover border border-slate-200/80 px-8 py-6 flex flex-col items-center gap-3">
    <div class="relative w-10 h-10">
      <div class="absolute inset-0 rounded-full border-[3px] border-slate-100"></div>
      <div class="absolute inset-0 rounded-full border-[3px] border-brand-500 border-t-transparent animate-spin"></div>
    </div>
    <span class="text-xs font-semibold text-slate-500 tracking-wide">Cargando...</span>
  </div>
</div>
`
