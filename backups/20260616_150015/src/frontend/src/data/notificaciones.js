/**
 * src/data/notificaciones.js
 * Extraído del HTML: ptab-notif (US-9.04), cfg-notif-trigger
 * Contiene: PlantillasEmail[], triggers[], variables[]
 */

export const triggersNotificacionDB = [
  { id: 'nueva-tarea',      nombre: 'Nueva Tarea Asignada',        trigger: 'Al asignar tarea',             icon: '📋' },
  { id: 'doc-vencimiento',   nombre: 'Alerta de Vencimiento',        trigger: '30 días antes',                icon: '⚠️' },
  { id: 'doc-aprobado',      nombre: 'Documento Aprobado',           trigger: 'Al publicar',                  icon: '✅' },
  { id: 'doc-observado',     nombre: 'Documento Observado',          trigger: 'Al devolver',                 icon: '↩️' },
  { id: 'examen-pendiente',  nombre: 'Evaluación Pendiente',          trigger: 'Al asignar eval.',             icon: '📝' },
  { id: 'auto-delegacion',   nombre: 'Auto-delegación Activada',     trigger: 'Por inactividad',             icon: '🔄' },
]

export const variablesPlantillaDB = [
  { variable: '{{CODIGO}}',       descripcion: 'Código del documento' },
  { variable: '{{TITULO}}',       descripcion: 'Título del documento' },
  { variable: '{{USUARIO}}',      descripcion: 'Nombre del destinatario' },
  { variable: '{{FECHA_LIMITE}}', descripcion: 'Fecha límite de atención' },
  { variable: '{{ETAPA}}',        descripcion: 'Etapa actual del flujo' },
  { variable: '{{LINK}}',         descripcion: 'Enlace al sistema' },
  { variable: '{{GERENCIA}}',     descripcion: 'Gerencia responsable' },
  { variable: '{{OBSERVACION}}',  descripcion: 'Observación del revisor' },
  { variable: '{{USUARIO_ORIGINAL}}', descripcion: 'Usuario que delegó (auto-delegación)' },
]

export const plantillasEmailDB = [
  {
    id: 'nueva-tarea',
    nombre: 'Nueva Tarea Asignada',
    trigger: 'al asignar tarea',
    asunto: '[COFAR · SGD] Nueva tarea asignada: {{CODIGO}} — {{TITULO}}',
    cuerpo: `Estimado/a {{USUARIO}},

Se le ha asignado una nueva tarea de {{ETAPA}} en el Sistema de Gestión Documental de COFAR.

Documento: {{TITULO}} ({{CODIGO}})
Fecha límite de atención: {{FECHA_LIMITE}}
Gerencia: {{GERENCIA}}

Para atender esta tarea, ingrese al sistema a través del siguiente enlace:
{{LINK}}

Por favor, complete la tarea dentro del plazo indicado. En caso de no poder atenderla, el sistema realizará una auto-delegación automática.

Saludos,
Sistema de Gestión Documental — COFAR`,
  },
  {
    id: 'doc-vencimiento',
    nombre: 'Alerta de Vencimiento',
    trigger: '30 días antes',
    asunto: '[COFAR · SGD] ⚠️ Alerta: documento próximo a vencer — {{CODIGO}}',
    cuerpo: `Estimado/a {{USUARIO}},

El documento {{TITULO}} ({{CODIGO}}) se encuentra próximo a vencer.

Fecha de vencimiento: {{FECHA_LIMITE}}

Le recomendamos iniciar el proceso de actualización con la debida anticipación para evitar interrupciones en las operaciones.

Saludos,
Sistema de Gestión Documental — COFAR`,
  },
  {
    id: 'doc-aprobado',
    nombre: 'Documento Aprobado',
    trigger: 'al publicar',
    asunto: '[COFAR · SGD] Nuevo documento vigente: {{CODIGO}} — {{TITULO}}',
    cuerpo: `Estimado/a {{USUARIO}},

Se ha publicado un nuevo documento oficial en el Sistema de Gestión Documental de COFAR:

{{TITULO}} ({{CODIGO}})

Por favor, tome conocimiento del contenido en el siguiente enlace:
{{LINK}}

Este documento aplica a: {{GERENCIA}}

Saludos,
Sistema de Gestión Documental — COFAR`,
  },
  {
    id: 'doc-observado',
    nombre: 'Documento Observado',
    trigger: 'al devolver',
    asunto: '[COFAR · SGD] Documento devuelto con observaciones: {{CODIGO}}',
    cuerpo: `Estimado/a {{USUARIO}},

Su documento {{TITULO}} ({{CODIGO}}) ha sido devuelto con las siguientes observaciones realizadas por el revisor:

{{OBSERVACION}}

Por favor, realice las correcciones solicitadas y reenvíe el documento para continuar con el flujo de aprobación.

Enlace para reenviar: {{LINK}}

Saludos,
Sistema de Gestión Documental — COFAR`,
  },
  {
    id: 'examen-pendiente',
    nombre: 'Evaluación Pendiente',
    trigger: 'al asignar eval.',
    asunto: '[COFAR · SGD] Evaluación pendiente: {{TITULO}}',
    cuerpo: `Estimado/a {{USUARIO}},

Se le ha asignado una nueva evaluación correspondiente al documento:

{{TITULO}} ({{CODIGO}})

Fecha límite para completar la evaluación: {{FECHA_LIMITE}}

Acceda al sistema para rendir su evaluación:
{{LINK}}

Recuerde que la nota mínima aprobatoria es del 70%.

Saludos,
Sistema de Gestión Documental — COFAR`,
  },
  {
    id: 'auto-delegacion',
    nombre: 'Auto-delegación Activada',
    trigger: 'por inactividad',
    asunto: '[COFAR · SGD] Reasignación automática de tarea',
    cuerpo: `Estimado/a {{USUARIO}},

Se ha activado la auto-delegación de tarea debido a que la tarea asignada ha superado el plazo máximo de atención sin ser procesada.

Detalles de la tarea:
- Documento: {{TITULO}} ({{CODIGO}})
- Responsable original: {{USUARIO_ORIGINAL}}
- Nueva tarea asignada a: {{USUARIO}}

Por favor, atienda esta tarea con la mayor brevedad posible.

Enlace para atender: {{LINK}}

Saludos,
Sistema de Gestión Documental — COFAR`,
  },
]

export function getPlantillaPorId(id) {
  return plantillasEmailDB.find(p => p.id === id) || null
}

export function previsualizarPlantilla(id, datosPrueba = {}) {
  const plantilla = getPlantillaPorId(id)
  if (!plantilla) return { asunto: '', cuerpo: '' }

  const defaults = {
    CODIGO: 'PRO-CAL-045',
    TITULO: 'Procedimiento de Muestreo',
    USUARIO: 'Juan Perez',
    FECHA_LIMITE: '17/01/2026',
    ETAPA: 'Revisión',
    LINK: 'https://sgd.cofar.com/bandeja',
    GERENCIA: 'Gerencia de Calidad',
    OBSERVACION: 'Falta incluir tabla de referencias ISO 9001:2015 sección 7.5',
    USUARIO_ORIGINAL: 'Carlos Flores',
  }

  const datos = { ...defaults, ...datosPrueba }

  let cuerpo = plantilla.cuerpo
  Object.entries(datos).forEach(([key, value]) => {
    cuerpo = cuerpo.replace(new RegExp(`{{${key}}}`, 'g'), value)
  })

  let asunto = plantilla.asunto
  Object.entries(datos).forEach(([key, value]) => {
    asunto = asunto.replace(new RegExp(`{{${key}}}`, 'g'), value)
  })

  return { asunto, cuerpo }
}