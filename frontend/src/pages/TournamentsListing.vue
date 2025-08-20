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
            <button @click="createTournament">Ajouter</button>
        </div>
    </div>

    <div v-if="!authStore.isAuthenticated" class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour voir les informations des tournois.</p>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { handleError, formatDate } from '../functions/utils';
import { useRouter } from 'vue-router';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';

const router = useRouter();
const authStore = useAuthStore();
const leaderboardsStore = useLeaderboardsStore();
const toast = useToast();

const tournaments = ref<Tournament[]>([]);
const matches = ref<{ [tournamentId: number]: Match[] }>({});
const registrationStatus = ref<{ [tournamentId: number]: boolean }>({});
const selectedTournament = ref<Tournament | null>(null);
const loading = ref(false);
const error = ref('');
const newTournamentName = ref('');
const newTournamentDescription = ref('');
const newTournamentStartDate = ref('');
const newTournamentIsActive = ref(true);
const showCreateTournament = ref(false);

const isEditor = computed(() => authStore.scopes.includes('editor'));

// Toggle create tournament form
const toggleCreateTournamentForm = () => {
    showCreateTournament.value = !showCreateTournament.value;
};

// Create a new tournament
const createTournament = async () => {
    try {
        const tournamentData = {
            name: newTournamentName.value,
            description: newTournamentDescription.value || null,
            start_date: newTournamentStartDate.value,
            is_active: newTournamentIsActive.value,
            type: null,
            status: 'open',
        };
        await backendApi.post('/tournaments/', tournamentData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        newTournamentName.value = '';
        newTournamentDescription.value = '';
        newTournamentStartDate.value = '';
        newTournamentIsActive.value = true;
        showCreateTournament.value = false;
        fetchTournaments();
        toast.success('Tournoi créé avec succès. Les joueurs peuvent maintenant s’inscrire.');
    } catch (err) {
        handleError(err, 'création du tournoi');
    }
};

// Fetch tournaments and related data
const fetchTournaments = async () => {
    loading.value = true;
    error.value = '';
    try {
        const { data } = await backendApi.get('/tournaments/', {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        tournaments.value = data;

        const outerPromises = tournaments.value.map((tournament) => {
            return Promise.all([
                fetchMatches(tournament.id),
                checkIfUserRegistered(tournament.id).then((isReg) => {
                    registrationStatus.value[tournament.id] = isReg;
                }),
                leaderboardsStore.fetchTournamentLeaderboard(tournament.id, authStore.token)
            ]);
        });

        await Promise.all(outerPromises);
    } catch (err) {
        handleError(err, 'récupération des tournois');
    } finally {
        loading.value = false;
    }
};

// Register user to a tournament
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
    } catch (err) {
        handleError(err, 'inscription au tournoi');
    }
};

// Check if the user is already registered
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

// Unregister user from a tournament
const unregisterFromTournament = async (tournamentId: number) => {
    try {
        await backendApi.delete(
            `/tournaments/registrations/${tournamentId}`,
            { headers: { Authorization: `Bearer ${authStore.token}` } }
        );
        toast.success('Désinscription du tournoi réussie.');
        registrationStatus.value[tournamentId] = false;
    } catch (err) {
        handleError(err, 'désinscription du tournoi');
    }
};

// Fetch matches and leaderboard
const fetchMatches = async (tournamentId: number) => {
    try {
        const { data } = await backendApi.get(`/tournaments/matches/tournament/${tournamentId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        matches.value[tournamentId] = data;
    } catch (err) {
        handleError(err, 'récupération des matchs');
    }
};

// Select tournament
const selectTournament = (tournament: Tournament) => {
    selectedTournament.value = tournament;
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
    background-color: var(--color-bg-lighter);
    color: var(--color-fg);
    font-family: var(--font-main);
    transition: background-color 0.2s ease, border-color 0.2s ease;
}

.tile.selected {
    background-color: var(--color-accent-bis);
    border-color: var(--color-fg-darker);
    color: var(--color-bg-lighter);
}

.tournament-details {
    margin-top: 2rem;
    border-top: 1px solid var(--color-light-shadow);
    padding-top: 1rem;
    font-family: var(--font-main);
}
</style>