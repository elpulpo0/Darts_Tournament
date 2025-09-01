<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="leaderboardsStore.loading">Loading season leaderboard...</div>
        <div v-if="leaderboardsStore.error" class="error">{{ leaderboardsStore.error }}</div>
        <div class="module">
            <h2>Classement de la saison {{ leaderboardsStore.currentSeason }}</h2>
            <div class="points-explanation">
                Les points sont calculés comme suit :
                <ul>
                    <li><strong>Mode simple :</strong> 1 point par manche gagnée + 1 point par match gagné.</li>
                    <li><strong>Mode double :</strong> 0.5 point par manche gagnée (par joueur) + 0.5 point par match
                        gagné (par joueur).</li>
                </ul>
            </div>
            <table v-if="leaderboardsStore.seasonLeaderboard.length">
                <thead>
                    <tr>
                        <th></th>
                        <th>Nom</th>
                        <th>Points</th>
                        <th>Victoires (Simple)</th>
                        <th>Victoires (Double)</th>
                        <th>Manches (Simple)</th>
                        <th>Manches (Double)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(entry, index) in leaderboardsStore.seasonLeaderboard"
                        :class="{ 'current-user': entry.name === currentUserName }" :key="entry.user_id">
                        <td>{{ getRank(index) }}</td>
                        <td>{{ entry.name }}</td>
                        <td>{{ entry.total_points }}</td>
                        <td>{{ entry.single_wins }}</td>
                        <td>{{ entry.double_wins }}</td>
                        <td>{{ entry.single_manches }}</td>
                        <td>{{ entry.double_manches }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-else-if="!leaderboardsStore.loading">Aucun match complété pour la saison {{
                leaderboardsStore.currentSeason }}.</p>
        </div>
    </div>
    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour accéder au classement.</p>
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
    if (index === 0) return 1;
    const prevEntry = leaderboardsStore.seasonLeaderboard[index - 1];
    const currentEntry = leaderboardsStore.seasonLeaderboard[index];
    if (
        prevEntry.total_points === currentEntry.total_points
    ) {
        return getRank(index - 1);
    }
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
    color: var(--color-error);
    font-weight: bold;
}
</style>