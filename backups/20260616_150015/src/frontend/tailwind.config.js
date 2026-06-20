/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html','./src/**/*.{js,html}'],
  safelist: [
    // Badges dinámicos (construidos desde variables JS en vistas)
    'badge-green','badge-amber','badge-blue','badge-red','badge-gray','badge-purple','badge-teal',
    // Opacidad dinámica para estados disabled / loading
    'opacity-0','opacity-50','opacity-100',
    // Cursor dinámico para estados interactivos
    'cursor-pointer','cursor-not-allowed',
  ],
  theme: {
    extend: {
      colors: {
        brand: { 50:'#eff6ff',100:'#dbeafe',200:'#bfdbfe',300:'#93c5fd',400:'#60a5fa',500:'#1a5fb4',600:'#174fa0',700:'#1e40af',800:'#1e3a8a',900:'#0f2244',950:'#07111e' },
      },
      fontFamily: { sans:['Inter','system-ui','-apple-system','BlinkMacSystemFont','sans-serif'] },
      animation: {
        'fade-in':'fadeIn 0.4s ease-out both',
        'slide-up':'slideUp 0.55s cubic-bezier(0.16,1,0.3,1) both',
        'slide-down':'slideDown 0.35s cubic-bezier(0.16,1,0.3,1) both',
        'scale-in':'scaleIn 0.3s cubic-bezier(0.16,1,0.3,1) both',
        'blob':'blob 12s ease-in-out infinite',
        'blob-slow':'blob 18s ease-in-out infinite',
        'toast-in':'toastIn 0.45s cubic-bezier(0.16,1,0.3,1) both',
        'toast-out':'toastOut 0.25s ease-in both',
        'pulse-ring':'pulseRing 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'shimmer':'shimmer 1.8s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:      {from:{opacity:'0'},to:{opacity:'1'}},
        slideUp:     {from:{transform:'translateY(28px)',opacity:'0'},to:{transform:'translateY(0)',opacity:'1'}},
        slideDown:   {from:{transform:'translateY(-16px)',opacity:'0'},to:{transform:'translateY(0)',opacity:'1'}},
        scaleIn:     {from:{transform:'scale(0.94)',opacity:'0'},to:{transform:'scale(1)',opacity:'1'}},
        blob:        {'0%,100%':{transform:'translate(0,0) scale(1)'},'25%':{transform:'translate(40px,-55px) scale(1.12)'},'50%':{transform:'translate(-25px,35px) scale(0.9)'},'75%':{transform:'translate(30px,10px) scale(1.05)'}},
        toastIn:     {from:{transform:'translateX(110%)',opacity:'0'},to:{transform:'translateX(0)',opacity:'1'}},
        toastOut:    {from:{transform:'translateX(0)',opacity:'1'},to:{transform:'translateX(110%)',opacity:'0'}},
        pulseRing:   {'0%':{boxShadow:'0 0 0 0 rgba(26,95,180,0.4)'},'70%':{boxShadow:'0 0 0 8px rgba(26,95,180,0)'},'100%':{boxShadow:'0 0 0 0 rgba(26,95,180,0)'}},
        shimmer:     {'0%':{backgroundPosition:'-400px 0'},'100%':{backgroundPosition:'400px 0'}},
      },
      boxShadow: {
        'glass':'0 8px 32px rgba(8,14,30,0.28), inset 0 1px 0 rgba(255,255,255,0.12)',
        'glass-lg':'0 24px 64px rgba(8,14,30,0.45), inset 0 1px 0 rgba(255,255,255,0.15)',
        'glass-card':'0 25px 60px -10px rgba(8,14,30,0.55), 0 8px 20px -5px rgba(8,14,30,0.3)',
        'card':'0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-md':'0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        'card-hover':'0 8px 24px rgba(0,0,0,0.1), 0 3px 8px rgba(0,0,0,0.06)',
      },
      backgroundImage: {
        'grid-dot':'radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)',
      },
      backgroundSize: { 'grid-sm':'24px 24px','grid-md':'32px 32px' },
    },
  },
  plugins: [require('@tailwindcss/forms'),require('@tailwindcss/typography')],
}
