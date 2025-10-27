import { ViteSSG } from 'vite-ssg'
import './styles/theme.css'
import './styles/styles.css'
import './styles/shop.css'
import App from './App.vue'
import { routes } from './router'
import { createPinia } from 'pinia'
import { useThemeStore } from './stores/themeStore'
import Vue3Toastify from 'vue3-toastify'
import 'vue3-toastify/dist/index.css'
import { watch } from 'vue'

export const createApp = ViteSSG(
  App,
  { routes },
  ({ app, router }) => {
    const pinia = createPinia()
    app.use(pinia)
    app.use(router)
    app.use(Vue3Toastify, {
      position: 'bottom-right',
      timeout: 3000,
      closeOnClick: true,
      pauseOnFocusLoss: true,
      pauseOnHover: true,
      draggable: true,
      draggablePercent: 0.6,
      showCloseButtonOnHover: false,
      hideProgressBar: false,
      closeButton: 'button',
      icon: true,
      rtl: false,
    })

    const themeStore = useThemeStore()

    watch(
      () => themeStore.currentTheme,
      (newTheme) => {
        document.documentElement.setAttribute('data-theme', newTheme)
      }
    )
  },
)