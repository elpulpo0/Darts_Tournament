<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useTournamentStore } from '../stores/useTournamentStore';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';
import { useAuthStore } from '../stores/useAuthStore';
import { getParticipantDisplayNickname, getParticipantName } from '../functions/management';

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
    tournamentStore.fetchParticipants(tournamentId.value)
});

const finalMatches = computed(() => tournamentStore.tournamentDetail?.final_matches || [] as MatchDetailSchema[]);
const maxRounds = computed(() => {
    const highestRound = Math.max(...finalMatches.value.map((m: MatchDetailSchema) => m.round || 0), 0);
    return highestRound > 0 ? highestRound : 1;
});

const matchesByRound = computed(() => {
    const rounds: { [key: number]: MatchDetailSchema[] } = {};
    for (let i = 1; i <= maxRounds.value; i++) {
        rounds[i] = finalMatches.value.filter((match: MatchDetailSchema) => match.round === i);
    }
    return rounds;
});

const totalEliminationRounds = computed(() => {
    const firstRoundMatches = matchesByRound.value[1]?.length || 0;
    if (firstRoundMatches === 0) return 1;
    const numPlayers = firstRoundMatches * 2;
    return Math.ceil(Math.log2(numPlayers));
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
        const roundIndex = totalEliminationRounds.value - round;
        return roundIndex >= 0 && roundIndex < roundNames.length ? roundNames[roundIndex] : `Tour ${round}`;
    };
});

const baseGap = 0.6;
const baseH = 5.2;

const gaps = computed(() => {
    const g: { [key: number]: number } = {};
    g[1] = baseGap;
    for (let r = 2; r <= maxRounds.value; r++) {
        g[r] = 2 * g[r - 1] + baseH;
    }
    return g;
});

const paddings = computed(() => {
    const p: { [key: number]: number } = {};
    p[1] = 0;
    for (let r = 2; r <= maxRounds.value; r++) {
        p[r] = p[r - 1] + (baseH / 2) + (gaps.value[r - 1] / 2);
    }
    return p;
});
</script>

<template>
    <div v-if="authStore.isAuthenticated" class="projection-root">
        <h2 class="tournament-title">{{ tournamentStore.tournamentDetail?.name }}</h2>
        <div v-if="tournamentStore.loading">Chargement...</div>
        <div v-else class="content-wrapper">
            <!-- Pools -->
            <div v-if="tournamentStore.tournamentDetail?.pools?.length" class="pools-block">
                <h3>Poules</h3>
                <div class="pool-cards">
                    <div v-for="pool in tournamentStore.tournamentDetail.pools" class="pool-tile" :key="pool.id">
                        <h4>{{ pool.name || `Poule ${pool.id}` }}</h4>
                        <div class="pool-participants">
                            <span v-for="participant in pool.participants" :title="getParticipantName(participant)"
                                class="participant-in-pool" :key="participant.participant_id">
                                {{ participant.name }}
                                <span v-if="participant.users?.length > 1">
                                    ({{participant.users.map(u => u.nickname).join(' & ')}})
                                </span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Leaderboards -->
            <div v-if="leaderboardsStore.poolsLeaderboard.length" class="leaderboard-section">
                <h3>Classements</h3>
                <div class="leaderboard-container">
                    <div v-for="poolLeaderboard in leaderboardsStore.poolsLeaderboard" class="leaderboard-tile"
                        :key="poolLeaderboard.pool_id">
                        <h4>{{ poolLeaderboard.pool_name }}</h4>
                        <table class="leaderboard-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Nom</th>
                                    <th>Victoires (Principal)</th>
                                    <th>Manches gagnées (Tiebreaker)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(entry, index) in poolLeaderboard.leaderboard.slice(0, 4)"
                                    :key="entry.participant_id">
                                    <td>{{ index + 1 }}</td>
                                    <td :title="getParticipantName(tournamentStore.participants.find(p => p.id ===
                                        entry.participant_id) ?? null)">
                                        {{getParticipantDisplayNickname(tournamentStore.participants.find(p => p.id ===
                                            entry.participant_id) ?? null)}}</td>
                                    <td>{{ entry.wins }}</td>
                                    <td>{{ entry.total_manches }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Bracket -->
            <div class="bracket-container">
                <h3>Tableau Final</h3>
                <div class="bracket">
                    <div v-for="round in maxRounds" class="round" :key="round">
                        <h5>{{ getRoundName(round) }}</h5>
                        <div class="matches" :style="{
                            gap: `${gaps[round]}em`,
                            paddingTop: `${paddings[round]}em`,
                            paddingBottom: `${paddings[round]}em`
                        }">
                            <div v-for="match in matchesByRound[round]" class="match" :key="match.id">
                                <div class="match-cell">
                                    <div v-for="participant in match.participants" class="participant-slot"
                                        :title="getParticipantName(participant)" :key="participant.participant_id">
                                        <span class="participant-name">
                                            {{ participant.name }}
                                            <span v-if="participant.users?.length > 1">
                                                ({{participant.users.map(u => u.name).join(' & ')}})
                                            </span>
                                        </span>
                                        <span v-if="typeof participant?.score === 'number'" class="score">({{
                                            participant.score }})</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
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
    padding: 1em;
    background-color: var(--color-bg);
    color: var(--color-fg);
    font-family: var(--font-main);
    display: flex;
    flex-direction: column;
}

.tournament-title {
    font-size: 1.5em;
    margin-bottom: 0.5em;
    color: var(--color-main);
    text-align: center;
}

.content-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1em;
}

.pools-block,
.leaderboard-section,
.bracket-container {
    width: 100%;
}

.pools-block h3,
.leaderboard-section h3,
.bracket-container h3 {
    font-size: 1.2em;
    margin-bottom: 0.3em;
    color: var(--color-main);
}

.pool-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
}

.pool-tile {
    padding: 0.5em;
    border-radius: 8px;
    box-shadow: 0 1px 3px var(--color-bg-lighter);
    width: 160px;
}

.pool-tile h4 {
    font-size: 0.9em;
    margin-bottom: 0.3em;
}

.pool-participants {
    display: flex;
    flex-direction: column;
    gap: 0.2em;
}

.participant-in-pool {
    font-size: 0.8em;
    background: color-mix(in srgb, var(--color-main) 10%, transparent);
    border-radius: 4px;
    padding: 0.1em 0.4em;
}

.leaderboard-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
}

.leaderboard-tile {
    flex: 1 1 200px;
    max-width: 300px;
}

.leaderboard-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8em;
}

.leaderboard-table th,
.leaderboard-table td {
    padding: 0.3em 0.5em;
    border-bottom: 1px solid var(--color-light-shadow);
    text-align: left;
}

.leaderboard-table th {
    color: var(--color-main);
    font-size: 0.9em;
}

.leaderboard-table tr:last-child td {
    border-bottom: none;
}

.bracket-container {
    display: flex;
    flex-direction: column;
}

.bracket {
    display: flex;
    justify-content: flex-start;
    gap: 0.5em;
    align-items: stretch;
    overflow-x: auto;
    padding-bottom: 1em;
}

.round {
    flex: 0 1 auto;
    display: flex;
    flex-direction: column;
    gap: 0.5em;
    min-width: 200px;
}

.round h5 {
    font-size: 0.9em;
    color: var(--color-main);
    text-align: center;
}

.matches {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}

.match {
    background: var(--color-bg-lighter);
    border-radius: 6px;
    padding: 0.5em;
    box-shadow: 0 4px 5px var(--color-fg-darker);
}

.match-cell {
    display: flex;
    flex-direction: column;
    gap: 0.5em;
    padding: 4px;
}

.participant-slot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.2em 0.4em;
    background: var(--color-fg-darker);
    border-radius: 4px;
}

.participant-name {
    font-size: 0.8em;
}

.score {
    font-size: 0.8em;
    font-weight: bold;
    color: var(--color-link);
}

.centered-block {
    text-align: center;
    padding: 2em;
}

.centered-block h2 {
    font-size: 1.5em;
    color: var(--color-main);
}

.centered-block p {
    font-size: 1em;
    color: var(--color-fg);
}
</style>