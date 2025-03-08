import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

import path from 'path'
import fs from 'fs'
import dotenv from 'dotenv'

// Manually load the .env file located one level above
const envPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../.env')
const envConfig = dotenv.parse(fs.readFileSync(envPath))

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
  ],
  server: {
    // Use the FRONTEND_PORT environment variable from .env file
    port: envConfig.FRONTEND_PORT || 5173, // Default port if variable not defined
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }

    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
