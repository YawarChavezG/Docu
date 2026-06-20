/**
 * pages/Bandeja.js — Mi Bandeja de Tareas
 * Pre-render (REGLA 3) para filas sin mutación; Alpine reactivo solo para copias físicas.
 */
import {
  tareasBandejaDB,
  evaluacionesPendientesDB,
  controlesLecturaDB,
  recepcionCopiasDB,
} from '../data/tasks.js'

// ── Pre-rendered rows (no per-row reactivity needed — REGLA 3) ────────────────
const tareasRows = tareasBandejaDB.map(t => `
  <tr>
    <td style="padding:9px 12px;font-family:monospace;font-weight:600;color:#64748b;font-size:11px">${t.id}</td>
    <td style="padding:9px 12px"><span class="badge ${t.tipoBadge}">${t.tipo}</span></td>
    <td style="padding:9px 12px;font-family:monospace;font-size:11px;color:#1a5fb4">${t.cod}</td>
    <td style="padding:9px 12px;font-size:11.5px;max-width:200px">${t.nombre}</td>
    <td style="padding:9px 12px;font-size:11px;color:#64748b">${t.remitente}</td>
    <td style="padding:9px 12px;font-size:11px;color:#64748b">${t.fecha}</td>
    <td style="padding:9px 12px"><span class="badge ${t.slaBadge}">${t.sla}</span></td>
    <td style="padding:9px 12px"><a href="#${t.ruta}" class="btn btn-primary btn-sm" style="white-space:nowrap">Atender →</a></td>
  </tr>`).join('')

const evalRows = evaluacionesPendientesDB.map(e => `
  <tr>
    <td style="padding:9px 12px;font-size:11.5px">${e.tipo}</td>
    <td style="padding:9px 12px;font-family:monospace;font-size:11px">${e.cod}</td>
    <td style="padding:9px 12px;font-size:11.5px">${e.nombre}</td>
    <td style="padding:9px 12px;font-size:11.5px">${e.fechaInicio}</td>
    <td style="padding:9px 12px;font-size:11px;font-weight:600;color:${e.urgente ? '#dc2626' : '#d97706'}">${e.fechaLimite}</td>
    <td style="padding:9px 12px"><a href="#${e.ruta}" class="btn ${e.btnClass} btn-sm">${e.btnLabel}</a></td>
  </tr>`).join('')

const lecturaRows = controlesLecturaDB.map(c => `
  <tr>
    <td style="padding:9px 12px;font-size:11.5px">${c.tipo}</td>
    <td style="padding:9px 12px;font-family:monospace;font-size:11px">${c.cod}</td>
    <td style="padding:9px 12px;font-size:11.5px">${c.nombre}</td>
    <td style="padding:9px 12px;font-size:11.5px">${c.fechaInicio}</td>
    <td style="padding:9px 12px;font-size:11px;color:#64748b">${c.fechaFin}</td>
    <td style="padding:9px 12px"><a href="#${c.ruta}" class="btn btn-primary btn-sm">${c.btnLabel}</a></td>
  </tr>`).join('')

export const page = {
  init() {
    window.Alpine?.data('bandeja', () => ({
      copias: [...recepcionCopiasDB],

      get isETO() {
        return window.Alpine?.store('auth')?.role === 'eto'
      },

      get fechaHoy() {
        return new Date().toLocaleDateString('es-BO')
      },

      recibirCopia(idx) {
        const c = this.copias[idx]
        window.authRecepcionModal?.abrir({
          docInfo: c.cod + ' — ' + c.nombre,
          destinatario: c.numCopia,
          onConfirm: () => {
            this.copias.splice(idx, 1)
            window.toast('✅ Recepción confirmada para ' + c.cod, 'success')
          },
        })
      },
    }))
  },

  template: /* html */`
<div x-data="bandeja" style="animation:fadeIn 0.35s ease-out both">

  <!-- Header -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Mi Bandeja de Tareas</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0"><span x-text="fechaHoy"></span> · Resumen del día</p>
    </div>
  </div>

  <!-- Tareas de Flujo (oculto para visualizador) -->
  <div x-show="$store.auth.role !== 'visualizador'"
       style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06);animation:slideUp 0.4s cubic-bezier(0.16,1,0.3,1) both;animation-delay:0.05s">
    <div style="display:flex;align-items:center;gap:8px;font-size:10.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid #f1f5f9">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="#1a5fb4"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/></svg>
      Tareas Pendientes (Flujo)
      <span class="badge badge-red" style="margin-left:4px">3</span>
    </div>
    <div style="overflow-x:auto;margin:0 -20px">
      <table class="data-table" style="min-width:700px;margin:0 20px;width:calc(100% - 40px)">
        <thead>
          <tr>
            <th>ID Proceso</th><th>Tarea</th><th>Código Doc.</th><th>Nombre Documento</th>
            <th>Remitente</th><th>Fecha Asignación</th><th>SLA</th><th>Acción</th>
          </tr>
        </thead>
        <tbody>${tareasRows}</tbody>
      </table>
    </div>
    <div style="text-align:right;margin-top:12px">
      <a href="#/tareas-completas" style="font-size:11px;color:#1a5fb4;font-weight:600;text-decoration:underline;text-underline-offset:2px">Ver lista completa →</a>
    </div>
  </div>

  <!-- Evaluaciones -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06);animation:slideUp 0.4s cubic-bezier(0.16,1,0.3,1) both;animation-delay:0.1s">
    <div style="display:flex;align-items:center;gap:8px;font-size:10.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid #f1f5f9">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="#d97706"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
      Evaluaciones Pendientes
      <span class="badge badge-amber" style="margin-left:4px">2</span>
    </div>
    <div style="overflow-x:auto;margin:0 -20px">
      <table class="data-table" style="min-width:560px;margin:0 20px;width:calc(100% - 40px)">
        <thead>
          <tr><th>Tarea</th><th>Código Doc.</th><th>Nombre Documento</th><th>Fecha Inicio</th><th>Fecha Fin</th><th>Acción</th></tr>
        </thead>
        <tbody>${evalRows}</tbody>
      </table>
    </div>
  </div>

  <!-- Control de Lectura -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06);animation:slideUp 0.4s cubic-bezier(0.16,1,0.3,1) both;animation-delay:0.15s">
    <div style="display:flex;align-items:center;gap:8px;font-size:10.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid #f1f5f9">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="#7c3aed"><path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"/></svg>
      Control de Lectura
      <span class="badge badge-blue" style="margin-left:4px">1</span>
    </div>
    <div style="overflow-x:auto;margin:0 -20px">
      <table class="data-table" style="min-width:500px;margin:0 20px;width:calc(100% - 40px)">
        <thead>
          <tr><th>Tarea</th><th>Código Doc.</th><th>Nombre Documento</th><th>Fecha Inicio</th><th>Fecha Fin</th><th>Acción</th></tr>
        </thead>
        <tbody>${lecturaRows}</tbody>
      </table>
    </div>
  </div>

  <!-- Copias Físicas (solo role 'user') — Alpine reactivo para authModal -->
  <div x-show="$store.auth.role === 'user'"
       style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06);animation:slideUp 0.4s cubic-bezier(0.16,1,0.3,1) both;animation-delay:0.2s">
    <div style="display:flex;align-items:center;gap:8px;font-size:10.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid #f1f5f9">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="#059669"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
      Recepción de Copias Físicas
      <span class="badge badge-green" style="margin-left:4px" x-text="copias.length"></span>
    </div>
    <p style="font-size:11.5px;color:#64748b;margin-bottom:12px">Confirme la recepción en físico de los documentos asignados. Esta acción requiere firma digital.</p>

    <template x-if="copias.length > 0">
      <div style="overflow-x:auto;margin:0 -20px">
        <table class="data-table" style="min-width:620px;margin:0 20px;width:calc(100% - 40px)">
          <thead>
            <tr>
              <th>Tipo de Copia</th><th>Código</th><th>Versión</th>
              <th>Nombre de Documento</th><th style="text-align:center">N° Copia</th><th style="text-align:center">Acción</th>
            </tr>
          </thead>
          <tbody>
            <template x-for="(c, idx) in copias" :key="c.cod+idx">
              <tr :style="c.prioridad ? 'background:rgba(254,242,242,0.5)' : ''">
                <td style="padding:9px 12px"><span class="badge" :class="c.tipoBadge" x-text="c.tipo"></span></td>
                <td style="padding:9px 12px;font-family:monospace;font-weight:700;font-size:11px"
                    :style="c.prioridad ? 'color:#dc2626' : 'color:#1a5fb4'"
                    x-text="c.cod"></td>
                <td style="padding:9px 12px;font-size:11px" x-text="c.ver"></td>
                <td style="padding:9px 12px;font-size:11.5px"
                    :style="c.prioridad ? 'color:#dc2626' : ''"
                    x-text="c.nombre"></td>
                <td style="padding:9px 12px;text-align:center;font-weight:700"
                    :style="c.prioridad ? 'color:#dc2626' : ''"
                    x-text="c.numCopia"></td>
                <td style="padding:9px 12px;text-align:center">
                  <button class="btn btn-primary btn-sm" style="white-space:nowrap" @click="recibirCopia(idx)">✅ Recibido</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </template>

    <div x-show="copias.length === 0" style="text-align:center;padding:30px;color:#94a3b8;font-size:12px">
      <svg width="32" height="32" viewBox="0 0 20 20" fill="#a3e635" style="margin-bottom:8px;opacity:0.6"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
      <div>No tiene copias físicas pendientes de recepción.</div>
    </div>
  </div>

</div>`
}
