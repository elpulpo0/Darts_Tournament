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
      if (error.response.status === 401) {
        const authStore = useAuthStore();
        authStore.logout();
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