<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import backendApi from '../axios/backendApi';
import axios from 'axios';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';

const authStore = useAuthStore();
const toast = useToast();
const route = useRoute();

const tokenCheckInterval = ref<number | null>(null);

interface User {
  email: string;
  name: string;
  password: string;
  role: string;
}

const email = ref('');
const name = ref('');
const password = ref('');
const confirmPassword = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const user = ref<User | null>(null);
const isRegistering = ref(false);
const showEditForm = ref(false);
const newName = ref('');
const newEmail = ref('');
const newPassword = ref('');

let isFetchingUser = false;

function isTokenExpired(token: string): boolean {
  return !authStore.isTokenValid(token);
}

function checkToken() {
  tokenCheckInterval.value = setInterval(async () => {
    if (authStore.token && !isFetchingUser) {
      if (isTokenExpired(authStore.token)) {
        handleLogout();
      }
    }
  }, 30000); // Check every 30 seconds
}

function resetMessages() {
  errorMessage.value = '';
  successMessage.value = '';
}

// Client-side validation for the name field
function validateName(name: string): string | null {
  if (!name.trim()) {
    return 'Le nom est requis.';
  }
  if (name.length < 3 || name.length > 20) {
    return 'Le nom doit contenir entre 3 et 20 caractères.';
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
    return 'Le nom ne peut contenir que des lettres, chiffres, tirets ou underscores.';
  }
  return null;
}

const login = async () => {
  resetMessages();
  try {
    const response = await backendApi.post(
      `/auth/login`,
      new URLSearchParams({
        username: email.value,
        password: password.value,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    if (response.status === 200 && response.data.access_token) {
      authStore.setAuthData({
        token: response.data.access_token,
        refreshToken: response.data.refresh_token,
        email: email.value,
        name: '',
        userId: response.data.id,
        scopes: [],
      });

      await fetchUser();
      resetMessages();
    } else {
      throw new Error("Token manquant ou statut inattendu");
    }
  } catch (error) {
    console.error(error);
    errorMessage.value = "Échec de la connexion. Vérifiez vos identifiants.";
    toast.error(errorMessage.value);
  }
};

const register = async () => {
  resetMessages();
  try {
    // Client-side validation
    const nameError = validateName(name.value);
    if (nameError) {
      errorMessage.value = nameError;
      toast.error(errorMessage.value);
      return;
    }

    if (!email.value.includes('@')) {
      errorMessage.value = "L'email saisi n'est pas valide.";
      toast.error(errorMessage.value);
      return;
    }

    if (password.value !== confirmPassword.value) {
      errorMessage.value = "Les mots de passe ne correspondent pas.";
      toast.error(errorMessage.value);
      return;
    }

    if (password.value.length < 6) {
      errorMessage.value = "Le mot de passe doit contenir au moins 6 caractères.";
      toast.error(errorMessage.value);
      return;
    }

    const response = await backendApi.post(
      `/users/users/`,
      {
        email: email.value,
        name: name.value,
        password: password.value,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (response.status === 201) {
      errorMessage.value = '';
      successMessage.value = 'Inscription réussie, vous pouvez maintenant vous connecter.';
      toast.success(successMessage.value);
      email.value = '';
      name.value = '';
      password.value = '';
      confirmPassword.value = '';
      isRegistering.value = false;
    }
  } catch (error: unknown) {
    console.error(error);

    if (axios.isAxiosError(error) && error.response?.status === 400) {
      const detail = error.response.data.detail;
      if (detail === 'A user with this name already exists.') {
        errorMessage.value = 'Ce nom est déjà utilisé. Veuillez en choisir un autre.';
      } else if (detail === 'A user with this email already exists.') {
        errorMessage.value = 'Cet email est déjà utilisé. Veuillez en choisir un autre.';
      } else {
        errorMessage.value = detail || 'Échec de la création du compte. Vérifiez les informations.';
      }
    } else {
      errorMessage.value = 'Une erreur s\'est produite, veuillez réessayer plus tard.';
    }
    toast.error(errorMessage.value);
  }
};

const updateProfile = async () => {
  resetMessages();

  if (!newName.value.trim() && !newEmail.value.trim() && !newPassword.value.trim()) {
    errorMessage.value = 'Veuillez remplir au moins un champ pour mettre à jour votre profil.';
    toast.error(errorMessage.value);
    return;
  }

  // Validate new name if provided
  if (newName.value.trim()) {
    const nameError = validateName(newName.value);
    if (nameError) {
      errorMessage.value = nameError;
      toast.error(errorMessage.value);
      return;
    }
  }

  if (newPassword.value && newPassword.value !== confirmPassword.value) {
    errorMessage.value = "Les mots de passe ne correspondent pas.";
    toast.error(errorMessage.value);
    return;
  }

  if (newPassword.value && newPassword.value.length < 6) {
    errorMessage.value = "Le mot de passe doit contenir au moins 6 caractères.";
    toast.error(errorMessage.value);
    return;
  }

  if (newEmail.value && !newEmail.value.includes('@')) {
    errorMessage.value = "L'email saisi n'est pas valide.";
    toast.error(errorMessage.value);
    return;
  }

  const payload: Record<string, string> = {};

  if (newName.value.trim()) payload.name = newName.value;
  if (newEmail.value.trim()) payload.email = newEmail.value;
  if (newPassword.value.trim()) payload.password = newPassword.value;

  try {
    await backendApi.patch(`/users/users/me`, payload, {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      }
    });

    successMessage.value = 'Profil mis à jour avec succès.';
    toast.success(successMessage.value);
    errorMessage.value = '';
    newEmail.value = '';
    newName.value = '';
    newPassword.value = '';
    confirmPassword.value = '';
    await fetchUser();
  } catch (error) {
    console.error('Update profile error:', error);
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      errorMessage.value = "Session expirée";
    } else if (axios.isAxiosError(error) && error.response?.status === 400) {
      const detail = error.response.data.detail;
      if (detail === 'A user with this name already exists.') {
        errorMessage.value = 'Ce nom est déjà utilisé. Veuillez en choisir un autre.';
      } else if (detail === 'A user with this email already exists.') {
        errorMessage.value = 'Cet email est déjà utilisé. Veuillez en choisir un autre.';
      } else {
        errorMessage.value = detail || 'Échec de la mise à jour du profil. Vérifiez les informations.';
      }
    } else {
      errorMessage.value = "Une erreur est survenue lors de la mise à jour. Veuillez réessayer.";
    }
    toast.error(errorMessage.value);
  }
};

const fetchUser = async () => {
  if (isFetchingUser || !authStore.isAuthenticated) {
    return;
  }
  isFetchingUser = true;
  try {
    const response = await backendApi.get(`/users/users/me`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    });

    authStore.setAuthData({
      token: authStore.token,
      refreshToken: authStore.refreshToken,
      email: authStore.email,
      name: response.data.name,
      scopes: response.data.scopes || []
    });

    user.value = {
      email: authStore.email,
      password: '',
      name: response.data.name.charAt(0).toUpperCase() + response.data.name.slice(1),
      role: response.data.role
    };
  } catch (error) {
    console.error('Fetch user error:', error);
    errorMessage.value = "Session expirée";
    handleLogout();
  } finally {
    isFetchingUser = false;
  }
};

const handleLogout = () => {
  authStore.logout();
  user.value = null;
  resetMessages();
};

onMounted(() => {
  checkToken();
});

onUnmounted(() => {
  if (tokenCheckInterval.value) {
    clearInterval(tokenCheckInterval.value);
    tokenCheckInterval.value = null;
  }
});

// Watch route changes for page navigation
watch(() => route.path, async () => {
  if (authStore.token && !isFetchingUser) {
    await fetchUser();
  }
  if (authStore.token && tokenCheckInterval.value) {
    clearInterval(tokenCheckInterval.value);
    tokenCheckInterval.value = null;
    checkToken();
  }
});

// Watch token changes
watch(() => authStore.token, async (newToken) => {
  if (isFetchingUser) {
    return;
  }
  if (!newToken) {
    handleLogout();
  } else if (isTokenExpired(newToken) && authStore.refreshToken) {
    await fetchUser();
  } else {
    await fetchUser();
  }
}, { immediate: true });
</script>

<template>
  <div :class="['auth-container', { 'wide': showEditForm }]">
    <div v-if="!authStore.isAuthenticated" class="auth-form">
      <h2 v-if="!isRegistering">Connexion</h2>
      <h2 v-else>Créer un compte</h2>

      <form v-if="!isRegistering" @submit.prevent="login" :key="'login-form'">
        <input id="email" v-model="email" type="email" placeholder="Email" autocomplete="username" class="input-auth" />
        <input id="password" v-model="password" type="password" placeholder="Mot de passe"
          autocomplete="current-password" class="input-auth" />
        <button type="submit">Se connecter</button>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <p v-if="successMessage" class="success">{{ successMessage }}</p>
        <p>Vous n'avez pas de compte ? <a href="#" @click="isRegistering = true; resetMessages()">Créer un compte</a>
        </p>
      </form>

      <form v-else @submit.prevent="register" :key="'register-form'">
        <input v-model="email" type="email" placeholder="Email" class="input-auth" />
        <input v-model="name" type="text" placeholder="Nom" class="input-auth" />
        <input v-model="password" type="password" placeholder="Mot de passe" autocomplete="new-password"
          class="input-auth" />
        <input v-model="confirmPassword" type="password" placeholder="Confirmer le mot de passe"
          autocomplete="new-password" class="input-auth" />
        <button type="submit">Créer un compte</button>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <p v-if="successMessage" class="success">{{ successMessage }}</p>
        <p>Vous avez déjà un compte ? <a href="#" @click="isRegistering = false; resetMessages()">Se connecter</a></p>
      </form>
    </div>

    <div v-else class="user-info">
      <h2>Bienvenue {{ user?.name }}</h2>
      <button @click="showEditForm = !showEditForm; resetMessages()">
        {{ showEditForm ? 'Annuler' : 'Voir / Modifier mon profil' }}
      </button>

      <div v-if="showEditForm" class="edit-form">
        <div class="user-details">
          <p><strong>Nom :</strong> {{ user?.name }}</p>
          <p><strong>Email :</strong> {{ user?.email }}</p>
        </div>

        <div>
          <h2>Modifier mes informations</h2>
          <form class="form-grid">
            <label for="newName">Nom</label>
            <input id="newName" v-model="newName" type="text" placeholder="Nom" autocomplete="name"
              class="input-auth" />

            <label for="newEmail">Email</label>
            <input id="newEmail" v-model="newEmail" type="email" placeholder="Email" autocomplete="email"
              class="input-auth" />

            <label for="newPassword">Mot de passe</label>
            <input id="newPassword" v-model="newPassword" type="password" placeholder="Mot de passe"
              autocomplete="new-password" class="input-auth" />

            <label for="confirmPassword">Confirmer le mot de passe</label>
            <input id="confirmPassword" v-model="confirmPassword" type="password"
              placeholder="Confirmer le mot de passe" autocomplete="new-password" class="input-auth" />
          </form>

          <button @click.prevent="updateProfile">Enregistrer les modifications</button>

          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <p v-if="successMessage" class="success">{{ successMessage }}</p>
        </div>
      </div>
      <button @click="handleLogout">Se déconnecter</button>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  width: 100%;
  max-width: 400px;
  padding: 30px;
  border: 1px solid var(--color-main);
  background-color: var(--color-bg);
  color: var(--color-main);
  border-radius: var(--radius);
}

h2 {
  text-align: center;
  margin-bottom: 24px;
  color: var(--color-main);
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
  align-items: center;
}

.form-grid label {
  text-align: right;
  padding-right: 8px;
  color: var(--color-main);
}

.form-grid input {
  width: 100%;
}

.input-auth {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-main);
  background-color: var(--color-bg);
  color: var(--color-main);
}

.input-auth:focus {
  outline: none;
  border-color: var(--color-main);
  background-color: var(--color-bg);
}

button {
  padding: 12px;
  background-color: var(--color-main);
  color: var(--color-bg);
  border: 1px solid var(--color-main);
  font-size: 15px;
  cursor: pointer;
  font-weight: bold;
  width: 100%;
}

button:hover {
  background-color: var(--color-success);
}

p {
  text-align: center;
  font-size: 14px;
  margin: 0;
}

p.error {
  color: var(--color-error);
  font-weight: bold;
}

p.success {
  color: var(--color-success);
  font-weight: bold;
}

a {
  color: var(--color-main);
  text-decoration: none;
  font-weight: bold;
}

a:hover {
  text-decoration: underline;
}

.user-info {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.edit-form {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-container.wide {
  max-width: 800px;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  gap: 24px;
  background-color: var(--color-bg);
}
</style>
