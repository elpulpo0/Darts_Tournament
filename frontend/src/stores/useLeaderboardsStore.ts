import { defineStore } from 'pinia';
import { ref } from 'vue';
import backendApi from '../axios/backendApi';
import { handleError } from '../functions/utils';

export const useLeaderboardsStore = defineStore('leaderboards', () => {
    const seasonLeaderboard = ref<LeaderboardEntry[]>([]);
    const currentSeason = ref('');
    const loading = ref(false);
    const error = ref('');
    const tournamentLeaderboard = ref<TournamentLeaderboardEntry[]>([]);
    const tournamentLeaderboardLoading = ref(false);
    const tournamentLeaderboardError = ref('');
    const poolsLeaderboard = ref<{ pool_id: number, pool_name: string, leaderboard: TournamentLeaderboardEntry[] }[]>([]);
    const poolsLeaderboardLoading = ref(false);
    const poolsLeaderboardError = ref('');

    const fetchSeasonLeaderboard = async (year: number, token: string) => {
        loading.value = true;
        error.value = '';
        try {
            const { data } = await backendApi.get(`/tournaments/leaderboard/season/${year}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            seasonLeaderboard.value = data.leaderboard;
            currentSeason.value = data.season;
        } catch (err) {
            handleError(err, 'fetching season leaderboard');
            error.value = 'Échec du chargement du classement de la saison.';
        } finally {
            loading.value = false;
        }
    };

    const fetchTournamentLeaderboard = async (tournamentId: number, token: string) => {
        tournamentLeaderboardLoading.value = true;
        tournamentLeaderboardError.value = '';
        try {
            const { data } = await backendApi.get(`/tournaments/leaderboard/tournament/${tournamentId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            tournamentLeaderboard.value = data.leaderboard;
        } catch (err) {
            handleError(err, 'fetching tournament leaderboard');
            tournamentLeaderboardError.value = 'Erreur lors du chargement du classement du tournoi.';
        } finally {
            tournamentLeaderboardLoading.value = false;
        }
    };

    const fetchPoolsLeaderboard = async (tournamentId: number, token: string) => {
        poolsLeaderboardLoading.value = true;
        poolsLeaderboardError.value = '';
        try {
            const { data } = await backendApi.get(`/tournaments/${tournamentId}/pools/leaderboard`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            poolsLeaderboard.value = data;
        } catch (err) {
            handleError(err, 'fetching pools leaderboard');
            poolsLeaderboardError.value = 'Erreur lors du chargement des classements par poule.';
        } finally {
            poolsLeaderboardLoading.value = false;
        }
    };

    return {
        seasonLeaderboard,
        currentSeason,
        loading,
        error,
        fetchSeasonLeaderboard,
        tournamentLeaderboard,
        tournamentLeaderboardLoading,
        tournamentLeaderboardError,
        fetchTournamentLeaderboard,
        poolsLeaderboard,
        poolsLeaderboardLoading,
        poolsLeaderboardError,
        fetchPoolsLeaderboard,
    };
});