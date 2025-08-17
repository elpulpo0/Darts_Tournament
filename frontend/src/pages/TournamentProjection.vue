<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useTournamentStore } from '../stores/useTournamentStore';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';
import { useAuthStore } from '../stores/useAuthStore';

const route = useRoute();
const tournamentId = computed(() => Number(route.params.tournamentId));

const authStore = useAuthStore();
const leaderboardsStore = useLeaderboardsStore();
const tournamentStore = useTournamentStore();

onMounted(() => {
    tournamentStore.fetchTournamentDetail(tournamentId.value);
    leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
    const currentYear = new Date().getFullYear();
    leaderboardsStore.fetchSeasonLeaderboard(currentYear, authStore.token);
});

const finalMatches = computed(() => tournamentStore.tournamentDetail?.final_matches || [] as Match[]);
const maxRounds = computed(() => {
    const highestRound = Math.max(...finalMatches.value.map((m: Match) => m.round || 0), 0);
    return highestRound + 1; // Only include rounds that exist in the data
});
const matchesByRound = computed(() => {
    const rounds: { [key: number]: Match[] } = {};
    finalMatches.value.forEach((match: Match) => {
        const round = match.round || 0;
        if (!rounds[round]) rounds[round] = [];
        rounds[round].push(match);
    });
    return rounds;
});

const getRoundName = computed(() => {
    const roundNames = [
        'Finale',
        'Demi-finale',
        'Quart de finale',
        'Huitième de finale',
        'Seizième de finale',
        'Trente-deuxième de finale',
        'Soixante-quatrième de finale'
    ];
    return (round: number) => {
        const roundIndex = maxRounds.value - round - 1;
        return roundIndex >= 0 && roundIndex < roundNames.length ? roundNames[roundIndex] : `Tour ${round}`;
    };
});
</script>

<template>
    <div class="projection-root">
        <h2>Projection du tournoi : {{ tournamentStore.tournamentDetail?.name }}</h2>
        <div v-if="tournamentStore.loading">Chargement...</div>
        <div v-else>
            <!-- Pools -->
            <div v-if="tournamentStore.tournamentDetail?.pools && tournamentStore.tournamentDetail.pools.length"
                class="pools-block">
                <h3>Poules</h3>
                <div class="pool-cards">
                    <div v-for="pool in tournamentStore.tournamentDetail.pools" class="pool-tile" :key="pool.id">
                        <h4>{{ pool.name || pool.id }}</h4>
                        <div class="pool-players">
                            <span v-for="player in pool.players" class="player-in-pool" :key="player.id">{{ player.name
                                }}</span>
                        </div>
                        <div v-for="match in pool.matches" class="pool-match" :key="match.id">
                            <div class="players">
                                <span>{{match.players?.map((p: any) => p.name).join(' vs ')}}</span>
                            </div>
                            <div class="scores">
                                <span v-if="match.status === 'completed'">Scores :
                                    {{match.players?.map((p: any) => typeof p.score === 'number' ? p.score :
                                        'N/A').join(' - ')}}
                                </span>
                                <span v-else>En attente</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Classements par poule -->
            <div class="leaderboard-section">
                <h4>Classements par poule</h4>
                <div v-if="leaderboardsStore.poolsLeaderboardLoading">Chargement des classements par poule...</div>
                <div v-if="leaderboardsStore.poolsLeaderboardError" class="error">{{
                    leaderboardsStore.poolsLeaderboardError }}</div>
                <div v-if="leaderboardsStore.poolsLeaderboard.length">
                    <div v-for="poolLeaderboard in leaderboardsStore.poolsLeaderboard" :key="poolLeaderboard.pool_id">
                        <h5>{{ poolLeaderboard.pool_name }}</h5>
                        <table>
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Victoires (Principal)</th>
                                    <th>Manches gagnées (Tiebreaker)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="entry in poolLeaderboard.leaderboard" :key="entry.user_id">
                                    <td>{{ entry.name }}</td>
                                    <td>{{ entry.wins }}</td>
                                    <td>{{ entry.total_manches }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <p v-else>Aucun classement par poule disponible.</p>
            </div>

            <!-- Bracket Table -->
            <div v-if="finalMatches.length" class="bracket-tree">
                <h3>Phases finales</h3>
                <table class="bracket-table">
                    <tr v-for="round in maxRounds" :key="round">
                        <th v-if="matchesByRound[round] && matchesByRound[round].length" colspan="100">
                            <h5>{{ getRoundName(round) }}</h5>
                        </th>
                    <tr v-if="matchesByRound[round] && matchesByRound[round].length">
                        <td v-for="match in matchesByRound[round]" :key="match.id">
                            <div class="match-cell">
                                <div v-for="(player, index) in match.players" class="player-slot" :key="index">
                                    <span>{{ player?.name || 'TBD' }}</span>
                                    <span v-if="typeof player?.score === 'number'" class="score">({{ player.score
                                        }})</span>
                                </div>
                                <div class="match-status">
                                    <span v-if="match.status === 'completed'">Terminé</span>
                                    <span v-else>En attente</span>
                                </div>
                            </div>
                        </td>
                    </tr>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</template>

<style scoped>
.projection-root {
    min-height: 100vh;
    padding: 2em;
    background-color: var(--color-bg);
    color: var(--color-fg);
    font-family: var(--font-main);
}

h2,
h3 {
    margin-bottom: 0.6em;
    color: var(--color-main);
}

.bracket-tree {
    margin-top: 2em;
}

.bracket-table {
    border-collapse: collapse;
    width: 100%;
}

.bracket-table th {
    border: 1px solid #ccc;
    padding: 10px;
    text-align: center;
    background-color: #f0f0f0;
}

.bracket-table td {
    border: 1px solid #ccc;
    padding: 10px;
    text-align: center;
    transition: opacity 0.3s;
}

.match-cell {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.player-slot {
    display: flex;
    justify-content: center;
    gap: 5px;
}

.score {
    color: var(--color-link);
}

.match-status {
    font-size: 0.9em;
    color: var(--color-fg-darker);
}

.pools-block {
    margin-top: 2em;
}

.pool-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 2em;
}

.pool-tile {
    background: var(--color-bg-lighter);
    padding: 1.1em 1.7em;
    border-radius: 14px;
    box-shadow: 0 1px 5px var(--color-light-shadow);
    min-width: 240px;
}

.pool-match {
    display: flex;
    flex-direction: column;
    background: var(--color-bg-lighter);
    margin: 0.6em 0;
    border-radius: var(--radius);
    padding: 0.7em 1em;
    box-shadow: 0 1px 2px var(--color-light-shadow);
}

.scores {
    font-size: 0.97em;
    color: var(--color-fg);
}

.leaderboard-section {
    margin-top: 3em;
}

.leaderboard-table {
    width: 280px;
    max-width: 95vw;
    background: var(--color-bg-lighter);
    border-radius: var(--radius);
    box-shadow: 0 1px 5px var(--color-light-shadow);
    border-collapse: collapse;
    margin-top: 1em;
}

.leaderboard-table th,
.leaderboard-table td {
    padding: 0.65em 1em;
    text-align: left;
    border-bottom: 1px solid var(--color-light-shadow);
}

.leaderboard-table th {
    color: var(--color-main);
    font-size: 1.04em;
}

.leaderboard-table tr:last-child td {
    border-bottom: none;
}

.pool-players {
    margin-bottom: 0.5em;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
}

.player-in-pool {
    background: color-mix(in srgb, var(--color-main) 10%, transparent);
    border-radius: 4px;
    padding: 0.1em 0.6em;
    font-size: 0.98em;
    margin-right: 2px;
    color: var(--color-fg);
}
</style>