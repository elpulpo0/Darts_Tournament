<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="leaderboardsStore.loading">Loading season leaderboard...</div>
        <div v-if="leaderboardsStore.error" class="error">{{ leaderboardsStore.error }}</div>
        <div class="module">
            <h2>Classement de la saison {{ leaderboardsStore.currentSeason }}</h2>
            <table v-if="leaderboardsStore.seasonLeaderboard.length">
                <thead>
                    <tr>
                        <th></th>
                        <th>Nom</th>
                        <th>Points</th>
                        <th>Victoires</th>
                        <th>Manches</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(entry, index) in leaderboardsStore.seasonLeaderboard"
                        :class="{ 'current-user': entry.name === currentUserName }" :key="entry.user_id">
                        <td>{{ getRank(index) }}</td>
                        <td>{{ entry.name }}</td>
                        <td>{{ entry.total_points }}</td>
                        <td>{{ entry.wins }}</td>
                        <td>{{ entry.total_manches }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-else-if="!leaderboardsStore.loading">Aucun match complété pour la saison {{
                leaderboardsStore.currentSeason }}.</p>
        </div>

        <!-- Ajout du leaderboard de tournoi si un tournamentId est fourni -->
        <div v-if="tournamentId" class="module">
            <h2>Classement du tournoi</h2>
            <div v-if="leaderboardsStore.tournamentLeaderboardLoading">Chargement du classement du tournoi...</div>
            <div v-if="leaderboardsStore.tournamentLeaderboardError" class="error">{{
                leaderboardsStore.tournamentLeaderboardError }}</div>
            <table v-if="leaderboardsStore.tournamentLeaderboard.length">
                <thead>
                    <tr>
                        <th></th>
                        <th>Nom</th>
                        <th>Victoires</th>
                        <th>Manches</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(entry, index) in leaderboardsStore.tournamentLeaderboard" :key="entry.participant_id">
                        <td>{{ getRank(index) }}</td>
                        <td>{{ entry.name }}</td>
                        <td>{{ entry.wins }}</td>
                        <td>{{ entry.total_manches }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-else-if="!leaderboardsStore.tournamentLeaderboardLoading">Aucun classement disponible pour ce tournoi.
            </p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/useAuthStore';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';
import { useRoute } from 'vue-router';

const authStore = useAuthStore();
const leaderboardsStore = useLeaderboardsStore();
const route = useRoute();

const tournamentId = computed(() => route.params.tournamentId ? Number(route.params.tournamentId) : null);

const currentUserName = computed(() => authStore.name || '');
const currentYear = new Date().getFullYear();

const getRank = (index: number) => {
    if (index === 0) return 1; // First entry is always rank 1
    const prevEntry = leaderboardsStore.seasonLeaderboard[index - 1];
    const currentEntry = leaderboardsStore.seasonLeaderboard[index];
    // Check for tie (same total_points, wins, and total_manches)
    if (
        prevEntry.total_points === currentEntry.total_points &&
        prevEntry.wins === currentEntry.wins &&
        prevEntry.total_manches === currentEntry.total_manches
    ) {
        // Same rank as previous entry
        return getRank(index - 1);
    }
    // New rank is index + 1 (1-based)
    return index + 1;
};

onMounted(() => {
    if (authStore.token) {
        console.log('Fetching season leaderboard for year:', currentYear);
        leaderboardsStore.fetchSeasonLeaderboard(currentYear, authStore.token);
        if (tournamentId.value) {
            leaderboardsStore.fetchTournamentLeaderboard(tournamentId.value, authStore.token);
        }
    }
});
</script>

<style>
.current-user {
    color: rgb(255, 153, 0) !important;
    font-weight: bold;
}
</style>