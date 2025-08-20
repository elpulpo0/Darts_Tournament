import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';
import { computed, ref } from 'vue';
import backendApi from '../axios/backendApi';

export const useAuthStore = defineStore('auth', () => {
  const scopes = useStorage<string[]>('scopes', [], localStorage, {
    serializer: {
      read: (v) => (v ? JSON.parse(v) : []),
      write: (v) => JSON.stringify(v),
    },
  });
  const token = useStorage<string>('token', '');
  const refreshToken = useStorage<string>('refreshToken', '');
  const email = useStorage<string>('email', '');
  const name = useStorage<string>('name', '');
  const userId = useStorage<number | null>('userId', null, localStorage, {
    serializer: {
      read: (v) => (v ? JSON.parse(v) : null),
      write: (v) => JSON.stringify(v),
    },
  });

  const setAuthData = (auth: {
    token: string;
    refreshToken?: string;
    email: string;
    name: string;
    userId?: number;
    scopes: string[];
  }) => {
    token.value = auth.token;
    if (auth.refreshToken) refreshToken.value = auth.refreshToken;
    email.value = auth.email;
    name.value = auth.name;
    userId.value = auth.userId;
    scopes.value = auth.scopes;
  };

  const logout = () => {
    token.value = '';
    refreshToken.value = '';
    email.value = '';
    name.value = '';
    scopes.value = [];
  };

  const isAuthenticated = computed(() => {
    return !!token.value;
  });

  const proxyAuthToken = ref<string | null>(null);

  const setAuthToken = (token: string | null) => {
    proxyAuthToken.value = token;
  };

  const isTokenValid = (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiration = payload.exp * 1000;
      return Date.now() < expiration;
    } catch (error) {
      console.error('Erreur lors de la validation du token:', error);
      return false;
    }
  };

  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      console.error('No refresh token available');
      logout(); // Log out if no refresh token
      return false;
    }

    try {
      const response = await backendApi.post('/auth/refresh', {}, {
        headers: { Authorization: `Bearer ${refreshToken.value}` }
      });

      if (response.status === 200 && response.data.access_token) {
        setAuthData({
          token: response.data.access_token,
          refreshToken: response.data.refresh_token,
          email: email.value,
          name: name.value,
          scopes: scopes.value
        });
        return true; // Refresh successful
      } else {
        throw new Error('Invalid refresh response');
      }
    } catch (error) {
      console.error('Refresh token failed:', error);
      logout(); // Log out on refresh failure
      return false;
    }
  };

  return {
    token,
    refreshToken,
    email,
    name,
    userId,
    scopes,
    setAuthData,
    logout,
    isAuthenticated,
    proxyAuthToken,
    setAuthToken,
    isTokenValid,
    refreshAccessToken
  };
});