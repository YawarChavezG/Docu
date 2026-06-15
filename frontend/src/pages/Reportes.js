/**
 * pages/Reportes.js — Reportes dinámicos ETO (US-8.03)
 */
export const page = {
  init() {
    window.Alpine?.data('reportesPage', () => ({
      showChart: false,
    }))
  },
  template: /* html */`
<div x-data="reportesPage" style="animation:fadeIn 0.35s ease-out both">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px">
    <div><h1 style="font-size:15px;font-weight:700;color:#1e293b;margin:0">Reportes</h1><p style="font-size:11px;color:#94a3b8;margin:3px 0 0">Reportes dinámicos del Sistema de Gestión Documental</p></div>
    <div style="display:flex;gap:8px">
      <select class="btn btn-sm" style="background:#fff;border-color:#e2e8f0;padding-right:20px" @change="if($el.value){window.toast('Descargando Reporte_SGD_COFAR_'+new Date().toLocaleDateString('es-BO').replace(/\//g,'')+'.'+(($el.value==='excel')?'xlsx':'pdf'),'info');$el.value=''}">
        <option value="">↓ Exportar reporte</option>
        <option value="excel">Formato Excel (.xlsx)</option>
        <option value="pdf">Formato PDF (.pdf)</option>
      </select>
      <button class="btn btn-primary" @click="showChart=!showChart">📊 Visualizar reporte gráfico</button>
    </div>
  </div>

  <!-- KPIs resumen -->
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px">
    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.04);text-align:center">
      <div style="font-size:26px;font-weight:800;color:#1a5fb4">284</div>
      <div style="font-size:10.5px;color:#64748b;font-weight:600;margin-top:4px">Total Procesos</div>
    </div>
    <div style="background:#fff;border:1px solid #a7f3d0;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.04);text-align:center">
      <div style="font-size:26px;font-weight:800;color:#059669">142</div>
      <div style="font-size:10.5px;color:#059669;font-weight:600;margin-top:4px">Concluidos</div>
    </div>
    <div style="background:#fff;border:1px solid #fde68a;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.04);text-align:center">
      <div style="font-size:26px;font-weight:800;color:#d97706">114</div>
      <div style="font-size:10.5px;color:#d97706;font-weight:600;margin-top:4px">En Ejecución</div>
    </div>
    <div style="background:#fff;border:1px solid #fecaca;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.04);text-align:center">
      <div style="font-size:26px;font-weight:800;color:#dc2626">28</div>
      <div style="font-size:10.5px;color:#dc2626;font-weight:600;margin-top:4px">Eliminados</div>
    </div>
  </div>

  <!-- Gráfica -->
  <div x-show="showChart" style="display:none;background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
    <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:20px">📊 Reporte Gráfico Interactivo</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
      <div>
        <div style="font-size:11.5px;font-weight:600;color:#475569;margin-bottom:14px">Documentos por Estado del Proceso</div>
        ${[
          {label:'Concluido',pct:50,color:'#059669'},
          {label:'En ejecución',pct:40,color:'#d97706'},
          {label:'Eliminado',pct:10,color:'#dc2626'},
        ].map(b=>`
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;cursor:pointer" onclick="window.toast('Detalle: ${b.label} — ${b.pct}% (${Math.round(b.pct*284/100)} procesos)','info')">
          <span style="width:105px;font-size:11px;color:#475569;flex-shrink:0">${b.label}</span>
          <div style="flex:1;height:18px;background:#f1f5f9;border-radius:9999px;overflow:hidden;position:relative">
            <div style="width:${b.pct}%;height:100%;background:${b.color};border-radius:9999px;transition:width 600ms;display:flex;align-items:center;justify-content:flex-end;padding-right:6px">
              <span style="font-size:10px;font-weight:700;color:#fff;white-space:nowrap">${b.pct}%</span>
            </div>
          </div>
          <span style="width:30px;font-size:11px;color:#64748b">${Math.round(b.pct*2.84)}</span>
        </div>`).join('')}
      </div>
      <div>
        <div style="font-size:11.5px;font-weight:600;color:#475569;margin-bottom:14px">Documentos por Área (Top 4)</div>
        ${[
          {label:'Control de Calidad',pct:65,color:'#1a5fb4',n:185},
          {label:'Producción',pct:20,color:'#7c3aed',n:57},
          {label:'Logística',pct:10,color:'#059669',n:28},
          {label:'Mantenimiento',pct:5,color:'#d97706',n:14},
        ].map(b=>`
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;cursor:pointer" onclick="window.toast('Detalle área ${b.label}: ${b.n} documentos','info')">
          <span style="width:130px;font-size:11px;color:#475569;flex-shrink:0">${b.label}</span>
          <div style="flex:1;height:18px;background:#f1f5f9;border-radius:9999px;overflow:hidden">
            <div style="width:${b.pct}%;height:100%;background:${b.color};border-radius:9999px;transition:width 600ms;display:flex;align-items:center;justify-content:flex-end;padding-right:6px">
              <span style="font-size:10px;font-weight:700;color:#fff;white-space:nowrap">${b.pct}%</span>
            </div>
          </div>
          <span style="width:30px;font-size:11px;color:#64748b">${b.n}</span>
        </div>`).join('')}
      </div>
    </div>
    <div style="margin-top:16px;padding:10px 14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;font-size:11px;color:#166534">
      💡 <strong>Interactivo:</strong> Haga clic en cualquier barra para ver el detalle de ese grupo.
    </div>
  </div>

  <!-- Tabla datos -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05);overflow:hidden">
    <div style="padding:12px 16px;border-bottom:1px solid #f1f5f9;font-size:10.5px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.07em">Datos del período actual</div>
    <div style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:11.5px">
        <thead><tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0">
          <th style="padding:10px 12px;text-align:left;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Área</th>
          <th style="padding:10px 12px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Total docs.</th>
          <th style="padding:10px 12px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Concluidos</th>
          <th style="padding:10px 12px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">En ejecución</th>
          <th style="padding:10px 12px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Eliminados</th>
          <th style="padding:10px 12px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">T. prom. revisión (hrs)</th>
          <th style="padding:10px 12px;text-align:center;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em">Devoluciones</th>
        </tr></thead>
        <tbody>
          ${[['Control de Calidad',185,97,78,10,48,23],['Producción',57,30,22,5,36,8],['Logística',28,11,12,5,52,6],['Mantenimiento',14,4,8,2,60,3],['RRHH',0,'—','—','—','—','—']].map(([a,...v])=>`
          <tr style="border-bottom:1px solid #f1f5f9;transition:background 100ms" onmouseenter="this.style.background='rgba(239,246,255,0.4)'" onmouseleave="this.style.background=''">
            <td style="padding:10px 12px;font-size:11.5px;font-weight:500">${a}</td>
            ${v.map(x=>`<td style="padding:10px 12px;text-align:center;font-size:11px;color:#64748b">${x}</td>`).join('')}
          </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>
</div>`
}
