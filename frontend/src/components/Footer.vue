<template>
  <footer class="footer">
    <p class="copyright">
      © {{ new Date().getFullYear() }} Badarts — Tout droits réservés.
    </p>
    <p>
      {{
        app_name
          ? (app_name.replace(/_/g, ' ').charAt(0).toUpperCase() + app_name.replace(/_/g, ' ').slice(1))
          : ''
      }}
      v{{ version }} – last update: {{ buildDate }}
    </p>
    <p v-if="authStore.scopes.includes('admin')" class="copyright">
      commit: <a class="footer-link" :href="commitUrl" target="_blank" rel="noopener">{{ commitHash }}</a> ({{
        commitMessage }})
    </p>
    <p v-if="authStore.scopes.includes('admin')" class="copyright">
      <a href="#" class="footer-link" @click.prevent="setTheme(currentTheme === 'geek' ? 'badarts' : 'geek')">
        Switch to {{ currentTheme === 'geek' ? 'Badarts' : 'Geek' }} theme
      </a>
    </p>
  </footer>
</template>

<script setup>
import { useThemeStore } from '../stores/themeStore';
import { useAuthStore } from '../stores/useAuthStore'
const authStore = useAuthStore();
const { currentTheme, setTheme } = useThemeStore();
const version = import.meta.env.VITE_APP_VERSION
const buildDate = import.meta.env.VITE_APP_BUILD_DATE
const commitHash = import.meta.env.VITE_APP_LAST_COMMIT_HASH
const commitMessage = import.meta.env.VITE_APP_LAST_COMMIT_MESSAGE
const githubUrl = import.meta.env.VITE_GITHUB_URL
const commitUrl = `${githubUrl}/commit/${commitHash}`
const app_name = import.meta.env.VITE_APP_NAME
</script>

<style scoped>
.footer {
  margin-top: 50px;
  text-align: center;
  font-size: 0.95rem;
}

.footer-link {
  color: var(--color-link);
  ;
  text-decoration: none;
  font-weight: 600;
}

.footer-link:hover {
  text-decoration: underline;
}

.copyright {
  margin-top: 8px;
  font-size: 0.85rem;
  color: var(--color-accent-bis);
}
</style>
