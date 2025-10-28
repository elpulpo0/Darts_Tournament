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

            <div class="mobile-rotate-notice hideonmobile-off">
                <span>📱</span> Tourne ton téléphone pour voir toutes les colonnes
            </div>

            <table v-if="filteredLeaderboard.length" class="leaderboardtable">
                <thead>
                    <tr>
                        <th></th>
                        <th>Nom</th>
                        <th>Points</th>
                        <th class="hideonmobile">Victoires (Simple)</th>
                        <th class="hideonmobile">Victoires (Double)</th>
                        <th class="hideonmobile">Manches (Simple)</th>
                        <th class="hideonmobile">Manches (Double)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(entry, index) in filteredLeaderboard"
                        :class="{ 'current-user': entry.nickname === currentUserName }" :key="entry.user_id">
                        <td>{{ getRank(index, filteredLeaderboard) }}</td>
                        <td>{{ entry.nickname }}</td>
                        <td>{{ entry.total_points }}</td>
                        <td class="hideonmobile">{{ entry.single_wins }}</td>
                        <td class="hideonmobile">{{ entry.double_wins }}</td>
                        <td class="hideonmobile">{{ entry.single_manches }}</td>
                        <td class="hideonmobile">{{ entry.double_manches }}</td>
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

const currentUserName = computed(() => authStore.nickname || '');
const currentYear = new Date().getFullYear();

const filteredLeaderboard = computed(() => {
    return leaderboardsStore.seasonLeaderboard.filter(entry => !entry.nickname.startsWith('guest'));
});

const getRank = (index: number, leaderboard: any[]) => {
    if (index === 0) return 1;
    const prevEntry = leaderboard[index - 1];
    const currentEntry = leaderboard[index];
    if (
        prevEntry.total_points === currentEntry.total_points
    ) {
        return getRank(index - 1, leaderboard);
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

@media screen and (max-width: 600px) {
    .hideonmobile {
        display: none;
    }
}
</style>