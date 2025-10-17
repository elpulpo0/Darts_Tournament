<template>
  <footer class="footer">
    <p class="copyright">
      © {{ new Date().getFullYear() }} Hérault Darts Club — Tous droits réservés.
    </p>
    <p class="copyright">Made with ❤️ by El Pulpo for Badarts</p>
    <p v-if="authStore.scopes.includes('admin')" class="copyright">
      <a href="#" class="footer-link"
        @click.prevent="setTheme(themeStore.currentTheme === 'geek' ? 'badarts' : 'geek')">
        Switch to {{ themeStore.currentTheme === 'geek' ? 'Badarts' : 'Geek' }} theme
      </a>
    </p>
  </footer>
</template>

<script setup>
import { useThemeStore } from '../stores/themeStore';
import { useAuthStore } from '../stores/useAuthStore';
import { storeToRefs } from 'pinia';

const authStore = useAuthStore();
const themeStore = useThemeStore();
const { currentTheme } = storeToRefs(themeStore); // Use storeToRefs to maintain reactivity
const { setTheme } = themeStore; // setTheme is a function, so it can be destructured safely
</script>

<style scoped>
.footer {
  margin-top: 50px;
  text-align: center;
  font-size: 0.95rem;
}

.footer-link {
  color: var(--color-link);
  text-decoration: none;
  font-weight: 600;
}

.footer-link:hover {
  text-decoration: underline;
  color: var(--color-link-hover);
}

.copyright {
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--color-accent-bis);
}
</style>