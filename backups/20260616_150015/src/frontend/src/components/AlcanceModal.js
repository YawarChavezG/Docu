/**
 * src/components/AlcanceModal.js
 * Modal de seguimiento de difusión — Vista resumen y detallada
 *
 * Uso:
 *   window.alcanceModal.abrir({ codigo, nombre, tipo, datos })
 *   window.alcanceModal.cerrar()
 */

import { listaEmpleados } from '../data/users.js'

export function initAlcanceModal() {
  window.Alpine?.data('alcanceModalData', () => ({
    open: false,
    titulo: 'Detalle de Seguimiento',
    subtitulo: '',
    docCodigo: '',
    docTipo: '',
    verDetallado: false,
    datosAlcance: [],
    empleados: listaEmpleados,

    abrir({ codigo = '', nombre = '', tipo = '', datos = [] } = {}) {
      this.titulo       = `Detalle de Seguimiento — ${codigo} : ${nombre}`
      this.subtitulo    = `Tipo de Difusión: ${tipo}`
      this.docCodigo    = codigo
      this.docTipo      = tipo
      this.datosAlcance = datos
      this.verDetallado = false
      this.open = true
    },

    cerrar() {
      this.open = false
    },

    toggleVista() {
      this.verDetallado = !this.verDetallado
    },

    exportarExcel() {
      if (!this.datosAlcance.length) {
        window.toast('⚠️ No hay datos para exportar.', 'warn')
        return
      }
      window.toast('📗 Exportando reporte a Excel...', 'info')
    },

    exportarPDF() {
      if (!this.datosAlcance.length) {
        window.toast('⚠️ No hay datos para exportar.', 'warn')
        return
      }
      window.toast('📕 Generando PDF...', 'info')
    },
  }))

  window.alcanceModal = {
    abrir(opts) {
      const el = document.querySelector('[x-data="alcanceModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.alcanceModal.abrir(opts), 200)
    },
    cerrar() {
      const el = document.querySelector('[x-data="alcanceModalData"]')
      if (el && el._x_dataStack) el._x_dataStack[0].cerrar()
    },
  }
}

export const AlcanceModalTemplate = /* html */`
<div x-data="alcanceModalData">
  <template x-teleport="body">
    <div x-show="open"
         @keydown.escape.window="cerrar()"
         class="modal-overlay"
         style="display:none"
         :style="open ? 'display:flex' : 'display:none'">

      <div @click.stop
           class="bg-white rounded-2xl shadow-glass-lg p-5 w-[95%] max-w-[1100px] max-h-[90vh] flex flex-col"
           style="animation: scaleIn 0.28s cubic-bezier(0.16,1,0.3,1) both">

        <!-- Header -->
        <div class="flex items-center justify-between border-b-2 border-brand-500 pb-2.5 flex-shrink-0 flex-wrap gap-2">
          <div class="flex flex-col gap-1">
            <span class="text-base font-bold text-brand-600" x-text="titulo"></span>
            <span class="text-[11px] text-slate-500 font-normal" x-text="subtitulo"></span>
            <div class="mt-0.5">
              <a href="#" @click.prevent="toggleVista()" class="text-[11px] text-brand-600 font-semibold underline cursor-pointer"
                 x-text="verDetallado ? '← Volver a vista resumen' : 'Ver más detalles'"></a>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button @click="exportarExcel()" class="btn btn-sm">📗 Exportar Excel</button>
            <button @click="exportarPDF()" class="btn btn-sm">📕 Exportar PDF</button>
            <button @click="cerrar()" class="btn btn-sm btn-danger">✕ Cerrar</button>
          </div>
        </div>

        <!-- Tabla -->
        <div class="flex-1 overflow-auto mt-4 rounded-md border border-slate-200 min-h-0">
          <table class="data-table min-w-[700px]">
            <thead class="sticky top-0 z-10 bg-slate-50">
              <tr>
                <th>Nombre y Apellido</th>
                <th>Cargo</th>
                <th>Área / Gerencia</th>
                <th>Estado</th>
                <th>Nota Obtenida</th>
                <th>Fecha de Realización</th>
                <th x-show="verDetallado">Tiempo (Duración)</th>
              </tr>
            </thead>
            <tbody>
              <template x-if="datosAlcance.length === 0">
                <tr>
                  <td colspan="7" class="text-center text-slate-400 py-6 text-xs">Sin datos de alcance disponibles</td>
                </tr>
              </template>
              <template x-for="item in datosAlcance" :key="item.id">
                <tr>
                  <td class="text-slate-800" x-text="item.nombre || '—'"></td>
                  <td class="text-slate-800" x-text="item.cargo || '—'"></td>
                  <td class="text-slate-800" x-text="item.area || '—'"></td>
                  <td>
                    <span :class="'badge ' + (item.estadoClase || 'badge-gray')" x-text="item.estado || 'Pendiente'"></span>
                  </td>
                  <td>
                    <template x-if="item.nota && item.nota !== '—' && item.nota !== 'N/A'">
                      <a href="#" class="text-brand-500 hover:underline cursor-pointer font-semibold" @click.prevent="window.respuestasExamenModal?.abrir({ key: docCodigo + '_' + item.nombre })" x-text="item.nota"></a>
                    </template>
                    <template x-if="!item.nota || item.nota === '—' || item.nota === 'N/A'">
                      <span class="text-slate-400" x-text="item.nota || '—'"></span>
                    </template>
                  </td>
                  <td class="text-slate-800" x-text="item.fecha || '—'"></td>
                  <td x-show="verDetallado" class="text-slate-800" x-text="item.tiempo || '—'"></td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>

        <!-- Footer nota -->
        <div x-show="verDetallado" class="mt-3 pt-2.5 border-t border-slate-200 text-[11px] text-slate-500 flex justify-between items-center flex-shrink-0">
          <span x-text="docTipo === 'Evaluación' ? '* Detalle del tiempo de Evaluación registrado del usuario.' : '* El tiempo registrado en Control de Lectura mide la permanencia en el visor hasta la confirmación.'"></span>
        </div>

      </div>
    </div>
  </template>
</div>`
