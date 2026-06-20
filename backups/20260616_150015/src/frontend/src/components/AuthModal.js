/**
 * src/components/AuthModal.js
 * Modal de Doble Autenticación (Firma Digital)
 */

export function initAuthModal() {
  window.Alpine?.data('authModalData', () => ({
    open: false,
    titulo: 'Firma Digital Requerida',
    icono: '✍️',
    mensaje: '',
    usuario: '',
    pass: '',
    submitting: false,
    _onSuccess: null,
    _onCancel: null,

    abrir({ titulo = 'Firma Digital Requerida', icono = '✍️', mensaje = '', onSuccess, onCancel } = {}) {
      this.titulo     = titulo
      this.icono      = icono
      this.mensaje    = mensaje
      this.pass       = ''
      this.submitting = false
      this._onSuccess = onSuccess || null
      this._onCancel  = onCancel  || null
      const auth = window.Alpine?.store('auth')
      this.usuario = auth?.usuario || auth?.user?.nombre || auth?.nombre || auth?.user?.name || 'Usuario Actual '
      this.open = true
    },

    cerrar() {
      this.open = false
      this.pass = ''
      if (this._onCancel) this._onCancel()
    },

    confirmar() {
      if (!this.pass || this.pass.trim() === '') {
        window.toast('⚠️ Debe ingresar su contraseña para firmar.', 'warn')
        return
      }
      this.submitting = true
      setTimeout(() => {
        this.submitting = false
        this.open = false
        window.toast('✅ Firma digital registrada. Acción realizada exitosamente.', 'success')
        if (this._onSuccess) this._onSuccess({ usuario: this.usuario, timestamp: new Date().toISOString() })
      }, 600)
    },
  }))

  window.authModal = {
    abrir(opts) {
      const store = document.querySelector('[x-data="authModalData"]')
      // CORRECCIÓN: Uso de la API de Alpine v3 (_x_dataStack)
      if (store && store._x_dataStack) store._x_dataStack[0].abrir(opts)
      else setTimeout(() => window.authModal.abrir(opts), 200)
    },
    cerrar() {
      const store = document.querySelector('[x-data="authModalData"]')
      // CORRECCIÓN: Uso de la API de Alpine v3 (_x_dataStack)
      if (store && store._x_dataStack) store._x_dataStack[0].cerrar()
    },
  }
}

export const AuthModalTemplate = /* html */`
<div x-data="authModalData">
  <template x-teleport="body">
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         @keydown.escape.window="cerrar()"
         class="modal-overlay" 
         style="z-index:9000;display:none;">

      <div @click.stop
           x-transition:enter="transition ease-out duration-200"
           x-transition:enter-start="opacity-0 scale-95"
           x-transition:enter-end="opacity-100 scale-100"
           class="modal-box max-w-[360px] relative max-h-[90vh] overflow-y-auto">

        <button @click="cerrar()"
                class="absolute top-3.5 right-3.5 text-slate-400 hover:text-red-500 transition-colors text-lg leading-none cursor-pointer">✕</button>

        <div class="text-center mb-5">
          <div class="text-4xl mb-2" x-text="icono"></div>
          <h2 class="text-[15px] font-bold text-slate-800" x-text="titulo"></h2>
          <p x-show="mensaje" x-html="$sanitize(mensaje)"
             class="text-[11.5px] text-slate-500 mt-1.5 leading-snug"></p>
        </div>

        <div class="mb-3">
          <label class="form-label">Usuario</label>
          <input type="text" x-model="usuario" readonly
                 class="form-input bg-slate-50 text-slate-400 font-mono">
        </div>
        <div class="mb-5">
          <label class="form-label">Contraseña</label>
          <input type="password" x-model="pass" placeholder="••••••••"
                 @keydown.enter="confirmar()"
                 class="form-input">
        </div>

        <div class="flex gap-2.5">
          <button @click="cerrar()" :disabled="submitting"
                  class="btn flex-1">Cancelar</button>
          <button @click="confirmar()" :disabled="submitting"
                  class="btn btn-primary flex-1"
                  :class="submitting && 'opacity-60 cursor-not-allowed'">
            <span x-text="submitting ? 'Firmando...' : 'Firmar (Doble Auth)'"></span>
          </button>
        </div>
      </div>
    </div>
  </template>
</div>`

export const AuthModalDevolucionTemplate = /* html */`
<div x-data="authModalData">
  <template x-teleport="body">
    <div x-show="open"
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0"
         x-transition:enter-end="opacity-100"
         x-transition:leave="transition ease-in duration-150"
         x-transition:leave-start="opacity-100"
         x-transition:leave-end="opacity-0"
         class="modal-overlay" 
         style="z-index:9000;display:none;">

      <div @click.stop class="modal-box max-w-[360px] text-center max-h-[90vh] overflow-y-auto">
        <div class="text-4xl mb-2.5">✏️</div>
        <h2 class="text-[15px] font-bold text-slate-800 mb-2">Confirmar Devolución</h2>
        <p class="text-xs text-slate-500 mb-5 leading-relaxed">
          Ingrese sus credenciales corporativas para firmar digitalmente la recepción y destrucción de esta copia física.
        </p>
        <div class="mb-3 text-left">
          <label class="form-label">Usuario Corporativo:</label>
          <input type="text" x-model="usuario" readonly
                 class="form-input bg-slate-50 text-slate-400 font-mono text-center">
        </div>
        <div class="mb-5 text-left">
          <label class="form-label">Contraseña:</label>
          <input type="password" x-model="pass" placeholder="••••••••"
                 @keydown.enter="confirmar()"
                 class="form-input">
        </div>
        <div class="flex gap-2.5">
          <button @click="cerrar()" class="btn flex-1">Cancelar</button>
          <button @click="confirmar()" class="btn btn-primary flex-1">Confirmar y firmar</button>
        </div>
      </div>
    </div>
  </template>
</div>`