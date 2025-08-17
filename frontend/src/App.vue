<script setup lang="ts">
import Auth from './components/Auth.vue';
import Footer from './components/Footer.vue';
import { useAuthStore } from './stores/useAuthStore';

const authStore = useAuthStore();
</script>

<template>
  <div>
    <header class="header">
      <div class="left-section">
        <img src="./assets/logo.png" alt="Logo" class="logo" />
        <ul class="nav-links">
          <!-- Liens accessibles à tous les utilisateurs authentifiés -->
          <li v-if="authStore.isAuthenticated">
            <router-link to="/tournaments" class="nav-link">Tournois</router-link>
          </li>
          <li v-if="authStore.isAuthenticated">
            <router-link to="/leaderboard" class="nav-link">Classement
            </router-link>
          </li>
          <!-- Liens réservés aux admins -->
          <li v-if="authStore.scopes.includes('admin')">
            <router-link to="/users" class="nav-link">Users</router-link>
          </li>
          <li v-if="authStore.scopes.includes('admin')">
            <router-link to="/database" class="nav-link">Database</router-link>
          </li>
          <li v-if="authStore.scopes.includes('admin')">
            <router-link to="/logs" class="nav-link">Logs</router-link>
          </li>
        </ul>
      </div>

      <Auth />
    </header>

    <!-- Affichage du contenu des routes -->
    <router-view></router-view>

    <Footer />
  </div>
</template>

<style scoped>
/* Header façon terminal */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  color: var(--color-fg);
}

/* Logo */
.logo {
  height: 250px;
  margin-bottom: 50px;
}

/* Liens de navigation façon terminal */
.nav-links {
  display: flex;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: 25px;
}

.nav-link {
  text-decoration: none;
  color: var(--color-accent);
  font-size: 16px;
  transition: color 0.3s;
}

.nav-link:hover {
  color: var(--color-success);
}
</style>