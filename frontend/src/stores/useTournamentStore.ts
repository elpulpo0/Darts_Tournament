import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useAuthStore } from '../stores/useAuthStore';
import { handleError } from '../functions/utils';

export const useTournamentStore = defineStore('tournament', () => {
    const tournamentDetail = ref<TournamentFullDetailSchema | null>(null);
    const registeredUsers = ref<User[]>([]);
    const teams = ref<Participant[]>([]);
    const loading = ref(false);

    // Fetch tournament details
    const fetchTournamentDetail = async (tournamentId: number) => {
        loading.value = true;
        try {
            const { data } = await backendApi.get(`/tournaments/${tournamentId}/details`);
            tournamentDetail.value = data;
        } catch (error) {
            console.error('Error fetching tournament details:', error);
            throw error; // Handle errors as needed in your app
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

    // Fetch teams
    const fetchTeams = async (tournamentId: number) => {
        const authStore = useAuthStore();
        try {
            const { data } = await backendApi.get(`/tournaments/${tournamentId}/participants`, {
                headers: { Authorization: `Bearer ${authStore.token}` },
            });
            teams.value = data.filter((p: Participant) => p.type === 'team');
        } catch (err) {
            handleError(err, 'fetching teams');
        }
    };

    // Combine registered users and teams into a single participants array
    const participants = computed<Participant[]>(() => {
        const playerParticipants: Participant[] = registeredUsers.value.map(user => ({
            id: user.id,
            type: 'player' as const,
            name: user.name,
            users: [user],
        }));
        return [...playerParticipants, ...teams.value];
    });

    // Create a map of participants for efficient lookup
    const participantMap = computed(() => {
        const map = new Map<number, Participant>();
        participants.value.forEach(p => map.set(p.id, p));
        return map;
    });

    // Get participant type by ID
    const getParticipantType = (participantId: number | undefined): string => {
        if (!participantId) return 'N/A';
        return participantMap.value.get(participantId)?.type || 'N/A';
    };

    // Get participant users by ID
    const getParticipantUsers = (participantId: number | undefined): User[] | undefined => {
        if (!participantId) return undefined;
        return participantMap.value.get(participantId)?.users;
    };

    return {
        tournamentDetail,
        registeredUsers,
        teams,
        loading,
        fetchTournamentDetail,
        fetchRegisteredUsers,
        fetchTeams,
        participants,
        participantMap,
        getParticipantType,
        getParticipantUsers,
    };
});