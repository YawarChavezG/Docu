import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: true,
    watch: {
      // Evita que Vite intente watchear node_modules en el contenedor
      ignored: ['**/node_modules/**', '**/dist/**'],
    },
  },
  css: {
    devSourcemap: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: 'hidden',
    target: 'es2020',
    rollupOptions: {
      input: './index.html',
      output: {
        manualChunks: {
          vendor: ['alpinejs', 'dompurify'],
        },
      },
    },
  },
})
