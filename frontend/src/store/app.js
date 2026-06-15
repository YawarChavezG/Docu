/**
 * store/app.js — Estado global de la aplicación
 */
export const appStore = {
  isLoading: false,
  pageTitle: 'COFAR · Sistema de Gestión Documental',

  setLoading(v) {
    this.isLoading = v
  },

  setPageTitle(title) {
    this.pageTitle = title
  },
}
