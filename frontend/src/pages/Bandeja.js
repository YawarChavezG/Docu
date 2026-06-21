import { apiGet } from '../utils/api.js'
import { recepcionCopiasDB } from '../data/tasks.js'

const COLORES_SLA = {
  VERDE: 'badge-green',
  AMARILLO: 'badge-amber',
  ROJO: 'badge-red',
}

const RUTAS_POR_TIPO = {
  LIBERACION: '/liberacion-detalle',
  REVISION: '/revision',
  APROBACION: '/aprobacion-final',
  CORRECCION: '/correccion',
}

function badgeTipo(tipo) {
  const map = {
    REVISION: 'badge-blue', APROBACION: 'badge-purple',
    LIBERACION: 'badge-green', CORRECCION: 'badge-amber',
    CONTROL_LECTURA: 'badge-teal', EVALUACION: 'badge-red',
  }
  return map[tipo] || 'badge-gray'
}

function etaSLA(fecha) {
  if (!fecha) return { label: '—', color: 'badge-gray' }
  const dias = Math.ceil((new Date(fecha) - new Date()) / (1000 * 60 * 60 * 24))
  if (dias > 7) return { label: `${dias} d`, color: 'badge-green' }
  if (dias > 3) return { label: `${dias} d`, color: 'badge-amber' }
  if (dias >= 0) return { label: `${dias} d`, color: 'badge-red' }
  return { label: 'Vencida', color: 'badge-red' }
}

export const page = {
  init() {
    window.Alpine?.data('bandeja', () => ({
      tareas: [],
      cargandoTareas: true,
      errorTareas: '',
      copias: [...recepcionCopiasDB],

      get isETO() {
        return window.Alpine?.store('auth')?.user?.roles?.includes('ETO') || false
      },

      get fechaHoy() {
        return new Date().toLocaleDateString('es-BO')
      },

      init() {
        this.cargarTareas()
      },

      async cargarTareas() {
        this.cargandoTareas = true
        this.errorTareas = ''
        try {
          const res = await apiGet('/tareas?page_size=50')
          if (res.ok) this.tareas = res.data?.items || []
          else this.errorTareas = res.message || 'Error al cargar tareas'
        } catch (e) {
          this.errorTareas = e?.message || 'Error de conexion'
        } finally {
          this.cargandoTareas = false
        }
      },

      badgeTipo(t) { return badgeTipo(t) },
      etaSLA(f) { return etaSLA(f) },

      rutaTarea(t) {
        return RUTAS_POR_TIPO[t.tipo_tarea] || '/bandeja'
      },

      recibirCopia(idx) {
        const c = this.copias[idx]
        window.authRecepcionModal?.abrir({
          docInfo: c.cod + ' — ' + c.nombre,
          destinatario: c.numCopia,
          onConfirm: () => {
            this.copias.splice(idx, 1)
            window.toast('Recepcion confirmada para ' + c.cod, 'success')
          },
        })
      },
    }))
  },

  template: /* html */ `
<div x-data="bandeja" style="animation:fadeIn 0.35s ease-out both">

  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Mi Bandeja de Tareas</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0"><span x-text="fechaHoy"></span> · Resumen del dia</p>
    </div>
  </div>

  <div x-show="$store.auth.role !== 'visualizador'"
       style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
    <div style="display:flex;align-items:center;gap:8px;font-size:10.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid #f1f5f9">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="#1a5fb4"><path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"/></svg>
      Tareas Pendientes
      <span class="badge badge-red" style="margin-left:4px" x-text="tareas.length"></span>
    </div>

    <div x-show="cargandoTareas" style="text-align:center;padding:30px;color:#94a3b8;font-size:12px">Cargando tareas...</div>
    <div x-show="errorTareas" style="text-align:center;padding:20px;color:#dc2626;font-size:12px" x-text="errorTareas"></div>

    <div x-show="!cargandoTareas && !errorTareas && tareas.length === 0" style="text-align:center;padding:30px;color:#94a3b8;font-size:12px">No tiene tareas pendientes.</div>

    <div x-show="!cargandoTareas && tareas.length > 0" style="overflow-x:auto;margin:0 -20px">
      <table class="data-table" style="min-width:700px;margin:0 20px;width:calc(100% - 40px)">
        <thead>
          <tr>
            <th>ID</th><th>Tarea</th><th>Codigo Doc.</th><th>Nombre Documento</th>
            <th>Fecha Asignacion</th><th>SLA</th><th>Accion</th>
          </tr>
        </thead>
        <tbody>
          <template x-for="t in tareas" :key="t.id">
            <tr>
              <td style="padding:9px 12px;font-family:monospace;font-weight:600;color:#64748b;font-size:11px" x-text="t.id"></td>
              <td style="padding:9px 12px"><span class="badge" :class="badgeTipo(t.tipo_tarea)" x-text="t.tipo_tarea"></span></td>
              <td style="padding:9px 12px;font-family:monospace;font-size:11px;color:#1a5fb4" x-text="t.codigo_completo"></td>
              <td style="padding:9px 12px;font-size:11.5px;max-width:200px" x-text="t.titulo_documento"></td>
              <td style="padding:9px 12px;font-size:11px;color:#64748b" x-text="new Date(t.fecha_asignacion).toLocaleDateString('es-BO')"></td>
              <td style="padding:9px 12px"><span class="badge" :class="etaSLA(t.fecha_vencimiento).color" x-text="etaSLA(t.fecha_vencimiento).label"></span></td>
              <td style="padding:9px 12px"><a :href="'#' + rutaTarea(t)" class="btn btn-primary btn-sm" style="white-space:nowrap">Atender →</a></td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>

  <div x-show="copias.length > 0"
       style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.06)">
    <div style="display:flex;align-items:center;gap:8px;font-size:10.5px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid #f1f5f9">
      <svg width="14" height="14" viewBox="0 0 20 20" fill="#059669"><path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
      Recepcion de Copias Fisicas
      <span class="badge badge-green" style="margin-left:4px" x-text="copias.length"></span>
    </div>
    <template x-if="copias.length > 0">
      <div style="overflow-x:auto;margin:0 -20px">
        <table class="data-table" style="min-width:620px;margin:0 20px;width:calc(100% - 40px)">
          <thead><tr><th>Tipo</th><th>Codigo</th><th>Version</th><th>Documento</th><th>N° Copia</th><th>Accion</th></tr></thead>
          <tbody>
            <template x-for="(c, idx) in copias" :key="c.cod+idx">
              <tr :style="c.prioridad ? 'background:rgba(254,242,242,0.5)' : ''">
                <td style="padding:9px 12px"><span class="badge" :class="c.tipoBadge" x-text="c.tipo"></span></td>
                <td style="padding:9px 12px;font-family:monospace;font-weight:700;font-size:11px;color:#1a5fb4" x-text="c.cod"></td>
                <td style="padding:9px 12px;font-size:11px" x-text="c.ver"></td>
                <td style="padding:9px 12px;font-size:11.5px" x-text="c.nombre"></td>
                <td style="padding:9px 12px;text-align:center;font-weight:700" x-text="c.numCopia"></td>
                <td style="padding:9px 12px;text-align:center">
                  <button class="btn btn-primary btn-sm" @click="recibirCopia(idx)">Recibido</button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </template>
    <div x-show="copias.length === 0" style="text-align:center;padding:30px;color:#94a3b8;font-size:12px">Sin copias pendientes.</div>
  </div>

</div>`
}
