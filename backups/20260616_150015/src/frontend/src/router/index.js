/**
 * router/index.js — Hash router con guardianes RBAC, 403/404 y topbar dinámico
 */

const routes = {
  '/login':                () => import('../pages/Login.js'),
  '/403':                  () => import('../pages/Error403.js'),
  '/404':                  () => import('../pages/Error404.js'),
  // Tanda 3
  '/bandeja':              () => import('../pages/Bandeja.js'),
  '/tareas-completas':     () => import('../pages/TareasCompletas.js'),
  '/lista':                () => import('../pages/ListaMaestra.js'),
  '/consulta':             () => import('../pages/ConsultaDocumentos.js'),
  '/biblioteca':           () => import('../pages/Placeholder.js'),
  // Tanda 4 — Evaluaciones
  '/evaluaciones':         () => import('../pages/Evaluaciones.js'),
  '/certificados':         () => import('../pages/Certificados.js'),
  '/certificado-imprimible':() => import('../pages/CertificadoImprimible.js'),
  '/pre-eval':             () => import('../pages/PreEval.js'),
  '/tomar-lectura':        () => import('../pages/TomarLectura.js'),
  // Tanda 4 — Plantillas
  '/plantillas':           () => import('../pages/Plantillas.js'),
  // Tanda 5 — Flujo Documental y Parametrización
  '/liberacion-detalle':   () => import('../pages/LiberacionDetalle.js'),
  '/revision':             () => import('../pages/Revision.js'),
  '/aprobacion-final':     () => import('../pages/AprobacionFinal.js'),
  '/correccion':           () => import('../pages/Correccion.js'),
  '/version-editable':     () => import('../pages/VersionEditable.js'),
  '/aprobacion-documento': () => import('../pages/AprobacionDocumento.js'),
  '/modulo-copias':        () => import('../pages/ModuloCopias.js'),
  '/copias-cc':            () => import('../pages/MonitorCC.js'),
  '/copias-cn':            () => import('../pages/MonitorCN.js'),
  '/publicacion':          () => import('../pages/Publicacion.js'),
  '/reportes':             () => import('../pages/Reportes.js'),
  '/chat':                 () => import('../pages/Chat.js'),
  '/parametrizacion':      () => import('../pages/Parametrizacion.js'),
  '/config-examen':        () => import('../pages/ConfigExamen.js'),
}

const routeTitles = {
  '/login': 'Iniciar Sesión',
  '/bandeja': 'Mi Bandeja',
  '/tareas-completas': 'Tareas Completas',
  '/lista': 'Lista Maestra',
  '/consulta': 'Consultar Documentos',
  '/biblioteca': 'Biblioteca',
  '/evaluaciones': 'Evaluaciones y Controles de Lectura',
  '/certificados': 'Mis Certificados',
  '/certificado-imprimible': 'Certificado',
  '/pre-eval': 'Pre-evaluación',
  '/tomar-lectura': 'Tomar Lectura',
  '/plantillas': 'Plantillas Documentales',
  '/liberacion-detalle': 'Atender Liberación',
  '/revision': 'Revisar Documento',
  '/aprobacion-final': 'Aprobación Final',
  '/correccion': 'Corregir Observaciones',
  '/version-editable': 'Documento en Versión Editable',
  '/aprobacion-documento': 'Aprobación de Documento',
  '/modulo-copias': 'Módulo de Copias',
  '/copias-cc': 'Copias Controladas',
  '/copias-cn': 'Copias No Controladas',
  '/publicacion': 'Monitor de Evaluaciones / Controles',
  '/reportes': 'Reportes',
  '/chat': 'Asistente IA',
  '/parametrizacion': 'Parametrización General',
  '/config-examen': 'Configuración de Exámenes',
  '/403': 'Acceso Denegado',
  '/404': 'Página no encontrada',
}

function getHash() {
  const raw = window.location.hash.replace(/^#/,'') || '/login'
  return raw.split('?')[0]
}
function getHashQuery() {
  const raw = window.location.hash.replace(/^#/,'') || ''
  const idx = raw.indexOf('?')
  return idx === -1 ? '' : raw.slice(idx + 1)
}
function setHash(p) { window.location.hash = '#' + p }
function isLayoutMounted() { return !!document.getElementById('page-content') }
function syncNavActive(r) { document.querySelectorAll('[data-route]').forEach(el=>el.classList.toggle('is-active',el.dataset.route===r)) }

function updatePageTitle(hash) {
  const title = routeTitles[hash] || 'COFAR · Sistema de Gestión Documental'
  const app = window.Alpine?.store('app')
  if (app) app.setPageTitle(title)
}

async function handleRoute() {
  const auth = window.Alpine?.store('auth')
  const hash = getHash()
  const appEl = document.getElementById('app')

  if(!appEl) return
  if(!auth?.isAuthenticated && hash!=='/login'){setHash('/login');return}
  if(auth?.isAuthenticated && hash==='/login'){setHash(auth.homeRoute);return}

  if(hash==='/login'){
    appEl.innerHTML=''
    const {page}=await import('../pages/Login.js')
    page.init?.();appEl.innerHTML=page.template;window.Alpine?.initTree(appEl)
    updatePageTitle(hash)
    return
  }

  if(!isLayoutMounted()){
    const {AppLayout}=await import('../layouts/AppLayout.js')
    AppLayout.init?.();appEl.innerHTML=AppLayout.render(auth);window.Alpine?.initTree(appEl)
  }

  const contentEl=document.getElementById('page-content')
  if(!contentEl) return

  // Guardián 404: ruta inexistente
  if(!routes[hash]){
    setHash('/404')
    return
  }

  // Guardián 403: ruta prohibida por rol
  if(hash!=='/403' && hash!=='/404' && !auth?.canAccessRoute(hash)){
    setHash('/403')
    return
  }

  try {
    const loader=routes[hash]
    const mod=await loader()
    const page=mod.page??mod.default
    page.init?.()
    contentEl.style.opacity='0'
    contentEl.style.transform='translateY(8px)'
    contentEl.innerHTML=page.template
    window.Alpine?.initTree(contentEl)

    requestAnimationFrame(()=>{
      contentEl.style.transition='opacity 0.2s ease-out,transform 0.22s cubic-bezier(0.16,1,0.3,1)'
      contentEl.style.opacity='1'
      contentEl.style.transform='translateY(0)'
    })
    syncNavActive(hash)
    updatePageTitle(hash)
    contentEl.scrollTop=0
  } catch (error) {
    console.error("Error cargando la página:", error);
    contentEl.innerHTML = `<div style="padding: 20px; color: red;">Error al cargar el módulo. Revisa la consola para más detalles.</div>`;
  }
}

export function navigate(p){window.location.hash='#'+p}
export function initRouter(){
  window.navigate=navigate
  window.addEventListener('hashchange',handleRoute)
  handleRoute()
}
