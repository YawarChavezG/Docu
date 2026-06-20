/**
 * pages/AprobacionDocumento.js — Wizard de aprobación documental (3 pasos)
 * Versión corregida: Carga de archivos múltiples para formularios con soporte industrial.
 */
import { gerenciasDB, arbolOutlookDB, tiposDocDB } from '../data/gerencias.js'
import { listaEmpleados } from '../data/users.js'

export const page = {
  init() {
    window.Alpine?.data('wizardAprobacion', () => ({
      paso: 1,

      // PASO 1: DATOS Y CARGA DE ARCHIVO
      tiposList: tiposDocDB,
      gerenciasList: gerenciasDB,
      empleadosList: listaEmpleados,
      tipodoc: '',
      gerencia: '',
      area: '',
      tipoSolicitud: '',
      titulo: '',
      justificacion: '',
      
      // Manejo de Documento Principal
      archivoPrincipal: null,
      dropPrincipal: false,

      // --- NUEVA FUNCIONALIDAD: FORMULARIOS MÚLTIPLES ---
      formulariosAsociados: [], // Array de archivos
      dropFormularios: false,

      get areasList() {
        const g = this.gerenciasList.find(x => x.id === this.gerencia)
        return g ? g.areas : []
      },
      get codigoAuto() {
        return (this.tipodoc && this.area) ? `${this.tipodoc}-${this.area}-0XX` : '---'
      },
      get versionAuto() {
        return this.tipoSolicitud === 'Actualización' ? '02' : '01'
      },

      // Lógica para añadir archivos a la lista de formularios
      agregarFormularios(files) {
        const nuevosArchivos = Array.from(files);
        // Evitamos duplicados por nombre y tamaño
        nuevosArchivos.forEach(file => {
          const existe = this.formulariosAsociados.some(f => f.name === file.name && f.size === file.size);
          if (!existe) this.formulariosAsociados.push(file);
        });
      },

      removerFormulario(index) {
        this.formulariosAsociados.splice(index, 1);
      },

      // PASO 2: DIFUSIÓN (OUTLOOK)
      requiereEval: 'si',
      requiereLectura: 'si',
      showTree: false,
      arbol: JSON.parse(JSON.stringify(arbolOutlookDB)).map(g => ({
        ...g,
        checked: false,
        indeterminate: false,
        subs: g.subs.map(s => ({ ...s, checked: false }))
      })),
      togglePadre(grupo) {
        grupo.checked = !grupo.checked
        grupo.indeterminate = false
        grupo.subs.forEach(s => s.checked = grupo.checked)
      },
      toggleHijo(grupo, hijo) {
        hijo.checked = !hijo.checked
        const todos = grupo.subs.every(s => s.checked)
        const algunos = grupo.subs.some(s => s.checked)
        grupo.checked = todos
        grupo.indeterminate = !todos && algunos
      },
      get chipsDifusion() {
        let chips = []
        this.arbol.forEach(g => {
          if (g.checked) {
            chips.push({ id: g.id, nombre: g.nombre, tipo: 'padre', ref: g })
          } else {
            g.subs.forEach(s => {
              if (s.checked) chips.push({ id: s.id, nombre: s.nombre, tipo: 'hijo', refPadre: g, refHijo: s })
            })
          }
        })
        return chips
      },
      removerChip(chip) {
        if (chip.tipo === 'padre') this.togglePadre(chip.ref)
        else this.toggleHijo(chip.refPadre, chip.refHijo)
      },

      // PASO 3: FLUJO Y FIRMAS
      revisores: [{ id: 1, nombre: 'Aracely Romero (Gestor Documental)' }],
      aprobadores: [{ id: 2, nombre: 'Carlos Flores (Jefe de Logística)' }],
      reemplaza: 'no',

      inputReemplazo: '',
      chipsReemplazo: [],
      addChipReemplazo() {
        const val = this.inputReemplazo.trim().toUpperCase()
        if (val && !this.chipsReemplazo.includes(val)) {
          this.chipsReemplazo.push(val)
        }
        this.inputReemplazo = ''
      },
      removeChipReemplazo(chip) {
        this.chipsReemplazo = this.chipsReemplazo.filter(c => c !== chip)
      },

      // Navegación
      nextPaso() {
        if (this.paso < 3) this.paso++
      },
      prevPaso() {
        if (this.paso > 1) this.paso--
      },
      firmarEnviar() {
        window.authModal?.abrir({
          titulo: 'Firmar y enviar a Liberación',
          icono: '✍️',
          mensaje: `Va a enviar la solicitud <strong>"${this.titulo || 'Nuevo Documento'}"</strong> al flujo de Liberación ETO. Esta acción requiere doble autenticación.`,
          onSuccess: () => {
            window.toast?.('✅ Solicitud enviada a ETO correctamente.', 'success')
            window.navigate?.('/bandeja')
          }
        })
      },
    }))
  },

  template: /* html */ `
<div x-data="wizardAprobacion" class="max-w-4xl mx-auto animate-fade-in-page">

  <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
    <div>
      <h1 class="page-header">Aprobación de Documento</h1>
      <p class="page-subtitle">Flujo completo de creación o actualización documental</p>
    </div>
    <button @click="window.confirmCancelModal.abrir({ titulo: 'Cancelar Solicitud', mensaje: '¿Está seguro de cancelar? Perderá el progreso.', onConfirm: () => window.navigate('/bandeja') })" class="btn btn-danger text-xs">
      ✕ Cancelar solicitud
    </button>
  </div>

  <!-- Stepper responsive: solo números en móvil, texto completo en md+ -->
  <div class="flex items-center mb-3 card-base overflow-x-auto gap-0">
    <template x-for="(s,i) in ['Datos y Carga de Archivo','Difusión y Evaluación','Flujo y Firmas']" :key="i">
      <div class="flex items-center flex-1 min-w-0">
        <div class="flex items-center gap-2 whitespace-nowrap">
          <div class="w-[26px] h-[26px] rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0"
               :class="paso>i+1 ? 'bg-emerald-600 text-white' : paso===i+1 ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-400'"
               x-text="paso>i+1?'✓':i+1"></div>
          <span class="hidden md:inline text-[11px] font-semibold"
                :class="paso===i+1 ? 'text-brand-500' : paso>i+1 ? 'text-emerald-600' : 'text-slate-400'"
                x-text="s"></span>
        </div>
        <div x-show="i<2" class="flex-1 h-0.5 bg-slate-100 mx-2.5 min-w-[12px]"></div>
      </div>
    </template>
  </div>
  <!-- Título del paso activo visible solo en móvil -->
  <div class="md:hidden text-center mb-4 px-2">
    <span class="text-xs font-bold text-brand-600 bg-brand-50 px-3 py-1 rounded-full border border-brand-200"
          x-text="['Datos y Carga de Archivo','Difusión y Evaluación','Flujo y Firmas'][paso-1]"></span>
  </div>

  <div x-show="paso===1" class="card-base">
    <div class="section-header">1. Datos del documento y carga de archivo</div>

    <div x-show="tipoSolicitud==='Actualización'"
         x-transition:enter="transition-all duration-200"
         x-transition:enter-start="opacity-0 -translate-y-1"
         x-transition:enter-end="opacity-100 translate-y-0"
         class="bg-amber-50 border border-amber-200 rounded-xl px-3.5 py-2.5 mb-4 flex items-start gap-2">
      <span class="text-base flex-shrink-0">⚠️</span>
      <div class="text-[11.5px] text-amber-800 leading-relaxed">
        <strong>Archivo obligatorio para Actualización:</strong> Es obligatorio cargar el documento principal en este momento, ya que el sistema leerá el archivo para extraer automáticamente el código y la versión anterior del documento.
      </div>
    </div>

    <div class="form-grid-2 mb-5">
      <div>
        <label class="form-label">Tipo de documento *</label>
        <select class="form-input text-xs" x-model="tipodoc">
          <option value="">Seleccionar...</option>
          <template x-for="t in tiposList" :key="t.cod">
            <option :value="t.cod" x-text="t.tipo + ' (' + t.cod + ')'"></option>
          </template>
        </select>
      </div>
      <div>
        <label class="form-label">Gerencia responsable *</label>
        <select class="form-input text-xs" x-model="gerencia" @change="area=''">
          <option value="">Seleccionar...</option>
          <template x-for="g in gerenciasList" :key="g.id">
            <option :value="g.id" x-text="g.id + ' — ' + g.nombre"></option>
          </template>
        </select>
      </div>
      <div>
        <label class="form-label">Área responsable *</label>
        <select class="form-input text-xs" x-model="area" :disabled="!gerencia">
          <option value="">Seleccione una gerencia primero...</option>
          <template x-for="a in areasList" :key="a.cod">
            <option :value="a.cod" x-text="a.cod + ' — ' + a.nombre"></option>
          </template>
        </select>
      </div>
      <div>
        <label class="form-label">Tipo de solicitud *</label>
        <select class="form-input text-xs" x-model="tipoSolicitud">
          <option value="">Seleccionar...</option>
          <option value="Creación">Creación de nuevo documento</option>
          <option value="Actualización">Actualización de documento</option>
        </select>
      </div>
      <div>
        <label class="form-label">Código (automático)</label>
        <input type="text" :value="codigoAuto" class="form-input bg-slate-50 text-slate-400 font-mono text-xs" readonly>
      </div>
      <div>
        <label class="form-label">Versión (automático)</label>
        <input type="text" :value="versionAuto" class="form-input bg-slate-50 text-slate-400 text-xs" readonly>
      </div>
      <div class="sm:col-span-2">
        <label class="form-label">Título del documento *</label>
        <input type="text" class="form-input text-xs" x-model="titulo" placeholder="Ej.: Procedimiento de Control de Documentos del SIG">
      </div>
      <div class="sm:col-span-2">
        <label class="form-label">Justificación / motivo de la solicitud</label>
        <textarea class="form-input text-xs resize-y" rows="3" x-model="justificacion" placeholder="Describa el motivo de creación o actualización del documento..."></textarea>
      </div>
    </div>

    <div class="pt-4 border-t border-slate-100">
      <div class="text-[11px] font-bold text-slate-800 mb-3 uppercase tracking-wider">Carga del documento elaborado</div>

      <div class="mb-5">
        <label class="form-label">
          Documento principal (.docx)
          <span x-show="tipoSolicitud==='Actualización'" class="text-red-600"> *</span>
        </label>
        <div class="border-2 border-dashed rounded-xl p-7 text-center cursor-pointer transition-all duration-150"
             :class="archivoPrincipal ? 'border-emerald-300 bg-emerald-50' : dropPrincipal ? 'border-brand-500 bg-blue-50' : 'border-blue-200 bg-slate-50'"
             @dragover.prevent="dropPrincipal=true"
             @dragleave="dropPrincipal=false"
             @drop.prevent="archivoPrincipal=$event.dataTransfer.files[0];dropPrincipal=false"
             @click="$refs.filePrincipal.click()">
          <template x-if="archivoPrincipal">
            <div class="animate-scale-in">
              <div class="text-2xl mb-1.5">📄</div>
              <div class="text-xs font-semibold text-emerald-700" x-text="archivoPrincipal.name"></div>
              <div class="text-[10.5px] text-slate-500 mt-0.5" x-text="(archivoPrincipal.size/1024/1024).toFixed(2) + ' MB — clic para cambiar'"></div>
            </div>
          </template>
          <template x-if="!archivoPrincipal">
            <div>
              <div class="text-[32px] mb-2">📄</div>
              <div class="text-xs font-semibold text-brand-600">Cargar documento principal</div>
              <div class="text-[11px] text-slate-400 mt-1">Arrastre su archivo .docx aquí o haga clic para seleccionar</div>
              <div class="text-[10px] text-slate-300 mt-0.5 font-mono">MS WORD (.DOCX) — MÁX 20MB</div>
            </div>
          </template>
        </div>
        <input type="file" x-ref="filePrincipal" accept=".docx" class="hidden" @change="archivoPrincipal=$event.target.files[0]">
      </div>

      <div class="mb-2">
        <label class="form-label">Formularios asociados y adjuntos adicionales</label>
        
        <div class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-150 mb-3"
             :class="dropFormularios ? 'border-brand-500 bg-blue-50' : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/50'"
             @dragover.prevent="dropFormularios=true"
             @dragleave="dropFormularios=false"
             @drop.prevent="agregarFormularios($event.dataTransfer.files); dropFormularios=false"
             @click="$refs.fileFormularios.click()">
          
          <div class="flex flex-col items-center">
            <div class="text-2xl mb-1">📂</div>
            <div class="text-[11.5px] font-semibold text-slate-600">Añadir archivos adicionales</div>
            <div class="text-[10px] text-slate-400 mt-0.5 uppercase tracking-tighter">
                PDF, WORD, EXCEL, PPT, DWG, VISIO, IMÁGENES
            </div>
          </div>
        </div>

        <input type="file" x-ref="fileFormularios" multiple class="hidden"
               accept=".docx,.doc,.xlsx,.xls,.pdf,.pptx,.ppt,.dwg,.dxf,.vsdx,.vsd,.png,.jpg,.jpeg"
               @change="agregarFormularios($event.target.files)">

        <div class="flex flex-col gap-1.5">
            <template x-for="(file, index) in formulariosAsociados" :key="file.name + file.lastModified">
                <div class="flex items-center justify-between bg-white border border-slate-200 rounded-lg p-2.5 shadow-sm animate-slide-up">
                    <div class="flex items-center gap-3 min-w-0">
                        <div class="w-8 h-8 rounded bg-slate-100 flex items-center justify-center text-base flex-shrink-0">
                           <span x-text="file.name.split('.').pop().toLowerCase() === 'pdf' ? '📕' : (['xlsx','xls'].includes(file.name.split('.').pop().toLowerCase()) ? '📗' : '📄')"></span>
                        </div>
                        <div class="truncate">
                            <div class="text-[11px] font-bold text-slate-700 truncate" x-text="file.name"></div>
                            <div class="text-[10px] text-slate-400 font-mono" x-text="(file.size/1024).toFixed(1) + ' KB'"></div>
                        </div>
                    </div>
                    <button @click="removerFormulario(index)" 
                            class="w-7 h-7 rounded-full flex items-center justify-center text-slate-400 hover:bg-red-50 hover:text-red-500 transition-colors cursor-pointer"
                            title="Eliminar archivo">
                        ✕
                    </button>
                </div>
            </template>
        </div>

        <div x-show="formulariosAsociados.length === 0" class="text-center py-4 bg-slate-50/30 rounded-lg border border-dotted border-slate-200">
            <span class="text-[10.5px] text-slate-400 italic font-mono tracking-tight">SIN FORMULARIOS ADJUNTOS</span>
        </div>
      </div>
    </div>
  </div>

  <div x-show="paso===2" class="card-base">
    <div class="section-header">2. Difusión y evaluación</div>

    <div class="form-grid-2 mb-5">
      <div>
        <label class="form-label">Tiempo de vigencia</label>
        <input type="text" value="4 años" class="form-input bg-slate-50 text-slate-400 text-xs" readonly>
      </div>
      <div>
        <label class="form-label">Requiere evaluación</label>
        <select class="form-input text-xs" x-model="requiereEval">
          <option value="si">Sí</option>
          <option value="no">No</option>
        </select>
      </div>
      <div class="sm:col-span-2">
        <label class="form-label">Requiere control de lectura</label>
        <select class="form-input text-xs" x-model="requiereLectura">
          <option value="si">Sí — firma de lectura obligatoria</option>
          <option value="no">No</option>
        </select>
      </div>
    </div>

    <div>
      <label class="form-label">Alcance de difusión (Grupos de Outlook) *</label>
      <div class="relative" @click.outside="showTree=false">

        <div @click="showTree=!showTree"
             class="bg-white border border-slate-200 rounded-md px-3 py-2.5 cursor-pointer flex justify-between items-center w-full min-h-[38px]">
          <span class="text-xs text-slate-600" x-text="chipsDifusion.length ? chipsDifusion.length + ' grupo(s) seleccionado(s)' : 'Seleccionar grupos de distribución...'"></span>
          <span class="text-[10px] text-slate-400 transition-transform duration-200"
                :class="showTree ? 'rotate-180' : ''">▼</span>
        </div>
        <div x-show="showTree" @click.stop
             class="absolute z-[100] left-0 w-full top-[calc(100%+4px)] bg-white border border-slate-200 rounded-xl p-3 shadow-card-md max-h-[300px] overflow-y-auto">
          <div class="text-[10px] text-slate-400 mb-2.5 pb-2 border-b border-slate-100">Marcar una Gerencia selecciona todos sus departamentos automáticamente</div>
          <template x-for="grupo in arbol" :key="grupo.id">
            <div class="mb-2.5">
              <label class="flex items-center gap-2 cursor-pointer px-1.5 py-1 rounded-md text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
                <input type="checkbox"
                       x-effect="$el.checked=grupo.checked;$el.indeterminate=grupo.indeterminate"
                       @change.stop="togglePadre(grupo)"
                       class="accent-brand-500 w-3.5 h-3.5 flex-shrink-0">
                🏢 <span x-text="grupo.nombre"></span>
              </label>
              <div class="ml-6 mt-0.5">
                <template x-for="hijo in grupo.subs" :key="hijo.id">
                  <label class="flex items-center gap-2 cursor-pointer px-1.5 py-0.5 rounded-md text-[11.5px] text-slate-600 hover:bg-slate-50 transition-colors">
                    <input type="checkbox"
                           x-effect="$el.checked=hijo.checked"
                           @change.stop="toggleHijo(grupo, hijo)"
                           class="accent-brand-500 w-3.5 h-3.5 flex-shrink-0">
                    <span x-text="hijo.nombre"></span>
                  </label>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="flex flex-wrap gap-1.5 mt-2.5 px-2.5 py-2 bg-slate-50 rounded-lg border border-slate-200 min-h-[42px] items-center">
        <template x-if="chipsDifusion.length===0">
          <span class="text-[11px] text-slate-300">Ningún grupo seleccionado aún...</span>
        </template>
        <template x-for="chip in chipsDifusion" :key="chip.id">
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span x-text="(chip.tipo==='padre'?'🏢 ':'')+chip.nombre"></span>
            <button type="button" @click="removerChip(chip)" class="text-red-600 cursor-pointer bg-transparent border-0 p-0 leading-none text-[13px] inline-flex">✕</button>
          </span>
        </template>
      </div>
    </div>
  </div>

  <div x-show="paso===3" class="card-base">
    <div class="section-header">3. Flujo y firmas</div>

    <div class="flex flex-col gap-4">

      <div>
        <label class="form-label">Revisores asignados (Mínimo 1)</label>
        <div class="flex flex-col gap-1.5">
          <template x-for="(r,i) in revisores" :key="r.id">
            <div class="flex gap-2">
              <input type="text" x-model="r.nombre" class="form-input flex-1 text-xs" list="lista-empleados" placeholder="Nombre del revisor...">
              <button @click="revisores.splice(i,1)" class="btn btn-danger px-2.5 text-[13px]">✕</button>
            </div>
          </template>
        </div>
        <button @click="revisores.push({id:Date.now(),nombre:''})" class="btn btn-sm text-brand-600 border-brand-500 mt-1.5 text-[11px]">➕ Agregar Revisor</button>
      </div>

      <div>
        <label class="form-label">Aprobadores asignados (Mínimo 1)</label>
        <div class="flex flex-col gap-1.5">
          <template x-for="(a,i) in aprobadores" :key="a.id">
            <div class="flex gap-2">
              <input type="text" x-model="a.nombre" class="form-input flex-1 text-xs" list="lista-empleados" placeholder="Nombre del aprobador...">
              <button @click="aprobadores.splice(i,1)" class="btn btn-danger px-2.5 text-[13px]">✕</button>
            </div>
          </template>
        </div>
        <button @click="aprobadores.push({id:Date.now(),nombre:''})" class="btn btn-sm text-brand-600 border-brand-500 mt-1.5 text-[11px]">➕ Agregar Aprobador</button>
      </div>

      <div>
        <label class="form-label">Reemplaza o da de baja algún documento</label>
        <select class="form-input text-xs max-w-sm" x-model="reemplaza">
          <option value="no">No — este documento no reemplaza a ninguno</option>
          <option value="si">Sí — este documento reemplaza a otro</option>
        </select>

        <div x-show="reemplaza==='si'" class="mt-3">
          <label class="form-label">Códigos de documento a reemplazar (Enter o coma para agregar)</label>
          <div class="border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 flex flex-wrap gap-1.5 items-center min-h-[42px]">
            <template x-for="chip in chipsReemplazo" :key="chip">
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] bg-slate-100 text-slate-600 border border-slate-200 font-mono">
                <span x-text="chip"></span>
                <button type="button" @click="removeChipReemplazo(chip)" class="text-red-600 cursor-pointer bg-transparent border-0 p-0 leading-none text-[13px] inline-flex">✕</button>
              </span>
            </template>
            <input type="text"
                   x-model="inputReemplazo"
                   @keydown.enter.prevent="addChipReemplazo()"
                   @keydown.comma.prevent="addChipReemplazo()"
                   @input="$el.value=$el.value.toUpperCase();inputReemplazo=$el.value"
                   placeholder="Ej.: CAL-MAN-001"
                   class="border-0 outline-none text-xs bg-transparent min-w-[140px] font-mono font-semibold">
          </div>
          <p class="text-[10px] text-slate-400 mt-1">Ingrese el código y presione Enter o coma para agregarlo</p>
        </div>
      </div>

      <div class="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3.5 flex items-center justify-between flex-wrap gap-2.5 mt-1">
        <div>
          <div class="text-[11px] font-bold text-emerald-700">Firma Digital Requerida</div>
          <div class="text-[11px] text-emerald-600 mt-0.5">Se solicitará doble autenticación para enviar al flujo de Liberación</div>
        </div>
        <button @click="firmarEnviar()" class="btn btn-primary whitespace-nowrap">✍️ Firmar y Enviar a Liberación →</button>
      </div>

    </div>
  </div>

  <datalist id="lista-empleados">
    <template x-for="emp in empleadosList" :key="emp">
      <option :value="emp" x-text="emp"></option>
    </template>
  </datalist>

  <div class="flex justify-between items-center mt-3.5 flex-wrap gap-2">
    <button x-show="paso>1" class="btn" @click="prevPaso()">← Anterior</button>
    <div class="flex-1"></div>
    <div x-show="paso<3" class="flex items-center gap-2.5">
      <span class="text-[11px] text-slate-400">Se solicitará doble autenticación al enviar</span>
      <button class="btn btn-primary" @click="nextPaso()">Siguiente →</button>
    </div>
  </div>

</div>`
}