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

const maxRounds = computed(() => {
    const highestRound = Math.max(...finalMatches.value.map((m: MatchDetailSchema) => m.round || 0), 0);
    return highestRound + 1;
});
const finalMatches = computed(() => tournamentStore.tournamentDetail?.final_matches || [] as MatchDetailSchema[]);
const matchesByRound = computed(() => {
    const rounds: { [key: number]: MatchDetailSchema[] } = {};
    finalMatches.value.forEach((match: MatchDetailSchema) => {
        const round = match.round || 0;
        if (!rounds[round]) rounds[round] = [];
        rounds[round].push(match);
    });
    return rounds;
});

// Calculate the total number of elimination rounds based on the first round's matches
const totalEliminationRounds = computed(() => {
    const firstRoundMatches = matchesByRound.value[1]?.length || 0; // Matches in round 1
    if (firstRoundMatches === 0) return 1; // Default to 1 if no matches
    const numPlayers = firstRoundMatches * 2; // 4 matches = 8 participants
    return Math.ceil(Math.log2(numPlayers)); // e.g., log₂(8) = 3 rounds
});

// Map round numbers to names based on total rounds
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
        // Adjust index based on total elimination rounds
        const roundIndex = totalEliminationRounds.value - round;
        return roundIndex >= 0 && roundIndex < roundNames.length ? roundNames[roundIndex] : `Tour ${round}`;
    };
});
</script>

<template>
    <div v-if="authStore.isAuthenticated" class="projection-root">
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
                        <div class="pool-participants">
                            <span v-for="participant in pool.participants" class="participant-in-pool"
                                :key="participant.participant_id">
                                {{ participant.name }}
                                <span v-if="participant.users && participant.users.length > 1">
                                    ({{participant.users.map(u => u.name).join(' & ')}})
                                </span>
                            </span>
                        </div>
                        <div v-for="match in pool.matches" class="pool-match" :key="match.id">
                            <div class="participants">
                                <span>{{match.participants?.map((p: MatchParticipantSchema) =>
                                    p.name + (p.users && p.users.length > 1 ?
                                        ' (' + p.users.map(u => u.name).join(' & ') + ')' : '')
                                ).join(' vs ')}}</span>
                            </div>
                            <div class="scores">
                                <span v-if="match.status === 'completed'">Scores :
                                    {{match.participants?.map((p: MatchParticipantSchema) => typeof p.score === 'number'
                                        ? p.score :
                                        'N/A').join(' - ')}}
                                </span>
                                <span v-else>En attente</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Leaderboards par poule -->
            <div v-if="leaderboardsStore.poolsLeaderboard.length" class="leaderboard-section">
                <h3>Classements des poules</h3>
                <div v-for="poolLeaderboard in leaderboardsStore.poolsLeaderboard" :key="poolLeaderboard.pool_id">
                    <h4>{{ poolLeaderboard.pool_name }}</h4>
                    <table class="leaderboard-table">
                        <thead>
                            <tr>
                                <th>Rang</th>
                                <th>Nom</th>
                                <th>Victoires</th>
                                <th>Manches</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="(entry, index) in poolLeaderboard.leaderboard" :key="entry.participant_id">
                                <td>{{ index + 1 }}</td>
                                <td>{{ entry.name }}</td>
                                <td>{{ entry.wins }}</td>
                                <td>{{ entry.total_manches }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Phases finales -->
            <div v-if="tournamentStore.tournamentDetail?.final_matches && tournamentStore.tournamentDetail.final_matches.length"
                class="finals-block">
                <h3>Phases finales</h3>
                <table class="bracket-table">
                    <tr v-for="round in maxRounds" :key="round">
                        <th v-if="matchesByRound[round] && matchesByRound[round].length" colspan="100">
                            <h5>{{ getRoundName(round) }}</h5>
                        </th>
                    <tr v-if="matchesByRound[round] && matchesByRound[round].length">
                        <td v-for="match in matchesByRound[round]" :key="match.id">
                            <div class="match-cell">
                                <div v-for="(participant) in match.participants" class="participant-slot"
                                    :key="participant.participant_id">
                                    <span>
                                        {{ participant.name }}
                                        <span v-if="participant.users && participant.users.length > 1">
                                            ({{participant.users.map(u => u.name).join(' & ')}})
                                        </span>
                                    </span>
                                    <span v-if="typeof participant?.score === 'number'" class="score">({{
                                        participant.score }})</span>
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
    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour accéder à ce tournoi.</p>
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

.participant-slot {
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
    padding: 1.1em 1.7em;
    border-radius: 14px;
    box-shadow: 0 1px 5px var(--color-bg-lighter);
    min-width: 240px;
}

.pool-match {
    display: flex;
    flex-direction: column;
    margin: 0.6em 0;
    border-radius: var(--radius);
    padding: 0.7em 1em;
    box-shadow: 0 1px 2px var(--color-bg-lighter);
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
    background: var(--color-bg);
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

.pool-participants {
    margin-bottom: 0.5em;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
}

.participant-in-pool {
    background: color-mix(in srgb, var(--color-main) 10%, transparent);
    border-radius: 4px;
    padding: 0.1em 0.6em;
    font-size: 0.98em;
    margin-right: 2px;
    color: var(--color-fg);
}
</style>