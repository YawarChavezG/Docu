/**
 * src/data/tasks.js
 * Extraído 1:1 de Mi Bandeja y Lista Completa de Tareas del HTML original
 */

// ─── Tareas Pendientes (Flujo) — Mini tabla en Bandeja ───────────────────────
export const tareasBandejaDB = [
  {
    id: '243', tipo: 'Corregir Observaciones', tipoBadge: 'badge-amber',
    cod: 'PRO-CAL-045', nombre: 'Procedimiento de Muestreo',
    remitente: 'Aracely Romero (ETO)', fecha: '10/01/2026',
    sla: '🔴 6 días', slaBadge: 'badge-red',
    ruta: '/correccion',
  },
  {
    id: '244', tipo: 'Revisar Documento', tipoBadge: 'badge-blue',
    cod: 'INS-PRO-012', nombre: 'Instructivo de Limpieza',
    remitente: 'Carlos Flores', fecha: '14/01/2026',
    sla: '🟡 2 días', slaBadge: 'badge-amber',
    ruta: '/revision',
  },
  {
    id: '245', tipo: 'Aprobar Documento', tipoBadge: 'badge-gray',
    cod: 'MAN-LOG-003', nombre: 'Manual de Logística',
    remitente: 'Lucía Castro', fecha: '15/01/2026 (Hoy)',
    sla: '🟢 0 días', slaBadge: 'badge-green',
    ruta: '/aprobacion-final',
  },
]

// ─── Tareas Completas (Lista Completa de Tareas Pendientes) ──────────────────
export const tareasCompletasDB = [
  { id: '243', tipo: 'Corregir Observaciones', tipoBadge: 'badge-amber', cod: 'PRO-CAL-045', nombre: 'Procedimiento de Muestreo',      remitente: 'Aracely Romero (ETO)', fecha: '10/01/2026', sla: '🔴 6 días', slaBadge: 'badge-red',   ruta: '/correccion'         },
  { id: '244', tipo: 'Revisar Documento',       tipoBadge: 'badge-blue',  cod: 'INS-PRO-012', nombre: 'Instructivo de Limpieza',        remitente: 'Carlos Flores',        fecha: '14/01/2026', sla: '🟡 2 días', slaBadge: 'badge-amber', ruta: '/revision'           },
  { id: '245', tipo: 'Aprobar Documento',       tipoBadge: 'badge-gray',  cod: 'MAN-LOG-003', nombre: 'Manual de Logística',            remitente: 'Lucía Castro',         fecha: '15/01/2026', sla: '🟢 0 días', slaBadge: 'badge-green', ruta: '/aprobacion-final'           },
  { id: '246', tipo: 'Liberación ETO',          tipoBadge: 'badge-amber', cod: 'MET-CAL-002', nombre: 'Metodología HPLC v3',            remitente: 'Juan Perez',           fecha: '13/01/2026', sla: '🟡 3 días', slaBadge: 'badge-amber', ruta: '/liberacion-detalle' },
  { id: '247', tipo: 'Liberación ETO',          tipoBadge: 'badge-amber', cod: 'PRO-LOG-018', nombre: 'Procedimiento de Despacho',      remitente: 'Carlos Flores',        fecha: '12/01/2026', sla: '🔴 4 días', slaBadge: 'badge-red',   ruta: '/liberacion-detalle' },
  { id: '248', tipo: 'Revisar Documento',       tipoBadge: 'badge-blue',  cod: 'FOR-RRHH-008',nombre: 'Formulario de Vacaciones',       remitente: 'María Condori',        fecha: '16/01/2026', sla: '🟢 0 días', slaBadge: 'badge-green', ruta: '/revision'           },
  { id: '249', tipo: 'Aprobar Documento',       tipoBadge: 'badge-gray',  cod: 'INS-CAL-003', nombre: 'Instructivo de Calibración',     remitente: 'Jasiel Sanjinés',      fecha: '11/01/2026', sla: '🟡 5 días', slaBadge: 'badge-amber', ruta: '/aprobacion-final'           },
  { id: '250', tipo: 'Corregir Observaciones', tipoBadge: 'badge-amber', cod: 'PRO-PRO-019', nombre: 'Procedimiento de Empaque',        remitente: 'Aracely Romero (ETO)', fecha: '09/01/2026', sla: '🔴 7 días', slaBadge: 'badge-red',   ruta: '/correccion'         },
  { id: '251', tipo: 'Revisar Documento',       tipoBadge: 'badge-blue',  cod: 'MAN-CAL-001', nombre: 'Manual de Calidad General',      remitente: 'Lucía Terán',          fecha: '15/01/2026', sla: '🟢 1 día',  slaBadge: 'badge-green', ruta: '/revision'           },
  { id: '252', tipo: 'Liberación ETO',          tipoBadge: 'badge-amber', cod: 'FOR-PRO-022', nombre: 'Registro de Temperatura',        remitente: 'Luis Mamani',          fecha: '16/01/2026', sla: '🟢 0 días', slaBadge: 'badge-green', ruta: '/liberacion-detalle' },
  { id: '253', tipo: 'Aprobar Documento',       tipoBadge: 'badge-gray',  cod: 'POL-GER-003', nombre: 'Política de Seguridad Interna',  remitente: 'Aracely Romero (ETO)', fecha: '08/01/2026', sla: '🔴 8 días', slaBadge: 'badge-red',   ruta: '/aprobacion-final'           },
  { id: '254', tipo: 'Revisar Documento',       tipoBadge: 'badge-blue',  cod: 'INS-LOG-005', nombre: 'Instructivo de Despacho Urgente',remitente: 'Carlos Flores',        fecha: '14/01/2026', sla: '🟡 2 días', slaBadge: 'badge-amber', ruta: '/revision'           },
]

// ─── Evaluaciones Pendientes (bandeja) ────────────────────────────────────────
export const evaluacionesPendientesDB = [
  {
    tipo: 'Evaluación de conocimiento', cod: 'PRO-RRHH-001', nombre: 'Política de Asistencia',
    fechaInicio: '11/01/2026', fechaLimite: '🔴 Hoy (15/01/2026)', urgente: true, ruta: '/pre-eval',
    btnLabel: 'Iniciar Examen', btnClass: 'btn-primary',
  },
  {
    tipo: 'Evaluación de actualización', cod: 'MET-CAL-005', nombre: 'Metodología HPLC',
    fechaInicio: '11/01/2026', fechaLimite: '🟡 17/01/2026', urgente: false, ruta: '/pre-eval',
    btnLabel: 'Iniciar Examen', btnClass: '',
  },
]

// ─── Controles de Lectura (bandeja) ───────────────────────────────────────────
export const controlesLecturaDB = [
  {
    tipo: 'Confirmar Lectura', cod: 'POL-GER-002', nombre: 'Política de Seguridad M.A.',
    fechaInicio: '10/01/2026', fechaFin: '10/02/2026', ruta: '/tomar-lectura', btnLabel: 'Leer y Confirmar',
  },
]

// ─── Recepción de Copias Físicas (bandeja usuario) ────────────────────────────
export const recepcionCopiasDB = [
  { tipo: 'Copia Controlada',    tipoBadge: 'badge-green', cod: 'CC-MET-287',   ver: '01', nombre: 'Alibrom solución oftálmica',         numCopia: 1, prioridad: false },
  { tipo: 'Copia No Controlada', tipoBadge: 'badge-amber', cod: 'MAN-RRHH-001', ver: '05', nombre: 'Manual de Bienvenida',               numCopia: 3, prioridad: false },
  { tipo: 'Copia Controlada',    tipoBadge: 'badge-green', cod: 'PRO-PRO-012',  ver: '03', nombre: 'Limpieza de Tanque Agitador',         numCopia: 2, prioridad: false },
  { tipo: 'Copia Controlada',    tipoBadge: 'badge-green', cod: 'INS-LOG-005',  ver: '02', nombre: 'Ingreso de Materia Prima (Prioridad Alta)', numCopia: 5, prioridad: true },
  { tipo: 'Copia No Controlada', tipoBadge: 'badge-amber', cod: 'FOR-PRO-022',  ver: '01', nombre: 'Registro de Temperatura',             numCopia: 1, prioridad: false },
]

// ─── Tareas de Liberación ETO (Bandeja Liberación / pages/Liberacion.js) ─────
export const tareasLiberacionDB = [
  {
    id: '246', tipo: 'Liberación ETO', cod: 'MET-CAL-002',
    nombre: 'Metodología de Análisis de Causa Raíz',
    remitente: 'Juan Perez', fecha: '12/01/2026',
    sla: 3, slaBadge: 'badge-amber', slaLabel: '🟡 3 días',
  },
  {
    id: '247', tipo: 'Liberación ETO', cod: 'PRO-LOG-018',
    nombre: 'Procedimiento de Recepción de Insumos',
    remitente: 'Carlos Flores', fecha: '14/01/2026',
    sla: 1, slaBadge: 'badge-green', slaLabel: '🟢 1 día',
  },
  {
    id: '248', tipo: 'Liberación ETO', cod: 'FOR-RRHH-008',
    nombre: 'Formulario de Vacaciones',
    remitente: 'María Condori', fecha: '16/01/2026',
    sla: 0, slaBadge: 'badge-green', slaLabel: '🟢 Hoy',
  },
]
