<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="loading">Chargement des tournois...</div>

        <div v-if="tournaments.length" class="module">
            <h2>Tournois</h2>
            <div class="tournament-tiles">
                <div v-for="tournament in tournaments" class="tile"
                    :class="{ 'selected': selectedTournament?.id === tournament.id }"
                    @click="selectTournament(tournament)" :key="tournament.id">
                    <h3>{{ tournament.name }}</h3>
                    <p>
                        {{
                            tournament.status === "open"
                                ? "Inscriptions ouvertes"
                                : tournament.status === "closed"
                                    ? "Tournoi terminé"
                                    : tournament.status === "running"
                                        ? "Tournoi en cours"
                                        : ""
                        }}
                    </p>
                    <p>Mode: {{ tournament.mode || 'Non défini' }}</p>
                    <p>Date : {{ formatDate(tournament.start_date) }}</p>
                </div>
            </div>

            <div v-if="selectedTournament" class="tournament-details">
                <p>{{ selectedTournament.description || 'Aucune description' }}</p>

                <button v-if="isEditor"
                    @click="router.push({ name: 'TournamentManagement', params: { tournamentId: selectedTournament.id } })">
                    Gérer le tournoi
                </button>

                <!-- Register or Unregister button -->
                <div v-if="selectedTournament.status === 'open'">
                    <div v-if="!registrationStatus[selectedTournament.id]">
                        <button @click="registerToTournament(selectedTournament.id)">S’inscrire</button>
                    </div>
                    <div v-else>
                        <button @click="unregisterFromTournament(selectedTournament.id)">Se désinscrire</button>
                        <p>Vous êtes déjà inscrit à ce tournoi.</p>
                    </div>
                </div>
                <div v-else>
                    <p>Les inscriptions sont closes pour ce tournoi.</p>
                </div>

                <!-- Affichage participants (players/teams) -->
                <h4>Participants</h4>
                <ul v-if="participants[selectedTournament.id]?.length">
                    <li v-for="participant in participants[selectedTournament.id]" :key="participant.id">
                        {{ participant.name }} ({{ participant.type }})
                        <span v-if="participant.type === 'team'"> - {{participant.users.map(u => u.name).join(' & ')
                            }}</span>
                    </li>
                </ul>
                <p v-else>Aucun participant.</p>

                <button v-if="selectedTournament && ['running', 'closed'].includes(selectedTournament.status)"
                    @click="openProjection">
                    Projeter l’arborescence
                </button>
            </div>
        </div>

        <div v-else class="module">
            <p>Aucun tournoi disponible.</p>
        </div>

        <button v-if="isEditor" @click="toggleCreateTournamentForm">
            {{ showCreateTournament ? 'Annuler' : 'Ajouter un tournoi' }}
        </button>
        <div v-if="showCreateTournament" class="module">
            <h3>Ajouter un tournoi</h3>
            <input v-model="newTournamentName" placeholder="Nom" class="form-input" />
            <input v-model="newTournamentDescription" placeholder="Description" class="form-input" />
            <input v-model="newTournamentStartDate" type="datetime-local" class="form-input" />
            <select v-model="newTournamentMode" class="form-input">
                <option value="single">Single (Joueurs individuels)</option>
                <option value="double">Double (Équipes de 2)</option>
            </select>
            <button @click="createTournament">Ajouter</button>
        </div>
    </div>

    <div v-if="!authStore.isAuthenticated" class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour voir les informations des tournois.</p>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { useRouter } from 'vue-router';
import { handleError } from '../functions/utils';

const authStore = useAuthStore();
const toast = useToast();
const router = useRouter();

const tournaments = ref<Tournament[]>([]);
const selectedTournament = ref<Tournament | null>(null);
const loading = ref(false);
const showCreateTournament = ref(false);
const newTournamentName = ref('');
const newTournamentDescription = ref('');
const newTournamentStartDate = ref('');
const newTournamentMode = ref<'single' | 'double'>('single'); // Nouveau champ pour le mode
const registrationStatus = ref<{ [key: number]: boolean }>({});
const participants = ref<{ [key: number]: Participant[] }>({});
const matches = ref<{ [key: number]: Match[] }>({});

const isEditor = computed(() => authStore.scopes.includes('editor') || authStore.scopes.includes('admin'));

const toggleCreateTournamentForm = () => {
    showCreateTournament.value = !showCreateTournament.value;
    if (!showCreateTournament.value) {
        newTournamentName.value = '';
        newTournamentDescription.value = '';
        newTournamentStartDate.value = '';
        newTournamentMode.value = 'single';
    }
};

const formatDate = (date: string) => new Date(date).toLocaleString();

const createTournament = async () => {
    if (!newTournamentName.value || !newTournamentStartDate.value) {
        toast.error('Le nom et la date de début sont requis.');
        return;
    }
    const tournamentData = {
        name: newTournamentName.value,
        description: newTournamentDescription.value || null,
        start_date: new Date(newTournamentStartDate.value).toISOString(),
        is_active: true,
        status: 'open',
        mode: newTournamentMode.value, // Ajout du mode
    };
    try {
        await backendApi.post('/tournaments/', tournamentData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Tournoi créé.');
        fetchTournaments();
        toggleCreateTournamentForm();
    } catch (err) {
        handleError(err, 'création du tournoi');
    }
};

const fetchTournaments = async () => {
    loading.value = true;
    try {
        const { data } = await backendApi.get('/tournaments/', {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        tournaments.value = data;
        for (const tournament of tournaments.value) {
            if (tournament.status === 'open') {
                registrationStatus.value[tournament.id] = await checkIfUserRegistered(tournament.id);
            }
            participants.value[tournament.id] = await fetchParticipants(tournament.id);
            matches.value[tournament.id] = await fetchMatches(tournament.id);
        }
    } catch (err) {
        handleError(err, 'récupération des tournois');
    } finally {
        loading.value = false;
    }
};

const fetchParticipants = async (tournamentId: number): Promise<Participant[]> => {
    try {
        const { data } = await backendApi.get(`/tournaments/${tournamentId}/participants`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        return data;
    } catch (err) {
        handleError(err, 'récupération des participants');
        return [];
    }
};

const registerToTournament = async (tournamentId: number) => {
    const playerData = {
        user_id: authStore.userId,
        tournament_id: tournamentId,
    };
    try {
        await backendApi.post(
            '/tournaments/registrations/', playerData,
            { headers: { Authorization: `Bearer ${authStore.token}` } }
        );
        toast.success('Inscription au tournoi réussie.');
        registrationStatus.value[tournamentId] = true;
        participants.value[tournamentId] = await fetchParticipants(tournamentId);
    } catch (err) {
        handleError(err, 'inscription au tournoi');
    }
};

const checkIfUserRegistered = async (tournamentId: number): Promise<boolean> => {
    try {
        const { data } = await backendApi.get(`/tournaments/${tournamentId}/my-registration`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        return data;
    } catch (err: any) {
        if (err.response?.status === 401) {
            toast.error('Veuillez vous connecter pour vérifier l’état de l’inscription.');
        } else {
            handleError(err, 'vérification de l’état de l’inscription');
        }
        return false;
    }
};

const unregisterFromTournament = async (tournamentId: number) => {
    try {
        await backendApi.delete(
            `/tournaments/registrations/${tournamentId}`,
            { headers: { Authorization: `Bearer ${authStore.token}` } }
        );
        toast.success('Désinscription du tournoi réussie.');
        registrationStatus.value[tournamentId] = false;
        participants.value[tournamentId] = await fetchParticipants(tournamentId);
    } catch (err) {
        handleError(err, 'désinscription du tournoi');
    }
};

const fetchMatches = async (tournamentId: number): Promise<Match[]> => {
    try {
        const { data } = await backendApi.get(`/tournaments/matches/tournament/${tournamentId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        return data;
    } catch (err) {
        handleError(err, 'récupération des matchs');
        return [];
    }
};

const selectTournament = async (tournament: Tournament) => {
    selectedTournament.value = tournament;
    participants.value[tournament.id] = await fetchParticipants(tournament.id);
    matches.value[tournament.id] = await fetchMatches(tournament.id);
};

watch(
    () => authStore.isAuthenticated,
    (isAuthenticated: boolean) => {
        if (isAuthenticated) {
            fetchTournaments();
        }
    },
    { immediate: true }
);

const openProjection = () => {
    if (!selectedTournament.value) return;
    router.push(`/tournaments/${selectedTournament.value.id}/projection`);
};
</script>

<style>
.tournament-tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.tile {
    border: 1px solid var(--color-light-shadow);
    padding: 1rem;
    cursor: pointer;
    border-radius: var(--radius);
    background-color: var(--color-light-shadow);
    color: var(--color-fg);
    font-family: var(--font-main);
    transition: background-color 0.2s ease, border-color 0.2s ease;
}

.tile.selected {
    background-color: var(--color-accent-bis);
    border-color: var(--color-fg-darker);
    color: var(--color-bg);
}

.tournament-details {
    margin-top: 2rem;
    border-top: 1px solid var(--color-light-shadow);
    padding-top: 1rem;
    font-family: var(--font-main);
}
</style>