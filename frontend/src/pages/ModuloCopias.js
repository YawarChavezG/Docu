/**
 * pages/ModuloCopias.js — Módulo de Generación de Copias
 * Reconstrucción fiel de s-modulo-copias del HTML original.
 */
import { listaEmpleados } from '../data/users.js'

export const page = {
  init() {
    window.Alpine?.data('moduloCopias', () => ({
      config: null,
      cantidad: 1,
      destinatarios: [],
      generados: [],
      mostrarResultados: false,

      get esControlada() {
        return this.config?.tipo === 'CONTROLADA'
      },

      get tituloPagina() {
        return 'Generación de Copias ' + (this.esControlada ? 'Controladas' : 'No Controladas')
      },

      init() {
        try {
          const raw = sessionStorage.getItem('moduloCopiasConfig')
          this.config = raw ? JSON.parse(raw) : { tipo: 'CONTROLADA', cod: 'DOC-XXX', tit: 'Documento', ver: '01' }
        } catch {
          this.config = { tipo: 'CONTROLADA', cod: 'DOC-XXX', tit: 'Documento', ver: '01' }
        }
        this.generarCampos()
      },

      generarCampos() {
        const cant = Math.max(1, Math.min(20, parseInt(this.cantidad) || 1))
        this.cantidad = cant
        const actuales = [...this.destinatarios]
        this.destinatarios = Array.from({ length: cant }, (_, i) => actuales[i] || '')
      },

      finalizarGeneracion() {
        const vacios = this.destinatarios.some(d => !d.trim())
        if (vacios) {
          window.toast('⚠️ Debe indicar el nombre de todos los destinatarios.', 'warn')
          return
        }

        window.toast('Procesando registros en base de datos...', 'info')

        this.generados = this.destinatarios.map((dest, idx) => ({
          idCopia: idx + 1,
          destinatario: dest.trim(),
          responsable: 'A. Romero',
        }))

        setTimeout(() => {
          this.mostrarResultados = true
          window.toast('✅ Copias registradas exitosamente.', 'success')
        }, 800)
      },

      previsualizarCopia(fila) {
        window.pdfViewer?.abrir({
          cod: this.config.cod,
          titulo: this.config.tit,
          tipo: this.config.tipo,
          numCopia: fila.idCopia,
          destinatario: fila.destinatario,
          returnRoute: '/modulo-copias',
        })
      },

      volver() {
        window.location.hash = '#/lista'
      },
    }))
  },

  template: /* html */`
<div x-data="moduloCopias" x-init="init()" class="animate-fade-in-page">

  <!-- Header -->
  <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="page-header" x-text="tituloPagina"></h1>
      <p class="page-subtitle">Módulo de generación y registro de copias</p>
    </div>
    <button class="btn btn-sm" @click="volver()">← Volver a Lista Maestra</button>
  </div>

  <!-- Configuración -->
  <div class="card-base" style="max-width:800px;margin:0 auto;">
    <div class="flex justify-between items-start mb-5">
      <div>
        <h3 class="text-sm font-bold text-brand-600 mb-1" x-text="config?.cod"></h3>
        <p class="text-sm text-slate-500" x-text="config?.tit"></p>
      </div>
      <span class="badge" :class="esControlada ? 'badge-green' : 'badge-amber'" x-text="config?.tipo"></span>
    </div>

    <div x-show="!mostrarResultados" id="zona-config-copias">
      <div class="form-grid-2 items-end">
        <div>
          <label class="form-label text-[10.5px]">Cantidad de copias a generar:</label>
          <input type="number" class="form-input text-xs" x-model.number="cantidad" min="1" max="20" @input="generarCampos()">
        </div>
        <div class="text-[11px] text-slate-400 pb-2">* Se generará un registro único por destinatario.</div>
      </div>

      <div class="mt-6">
        <label class="block text-[13px] font-bold text-slate-700 mb-3">Asignación de Destinatarios:</label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <template x-for="(dest, idx) in destinatarios" :key="idx">
            <input type="text"
                   class="form-input text-xs"
                   x-model="destinatarios[idx]"
                   :placeholder="'Destinatario ' + (idx+1) + '...'"
                   list="lista-empleados">
          </template>
        </div>
      </div>

      <div class="mt-8 pt-5 border-t border-slate-100 text-right">
        <button class="btn btn-primary" @click="finalizarGeneracion()">Generar Copias</button>
      </div>
    </div>

    <!-- Resultados -->
    <div x-show="mostrarResultados" id="zona-resultados-copias" class="mt-5 pt-5 border-t-2 border-slate-100">
      <h4 class="text-sm font-bold text-brand-600 mb-4">Copias Generadas Exitosamente</h4>
      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID Copia</th>
              <th>Destinatario</th>
              <th>Responsable</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="fila in generados" :key="fila.idCopia">
              <tr>
                <td class="font-bold" x-text="fila.idCopia"></td>
                <td x-text="fila.destinatario"></td>
                <td x-text="fila.responsable"></td>
                <td>
                  <button class="btn btn-sm btn-primary" @click="previsualizarCopia(fila)">👁️ Previsualizar Copia</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <div class="mt-5 text-right">
        <button class="btn" @click="mostrarResultados=false;generarCampos()">← Nueva Generación</button>
      </div>
    </div>
  </div>

  <!-- Datalist empleados (render estático para compatibilidad universal) -->
  <datalist id="lista-empleados">
    ${listaEmpleados.map(e => `<option value="${e}">`).join('\n    ')}
  </datalist>

</div>`
}
