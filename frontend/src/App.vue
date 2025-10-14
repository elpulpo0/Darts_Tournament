<script setup lang="ts">
import Auth from './components/Auth.vue';
import Footer from './components/Footer.vue';
import { useAuthStore } from './stores/useAuthStore';
import { ref } from 'vue';

const showDropdown = ref(false);

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value;
};

const closeDropdown = () => {
  showDropdown.value = false;
};

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
            <router-link to="/tournaments" class="nav-link">Tournois Badarts</router-link>
          </li>
          <li v-if="authStore.isAuthenticated">
            <router-link to="/calendar" class="nav-link">Calendrier LSEF/CMER</router-link>
          </li>
          <!-- Dropdown pour Classement -->
          <li v-if="authStore.isAuthenticated" class="dropdown">
            <a href="#" class="nav-link dropdown-toggle" @click.prevent="toggleDropdown">Classements</a>
            <ul v-show="showDropdown" class="dropdown-menu">
              <li>
                <router-link to="/leaderboard/club" class="dropdown-item" @click="closeDropdown">Classement des
                  tournois locaux</router-link>
              </li>
              <li>
                <router-link to="/leaderboard/ligue" class="dropdown-item" @click="closeDropdown">Classement de la
                  Ligue</router-link>
              </li>
              <li>
                <router-link to="/leaderboard/comite" class="dropdown-item" @click="closeDropdown">Classement du
                  Comité</router-link>
              </li>
            </ul>
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

/* Dropdown styles */
.dropdown {
  position: relative;
}

.dropdown-toggle {
  cursor: pointer;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--color-bg);
  /* Adaptez à votre thème */
  border: 1px solid var(--color-light-shadow);
  border-radius: var(--radius);
  list-style: none;
  padding: 10px 0;
  margin: 0;
  min-width: 200px;
  z-index: 1000;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.dropdown-item {
  display: block;
  padding: 10px 20px;
  text-decoration: none;
  color: var(--color-fg);
  transition: background 0.3s;
}

.dropdown-item:hover {
  background: var(--color-success);
}

/* Mobile adjustments */
@media (max-width: 768px) {
  .dropdown-menu {
    position: static;
    /* Pour un affichage stacké sur mobile */
    border: none;
    box-shadow: none;
    padding-left: 20px;
    /* Indentation pour sous-menus */
  }
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