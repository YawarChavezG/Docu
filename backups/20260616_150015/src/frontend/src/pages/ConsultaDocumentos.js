/**
 * pages/ConsultaDocumentos.js — Tabla de procesos con timeline accordion (US-8.01)
 * Campos en procesosConsultaDB: id, user, area, cod, f_sol, f_lib, f_rev, f_apr, etapa, resp, est, log[]
 * Log entries: { etapa, user, acc, fecha, hora, obs }
 */
import { procesosConsultaDB, TIMELINE_CONFIG } from '../data/documents.js'
import { exportarProcesosExcel } from '../utils/exportExcel.js'

const BG_MAP = {
  '#3b82f6': '#eff6ff',
  '#10b981': '#ecfdf5',
  '#ef4444': '#fef2f2',
  '#d97706': '#fffbeb',
  '#6b7280': '#f9fafb',
}

function tlNode(acc) {
  const cfg = TIMELINE_CONFIG[acc] || { icon: '?', color: '#6b7280', title: 'Nota:' }
  return {
    icon:  cfg.icon,
    color: cfg.color,
    bg:    BG_MAP[cfg.color] || '#f9fafb',
    title: cfg.title,
  }
}

const ESTADO_STYLE = {
  'Concluido':    { bg: '#ecfdf5', color: '#059669', border: '#a7f3d0' },
  'En ejecución': { bg: '#eff6ff', color: '#2563eb', border: '#bfdbfe' },
  'Eliminado':    { bg: '#fef2f2', color: '#dc2626', border: '#fecaca' },
}

export const page = {
  init() {
    window.Alpine?.data('consultaDocs', () => ({
      procesos: procesosConsultaDB,
      q: { nro: '', user: '', area: '', cod: '', ver: '' },
      expanded: {},
      showChart: false,
      filterEstado: [],
      showFiltroEst: false,

      get isETO() {
        return window.Alpine?.store('auth')?.role === 'eto'
      },

      get filtered() {
        const fe = this.filterEstado
        return this.procesos.filter(p => {
          if (fe.length && !fe.includes(p.est)) return false
          if (this.q.nro  && !String(p.id).includes(this.q.nro)) return false
          if (this.q.user && !p.user.toLowerCase().includes(this.q.user.toLowerCase())) return false
          if (this.q.area && !p.area.toLowerCase().includes(this.q.area.toLowerCase())) return false
          if (this.q.cod  && !p.cod.toLowerCase().includes(this.q.cod.toLowerCase())) return false
          if (this.q.ver  && !(p.ver || '').toLowerCase().includes(this.q.ver.toLowerCase())) return false
          return true
        })
      },

      get chartData() {
        const data = this.filtered
        const total = data.length || 1
        const estados = {}
        const areas = {}
        data.forEach(p => {
          estados[p.est] = (estados[p.est] || 0) + 1
          areas[p.area] = (areas[p.area] || 0) + 1
        })
        const estadoRows = Object.entries(estados)
          .sort((a, b) => b[1] - a[1])
          .map(([k, v]) => ({ label: k, pct: Math.round((v / total) * 100), color: k === 'En ejecución' ? '#d97706' : k === 'Concluido' ? '#059669' : '#dc2626' }))
        const areaRows = Object.entries(areas)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 4)
          .map(([k, v]) => ({ label: k, pct: Math.round((v / total) * 100) }))
        return { estadoRows, areaRows, total }
      },

      togRow(id)     { this.expanded[id] = !this.expanded[id] },
      togEst(v)      { const i = this.filterEstado.indexOf(v); if (i === -1) this.filterEstado.push(v); else this.filterEstado.splice(i, 1) },
      estadoStyle(e) { return ESTADO_STYLE[e] || ESTADO_STYLE['Concluido'] },
      tlNode(acc)    { return tlNode(acc) },
      isPendiente(acc) { return acc === 'Pendiente' },

      eliminar(p) {
        window.authModal?.abrir({
          titulo: '⚠️ Eliminar Proceso',
          icono: '🗑️',
          mensaje: `¿Confirma la anulación del proceso <strong>${p.id}</strong> — <strong>${p.cod}</strong>? Esta acción quedará registrada en la bitácora y no puede revertirse.`,
          onSuccess: () => {
            p.est = 'Eliminado'; p.etapa = 'Anulado'
            p.log.push({ etapa: 'Anulado', user: window.Alpine?.store('auth')?.nombre || 'ETO', acc: 'Eliminado', fecha: new Date().toLocaleDateString('es-BO'), hora: new Date().toLocaleTimeString('es-BO', {hour:'2-digit',minute:'2-digit'}), obs: 'Anulado por ETO desde Consulta de Documentos' })
            window.toast('🗑️ Proceso ' + p.id + ' anulado', 'warn')
          },
        })
      },

      reasModal: { show: false, nodo: null, proceso: null, persona: '' },
      listaPersonas: ['Aracely Romero (ETO Calidad)', 'Maria Condori (Analista)', 'Carlos Flores (Jefe Logística)', 'Luis Mamani (Gerente)', 'Jasiel Sanjinés (Jefe Excelencia)', 'Lucia Terán (Analista Sr.)', 'Pedro Mamani (Operario)'],
      reasignar(l, p) {
        this.reasModal = { show: true, nodo: l, proceso: p, persona: '' }
      },
      confirmarReasignar() {
        if (!this.reasModal.persona.trim()) { window.toast('⚠️ Seleccione una persona', 'warn'); return }
        const m = this.reasModal
        window.authModal?.abrir({
          titulo: '🔄 Confirmar Reasignación',
          icono: '🔄',
          mensaje: `Va a reasignar el nodo <strong>${m.nodo.etapa}</strong> a <strong>${m.persona}</strong>. La acción quedará registrada en la bitácora del proceso.`,
          onSuccess: () => {
            const antes = m.nodo.user
            const idx = m.proceso.log.indexOf(m.nodo)
            if (idx !== -1) {
              // Extraer nodo original
              const nodoOriginal = m.proceso.log.splice(idx, 1)[0]
              const actor = window.Alpine?.store('auth')?.nombre || 'ETO'
              // 1. Penúltimo: nodo original mutado
              nodoOriginal.acc = 'Reasignado'
              nodoOriginal.obs = 'Reasignado de ' + antes + ' a ' + m.persona + ' por ' + actor
              m.proceso.log.push(nodoOriginal)
              // 2. Último: nuevo usuario pendiente
              m.proceso.log.push({
                etapa: nodoOriginal.etapa,
                user: m.persona,
                acc: 'Pendiente',
                fecha: new Date().toLocaleDateString('es-BO'),
                hora: new Date().toLocaleTimeString('es-BO', {hour:'2-digit',minute:'2-digit'}),
                obs: ''
              })
            }
            m.proceso.resp = m.persona
            this.reasModal.show = false
            window.toast('✅ Nodo reasignado a ' + m.persona, 'success')
          },
        })
      },
    }))
  },

  template: /* html */`
<div x-data="consultaDocs" @click.outside="showFiltroEst=false" style="animation:fadeIn 0.35s ease-out both">

  <!-- Header -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px">
    <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Consultar Documentos</h1>
    <div style="display:flex;gap:8px">
      <select class="btn btn-sm" style="background:#fff;border-color:#e2e8f0;padding-right:20px"
              @change="if($el.value==='Excel'){exportarProcesosExcel(filtered);$el.value=''}else if($el.value){window.toast('Generando reporte en '+$el.value+'...','info');$el.value=''}">
        <option value="">↓ Exportar reporte</option>
        <option value="Excel">Formato Excel (.xlsx)</option>
        <option value="PDF">Formato PDF (.pdf)</option>
      </select>
      <button class="btn btn-primary btn-sm" @click="showChart=!showChart">📊 Visualizar reporte gráfico</button>
    </div>
  </div>

  <!-- Gráfica (toggle) -->
  <div x-show="showChart" style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
    <div style="font-size:13px;font-weight:600;color:#1e293b;margin-bottom:16px">Reporte Gráfico del Listado Actual</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div>
        <div style="font-size:11.5px;font-weight:500;color:#475569;margin-bottom:10px">Documentos por Estado del Proceso</div>
        <div style="display:flex;flex-direction:column;gap:6px">
          <template x-for="row in chartData.estadoRows" :key="row.label">
            <div style="display:flex;align-items:center;gap:8px;font-size:11px">
              <span style="width:90px;color:#475569" x-text="row.label"></span>
              <div style="flex:1;height:12px;background:#f1f5f9;border-radius:9999px;overflow:hidden">
                <div :style="'width:'+row.pct+'%;height:100%;background:'+row.color+';border-radius:9999px'"></div>
              </div>
              <span style="width:32px;color:#64748b" x-text="row.pct+'%'"></span>
            </div>
          </template>
        </div>
      </div>
      <div>
        <div style="font-size:11.5px;font-weight:500;color:#475569;margin-bottom:10px">Documentos por Área (Top 4)</div>
        <div style="display:flex;flex-direction:column;gap:6px">
          <template x-for="row in chartData.areaRows" :key="row.label">
            <div style="display:flex;align-items:center;gap:8px;font-size:11px">
              <span style="width:120px;color:#475569" x-text="row.label"></span>
              <div style="flex:1;height:12px;background:#f1f5f9;border-radius:9999px;overflow:hidden">
                <div :style="'width:'+row.pct+'%;height:100%;background:#1a5fb4;border-radius:9999px'"></div>
              </div>
              <span style="width:32px;color:#64748b" x-text="row.pct+'%'"></span>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>

  <p style="font-size:11.5px;color:#64748b;margin-bottom:10px">Para proceder con la búsqueda de un documento, puede utilizar los siguientes filtros en cada columna:</p>

  <!-- Tabla -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05);overflow:hidden">
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:11.5px;min-width:1400px">
        <thead>
          <tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0">
            <th style="width:32px;padding:8px 6px"></th>

            <th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:100px">
              <div>NRO PROCESO</div>
              <input type="text" x-model="q.nro" placeholder="Buscar..."
                     style="width:100%;padding:3px 6px;margin-top:5px;border:1px solid #e2e8f0;border-radius:4px;font-size:10.5px;font-weight:400;text-transform:none;letter-spacing:0;outline:none;font-family:inherit"
                     @focus="$el.style.borderColor='#1a5fb4'" @blur="$el.style.borderColor='#e2e8f0'">
            </th>

            <th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:110px">
              <div>USUARIO CREADOR</div>
              <input type="text" x-model="q.user" placeholder="Buscar..."
                     style="width:100%;padding:3px 6px;margin-top:5px;border:1px solid #e2e8f0;border-radius:4px;font-size:10.5px;font-weight:400;text-transform:none;letter-spacing:0;outline:none;font-family:inherit"
                     @focus="$el.style.borderColor='#1a5fb4'" @blur="$el.style.borderColor='#e2e8f0'">
            </th>

            <th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:140px">
              <div>ÁREA</div>
              <input type="text" x-model="q.area" placeholder="Buscar..."
                     style="width:100%;padding:3px 6px;margin-top:5px;border:1px solid #e2e8f0;border-radius:4px;font-size:10.5px;font-weight:400;text-transform:none;letter-spacing:0;outline:none;font-family:inherit"
                     @focus="$el.style.borderColor='#1a5fb4'" @blur="$el.style.borderColor='#e2e8f0'">
            </th>

            <th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:110px">
              <div>CÓDIGO</div>
              <input type="text" x-model="q.cod" placeholder="Buscar..."
                     style="width:100%;padding:3px 6px;margin-top:5px;border:1px solid #e2e8f0;border-radius:4px;font-size:10.5px;font-weight:400;text-transform:none;letter-spacing:0;outline:none;font-family:inherit"
                     @focus="$el.style.borderColor='#1a5fb4'" @blur="$el.style.borderColor='#e2e8f0'">
            </th>

            <th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:70px">
              <div>VERSIÓN</div>
              <input type="text" x-model="q.ver" placeholder="Buscar..."
                     style="width:100%;padding:3px 6px;margin-top:5px;border:1px solid #e2e8f0;border-radius:4px;font-size:10.5px;font-weight:400;text-transform:none;letter-spacing:0;outline:none;font-family:inherit"
                     @focus="$el.style.borderColor='#1a5fb4'" @blur="$el.style.borderColor='#e2e8f0'">
            </th>

            <th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:90px">SOLICITUD</th>
            <th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:90px">LIBERACIÓN</th>
            <th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:90px">REVISIÓN</th>
            <th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:90px">APROBACIÓN</th>
            <th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:140px">ETAPA ACTUAL</th>
            <th style="padding:6px 10px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:140px">RESPONSABLE</th>

            <!-- ESTADO con filtro checkbox -->
            <th style="padding:6px 10px;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:130px;position:relative">
              <div style="display:flex;align-items:center;gap:4px;cursor:pointer;color:#1a5fb4" @click.stop="showFiltroEst=!showFiltroEst">
                ESTADO <span style="font-size:9px">▼</span>
                <span x-show="filterEstado.length" style="width:16px;height:16px;background:#1a5fb4;color:#fff;border-radius:9999px;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700" x-text="filterEstado.length"></span>
              </div>
              <div x-show="showFiltroEst" @click.stop style="position:absolute;top:100%;left:0;z-index:200;background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:8px;box-shadow:0 8px 24px rgba(0,0,0,0.1);min-width:155px;display:flex;flex-direction:column;gap:4px">
                <template x-for="e in ['Concluido','En ejecución','Eliminado']" :key="e">
                  <label style="display:flex;align-items:center;gap:6px;font-size:11px;font-weight:500;color:#1e293b;cursor:pointer;text-transform:none;letter-spacing:0;padding:3px 2px">
                    <input type="checkbox" :value="e" :checked="filterEstado.includes(e)" @change="togEst(e)" style="accent-color:#1a5fb4">
                    <span x-text="e"></span>
                  </label>
                </template>
                <button class="btn btn-sm" style="margin-top:4px;font-size:10px" @click="filterEstado=[];showFiltroEst=false">Limpiar</button>
              </div>
            </th>

            <th style="padding:6px 10px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;width:80px">DOCUMENTO</th>
          </tr>
        </thead>
          <template x-for="p in filtered" :key="p.id">
            <tbody style="border-bottom: 1px solid #f1f5f9;">
              <!-- Fila principal -->
              <tr :style="p.est==='Eliminado'?'opacity:0.6':''"
                  style="border-bottom:1px solid #f1f5f9;transition:background 100ms"
                  @mouseenter="$el.style.background='rgba(239,246,255,0.4)'"
                  @mouseleave="$el.style.background=''">
                <td style="padding:8px 6px;text-align:center">
                  <button @click="togRow(p.id)"
                          style="width:20px;height:20px;border-radius:4px;border:1px solid #e2e8f0;background:#f8fafc;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-family:inherit"
                          x-text="expanded[p.id]?'−':'+'"></button>
                </td>
                <td style="padding:8px 10px;font-family:monospace;font-weight:700;color:#475569;font-size:11px" x-text="p.id"></td>
                <td style="padding:8px 10px;font-size:11px;color:#64748b" x-text="p.user"></td>
                <td style="padding:8px 10px;font-size:11px;color:#64748b" x-text="p.area"></td>
                <td style="padding:8px 10px;font-family:monospace;font-size:11px;font-weight:600;color:#1a5fb4" x-text="p.cod"></td>
                <td style="padding:8px 10px;text-align:center;font-size:10.5px;color:#64748b" x-text="p.ver || '—'"></td>
                <td style="padding:8px 10px;text-align:center;font-size:10.5px;color:#64748b" x-text="p.f_sol"></td>
                <td style="padding:8px 10px;text-align:center;font-size:10.5px;color:#64748b" x-text="p.f_lib"></td>
                <td style="padding:8px 10px;text-align:center;font-size:10.5px;color:#64748b" x-text="p.f_rev"></td>
                <td style="padding:8px 10px;text-align:center;font-size:10.5px;color:#64748b" x-text="p.f_apr"></td>
                <td style="padding:8px 10px;font-size:11px;color:#1e293b;font-weight:500" x-text="p.etapa"></td>
                <td style="padding:8px 10px;font-size:10.5px;color:#64748b" x-text="p.resp"></td>
                <td style="padding:8px 10px">
                  <div style="display:flex;align-items:center;gap:6px">
                    <span :style="'display:inline-flex;padding:2px 9px;border-radius:9999px;font-size:10px;font-weight:600;background:'+estadoStyle(p.est).bg+';color:'+estadoStyle(p.est).color+';border:1px solid '+estadoStyle(p.est).border"
                          x-text="p.est"></span>
                    <button x-show="isETO && p.est==='En ejecución'" @click="eliminar(p)"
                            style="width:18px;height:18px;border-radius:4px;border:1px solid #fecaca;background:#fef2f2;color:#dc2626;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-family:inherit"
                            title="Anular proceso">✕</button>
                  </div>
                </td>
                <td style="padding:8px 10px;text-align:center">
                  <button @click="window.pdfViewer?.abrir({cod:p.cod,titulo:p.cod,tipo:'original',esVencido:false,esObsoleto:false,returnRoute:'/consulta'})"
                          style="padding:2px 8px;font-size:10px;font-weight:700;border-radius:4px;border:1px solid #b5d4f4;background:#eff6ff;color:#1a5fb4;cursor:pointer;font-family:inherit;white-space:nowrap">⊙ Ver doc</button>
                </td>
              </tr>

              <!-- Timeline accordion -->
              <tr x-show="expanded[p.id]">
                <td colspan="14" style="padding:0;background:#f8fafc;border-bottom:2px solid #e2e8f0">
                  <div style="padding:14px 16px 14px 50px">
                    <div style="font-size:10.5px;font-weight:700;color:#1a5fb4;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.05em"
                         x-text="'HISTORIAL DEL PROCESO: '+p.cod"></div>
                    <div style="display:flex;flex-direction:column;gap:0">
                      <template x-for="(l,li) in p.log" :key="li">
                        <div style="display:flex;gap:12px;position:relative">
                          <div style="display:flex;flex-direction:column;align-items:center;width:28px;flex-shrink:0">
                            <div :style="'width:28px;height:28px;border-radius:9999px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0;background:'+tlNode(l.acc).bg+';border:2px solid '+tlNode(l.acc).color+';color:'+tlNode(l.acc).color"
                                 x-text="tlNode(l.acc).icon"></div>
                            <div x-show="li < p.log.length-1" style="width:2px;flex:1;background:#e2e8f0;min-height:24px;margin:2px 0"></div>
                          </div>
                          <div style="padding-bottom:16px;flex:1">
                            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                              <div style="font-size:11.5px">
                                <span style="font-weight:600;color:#1e293b" x-text="l.etapa"></span>
                                <span style="color:#94a3b8"> | Acción: </span>
                                <span :style="'font-weight:700;color:'+tlNode(l.acc).color" x-text="l.acc"></span>
                              </div>
                              <span style="font-size:10px;color:#94a3b8;margin-left:auto;white-space:nowrap"
                                    x-text="'📅 '+l.fecha+' 🕐 '+l.hora"></span>
                              <button x-show="isETO && isPendiente(l.acc)" @click="reasignar(l, p)"
                                      style="padding:2px 10px;font-size:10px;font-weight:700;border-radius:4px;border:1px solid #bfdbfe;background:#eff6ff;color:#1a5fb4;cursor:pointer;font-family:inherit">Reasignar</button>
                            </div>
                            <div style="font-size:11px;color:#475569;margin-top:3px">
                              👤 Responsable:
                              <strong x-text="l.user" :style="l.acc==='Reasignado' ? 'text-decoration:line-through;opacity:0.6' : ''"></strong>
                              <span x-show="l.acc==='Reasignado'" style="font-size:10px;color:#6b7280;margin-left:4px">(Reasignado)</span>
                            </div>
                            <div x-show="l.obs && l.obs !== '-'"
                                 :style="'margin-top:6px;padding:7px 10px;border-radius:6px;font-size:11px;background:'+tlNode(l.acc).bg+';border:1px solid '+tlNode(l.acc).color+'33;color:'+tlNode(l.acc).color+'dd'"
                                 x-text="tlNode(l.acc).title+' '+l.obs"></div>
                          </div>
                        </div>
                      </template>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody> 
          </template>
          
          <tbody x-show="filtered.length===0">
            <tr>
              <td colspan="14" style="text-align:center;padding:40px;color:#94a3b8;font-style:italic">
                No se encontraron procesos con los filtros aplicados.
              </td>
            </tr>
          </tbody>
      </table>
    </div>
  </div>

  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:10.5px;color:#94a3b8;flex-wrap:wrap;gap:6px">
    <span x-text="'Mostrando '+filtered.length+' de '+procesos.length+' procesos'"></span>
    <span>Clic en + para ver historial · Filtros en cabecera para buscar</span>
  </div>

  <!-- Modal Reasignación -->
  <template x-teleport="body">
    <div x-show="reasModal.show"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         @click.self="reasModal.show=false"
         class="modal-overlay"
         style="display:none;">
      <div @click.stop class="modal-box max-w-sm">
        <div style="font-size:32px;text-align:center;margin-bottom:12px">🔄</div>
        <h2 style="font-size:15px;font-weight:700;color:#1e293b;margin:0 0 6px;text-align:center">Reasignar Responsable</h2>
        <p style="font-size:11.5px;color:#64748b;margin:0 0 18px;text-align:center" x-text="'Nodo: ' + (reasModal.nodo?.etapa || '') + ' · Proceso ' + (reasModal.proceso?.cod || '')"></p>
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;margin-bottom:14px;font-size:11px;color:#475569">
          Responsable actual: <strong x-text="reasModal.nodo?.user"></strong>
        </div>
        <div style="margin-bottom:18px">
          <label style="font-size:10.5px;font-weight:600;color:#64748b;display:block;margin-bottom:6px">Seleccionar nuevo responsable</label>
          <input type="text" class="form-input" x-model="reasModal.persona"
                 list="lista-empleados-reas"
                 placeholder="Escriba el nombre del responsable..."
                 style="font-size:12px">
          <datalist id="lista-empleados-reas">
            <template x-for="p in listaPersonas" :key="p">
              <option :value="p"></option>
            </template>
          </datalist>
        </div>
        <div style="display:flex;gap:10px">
          <button class="btn flex-1" @click="reasModal.show=false">Cancelar</button>
          <button class="btn btn-primary flex-1" @click="confirmarReasignar()">✅ Confirmar Reasignación</button>
        </div>
      </div>
    </div>
  </template>

</div>`
}
