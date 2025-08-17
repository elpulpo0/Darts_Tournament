<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="leaderboardsStore.loading">Loading season leaderboard...</div>
        <div v-if="leaderboardsStore.error" class="error">{{ leaderboardsStore.error }}</div>
        <div class="module">
            <h2>Classement de la saison {{ leaderboardsStore.currentSeason }}</h2>
            <table v-if="leaderboardsStore.seasonLeaderboard.length">
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="entry in leaderboardsStore.seasonLeaderboard"
                        :class="{ 'current-user': entry.name === currentUserName }" :key="entry.user_id">
                        <td>{{ entry.name }}</td>
                        <td>{{ entry.total_points }}</td>
                    </tr>
                </tbody>
            </table>
            <p v-else>Pas de classement disponible</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/useAuthStore'
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore'

const authStore = useAuthStore()
const leaderboardsStore = useLeaderboardsStore()

const currentUserName = computed(() => authStore.name || '')
const currentYear = new Date().getFullYear()

onMounted(() => {
    if (authStore.token) {
        leaderboardsStore.fetchSeasonLeaderboard(currentYear, authStore.token)
    }
})
</script>


<style>
.current-user {
    color: rgb(255, 153, 0);
    font-weight: bold;
}
</style>