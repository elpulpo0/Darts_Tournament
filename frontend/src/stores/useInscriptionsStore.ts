import { defineStore } from 'pinia';
import { ref } from 'vue';
import backendApi from '../axios/backendApi';
import { handleError } from '../functions/utils';

export const useInscriptionsStore = defineStore('inscriptions', () => {
    const activeInscriptions = ref<InscriptionResponse[]>([]);
    const loading = ref(false);
    const error = ref('');

    const fetchActiveInscriptions = async (token: string) => {
        loading.value = true;
        error.value = '';
        try {
            const { data } = await backendApi.get('/inscriptions/active', {
                headers: { Authorization: `Bearer ${token}` },
            });
            activeInscriptions.value = data;
        } catch (err) {
            handleError(err, 'fetching active inscriptions');
            error.value = 'Échec du chargement des inscriptions actives.';
        } finally {
            loading.value = false;
        }
    };

    return {
        activeInscriptions,
        loading,
        error,
        fetchActiveInscriptions
    };
});