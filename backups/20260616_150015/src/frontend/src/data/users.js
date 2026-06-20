/**
 * src/data/users.js
 * Extraído de USUARIOS_DB del HTML original + datos de login
 */

export const AVATARES_COLORES = [
  '#1a5fb4','#166534','#5b21b6','#b45309',
  '#0f766e','#be185d','#1d4ed8','#b91c1c',
  '#0369a1','#4338ca',
]

export const usuariosDB = [
  { id: 1,  nombre: 'Aracely Romero',   usuario: 'aromero',     rol: 'ETO',          perfil: 'Calidad',      area: 'Gestión Documental',    delegado: 'mbustamante', vacaciones: false, iniciales: 'AR' },
  { id: 2,  nombre: 'Mario Bustamante', usuario: 'mbustamante', rol: 'Estándar',     perfil: 'Producción',   area: 'Manufactura',            delegado: 'ccardenas',   vacaciones: false, iniciales: 'MB' },
  { id: 3,  nombre: 'Carmen Cárdenas',  usuario: 'ccardenas',   rol: 'Estándar',     perfil: 'Calidad',      area: 'Control de Calidad',     delegado: 'aromero',     vacaciones: true,  iniciales: 'CC' },
  { id: 4,  nombre: 'Roberto Vargas',   usuario: 'rvargas',     rol: 'Visualizador', perfil: 'Logística',    area: 'Almacenes',              delegado: '',            vacaciones: false, iniciales: 'RV' },
  { id: 5,  nombre: 'Lucía Herrera',    usuario: 'lherrera',    rol: 'Admin',        perfil: 'TI / Sistemas',area: 'Tecnología',             delegado: '',            vacaciones: false, iniciales: 'LH' },
  { id: 6,  nombre: 'Pedro Mamani',     usuario: 'pmamani',     rol: 'Estándar',     perfil: 'Manufactura',  area: 'Planta Líquidos',        delegado: 'aromero',     vacaciones: false, iniciales: 'PM' },
  { id: 7,  nombre: 'Silvana Torres',   usuario: 'storres',     rol: 'Estándar',     perfil: 'Regulatorio',  area: 'Asuntos Regulatorios',   delegado: 'floza',       vacaciones: true,  iniciales: 'ST' },
  { id: 8,  nombre: 'Diego Quispe',     usuario: 'dquispe',     rol: 'Visualizador', perfil: 'Producción',   area: 'Planta Sólidos',         delegado: '',            vacaciones: false, iniciales: 'DQ' },
  { id: 9,  nombre: 'Fernanda Loza',    usuario: 'floza',       rol: 'ETO',          perfil: 'Validación',   area: 'Aseguramiento Calidad',  delegado: 'ccardenas',   vacaciones: false, iniciales: 'FL' },
  { id: 10, nombre: 'Gonzalo Pinto',    usuario: 'gpinto',      rol: 'Estándar',     perfil: 'Mantenimiento',area: 'Mantenimiento',          delegado: 'rvargas',     vacaciones: false, iniciales: 'GP' },
]

// Usuarios que NO tienen delegado configurado (para alerta de desvinculado)
export const USUARIOS_SIN_DELEGADO = ['solicitante']

// Mapa de login → datos de sesión
export const LOGIN_MAP = {
  aromero:     { pass: 'cofar.2026', rol: 'eto',         nombre: 'Aracely Romero', cargo: 'Gestor Documental ETO',    iniciales: 'AR', rutaInicio: '/bandeja' },
  solicitante: { pass: 'cofar.2026', rol: 'user',        nombre: 'Juan Perez',     cargo: 'Analista de Calidad',      iniciales: 'JP', rutaInicio: '/bandeja', alertaDelegado: true },
  admin:       { pass: 'cofar.2026', rol: 'admin',       nombre: 'Lucía Herrera',  cargo: 'Administrador del Sistema', iniciales: 'LH', rutaInicio: '/parametrizacion' },
  visualizador:{ pass: 'cofar.2026', rol: 'visualizador',nombre: 'Diego Quispe',   cargo: 'Visualizador',             iniciales: 'DQ', rutaInicio: '/bandeja' },
}

// Datalist de empleados (para autocomplete en modales y formularios)
export const listaEmpleados = [
  'Aracely Romero (Gestor Documental)',
  'Mario Bustamante (Analista de Producción)',
  'Carmen Cárdenas (Analista de Calidad)',
  'Roberto Vargas (Encargado de Almacenes)',
  'Lucía Herrera (Administradora del Sistema)',
  'Pedro Mamani (Operario Planta Líquidos)',
  'Silvana Torres (Especialista Regulatorio)',
  'Diego Quispe (Operario Planta Sólidos)',
  'Fernanda Loza (Analista ETO)',
  'Gonzalo Pinto (Técnico Mantenimiento)',
  'Juan Perez (Analista de Calidad)',
  'Carlos Flores (Jefe de Logística)',
  'Maria Condori (Analista de Calidad Sr.)',
  'Jasiel Sanjinés (Jefe de Excelencia)',
  'Luis Mamani (Gerente de Planta)',
  'Lucía Castro (Supervisora RRHH)',
  'Jasiel Perez Planta (Jefe de Planta)',
]

// Función helper para obtener color de avatar por índice
export function getAvatarColor(idx) {
  return AVATARES_COLORES[idx % AVATARES_COLORES.length]
}

// Función helper para obtener usuario por nombre de usuario
export function getUserByUsuario(usr) {
  return usuariosDB.find(u => u.usuario === usr) || null
}
