import { createApp } from 'vue'
import './styles/theme.css'
import './styles/styles.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia';
import { useThemeStore } from './stores/themeStore'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

const app = createApp(App);

const pinia = createPinia();

app.use(pinia)

app.use(router)

app.use(Toast, {
  position: "bottom-right",
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: "button",
  icon: true,
  rtl: false,
})

const { currentTheme } = useThemeStore()
document.documentElement.setAttribute('data-theme', currentTheme.value)

app.mount('#app')
