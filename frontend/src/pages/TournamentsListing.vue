<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="loading">Loading tournaments...</div>

        <div v-if="tournaments.length" class="module">
            <h2>Tournaments</h2>
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
                <p>{{ selectedTournament.description || 'No description' }}</p>

                <button v-if="isEditor"
                    @click="router.push({ name: 'TournamentManagement', params: { tournamentId: selectedTournament.id } })">
                    Manage Tournament
                </button>

                <!-- Register or Unregister button -->
                <div v-if="selectedTournament.status === 'open' && !registrationStatus[selectedTournament.id]">
                    <button @click="registerToTournament(selectedTournament.id)">Register</button>
                </div>

                <div v-else-if="registrationStatus[selectedTournament.id]">
                    <button @click="unregisterFromTournament(selectedTournament.id)">Unregister</button>
                    <p>You are already registered for this tournament.</p>
                </div>

                <div v-else>
                    <p>Registrations are closed for this tournament.</p>
                </div>

                <h4>Matches</h4>
                <table v-if="matches[selectedTournament.id]?.length">
                    <thead>
                        <tr>
                            <th>Players</th>
                            <th>Status</th>
                            <th>Scores</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="match in matches[selectedTournament.id]" :key="match.id">
                            <td>{{match.players.map((p) => p?.name || 'Unknown').join(' vs ')}}</td>
                            <td>{{ match.status }}</td>
                            <td>
                                <span v-if="match.players?.length">
                                    {{match.players.map((p) => `${p?.name || 'Unknown'}: ${p?.score ?? 0}`).join(', ')}}
                                </span>
                                <span v-else>No scores available</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <p v-else>No matches available</p>

                <h4>Leaderboard</h4>
                <div v-if="leaderboardsStore.tournamentLeaderboardLoading">Chargement du classement...</div>
                <div v-if="leaderboardsStore.tournamentLeaderboardError" class="error">{{
                    leaderboardsStore.tournamentLeaderboardError }}</div>
                <table v-if="leaderboardsStore.tournamentLeaderboard.length">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Total Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="entry in leaderboardsStore.tournamentLeaderboard" :key="entry.user_id">
                            <td>{{ entry.name }}</td>
                            <td>{{ entry.total_manches }}</td>
                        </tr>
                    </tbody>
                </table>
                <p v-else>Pas de classement disponible</p>
            </div>
        </div>

        <div v-else class="module">
            <p>Aucun tournoi disponible.</p>
        </div>

        <button v-if="isEditor" @click="toggleCreateTournamentForm">
            {{ showCreateTournament ? 'Cancel' : 'Add Tournament' }}
        </button>
        <div v-if="showCreateTournament" class="module">
            <h3>Add Tournament</h3>
            <input v-model="newTournamentName" placeholder="Name" class="form-input" />
            <input v-model="newTournamentDescription" placeholder="Description" class="form-input" />
            <input v-model="newTournamentStartDate" type="datetime-local" class="form-input" />
            <button @click="createTournament">Add</button>
        </div>
    </div>

    <div v-if="!authStore.isAuthenticated" class="centered-block">
        <h2>🔒 Login required</h2>
        <p>Please log in to view tournament information.</p>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { handleError, formatDate } from '../functions/utils';
import { useRouter } from 'vue-router';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore'

const router = useRouter();
const authStore = useAuthStore();
const leaderboardsStore = useLeaderboardsStore()
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
        toast.success('Tournament created successfully. Players can now register.');
    } catch (err) {
        handleError(err, 'creating tournament');
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
        handleError(err, 'fetching tournaments');
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
        toast.success('Successfully registered to the tournament.');
        registrationStatus.value[tournamentId] = true;
    } catch (err) {
        handleError(err, 'registering to tournament');
    }
};

// Check if the user is already registered
const checkIfUserRegistered = async (tournamentId: number): Promise<boolean> => {
    try {
        const { data } = await backendApi.get(`/tournaments/registrations/${tournamentId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        return data.some((registration: any) => registration.user_id === authStore.userId);
    } catch (err) {
        handleError(err, 'checking registration status');
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
        toast.success('Successfully unregistered from the tournament.');
        // Update registration status locally
        registrationStatus.value[tournamentId] = false;
    } catch (err) {
        handleError(err, 'unregistering from tournament');
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
        handleError(err, 'fetching matches');
    }
};

// Select tournament
const selectTournament = (tournament: Tournament) => {
    selectedTournament.value = tournament;
};

fetchTournaments();
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
    color: var(--color-fg-darker);
}
</style>