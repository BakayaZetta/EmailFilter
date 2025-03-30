import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'
import fs from 'fs'
import dotenv from 'dotenv'

// Load environment variables safely
let envConfig = {}
try {
  // First try to load from the project's own .env file
  const localEnvPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '.env')
  if (fs.existsSync(localEnvPath)) {
    envConfig = dotenv.parse(fs.readFileSync(localEnvPath))
    console.log('Loaded environment from local .env file')
  } else {
    // Then try the parent directory
    const parentEnvPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../.env')
    if (fs.existsSync(parentEnvPath)) {
      envConfig = dotenv.parse(fs.readFileSync(parentEnvPath))
      console.log('Loaded environment from parent .env file')
    } else {
      console.log('No .env file found, using default values')
    }
  }
} catch (error) {
  console.warn('Error loading .env file:', error.message)
}

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
        target: envConfig.VITE_BACKEND_URL || 'http://localhost:3000',
        changeOrigin: true,
      },
      '/analyse': {
        target: envConfig.VITE_DETECTISH_URL || 'http://localhost:6969',
        changeOrigin: true,
      }
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
