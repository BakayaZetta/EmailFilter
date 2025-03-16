import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

import path from 'path'
import fs from 'fs'
import dotenv from 'dotenv'

// Try to load environment variables from .env file if it exists
// Otherwise, use process.env variables directly
let envConfig = {}
// try {
  const envPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '.env')
  envConfig = dotenv.parse(fs.readFileSync(envPath))
  console.log('Loaded environment from .env file')
// } catch (error) {
  // console.log('No .env file found, using process.env variables')
// }

// Get values from loaded .env file
const frontendPort = envConfig.FRONTEND_PORT || 5173

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
  ],
  server: {
    port: frontendPort,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // Make environment variables available to the client code
  define: {
    'process.env': {
      VITE_API_URL: '/api'
    }
  }
})
