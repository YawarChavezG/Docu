/**
 * src/data/gerencias.js
 * Extraído de GERENCIAS_DB del HTML original
 */

export const gerenciasDB = [
  { id: 'CAL', nombre: 'Gerencia de Calidad', areas: [
    { cod: 'GAR', nombre: 'Garantía de Calidad',              activo: true  },
    { cod: 'VAL', nombre: 'Validaciones',                     activo: true  },
    { cod: 'DTE', nombre: 'Dirección Técnica',                activo: true  },
    { cod: 'LCC', nombre: 'Laboratorio de Control de Calidad',activo: true  },
  ]},
  { id: 'PRO', nombre: 'Gerencia de Producción', areas: [
    { cod: 'CAP', nombre: 'Cápsulas Blandas',       activo: true },
    { cod: 'SNE', nombre: 'Sólidos No Estériles',   activo: true },
    { cod: 'BET', nombre: 'Betalactámicos',         activo: true },
    { cod: 'PLI', nombre: 'Planta Líquidos',        activo: true },
    { cod: 'PSO', nombre: 'Planta Sólidos',         activo: true },
  ]},
  { id: 'LOG', nombre: 'Gerencia de Logística', areas: [
    { cod: 'ALM', nombre: 'Almacenes',    activo: true },
    { cod: 'DIS', nombre: 'Distribución', activo: true },
    { cod: 'REC', nombre: 'Recepción',    activo: true },
  ]},
  { id: 'RRH', nombre: 'Gerencia de RRHH', areas: [
    { cod: 'ADM', nombre: 'Administración RRHH', activo: true },
    { cod: 'CAP', nombre: 'Capacitación',        activo: true },
  ]},
  { id: 'AUD', nombre: 'Auditoría Interna', areas: [
    { cod: 'AUI', nombre: 'Auditoría Interna', activo: true },
  ]},
  { id: 'ADM', nombre: 'Administración y Finanzas', areas: [
    { cod: 'CON', nombre: 'Contabilidad', activo: true },
    { cod: 'FIN', nombre: 'Finanzas',     activo: true },
    { cod: 'TES', nombre: 'Tesorería',    activo: true },
  ]},
  { id: 'COM', nombre: 'Gerencia Comercial', areas: [
    { cod: 'VEN', nombre: 'Ventas',    activo: true },
    { cod: 'MKT', nombre: 'Marketing', activo: true },
  ]},
  { id: 'GER', nombre: 'Gerencia General', areas: [
    { cod: 'DIR', nombre: 'Dirección', activo: true },
  ]},
]

// Árbol Outlook (grupos de difusión)
export const arbolOutlookDB = [
  { id: 'CAL-GER', nombre: 'Gerencia de Calidad', subs: [
    { id: 'CAL-GAR', nombre: 'Garantía de Calidad' },
    { id: 'CAL-VAL', nombre: 'Validaciones'         },
    { id: 'CAL-DTE', nombre: 'Dirección Técnica'    },
  ]},
  { id: 'ADM-GER', nombre: 'Administración y Finanzas', subs: [
    { id: 'ADM-CON', nombre: 'Contabilidad' },
    { id: 'ADM-FIN', nombre: 'Finanzas'     },
    { id: 'ADM-TES', nombre: 'Tesorería'    },
  ]},
  { id: 'PRO-GER', nombre: 'Gerencia de Producción', subs: [
    { id: 'PRO-PLI', nombre: 'Planta Líquidos' },
    { id: 'PRO-PSO', nombre: 'Planta Sólidos'  },
    { id: 'PRO-BET', nombre: 'Betalactámicos'  },
  ]},
  { id: 'LOG-GER', nombre: 'Gerencia de Logística', subs: [
    { id: 'LOG-ALM', nombre: 'Almacenes'    },
    { id: 'LOG-DIS', nombre: 'Distribución' },
    { id: 'LOG-REC', nombre: 'Recepción'    },
  ]},
  { id: 'RRH-GER', nombre: 'Gerencia de RRHH', subs: [
    { id: 'RRH-ADM', nombre: 'Administración RRHH' },
    { id: 'RRH-CAP', nombre: 'Capacitación'        },
  ]},
]

// Matriz de Enrutamiento ETO
export const matrizEnrutamientoETO = [
  { gerencia: 'Calidad',    analista: 'aromero',     disponible: true,  delegado: ''      },
  { gerencia: 'Producción', analista: 'jmamani',     disponible: true,  delegado: ''      },
  { gerencia: 'Logística',  analista: 'cflores',     disponible: false, delegado: 'jmamani' },
  { gerencia: 'RRHH',       analista: 'aromero',     disponible: true,  delegado: ''      },
  { gerencia: 'Gerencia',   analista: 'jmamani',     disponible: true,  delegado: ''      },
]

// Tipos de Documentos (para desplegables y diccionarios)
export const tiposDocDB = [
  { tipo: 'Procedimiento', cod: 'PRO' },
  { tipo: 'Instructivo',   cod: 'INS' },
  { tipo: 'Formulario',    cod: 'FOR' },
  { tipo: 'Metodología',   cod: 'MET' },
  { tipo: 'Manual',        cod: 'MAN' },
  { tipo: 'Política',      cod: 'POL' },
]

// Estados de Proceso y Tarea
export const estadosProcesoDB = [
  { est: 'Elaboración',       ctx: 'Tarea'   },
  { est: 'Liberación ETO',    ctx: 'Tarea'   },
  { est: 'Revisión Paralela', ctx: 'Proceso' },
  { est: 'Corrección',        ctx: 'Proceso' },
  { est: 'Aprobación',        ctx: 'Proceso' },
  { est: 'Finalizado',        ctx: 'Proceso' },
  { est: 'Anulado',           ctx: 'Proceso' },
]

// Configuración global SLA (tabla config_global)
export const configGlobalDB = {
  vigenciaAnios:     4,
  plazoRevision:    10,
  esperaDelegacion:  3,
  plazoLectura:     30,
  slaVerde:          5,
  slaAmarillo:       3,
  maxAdjuntos:       5,
  maxSizeMB:        20,
  maxDescargasDia:   3,
  paginacionBandeja: 20,
  tiposExcluidos:   ['Formulario', 'Manual'],
}

// Plantillas de notificación email
export const plantillasEmailDB = [
  {
    nombre: 'Nueva Tarea Asignada',
    trigger: 'Al crear y asignar una tarea de flujo documental',
    asunto: '[COFAR · SGD] Nueva tarea asignada: {{CODIGO}} — {{TITULO}}',
    cuerpo: `Estimado/a {{USUARIO}},\n\nSe le ha asignado una nueva tarea de {{ETAPA}} en el Sistema de Gestión Documental de COFAR.\n\nDocumento: {{TITULO}} ({{CODIGO}})\nFecha límite de atención: {{FECHA_LIMITE}}\nGerencia: {{GERENCIA}}\n\nPara atender esta tarea, ingrese al sistema:\nhttps://sgd.cofar.com/bandeja\n\nSaludos,\nSistema de Gestión Documental — COFAR`,
  },
  {
    nombre: 'Alerta de Vencimiento',
    trigger: '30 días antes del vencimiento de un documento',
    asunto: '[COFAR · SGD] ⚠️ Alerta: documento próximo a vencer',
    cuerpo: `Estimado/a {{USUARIO}},\n\nEl siguiente documento está próximo a vencer:\n\nCódigo: {{CODIGO}}\nTítulo: {{TITULO}}\nFecha de vencimiento: {{FECHA_LIMITE}}\n\nPor favor, inicie el proceso de actualización a la brevedad posible.\n\nSaludos,\nSistema de Gestión Documental — COFAR`,
  },
  {
    nombre: 'Documento Aprobado',
    trigger: 'Al publicar un documento (última firma de aprobación)',
    asunto: '[COFAR · SGD] Nuevo documento vigente: {{CODIGO}} — {{TITULO}}',
    cuerpo: `Estimado/a {{USUARIO}},\n\nSe ha publicado un nuevo documento oficial:\n\n{{TITULO}} ({{CODIGO}})\n\nPor favor, revise el contenido en el siguiente enlace:\nhttps://sgd.cofar.com/lista\n\nSaludos,\nSistema de Gestión Documental — COFAR`,
  },
  {
    nombre: 'Documento Observado',
    trigger: 'Al devolver un documento por observaciones',
    asunto: '[COFAR · SGD] Documento devuelto con observaciones: {{CODIGO}}',
    cuerpo: `Estimado/a {{USUARIO}},\n\nSu documento {{TITULO}} ({{CODIGO}}) ha sido devuelto con las siguientes observaciones:\n\n{{OBSERVACION}}\n\nPor favor, realice las correcciones y reenvíe.\n\nhttps://sgd.cofar.com/bandeja\n\nSaludos,\nSistema de Gestión Documental — COFAR`,
  },
  {
    nombre: 'Evaluación Pendiente',
    trigger: 'Al asignar examen a grupo de difusión',
    asunto: '[COFAR · SGD] Evaluación pendiente: {{TITULO}}',
    cuerpo: `Estimado/a {{USUARIO}},\n\nTiene una evaluación pendiente para el documento:\n\n{{TITULO}} ({{CODIGO}})\n\nFecha límite: {{FECHA_LIMITE}}\n\nAcceda al sistema para rendir la evaluación:\nhttps://sgd.cofar.com/evaluaciones\n\nSaludos,\nSistema de Gestión Documental — COFAR`,
  },
  {
    nombre: 'Auto-delegación Activada',
    trigger: 'Por inactividad de 10 días hábiles',
    asunto: '[COFAR · SGD] Reasignación automática de tarea',
    cuerpo: `Estimado/a {{USUARIO}},\n\nDado que la tarea asignada ha superado el plazo de 10 días hábiles sin ser atendida, ha sido reasignada automáticamente a usted como delegado de {{USUARIO_ORIGINAL}}.\n\nDocumento: {{TITULO}} ({{CODIGO}})\n\nPor favor, atienda a la brevedad.\n\nhttps://sgd.cofar.com/bandeja\n\nSaludos,\nSistema de Gestión Documental — COFAR`,
  },
]
