import axios from 'axios';
import { useAuthStore } from '../stores/useAuthStore';
import { backend_url } from '../config/config';

const backendApi = axios.create({
  baseURL: backend_url,
});

backendApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      if (error.response.status === 401 && !error.config._retry) {
        const authStore = useAuthStore();
        error.config._retry = true; // Mark request as retried to prevent infinite loops

        // Attempt to refresh the token
        const refreshed = await authStore.refreshAccessToken();
        if (refreshed) {
          // Update the Authorization header with the new access token
          error.config.headers['Authorization'] = `Bearer ${authStore.token}`;
          return backendApi(error.config); // Retry the original request
        } else {
          // Refresh failed, log out
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