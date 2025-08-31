import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useAuthStore } from './useAuthStore';
import { handleError } from '../functions/utils';

export const useTournamentStore = defineStore('tournament', () => {
    const tournament = ref<Tournament | null>(null);
    const tournamentDetail = ref<TournamentFullDetailSchema | null>(null);
    const registeredUsers = ref<User[]>([]);
    const participants = ref<Participant[]>([]);
    const loading = ref(false);

    // Fetch tournament details
    const fetchTournamentDetail = async (tournamentId: number) => {
        loading.value = true;
        try {
            const { data } = await backendApi.get(`/tournaments/${tournamentId}/details`);
            tournamentDetail.value = data;
        } catch (error) {
            console.error('Error fetching tournament details:', error);
            throw error;
        } finally {
            loading.value = false;
        }
    };

    // Fetch registered users
    const fetchRegisteredUsers = async (tournamentId: number) => {
        try {
            const { data } = await backendApi.get(`/tournaments/${tournamentId}/registered-users`);
            registeredUsers.value = data;
        } catch (error) {
            console.error('Error fetching registered users:', error);
            throw error;
        }
    };

    // Fetch participants
    const fetchParticipants = async (tournamentId: number) => {
        const authStore = useAuthStore();
        try {
            const { data } = await backendApi.get(`/tournaments/${tournamentId}/participants`, {
                headers: { Authorization: `Bearer ${authStore.token}` },
            });
            participants.value = data;
        } catch (err) {
            handleError(err, 'fetching participants');
        }
    };

    // Create a map of participants for efficient lookup
    const participantMap = computed(() => {
        const map = new Map<number, Participant>();
        participants.value.forEach(p => map.set(p.id, p));
        return map;
    });

    // Get participant users by ID
    const getParticipantUsers = (participantId: number | undefined): User[] | undefined => {
        if (!participantId) return undefined;
        return participantMap.value.get(participantId)?.users;
    };

    return {
        tournament,
        tournamentDetail,
        registeredUsers,
        participants,
        loading,
        fetchTournamentDetail,
        fetchRegisteredUsers,
        fetchParticipants,
        participantMap,
        getParticipantUsers,
    };
});