import { apiGet, apiPost, apiPatch, apiDelete, apiDownload } from '../utils/api.js'

export const plantillas = {
  list: () => apiGet('/plantillas-documentales'),
  download: (nombreArchivo) => apiDownload(`/plantillas-documentales/${encodeURIComponent(nombreArchivo)}/download`),
  upload: (file, nombreDisplay, descripcion) => {
    const fd = new FormData()
    fd.append('archivo', file)
    fd.append('nombre_display', nombreDisplay)
    fd.append('descripcion', descripcion)
    return apiPost('/plantillas-documentales/admin/upload', fd)
  },
  rename: (nombreArchivo, nombreDisplay, descripcion) =>
    apiPatch(`/plantillas-documentales/admin/${encodeURIComponent(nombreArchivo)}`, { nombre_display: nombreDisplay, descripcion }),
  eliminar: (nombreArchivo) => apiDelete(`/plantillas-documentales/admin/${encodeURIComponent(nombreArchivo)}`),
}
