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
            <router-link to="/home" class="nav-link">Accueil</router-link>
          </li>
          <li v-if="authStore.isAuthenticated">
            <router-link to="/tournaments" class="nav-link">Tournois</router-link>
          </li>
          <li v-if="authStore.isAuthenticated">
            <router-link to="/leaderboard" class="nav-link">Classement</router-link>
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
/* Header layout */
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
  /* Default size for desktop */
  margin-bottom: 20px;
  /* Reduced for better spacing */
}

/* Navigation links */
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

/* Mobile responsiveness */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    /* Stack elements vertically */
    align-items: center;
    /* Center all content */
    padding: 10px;
    /* Reduce padding for mobile */
  }

  .left-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    /* Center logo and nav links */
    width: 100%;
    /* Ensure full width */
  }

  .logo {
    height: 100px;
    /* Smaller logo size for mobile */
    margin-bottom: 10px;
    /* Adjust spacing */
  }

  .nav-links {
    flex-direction: column;
    /* Stack nav links vertically */
    align-items: center;
    gap: 15px;
    /* Smaller gap for mobile */
  }

  /* Ensure Auth component is centered and full-width */
  .auth-container {
    width: 100%;
    max-width: 300px;
    /* Slightly smaller than desktop */
    margin-top: 10px;
    /* Space above login section */
  }
}
</style>