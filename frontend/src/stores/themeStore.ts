import { ref } from 'vue'

const currentTheme = ref<'geek' | 'badarts'>(localStorage.getItem('theme') as 'geek' | 'badarts' || 'geek')

export function useThemeStore() {
  const setTheme = (theme: 'geek' | 'badarts') => {
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }

  return {
    currentTheme,
    setTheme
  }
}
