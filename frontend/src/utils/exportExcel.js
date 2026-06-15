/**
 * src/utils/exportExcel.js
 * Utilidad para exportar los procesos y su historial a Excel (.xlsx)
 */
import * as XLSX from 'xlsx'

/**
 * Genera y descarga un archivo Excel con dos hojas:
 * 1. Resumen de Procesos
 * 2. Historial Detallado
 * @param {Array} procesos - Lista de procesos filtrados (de documents.js)
 */
function exportarProcesosExcel(procesos) {
  if (!procesos || procesos.length === 0) {
    window.toast?.('No hay procesos para exportar.', 'warn')
    return
  }

  // ─── Hoja 1: Resumen ──────────────────────────────────────────────────────
  const resumen = procesos.map(p => ({
    'Nro Proceso': p.id,
    'Usuario Creador': p.user,
    'Área': p.area,
    'Código': p.cod,
    'Versión': p.ver || '—',
    'Fecha Solicitud': p.f_sol,
    'Fecha Liberación': p.f_lib,
    'Fecha Revisión': p.f_rev,
    'Fecha Aprobación': p.f_apr,
    'Etapa Actual': p.etapa,
    'Responsable': p.resp,
    'Estado': p.est,
  }))

  // ─── Hoja 2: Historial Detallado ──────────────────────────────────────────
  const historial = []
  procesos.forEach(p => {
    if (Array.isArray(p.log)) {
      p.log.forEach(l => {
        historial.push({
          'Nro Proceso': p.id,
          'Código': p.cod,
          'Etapa del Historial': l.etapa,
          'Responsable del Nodo': l.user,
          'Acción': l.acc,
          'Fecha': l.fecha,
          'Hora': l.hora,
          'Observación': l.obs && l.obs !== '-' ? l.obs : '',
        })
      })
    }
  })

  // ─── Construir libro ──────────────────────────────────────────────────────
  const wb = XLSX.utils.book_new()

  const wsResumen = XLSX.utils.json_to_sheet(resumen)
  const wsHistorial = XLSX.utils.json_to_sheet(historial)

  // Ajustar anchos de columna (aproximado) para mejor lectura
  wsResumen['!cols'] = [
    { wch: 12 }, { wch: 18 }, { wch: 22 }, { wch: 14 },
    { wch: 10 }, { wch: 16 }, { wch: 16 }, { wch: 16 },
    { wch: 16 }, { wch: 18 }, { wch: 22 }, { wch: 14 },
  ]
  wsHistorial['!cols'] = [
    { wch: 12 }, { wch: 14 }, { wch: 22 }, { wch: 22 },
    { wch: 14 }, { wch: 12 }, { wch: 10 }, { wch: 45 },
  ]

  XLSX.utils.book_append_sheet(wb, wsResumen, 'Resumen de Procesos')
  XLSX.utils.book_append_sheet(wb, wsHistorial, 'Historial Detallado')

  // ─── Descarga ─────────────────────────────────────────────────────────────
  const fecha = new Date().toLocaleDateString('es-BO').replace(/\//g, '-')
  XLSX.writeFile(wb, `Reporte_Procesos_${fecha}.xlsx`)

  window.toast?.('Reporte Excel generado correctamente.', 'success')
}

// Exponer globalmente para que Alpine.js pueda invocarlo desde templates inline
window.exportarProcesosExcel = exportarProcesosExcel

export { exportarProcesosExcel }
