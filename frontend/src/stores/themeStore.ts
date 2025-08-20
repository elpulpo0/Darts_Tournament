import { defineStore } from 'pinia';
import { ref } from 'vue';

type Theme = 'geek' | 'badarts';

export const useThemeStore = defineStore('theme', () => {
  // Initialize theme from localStorage or default to 'badarts'
  const currentTheme = ref<Theme>(
    (localStorage.getItem('theme') as Theme) || 'badarts'
  );

  // Function to set the theme
  const setTheme = (theme: Theme) => {
    currentTheme.value = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  };

  // Initialize theme immediately
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme && ['geek', 'badarts'].includes(savedTheme)) {
    setTheme(savedTheme as Theme);
  } else {
    setTheme('badarts'); // Default theme
  }

  return { currentTheme, setTheme };
});