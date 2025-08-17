import { isAxiosError } from 'axios';
import { ref } from 'vue';
import { useToast } from 'vue-toastification';

const toast = useToast();

const error = ref('');

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) {
    console.warn('Invalid date:', dateStr);
    return '—';
  }
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

export const handleError = (err: any, context: string) => {
  console.error(`Error while ${context}`, err);

  if (isAxiosError(err)) {
    if (err.response) {
      // Vérification du statut HTTP
      if (err.response?.status === 403) {
        error.value = '⛔ Access denied: administrators or editors only.';
      } else if (err.response.status === 401) {
        error.value = '🔐 Session expired. Please log in again.';
      } else {
        // Accès au message d'erreur renvoyé par l'API
        const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'An unknown error occurred';
        error.value = `An error occurred while ${context}: ${errorMessage}`;
      }
    } else if (err.request) {
      // Si aucune réponse n'a été reçue (erreur réseau par exemple)
      error.value = `Network error while ${context}. Please check your connection.`;
    } else {
      // Si l'erreur est interne à Axios (par exemple une erreur de configuration)
      error.value = `Error while ${context}: ${err.message}`;
    }

    // Affichage du toast avec l'erreur
    toast.error(error.value);
  } else {
    // Si l'erreur n'est pas une erreur Axios, affiche un message générique
    error.value = `An error occurred while ${context}: ${err.message || 'Unknown error'}`;
    toast.error(error.value);
  }
};
