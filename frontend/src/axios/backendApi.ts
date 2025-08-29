import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';
import { backend_url } from '../config/config';

const backendApi = axios.create({
  baseURL: backend_url,
});

// Intercepteur de requête pour ajouter le token
backendApi.interceptors.request.use(
  async (config) => {
    const authStore = useAuthStore();
    // Attendre que le token soit disponible
    if (!authStore.token || !authStore.isTokenValid(authStore.token)) {
      // Tenter de rafraîchir le token si nécessaire
      const refreshed = await authStore.refreshAccessToken();
      if (!refreshed) {
        console.warn('Aucun token valide disponible pour la requête:', config.url);
      }
    }
    if (authStore.token) {
      config.headers['Authorization'] = `Bearer ${authStore.token}`;
    } else {
      console.warn('Aucun token disponible pour la requête:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur de réponse existant
backendApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      if (error.response.status === 401 && !error.config._retry) {
        const authStore = useAuthStore();
        error.config._retry = true;

        // Tenter de rafraîchir le token
        const refreshed = await authStore.refreshAccessToken();
        if (refreshed) {
          error.config.headers['Authorization'] = `Bearer ${authStore.token}`;
          return backendApi(error.config); // Réessayer la requête
        } else {
          authStore.logout();
          console.error('Échec de la réactualisation du token, déconnexion.');
        }
      }

      if (error.response.status === 400) {
        console.error("Erreur de requête (auth):", error.response.data);
      }

      if (error.response.status === 500) {
        console.error("Erreur serveur (auth):", error.response.data);
      }
    } else {
      console.error("Erreur réseau ou d'URL (auth):", error.message);
      if (error.config) {
        console.error("Requête envoyée vers :", error.config.baseURL + error.config.url);
      }
    }

    return Promise.reject(error);
  }
);

export default backendApi;