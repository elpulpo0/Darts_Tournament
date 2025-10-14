import { defineStore } from 'pinia';
import { ref } from 'vue';
import backendApi from '../axios/backendApi';
import { useAuthStore } from './useAuthStore';
import { handleError } from '../functions/utils';

export const useEventStore = defineStore('event', () => {
    const event = ref<OfficialEvent | null>(null);
    const events = ref<OfficialEvent[]>([]);
    const registeredUsers = ref<User[]>([]);
    const participants = ref<Participant[]>([]);
    const loading = ref(false);

    const fetchEvents = async () => {
        const authStore = useAuthStore();
        loading.value = true;
        try {
            const { data } = await backendApi.get('/events/', {
                headers: { Authorization: `Bearer ${authStore.token}` },
            });
            events.value = data;
        } catch (err) {
            handleError(err, 'récupération des events');
        } finally {
            loading.value = false;
        }
    };

    const fetchEventDetail = async (eventId: number) => {
        loading.value = true;
        try {
            const { data } = await backendApi.get(`/events/${eventId}`);
            event.value = data;
        } catch (error) {
            console.error('Error fetching event details:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    return {
        event,
        events,
        registeredUsers,
        participants,
        loading,
        fetchEvents,
        fetchEventDetail,
    };
});