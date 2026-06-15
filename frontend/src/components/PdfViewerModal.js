/**
 * src/components/PdfViewerModal.js
 * Visor de Documentos PDF corregido:
 * - Teleports separados para cumplir el estándar de AlpineJS.
 * - Visibilidad controlada estrictamente por x-show.
 */

export function initPdfViewerModal() {
  window.Alpine?.data('pdfViewerData', () => ({
    // Estado del visor
    open: false,
    // Estado del modal de advertencia (VENCIDO)
    alertaOpen: false,
    // Datos del documento
    cod: '',
    titulo: '',
    tipo: 'normal',          // 'normal' | 'EDITABLE' | 'CONTROLADA' | 'NO CONTROLADA' | 'VISUALIZACION'
    esVencido: false,
    esObsoleto: false,
    esEditable: false,
    marcaAguaExterno: null,
    returnRoute: '/lista',   // ruta a la que vuelve (memoria de navegación US-5.04)
    // Herramientas visor
    zoom: 100,               // porcentaje
    rotacion: 0,             // grados
    isETO: false,
    // Datos copia
    numCopia: 0,
    destinatario: '',
    // Datos internos
    _pendingOpen: false,

    // Computed: texto y color de la marca de agua
    get marcaAgua() {
      if (this.marcaAguaExterno) {
        const map = {
          'VENCIDO':   { text: 'VENCIDO',            color: 'rgba(220,38,38,0.18)' },
          'OBSOLETO':  { text: 'DOCUMENTO OBSOLETO', color: 'rgba(148,163,184,0.2)' },
          'CONTROLADA':{ text: 'COPIA CONTROLADA',    color: 'rgba(220,38,38,0.15)' },
          'NO CONTROLADA': { text: 'COPIA NO CONTROLADA', color: 'rgba(220,38,38,0.12)' },
        }
        return map[this.marcaAguaExterno] || null
      }
      if (this.esVencido)   return { text: 'VENCIDO',            color: 'rgba(220,38,38,0.18)'  }
      if (this.esObsoleto)  return { text: 'DOCUMENTO OBSOLETO', color: 'rgba(148,163,184,0.2)' }
      if (this.tipo === 'CONTROLADA')    return { text: 'COPIA CONTROLADA',    color: 'rgba(220,38,38,0.15)'  }
      if (this.tipo === 'NO CONTROLADA') return { text: 'COPIA NO CONTROLADA', color: 'rgba(220,38,38,0.12)'  }
      return null
    },

    get tituloTopbar() {
      if (this.tipo === 'EDITABLE')      return `Editando: ${this.cod} (Office 365)`
      if (this.tipo === 'CONTROLADA')    return `Copia Controlada — ${this.cod}`
      if (this.tipo === 'NO CONTROLADA') return `Copia No Controlada — ${this.cod}`
      if (this.tipo === 'VISUALIZACION') return `Copia de Visualización — ${this.cod}`
      return `Visor PDF — ${this.cod}`
    },

    get puedeImprimir() {
      if (this.tipo === 'CONTROLADA' || this.tipo === 'NO CONTROLADA') return true
      return this.isETO
    },

    // API: Verificar si abrir directo o mostrar alerta VENCIDO
    verificar({ cod, titulo, tipo = 'normal', esVencido = false, esObsoleto = false, esEditable = false, marcaAgua = null, returnRoute = '/lista', numCopia = 0, destinatario = '' } = {}) {
      this.cod        = cod
      this.titulo     = titulo
      this.tipo       = tipo
      this.esVencido  = esVencido
      this.esObsoleto = esObsoleto
      this.esEditable = esEditable
      this.marcaAguaExterno = marcaAgua
      this.returnRoute = returnRoute
      this.numCopia    = numCopia
      this.destinatario = destinatario
      this.isETO       = window.Alpine?.store('auth')?.role === 'eto'

      if (esVencido) {
        this.alertaOpen = true
      } else {
        this._abrirVisor()
      }
    },

    confirmarVencido() {
      this.alertaOpen = false
      this._abrirVisor()
    },

    _abrirVisor() {
      this.zoom     = 100
      this.rotacion = 0
      this.open     = true
    },

    cerrar() {
      this.open       = false
      this.alertaOpen = false
    },

    volver() {
      this.cerrar()
      window.navigate(this.returnRoute)
    },

    zoomIn()  { if (this.zoom < 200) this.zoom += 20 },
    zoomOut() { if (this.zoom > 40)  this.zoom -= 20 },
    rotar()   { this.rotacion = (this.rotacion + 90) % 360 },

    imprimir() {
      window.toast('🖨️ Abriendo diálogo de impresión...', 'info')
      window.print()
    },
  }))

  window.pdfViewer = {
    abrir(opts) {
      const el = document.querySelector('[x-data="pdfViewerData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].verificar(opts)
      else setTimeout(() => window.pdfViewer.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="pdfViewerData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }

  // Retrocompatibilidad con funciones del HTML original
  window.verificarVisor = (btn, esVencido, modo = '') => {
    const pantallaActual = (document.querySelector('.screen.active')?.id || 's-lista').replace('s-', '')
    window.pdfViewer.abrir({
      cod:    'DOC-XXX',
      titulo: 'Documento',
      tipo:   modo || 'normal',
      esVencido,
      returnRoute: '/' + pantallaActual,
    })
  }
}

export const PdfViewerModalTemplate = /* html */`
<div x-data="pdfViewerData">

  <template x-teleport="body">
    <div x-show="alertaOpen"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="alertaOpen=false"
         class="modal-overlay z-[9500]"
         style="display:none;">
      <div @click.stop class="modal-box text-center max-h-[90vh] overflow-y-auto">
        <div class="text-[44px] mb-3">⚠️</div>
        <div class="text-[17px] font-bold text-red-600 mb-2.5">¡ADVERTENCIA!</div>
        <p class="text-xs text-slate-600 mb-6 leading-relaxed">
          Usted está a punto de visualizar un documento que se encuentra <strong>VENCIDO</strong>.<br><br>
          ¿Está seguro que desea continuar con la visualización?
        </p>
        <div class="flex gap-2.5">
          <button @click="alertaOpen=false" class="btn flex-1">Cancelar</button>
          <button @click="confirmarVencido()" class="btn btn-danger flex-1">Sí, continuar</button>
        </div>
      </div>
    </div>
  </template>

  <template x-teleport="body">
    <div x-show="open"
         @keydown.escape.window="cerrar()"
         class="fixed inset-0 z-[9000] flex flex-col bg-[#525659]"
         style="display:none;">

      <div class="flex items-center justify-between px-4 py-2.5 bg-slate-800 flex-shrink-0 flex-wrap gap-2">
        <div class="text-white text-[13px] font-semibold" x-text="tituloTopbar"></div>
        <div class="flex gap-1.5 items-center flex-wrap">
          <div class="flex gap-1 border-r border-white/20 pr-2.5 mr-1">
            <button @click="zoomIn()"
                    class="px-2.5 py-1 rounded-md border border-white/20 bg-white/10 text-white text-[11px] hover:bg-white/20 transition-colors"
                    title="Aumentar zoom (+20%)">🔍+</button>
            <button @click="zoomOut()"
                    class="px-2.5 py-1 rounded-md border border-white/20 bg-white/10 text-white text-[11px] hover:bg-white/20 transition-colors"
                    title="Reducir zoom (-20%)">🔍−</button>
            <button @click="rotar()"
                    class="px-2.5 py-1 rounded-md border border-white/20 bg-white/10 text-white text-[11px] hover:bg-white/20 transition-colors"
                    title="Rotar 90°">↻ Rotar</button>
            <span class="text-[10px] text-slate-400 self-center px-1.5 min-w-[38px] text-center"
                  x-text="zoom+'%'"></span>
          </div>
          <button x-show="puedeImprimir" @click="imprimir()"
                  class="px-3 py-1 rounded-md border-none bg-brand-600 text-white text-[11px] font-semibold hover:bg-brand-700 transition-colors">
            🖨️ Imprimir Copia
          </button>
          <button @click="volver()"
                  class="px-3 py-1 rounded-md border border-white/20 bg-white/10 text-white text-[11px] hover:bg-white/20 transition-colors">
            ← Volver
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-auto flex justify-center items-start p-5 relative">
        <div x-show="marcaAgua" class="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div class="font-black text-center whitespace-nowrap font-mono select-none -rotate-[35deg] tracking-widest"
               style="font-size:clamp(36px,6vw,80px)"
               :style="marcaAgua ? 'color:'+marcaAgua.color : ''"
               x-text="marcaAgua ? marcaAgua.text : ''"></div>
        </div>

        <div class="bg-white relative flex-shrink-0 shadow-2xl"
             style="width:21cm;min-height:29.7cm;padding:2cm;transform-origin:top center"
             :style="'transform:rotate('+rotacion+'deg) scale('+(zoom/100)+');transition:transform 0.25s ease'">

          <div class="border-2 border-black p-4" style="min-height:25cm">
            <div class="flex justify-between border-b-2 border-black pb-2.5 mb-5">
              <div class="font-bold text-sm">COFAR S.A.</div>
              <div class="font-bold text-xs font-mono" x-text="cod"></div>
            </div>
            <h1 class="text-center mt-10 text-lg text-slate-800 font-bold" x-text="titulo || 'Documento'"></h1>

            <div class="mt-8 text-[11px] text-slate-600 border border-slate-400 p-3 bg-slate-50 rounded">
              <strong>TABLA DE FIRMAS (Carátula generada por el sistema — US-5.07)</strong>
              <table class="w-full mt-2 text-[10.5px] border-collapse">
                <tr><td class="p-1 border-b border-dotted border-slate-400"><strong>Elaborado por:</strong></td><td class="p-1 border-b border-dotted border-slate-400">Juan Perez — 22/04/2026</td></tr>
                <tr><td class="p-1 border-b border-dotted border-slate-400"><strong>Revisado por:</strong></td><td class="p-1 border-b border-dotted border-slate-400">Maria Condori, Jasiel Sanjinés — 23/04/2026</td></tr>
                <tr><td class="p-1"><strong>Aprobado por:</strong></td><td class="p-1">Luis Mamani — 24/04/2026</td></tr>
              </table>
            </div>

            <div class="mt-12 text-slate-300 text-sm text-justify italic">[ CONTENIDO PROTEGIDO DEL DOCUMENTO — Visualización en modo seguro ]</div>

            <div class="absolute bottom-5 left-5 right-5 text-[8px] text-slate-500 border-t border-slate-300 pt-1.5 font-mono"
                 x-show="tipo === 'CONTROLADA' || tipo === 'NO CONTROLADA'">
              <span x-text="'Copia '+tipo+'. ID copia '+tipo+': '+(numCopia||1)+'. Fecha de emisión: '+new Date().toLocaleDateString('es-BO')+' '+new Date().toLocaleTimeString('es-BO',{hour:'2-digit',minute:'2-digit'})+'. Responsable: Aracely Romero. (Destino: '+(destinatario||'Destinatario Asignado')+')'"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>

</div>`

/** Template del Certificado PDF */
export const CertificadoPdfTemplate = /* html */`
<div x-data="{
  open: false,
  nombre: '',
  titulo: '',
  nota: '',
  fecha: '',
  uuid: '',
  abrir(data) {
    this.nombre = data.nombre || 'Nombre Apellido';
    this.titulo = data.titulo || 'Documento';
    this.nota   = data.nota   || '—';
    this.fecha  = data.fecha  || new Date().toLocaleDateString();
    this.uuid   = 'CF-' + Math.floor(Math.random()*9000+1000) + '-2026';
    this.open   = true;
  },
  cerrar() { this.open = false; }
}" x-init="window.certModal = { abrir: (d) => $data.abrir(d), cerrar: () => $data.cerrar() }">

  <template x-teleport="body">
    <div x-show="open"
         class="fixed inset-0 z-[9000] flex flex-col items-center justify-center bg-[#525659]"
         style="display:none;">

      <div class="w-full flex items-center justify-between px-4 py-2.5 bg-slate-800 flex-shrink-0">
        <span class="text-white text-[13px] font-semibold">Certificado de Aprobación</span>
        <div class="flex gap-2">
          <button @click="window.print()" class="px-3 py-1.5 rounded-md border-none bg-brand-600 text-white text-[11px] font-semibold hover:bg-brand-700 transition-colors">🖨️ Imprimir</button>
          <button @click="cerrar()" class="px-3 py-1.5 rounded-md border border-white/20 bg-white/10 text-white text-[11px] hover:bg-white/20 transition-colors">← Volver</button>
        </div>
      </div>

      <div class="flex-1 overflow-auto w-full flex justify-center items-start p-8">
        <div class="bg-white w-[25cm] min-h-[17cm] p-[2.5cm] shadow-2xl border-l-[12px] border-brand-600 rounded-md">
          <div class="text-center border-b-2 border-brand-600 pb-4 mb-6">
            <div class="text-lg font-extrabold text-brand-600 tracking-wider">COFAR S.A.</div>
            <div class="text-[11px] text-slate-500 mt-0.5">Sistema de Gestión de Calidad</div>
          </div>
          <h1 class="text-center text-4xl font-black text-slate-800 tracking-[4px] m-0 mb-2">CERTIFICADO</h1>
          <div class="text-center text-[13px] text-slate-500 mb-6">Otorgado por la presente a:</div>
          <h2 class="text-center text-3xl font-bold text-brand-600 m-0 mb-5" x-text="nombre"></h2>
          <div class="text-center text-[13px] text-slate-600 mb-2">ha aprobado satisfactoriamente la capacitación y evaluación en el documento:</div>
          <div class="text-center text-base font-bold text-brand-600 mb-1.5" x-text="titulo"></div>
          <div class="text-center text-xs text-slate-500 mb-6">obteniendo una calificación final de:</div>
          <div class="text-center text-[52px] font-black text-emerald-600 mb-7" x-text="nota + ' / 100'"></div>
          <div class="flex justify-between items-end border-t border-slate-200 pt-5 mt-2">
            <div class="text-center">
              <div class="w-40 border-b border-black mb-1.5"></div>
              <div class="text-[11px] text-slate-500">Firma Responsable ETO</div>
            </div>
            <div class="text-right text-[10.5px] text-slate-400">
              <div>ID Verificación: <strong class="text-slate-600" x-text="uuid"></strong></div>
              <div class="mt-1">Fecha de emisión: <strong class="text-slate-600" x-text="fecha"></strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
</div>`