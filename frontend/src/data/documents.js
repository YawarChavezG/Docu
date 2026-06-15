/**
 * src/data/documents.js
 * Datos extraídos 1:1 del HTML original (SistemaGestionDocumental-29-4-2026-v2.html)
 * Contiene: Lista Maestra, Consultar Documentos, Monitor CC, Monitor CN, Biblioteca
 */

// ─── Lista Maestra ────────────────────────────────────────────────────────────
export const listaMaestraDB = [
  { id: '1',  ger: 'CALIDAD',    area: 'Control Calidad',  proc: 'Análisis',    tipo: 'Metodología',  cod: 'CC-MET-287',   ver: '01', tit: 'Alibrom solución oftálmica',           f_ap: '28/03/24', f_ex: '28/03/28', vig: 'Vigente',   est: 'Aprobado', ant: 'CC-MET-286', com: '-', forms: ['F01','F02'] },
  { id: '2',  ger: 'PRODUCCIÓN', area: 'Planta Líquidos',  proc: 'Fabricación', tipo: 'Procedimiento', cod: 'PRO-PRO-012',  ver: '03', tit: 'Limpieza de Tanque Agitador',          f_ap: '10/01/25', f_ex: '10/01/29', vig: 'Vigente',   est: 'Aprobado', ant: 'PRO-PRO-011', com: '-', forms: ['F01'] },
  { id: '3',  ger: 'LOGÍSTICA',  area: 'Almacenes',        proc: 'Recepción',   tipo: 'Instructivo',  cod: 'INS-LOG-005',  ver: '02', tit: 'Ingreso de Materia Prima',              f_ap: '05/02/26', f_ex: '05/02/30', vig: 'Vigente',   est: 'Aprobado', ant: 'N/A',        com: '-', forms: ['F01','F02','F03'] },
  { id: '4',  ger: 'RRHH',       area: 'Administración',   proc: 'Inducción',   tipo: 'Manual',       cod: 'MAN-RRHH-001', ver: '05', tit: 'Manual de Bienvenida',                  f_ap: '20/11/23', f_ex: '20/11/27', vig: 'Vigente',   est: 'Aprobado', ant: 'N/A',        com: '-', forms: [] },
  { id: '5',  ger: 'CALIDAD',    area: 'Aseguramiento',    proc: 'SIG',         tipo: 'Metodología',  cod: 'MET-CAL-002',  ver: '02', tit: 'Control de Desviaciones',               f_ap: '12/03/20', f_ex: '12/03/24', vig: 'Vencido',   est: 'Aprobado', ant: 'MET-CAL-001', com: '-', forms: ['F01'] },
  { id: '6',  ger: 'PRODUCCIÓN', area: 'Planta Sólidos',   proc: 'Empaque',     tipo: 'Formulario',   cod: 'FOR-PRO-022',  ver: '01', tit: 'Registro de Temperatura',               f_ap: '15/04/26', f_ex: '15/04/30', vig: 'Vigente',   est: 'Aprobado', ant: 'N/A',        com: '-', forms: [] },
  { id: '7',  ger: 'GERENCIA',   area: 'Auditoria',        proc: 'Control',     tipo: 'Procedimiento', cod: 'PRO-LOG-018', ver: '04', tit: 'Auditoria de Inventarios',              f_ap: '10/05/25', f_ex: '10/05/29', vig: 'Vigente',   est: 'Aprobado', ant: 'PRO-LOG-017', com: '-', forms: ['F01'] },
  // Extras de densidad para ETO
  { id: '8',  ger: 'CALIDAD',    area: 'Control Calidad',  proc: 'Validación',  tipo: 'Procedimiento', cod: 'PRO-CAL-045', ver: '05', tit: 'Procedimiento de Muestreo de Control de Calidad', f_ap: '01/01/26', f_ex: '01/01/27', vig: 'Por vencer', est: 'En revisión', ant: 'N/A', com: 'En proceso de actualización', forms: [] },
  { id: '9',  ger: 'RRHH',       area: 'Administración',   proc: 'SSOO',        tipo: 'Procedimiento', cod: 'PRO-RRHH-001',ver: '06', tit: 'Política de Asistencia',                f_ap: '16/04/26', f_ex: '16/04/30', vig: 'Vigente',   est: 'Aprobado', ant: 'N/A',        com: '-', forms: [] },
  { id: '10', ger: 'CALIDAD',    area: 'Aseguramiento',    proc: 'Análisis',    tipo: 'Metodología',  cod: 'MET-CAL-005',  ver: '02', tit: 'Metodología de Análisis HPLC',          f_ap: '01/07/25', f_ex: '01/07/29', vig: 'Vigente',   est: 'Aprobado', ant: 'N/A',        com: '-', forms: [] },
  { id: '11', ger: 'PRODUCCIÓN', area: 'Planta Líquidos',  proc: 'Limpieza',    tipo: 'Instructivo',  cod: 'INS-PRO-012',  ver: '03', tit: 'Instructivo de Limpieza de Manufactura', f_ap: '12/08/25', f_ex: '12/08/29', vig: 'Vigente',   est: 'Aprobado', ant: 'N/A',        com: '-', forms: [] },
  { id: '12', ger: 'LOGÍSTICA',  area: 'Almacenes',        proc: 'Distribución', tipo: 'Manual',      cod: 'MAN-LOG-003',  ver: '01', tit: 'Manual de Logística y Distribución',    f_ap: '05/10/25', f_ex: '05/10/29', vig: 'Vigente',   est: 'En liberación', ant: 'N/A', com: 'Pendiente de firma', forms: ['F01'] },
  { id: '13', ger: 'GERENCIA',   area: 'Gestión Doc.',     proc: 'SGD',         tipo: 'Procedimiento', cod: 'PRO-GER-001', ver: '02', tit: 'Procedimiento de Gestión del Sistema Documental', f_ap: '15/01/26', f_ex: '15/01/30', vig: 'Vigente', est: 'En corrección', ant: 'N/A', com: 'Observaciones de revisor 2', forms: [] },
  // Obsoletos (solo visibles para ETO)
  { id: '14', ger: 'CALIDAD',    area: 'Control Calidad',  proc: 'Análisis',    tipo: 'Metodología',  cod: 'CC-MET-286',   ver: '01', tit: 'Alibrom solución oftálmica (versión anterior)', f_ap: '20/03/20', f_ex: '20/03/24', vig: 'Obsoleto', est: 'Obsoleto', ant: 'N/A', com: 'Reemplazado por CC-MET-287', obsoleto: true, forms: [] },
  { id: '15', ger: 'PRODUCCIÓN', area: 'Planta Líquidos',  proc: 'Fabricación', tipo: 'Procedimiento', cod: 'PRO-PRO-011', ver: '02', tit: 'Limpieza de Tanques v2',                f_ap: '05/01/20', f_ex: '05/01/24', vig: 'Obsoleto', est: 'Obsoleto', ant: 'N/A', com: 'Reemplazado por PRO-PRO-012', obsoleto: true, forms: [] },
  { id: '16', ger: 'CALIDAD',    area: 'Aseguramiento',    proc: 'SIG',         tipo: 'Metodología',  cod: 'MET-CAL-001',  ver: '01', tit: 'Control de Desviaciones v1',            f_ap: '01/03/18', f_ex: '01/03/22', vig: 'Obsoleto', est: 'Obsoleto', ant: 'N/A', com: 'Reemplazado por MET-CAL-002', obsoleto: true, forms: [] },
]

// ─── Consultar Documentos (Procesos con Timeline) ────────────────────────────
export const procesosConsultaDB = [
  {
    id: '2186', user: 'gchambi', area: 'CONTROL DE CALIDAD', cod: 'CC-1-692', ver: 'v2.1',
    f_sol: '15/09/25', f_lib: '17/09/25', f_rev: '26/09/25', f_apr: '10/10/25',
    etapa: 'Finalizado', resp: 'Sistema', est: 'Concluido',
    log: [
      { etapa: 'Solicitud',       user: 'gchambi',  acc: 'Creado',        fecha: '15/09/25', hora: '08:30', obs: '-' },
      { etapa: 'Liberación ETO',  user: 'aromero',  acc: 'Liberado',      fecha: '17/09/25', hora: '10:00', obs: 'Documento cumple con los formatos estándar.' },
      { etapa: 'Revisión (R1)',   user: 'jsanjines',acc: 'Aprobado',      fecha: '22/09/25', hora: '11:00', obs: '-' },
      { etapa: 'Aprobación (A1)', user: 'vvillegas',acc: 'Aprobado Final',fecha: '10/10/25', hora: '15:45', obs: '-' },
    ]
  },
  {
    id: '1943', user: 'faguilar', area: 'CONTROL DE CALIDAD', cod: 'CC-1-1020', ver: 'v1.0',
    f_sol: '14/04/26', f_lib: '—', f_rev: '—', f_apr: '—',
    etapa: 'Liberación ETO', resp: 'aromero', est: 'En ejecución',
    log: [
      { etapa: 'Solicitud',      user: 'faguilar', acc: 'Creado',   fecha: '14/04/26', hora: '10:45', obs: 'Nueva solicitud de manual.' },
      { etapa: 'Liberación ETO', user: 'aromero',  acc: 'Pendiente',fecha: '14/04/26', hora: '10:46', obs: 'Tarea pendiente de auditoría de Calidad.' },
    ]
  },
  {
    id: '3045', user: 'mrodriguez', area: 'PRODUCCIÓN', cod: 'PRO-2-115', ver: 'v3.2',
    f_sol: '18/04/26', f_lib: '19/04/26', f_rev: '—', f_apr: '—',
    etapa: 'Revisión Paralela', resp: 'jsanjines, faguilar, lteran', est: 'En ejecución',
    log: [
      { etapa: 'Solicitud',      user: 'mrodriguez', acc: 'Creado',   fecha: '18/04/26', hora: '09:00', obs: 'Actualización de procedimiento.' },
      { etapa: 'Liberación ETO', user: 'aromero',    acc: 'Liberado', fecha: '19/04/26', hora: '11:30', obs: 'Enviado a revisión técnica.' },
      { etapa: 'Revisión (R1)',  user: 'jsanjines',  acc: 'Pendiente',fecha: '19/04/26', hora: '11:31', obs: 'Esperando visto bueno técnico.' },
      { etapa: 'Revisión (R2)',  user: 'faguilar',   acc: 'Pendiente',fecha: '19/04/26', hora: '11:31', obs: 'Esperando visto bueno de planta.' },
      { etapa: 'Revisión (R3)',  user: 'lteran',     acc: 'Pendiente',fecha: '19/04/26', hora: '11:31', obs: 'Esperando validación de seguridad.' },
    ]
  },
  {
    id: '2391', user: 'cparedes', area: 'LOGISTICA', cod: 'LOG-3-001', ver: 'v1.0',
    f_sol: '15/10/25', f_lib: '17/10/25', f_rev: '—', f_apr: '—',
    etapa: 'Anulado', resp: 'cparedes', est: 'Eliminado',
    log: [
      { etapa: 'Solicitud',  user: 'cparedes', acc: 'Creado',   fecha: '15/10/25', hora: '16:00', obs: '-' },
      { etapa: 'Eliminación',user: 'cparedes', acc: 'Eliminado',fecha: '18/10/25', hora: '09:00', obs: 'Se anula proceso por error de matriz.' },
    ]
  },
]

// ─── Monitor Copias Controladas ───────────────────────────────────────────────
export const copiasCCDB = [
  { id: '1', cod: 'CC-MET-287',   ver: '01', doc: 'Alibrom solución oftálmica',       fe: '15/04/26 10:30', fd: '—',              orig: 'A. Romero', dest: 'Juan Perez',      est: 'Generado'  },
  { id: '2', cod: 'CC-MET-287',   ver: '01', doc: 'Alibrom solución oftálmica',       fe: '14/04/26 09:15', fd: '—',              orig: 'A. Romero', dest: 'Maria Gomez',     est: 'Entregado' },
  { id: '1', cod: 'PRO-PRO-012',  ver: '03', doc: 'Limpieza de Tanque',               fe: '10/04/26 14:00', fd: '12/04/26 16:30', orig: 'A. Romero', dest: 'Luis Lopez',      est: 'Devuelto'  },
  { id: '1', cod: 'INS-LOG-005',  ver: '02', doc: 'Ingreso de Materia Prima',         fe: '16/04/26 08:00', fd: '—',              orig: 'A. Romero', dest: 'Ana Torroja',     est: 'Generado'  },
]

// ─── Monitor Copias No Controladas ───────────────────────────────────────────
export const copiasCNDB = [
  { id: '1', cod: 'MAN-RRHH-001', ver: '05', doc: 'Manual de Bienvenida',     fe: '16/04/26 09:00', orig: 'A. Romero', dest: 'Nuevo Empleado',      est: 'Entregado' },
  { id: '2', cod: 'MAN-RRHH-001', ver: '05', doc: 'Manual de Bienvenida',     fe: '16/04/26 09:15', orig: 'A. Romero', dest: 'Nuevo Empleado 2',    est: 'Generado'  },
  { id: '1', cod: 'FOR-PRO-022',  ver: '01', doc: 'Registro de Temperatura',  fe: '12/04/26 11:00', orig: 'A. Romero', dest: 'Supervisor Planta',   est: 'Entregado' },
]

// ─── Biblioteca Virtual ───────────────────────────────────────────────────────
export const bibliotecaDB = [
  { id: 1,  cod: 'PRO-CAL-045',  titulo: 'Procedimiento de Muestreo de Materia Prima',      area: 'Calidad',    tipo: 'PRO', icono: '📄', fav: true,  fecha: '10/01/26', rev: 'v03' },
  { id: 2,  cod: 'FOR-PRO-012',  titulo: 'Registro de Limpieza de Equipos Nivel 2',          area: 'Producción', tipo: 'FOR', icono: '📊', fav: true,  fecha: '15/12/25', rev: 'v05' },
  { id: 3,  cod: 'INS-LOG-004',  titulo: 'Instructivo de Despacho de Producto Terminado',    area: 'Logística',  tipo: 'INS', icono: '📄', fav: false, fecha: '02/02/26', rev: 'v01' },
  { id: 4,  cod: 'MAN-RRHH-001', titulo: 'Manual de Funciones y Perfiles de Cargo',          area: 'RRHH',       tipo: 'MAN', icono: '📕', fav: true,  fecha: '20/11/25', rev: 'v08' },
  { id: 5,  cod: 'MET-CAL-002',  titulo: 'Metodología de Análisis de Causa Raíz',            area: 'Calidad',    tipo: 'MET', icono: '📄', fav: false, fecha: '12/01/26', rev: 'v02' },
  { id: 6,  cod: 'PRO-PRO-018',  titulo: 'Procedimiento de Despeje de Línea',                area: 'Producción', tipo: 'PRO', icono: '📄', fav: false, fecha: '18/02/26', rev: 'v02' },
  { id: 7,  cod: 'FOR-CAL-088',  titulo: 'Matriz de Capacitación Anual',                     area: 'Calidad',    tipo: 'FOR', icono: '📊', fav: false, fecha: '08/02/26', rev: 'v06' },
  { id: 8,  cod: 'POL-GER-001',  titulo: 'Política de Calidad Institucional',                area: 'Gerencia',   tipo: 'POL', icono: '📘', fav: true,  fecha: '01/01/26', rev: 'v01' },
  { id: 9,  cod: 'INS-CAL-010',  titulo: 'Uso de Balanzas Analíticas',                       area: 'Calidad',    tipo: 'INS', icono: '📄', fav: false, fecha: '10/03/26', rev: 'v04' },
  { id: 10, cod: 'FOR-LOG-005',  titulo: 'Control de Inventario Cíclico',                    area: 'Logística',  tipo: 'FOR', icono: '📊', fav: false, fecha: '22/03/26', rev: 'v02' },
]

// ─── Tipos de Documento (array simple, página LiberacionDetalle.js) ──────────
export const tiposDocumentoList = [
  'Procedimiento','Instructivo','Formulario','Metodología','Manual','Política'
]

// ─── Publicaciones / Monitor de Evaluaciones (página Publicacion.js) ─────────
export const publicacionesDB = [
  {codigo:'PRO-CAL-045',nombre:'Procedimiento de Muestreo',fechaLanz:'01/02/26',plazo:'17/01/26',tipo:'Evaluación',estado:'Pendiente',alcance:'23/35',prom:'62%',btnEnabled:true},
  {codigo:'FOR-RRHH-020',nombre:'Formulario de Inducción',fechaLanz:'10/03/26',plazo:'20/03/26',tipo:'Control Lectura',estado:'Pendiente',alcance:'5/100',prom:'N/A',btnEnabled:false},
  {codigo:'MAN-LOG-003',nombre:'Manual de Logística',fechaLanz:'15/01/24',plazo:'15/02/24',tipo:'Control Lectura',estado:'Finalizado',alcance:'40/40',prom:'N/A',btnEnabled:true},
  {codigo:'POL-GER-001',nombre:'Política General de Calidad',fechaLanz:'01/01/25',plazo:'31/01/25',tipo:'Evaluación',estado:'Finalizado',alcance:'200/200',prom:'92%',btnEnabled:true},
  {codigo:'INS-PRO-012',nombre:'Instructivo de Limpieza',fechaLanz:'—',plazo:'N/A',tipo:'Sin Control',estado:'Finalizado',alcance:'N/A',prom:'N/A',btnEnabled:false},
  {codigo:'MET-CAL-480',nombre:'Control de Desviaciones',fechaLanz:'06/04/26',plazo:'06/04/26',tipo:'Evaluación',estado:'Cancelado',alcance:'0/15',prom:'—',btnEnabled:false},
  {codigo:'FOR-PRO-022',nombre:'Registro de Temperatura',fechaLanz:'06/04/26',plazo:'06/04/26',tipo:'Control Lectura',estado:'Cancelado',alcance:'0/10',prom:'N/A',btnEnabled:false},
]

// ─── Configuración de colores del timeline ─────────────────────────────────
export const TIMELINE_CONFIG = {
  Creado:        { cls: 'icon-blue',  icon: 'S', color: '#3b82f6',  msgClass: 'msg-blue',  title: 'Mensaje adjunto:' },
  Corregido:     { cls: 'icon-blue',  icon: 'C', color: '#3b82f6',  msgClass: 'msg-blue',  title: 'Mensaje adjunto:' },
  Liberado:      { cls: 'icon-green', icon: 'E', color: '#10b981',  msgClass: 'msg-green', title: 'Mensaje adjunto:' },
  Aprobado:      { cls: 'icon-green', icon: '✓', color: '#10b981',  msgClass: 'msg-green', title: 'Mensaje adjunto:' },
  'Aprobado Final': { cls: 'icon-green', icon: '✓', color: '#10b981', msgClass: 'msg-green', title: 'Mensaje adjunto:' },
  Devuelto:      { cls: 'icon-red',   icon: 'X', color: '#ef4444',  msgClass: 'msg-red',   title: 'Observación adjunta:' },
  Eliminado:     { cls: 'icon-red',   icon: 'X', color: '#ef4444',  msgClass: 'msg-red',   title: 'Observación adjunta:' },
  Pendiente:     { cls: 'icon-amber', icon: '⏳',color: '#d97706',  msgClass: 'msg-amber', title: 'Estado de Tarea:' },
  Reasignado:    { cls: 'icon-gray',  icon: 'R', color: '#6b7280',  msgClass: 'msg-gray',  title: 'Reasignación ETO:' },
}
