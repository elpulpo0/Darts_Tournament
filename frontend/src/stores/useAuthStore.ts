import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';
import { computed } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  // Utilisation de useStorage pour persister les données dans localStorage
  const token = useStorage<string>('token', '', localStorage);
  const email = useStorage<string>('email', '', localStorage);
  const name = useStorage<string>('name', '', localStorage);
  const userId = useStorage<number | null>('userId', null, localStorage, {
    serializer: {
      read: (v) => (v ? JSON.parse(v) : null),
      write: (v) => JSON.stringify(v),
    },
  });
  const scopes = useStorage<string[]>('scopes', [], localStorage, {
    serializer: {
      read: (v) => (v ? JSON.parse(v) : []),
      write: (v) => JSON.stringify(v),
    },
  });

  // Fonction pour définir les données d'authentification
  const setAuthData = (auth: { token: string; email: string; name: string; userId: number; scopes: string[] }) => {
    token.value = auth.token;
    email.value = auth.email;
    name.value = auth.name;
    userId.value = auth.userId;
    scopes.value = auth.scopes;
  };

  // Fonction pour déconnexion
  const logout = () => {
    token.value = '';
    email.value = '';
    name.value = '';
    userId.value = null;
    scopes.value = [];
  };

  // Computed property pour vérifier si l'utilisateur est authentifié
  const isAuthenticated = computed(() => !!token.value);

  return {
    token,
    email,
    name,
    userId,
    scopes,
    setAuthData,
    logout,
    isAuthenticated,
  };
});