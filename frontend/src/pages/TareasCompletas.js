/**
 * pages/TareasCompletas.js — Lista completa de tareas filtrable (robust styles)
 */
import { tareasCompletasDB } from '../data/tasks.js'

export const page = {
  init() {
    window.Alpine?.data('tareasPage', () => ({
      items: tareasCompletasDB,
      filters: { id:'', tipo:'', codigo:'', nombre:'', remitente:'', fecha:'' },
      sortKey: 'sla', sortDir: 'desc',
      get filtered() {
        return this.items
          .filter(t => {
            const f = this.filters
            return (!f.id||String(t.id).includes(f.id)) &&
                   (!f.tipo||t.tipo.toLowerCase().includes(f.tipo.toLowerCase())) &&
                   (!f.codigo||t.codigo.toLowerCase().includes(f.codigo.toLowerCase())) &&
                   (!f.nombre||t.nombre.toLowerCase().includes(f.nombre.toLowerCase())) &&
                   (!f.remitente||t.remitente.toLowerCase().includes(f.remitente.toLowerCase())) &&
                   (!f.fecha||t.fecha.includes(f.fecha))
          })
          .sort((a,b) => {
            let va=a[this.sortKey], vb=b[this.sortKey]
            if(typeof va==='string'){va=va.toLowerCase();vb=vb.toLowerCase()}
            if(va<vb)return this.sortDir==='asc'?-1:1
            if(va>vb)return this.sortDir==='asc'?1:-1
            return 0
          })
      },
      sort(key) { if(this.sortKey===key){this.sortDir=this.sortDir==='asc'?'desc':'asc'}else{this.sortKey=key;this.sortDir='asc'} },
      sortIcon(key) { if(this.sortKey!==key)return'↕';return this.sortDir==='asc'?'↑':'↓' },
      slaCls(b){return b||'badge-gray'},
      tipoCls(b){return b||'badge-gray'},
      clearFilters(){this.filters={id:'',tipo:'',codigo:'',nombre:'',remitente:'',fecha:''}}
    }))
  },
  template: /* html */`
<div x-data="tareasPage" style="animation:fadeIn 0.35s ease-out both">

  <!-- Header -->
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:8px">
    <div>
      <h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Lista Completa de Tareas Pendientes</h1>
      <p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Flujo documental — todas las asignaciones activas</p>
    </div>
    <div style="display:flex;align-items:center;gap:8px">
      <span class="badge badge-blue" x-text="filtered.length + ' tareas'"></span>
      <button class="btn btn-sm" @click="clearFilters()">✕ Limpiar filtros</button>
      <a href="#/bandeja" class="btn btn-sm">← Bandeja</a>
    </div>
  </div>

  <!-- IA -->
  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px 14px;margin-bottom:16px">
    <div style="font-size:10px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px">✦ IA — Análisis de carga</div>
    <div style="font-size:11.5px;color:#1e3a8a;line-height:1.5">Se detectan <strong>3 tareas vencidas</strong> (SLA > 5 días) y <strong>3 Liberaciones ETO</strong> pendientes. Prioridad: PRO-PRO-019 (7d), POL-GER-003 (8d), PRO-CAL-045 (6d).</div>
  </div>

  <!-- Tabla filtrable -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden">
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:11.5px;min-width:860px">
        <thead>
          <tr style="border-bottom:2px solid #e2e8f0">
            <th @click="sort('id')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:72px">
              <span style="display:flex;align-items:center;gap:4px">ID <span style="opacity:0.5;font-size:9px" x-text="sortIcon('id')"></span></span>
              <input class="th-filter" placeholder="Filtrar…" x-model="filters.id" @click.stop style="margin-top:6px">
            </th>
            <th @click="sort('tipo')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:145px">
              <span style="display:flex;align-items:center;gap:4px">Tarea <span style="opacity:0.5;font-size:9px" x-text="sortIcon('tipo')"></span></span>
              <input class="th-filter" placeholder="Filtrar…" x-model="filters.tipo" @click.stop style="margin-top:6px">
            </th>
            <th @click="sort('codigo')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:110px">
              <span style="display:flex;align-items:center;gap:4px">Código Doc. <span style="opacity:0.5;font-size:9px" x-text="sortIcon('codigo')"></span></span>
              <input class="th-filter" placeholder="Filtrar…" x-model="filters.codigo" @click.stop style="margin-top:6px">
            </th>
            <th @click="sort('nombre')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc">
              <span style="display:flex;align-items:center;gap:4px">Nombre Documento <span style="opacity:0.5;font-size:9px" x-text="sortIcon('nombre')"></span></span>
              <input class="th-filter" placeholder="Filtrar…" x-model="filters.nombre" @click.stop style="margin-top:6px">
            </th>
            <th @click="sort('remitente')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:140px">
              <span style="display:flex;align-items:center;gap:4px">Remitente <span style="opacity:0.5;font-size:9px" x-text="sortIcon('remitente')"></span></span>
              <input class="th-filter" placeholder="Filtrar…" x-model="filters.remitente" @click.stop style="margin-top:6px">
            </th>
            <th @click="sort('fecha')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:100px">
              <span style="display:flex;align-items:center;gap:4px">Fecha <span style="opacity:0.5;font-size:9px" x-text="sortIcon('fecha')"></span></span>
              <input class="th-filter" placeholder="Filtrar…" x-model="filters.fecha" @click.stop style="margin-top:6px">
            </th>
            <th @click="sort('sla')" class="cursor-pointer" style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:80px">
              <span style="display:flex;align-items:center;gap:4px">SLA <span style="opacity:0.5;font-size:9px" x-text="sortIcon('sla')"></span></span>
            </th>
            <th style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;background:#f8fafc;width:80px">Acción</th>
          </tr>
        </thead>
        <tbody>
          <template x-for="t in filtered" :key="t.id">
            <tr style="border-bottom:1px solid #f1f5f9;transition:background 100ms" @mouseenter="$el.style.background='rgba(239,246,255,0.5)'" @mouseleave="$el.style.background=''">
              <td style="padding:9px 12px;font-family:monospace;font-weight:600;color:#64748b;font-size:11px" x-text="t.id"></td>
              <td style="padding:9px 12px"><span class="badge" :class="tipoCls(t.tipoBadge)" x-text="t.tipo"></span></td>
              <td style="padding:9px 12px;font-family:monospace;font-size:11px;color:#1a5fb4" x-text="t.cod"></td>
              <td style="padding:9px 12px;font-size:11.5px" x-text="t.nombre"></td>
              <td style="padding:9px 12px;font-size:11px;color:#64748b" x-text="t.remitente"></td>
              <td style="padding:9px 12px;font-size:11px;color:#64748b" x-text="t.fecha"></td>
              <td style="padding:9px 12px">
                <span class="badge" :class="slaCls(t.slaBadge)" x-text="t.sla"></span>
              </td>
              <td style="padding:9px 12px">
                <a :href="'#'+t.ruta" class="btn btn-primary btn-sm" style="white-space:nowrap">Atender →</a>
              </td>
            </tr>
          </template>
          <tr x-show="filtered.length===0">
            <td colspan="8" style="text-align:center;padding:40px;color:#94a3b8;font-style:italic;font-size:13px">
              No se encontraron tareas con los filtros aplicados.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Footer -->
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;font-size:10.5px;color:#94a3b8">
    <span x-text="'Mostrando ' + filtered.length + ' de ' + items.length + ' tareas'"></span>
    <span>Clic en cabecera para ordenar · Escriba en filtros para buscar</span>
  </div>

</div>`
}
