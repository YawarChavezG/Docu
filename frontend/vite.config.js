import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    host: '0.0.0.0',
    strictPort: true,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '.cofar.com.bo',
    ],
    watch: {
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
