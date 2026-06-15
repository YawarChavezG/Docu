/**
 * src/data/iaRespuestas.js
 * Extraído de Chat.js — respuestas del asistente IA
 */

export const iaRespuestasDB = {
  vencer: {
    msg: 'Revisando la base de datos... He detectado <strong>3 documentos</strong> próximos a vencer en los próximos 30 días:<br><br>• <strong style="color:#1a5fb4">MET-CAL-480</strong> — Control de Desviaciones — Vence: 12/04/2026<br>• <strong style="color:#1a5fb4">PRO-RRHH-001</strong> — Política de Asistencia — Vence: 20/04/2026<br>• <strong style="color:#d97706">MAN-LOG-003</strong> — Manual de Logística — Vence: 05/05/2026',
    btns: ['Ver en Lista Maestra','Generar Reporte en Excel']
  },
  pendientes: {
    msg: 'Revisando los flujos en ejecución... He detectado <strong>3 documentos</strong> que llevan más de 3 meses en la etapa de "Revisión":<br><br>• <strong style="color:#1a5fb4">LOG-3-001</strong> — El mayor cuello de botella. Asignado a la Jefatura de Logística.<br>• <strong style="color:#1a5fb4">PRO-2-115</strong> — En revisión paralela desde 18/01/2026.',
    btns: ['Generar Reporte de Retrasos en Excel','Reasignar automáticamente']
  },
  obsoletos: {
    msg: 'En la Lista Maestra existen actualmente <strong>147 documentos</strong> en estado Obsoleto. Los 3 más recientes son:<br><br>• <strong style="color:#94a3b8">CC-MET-286</strong> — Reemplazado por CC-MET-287 (22/04/2026)<br>• <strong style="color:#94a3b8">PRO-PRO-011</strong> — Reemplazado por PRO-PRO-812<br>• <strong style="color:#94a3b8">MET-CAL-001</strong> — Declarado obsoleto manualmente por ETO',
    btns: ['Exportar lista de obsoletos']
  },
}

export function obtenerRespuestaIA(txt) {
  const q = txt.toLowerCase()
  if (q.includes('vencer') || q.includes('expir')) return iaRespuestasDB.vencer
  if (q.includes('pendiente') || q.includes('estancado') || q.includes('atrasado')) return iaRespuestasDB.pendientes
  if (q.includes('obsoleto')) return iaRespuestasDB.obsoletos
  return {
    msg: `Entendido. Consultando la base de datos con tu búsqueda: "<em>${txt}</em>"...<br><br>Por ahora no encontré resultados exactos. Intenta preguntar sobre:<br>• "documentos próximos a vencer"<br>• "procesos pendientes hace más de 3 meses"<br>• "documentos obsoletos"`,
    btns: []
  }
}
