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
    build: {
      sourcemap: true,
    },
    define: {
      'import.meta.env.VITE_APP_VERSION': JSON.stringify(packageJson.version),
      'import.meta.env.VITE_APP_BUILD_DATE': JSON.stringify(formattedDate),
      'import.meta.env.VITE_APP_LAST_COMMIT_HASH': JSON.stringify(buildMeta.hash),
      'import.meta.env.VITE_APP_LAST_COMMIT_MESSAGE': JSON.stringify(buildMeta.message),
    },
    base: './',
  }
})
