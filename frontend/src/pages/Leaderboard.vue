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
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useAuthStore } from '../stores/useAuthStore';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';

const authStore = useAuthStore();
const leaderboardsStore = useLeaderboardsStore();

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
    }
});
</script>

<style>
.current-user {
    color: rgb(255, 153, 0) !important;
    font-weight: bold;
}
</style>