import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  const packageJson = JSON.parse(readFileSync('./package.json', 'utf-8'))

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]
  const now = new Date()
  const formattedDate = `${String(now.getDate()).padStart(2, '0')} ${months[now.getMonth()]} ${now.getFullYear()}`

  let buildMeta = { hash: 'unknown', message: 'message unavailable' }
  try {
    const buildMetaPath = resolve(__dirname, 'build-meta.json')
    const raw = readFileSync(buildMetaPath, 'utf-8')
    buildMeta = JSON.parse(raw)
  } catch (e) {
    console.warn('⚠️ No build-meta.json file found, using default values.')
  }

  return {
    server: {
      port: parseInt(env.VITE_PORT) || 5173,
    },
    plugins: [vue()],
    ssgOptions: {
      script: 'async',
      formatting: 'minify',
      includedRoutes(paths, routes) {
        return ['/', '/home']
      },
      vite: {
        ssr: {
          external: ['@vue/devtools-kit', '@vue/devtools-api']
        }
      },
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    build: {
      sourcemap: true,
    },
    base: '/',
  }
})