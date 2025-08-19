<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { createPools, generateEliminationMatches, getMatchWinner, computePoolRanking } from '../functions/tournamentStructure';
import { handleError } from '../functions/utils';
import { useRoute } from 'vue-router';
import { useRouter } from 'vue-router';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';
import { useTournamentStore } from '../stores/useTournamentStore';

const route = useRoute();
const router = useRouter();
const tournamentId = computed(() => Number(route.params.tournamentId));

const authStore = useAuthStore();
const toast = useToast();
const leaderboardsStore = useLeaderboardsStore();
const tournamentStore = useTournamentStore();

const tournament = ref<Tournament | null>(null);
const players = ref<Player[]>([]);
const matches = ref<Match[]>([]);
const loading = ref(false);
const error = ref('');
const registeringTournamentId = ref<number | null>(null);
const editForm = ref<any>({});
const newPlayerName = ref<string>('');
const newPlayerEmail = ref<string>('');
const tempScores = ref<{ [matchId: number]: number[] }>({});
const launchingTournamentId = ref<number | null>(null);
const launchTargetCount = ref<number>(4);
const launchTypeMode = ref<'auto' | 'manual'>('auto');
const launchTournamentType = ref<'pool' | 'elimination'>('pool');
const isEditing = ref(false);
const allUsers = ref<Player[]>([]);
const selectedUserId = ref<number | null>(null);

const poolIds = computed(() => {
    const ids = matches.value.map(m => m.pool_id).filter(id => id != null);
    return [...new Set(ids)];
});

const isPoolFinished = computed(() =>
    poolIds.value.length > 0 &&
    poolIds.value.every(poolId =>
        matches.value
            .filter(m => m.pool_id === poolId)
            .every(m => m.status === 'completed')
    )
);

const isTournamentFinished = computed(() => {
    if (currentRound.value === 0) return false; // Pas fini pendant les poules
    const currentRoundMatches = matches.value.filter(
        m => m.pool_id == null && m.round === currentRound.value
    );
    // Le tournoi est fini si : un seul match dans le tour actuel, complété, avec un gagnant
    if (currentRoundMatches.length === 1 && currentRoundMatches[0].status === 'completed') {
        const winner = getMatchWinner(currentRoundMatches[0]);
        return !!winner; // Vrai si un gagnant est trouvé
    }
    return false;
});

const currentRound = computed(() => {
    const finalMatches = matches.value.filter(m => m.pool_id == null);
    if (finalMatches.length === 0) return 0;
    return Math.max(...finalMatches.map(m => m.round || 0));
});

const isCurrentRoundFinished = computed(() => {
    if (currentRound.value === 0) return isPoolFinished.value;
    return matches.value
        .filter(m => m.pool_id == null && m.round === currentRound.value)
        .every(m => m.status === 'completed');
});

const openProjection = () => {
    if (!tournament.value) return;
    window.open(`/tournaments/${tournament.value.id}/projection`, '_blank');
};

const fetchTournament = async (id: number) => {
    loading.value = true;
    error.value = '';
    try {
        const { data } = await backendApi.get(`/tournaments/${id}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        tournament.value = data;
        resetEditForm(data);
        await fetchPlayers();
        if (data.status === 'running' || data.status === 'closed') {
            await fetchMatches();
            await leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
            const currentYear = new Date().getFullYear();
            await leaderboardsStore.fetchSeasonLeaderboard(currentYear, authStore.token);
        }
    } catch (err) {
        handleError(err, 'fetching tournament');
    } finally {
        loading.value = false;
    }
};

const resetEditForm = (data: Tournament) => {
    editForm.value = {
        name: data.name,
        description: data.description,
        start_date: data.start_date.split('T')[0],
        type: data.type,
        status: data.status,
    };
};

const fetchAllUsers = async () => {
    try {
        const { data } = await backendApi.get('/users/users', {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        allUsers.value = data;
    } catch (err) {
        handleError(err, 'fetching all users');
    }
};

const selectableUsers = computed(() => {
    const alreadyRegisteredIds = new Set(players.value.map(p => p.id));
    return allUsers.value.filter(user => !alreadyRegisteredIds.has(user.id));
});

const fetchPlayers = async () => {
    try {
        const { data } = await backendApi.get(`/tournaments/${tournamentId.value}/players`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        players.value = data;
    } catch (err) {
        handleError(err, 'fetching players');
    }
};

const fetchMatches = async () => {
    try {
        const { data } = await backendApi.get(`/tournaments/matches/tournament/${tournamentId.value}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        matches.value = data;
        for (const match of data) {
            if (match.status === 'pending') {
                tempScores.value[match.id] = match.players.map(() => 0);
            }
        }
    } catch (err) {
        handleError(err, 'fetching matches');
    }
};

const startEditing = () => {
    if (tournament.value) {
        resetEditForm(tournament.value);
    }
    isEditing.value = true;
};

const cancelEditing = () => {
    isEditing.value = false;
};

const updateTournament = async () => {
    try {
        const { data } = await backendApi.patch(`/tournaments/${tournamentId.value}`, editForm.value, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        tournament.value = data;
        resetEditForm(data);
        toast.success('Tournoi mis à jour');
        if (data.status === 'running' || data.status === 'closed') {
            await fetchMatches();
            await leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
        }
    } catch (err) {
        handleError(err, 'updating tournament');
    }
};

const deleteTournament = async () => {
    try {
        await backendApi.delete(`/tournaments/${tournamentId.value}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Tournoi supprimé');
        try {
            await router.push('/tournaments');
        } catch (navError) {
            console.error('Erreur de navigation:', navError);
            window.location.href = '/tournaments';
        }
    } catch (err) {
        handleError(err, 'deleting tournament');
    }
};

const startLaunchingTournament = (tournamentId: number) => {
    launchingTournamentId.value = tournamentId;
    launchTargetCount.value = 4;
    launchTypeMode.value = 'auto';
    launchTournamentType.value = 'pool';
};

const cancelLaunchingTournament = () => {
    launchingTournamentId.value = null;
    launchTargetCount.value = 4;
    launchTypeMode.value = 'auto';
    launchTournamentType.value = 'pool';
};

const launchTournament = async () => {
    loading.value = true;
    try {
        const { data: players } = await backendApi.get(`/tournaments/${tournamentId.value}/players`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        if ((players?.length ?? 0) < 2) throw new Error("Minimum 2 joueurs requis");

        let tournamentType: 'pool' | 'elimination';
        let numPools: number = 1;

        if (launchTypeMode.value === 'manual') {
            tournamentType = launchTournamentType.value;
            numPools = Math.max(1, Math.min(launchTargetCount.value, players.length));
        } else {
            if (players.length === 2) {
                tournamentType = 'elimination';
                numPools = 0;
            } else if (players.length <= 4) {
                tournamentType = 'elimination';
                numPools = 0;
            } else if (players.length <= 6) {
                tournamentType = 'pool';
                numPools = 2;
            } else if (players.length <= 8) {
                tournamentType = 'pool';
                numPools = 2;
            } else {
                tournamentType = 'pool';
                numPools = Math.ceil(players.length / 4);
            }
        }

        if (tournamentType === 'elimination' && players.length % 2 !== 0) {
            throw new Error("Nombre impair de joueurs non supporté en mode élimination sans bye");
        }

        console.log('Mode de lancement:', launchTypeMode.value, 'Type de tournoi:', tournamentType, 'Nombre de poules:', numPools);

        await backendApi.patch(`/tournaments/${tournamentId.value}`, { type: tournamentType }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        await backendApi.patch(`/tournaments/${tournamentId.value}`, { status: 'running' }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });

        if (tournamentType === 'pool') {
            const pools = createPools(players, numPools);
            const poolIdMap: Record<number, number> = {};
            for (const pool of pools) {
                const { data: createdPool } = await backendApi.post(
                    `/tournaments/${tournamentId.value}/pools/`,
                    {
                        name: pool.name || null,
                        player_ids: pool.players.map((p: any) => p.id),
                    },
                    {
                        headers: { Authorization: `Bearer ${authStore.token}` },
                    }
                );
                poolIdMap[pool.id] = createdPool.id;
                console.log("pool id virtuel", pool.id, "-> pool id SQL", createdPool.id);
            }
            for (const pool of pools) {
                const poolSqlId = poolIdMap[pool.id];
                if (!poolSqlId) {
                    console.error("poolSqlId introuvable pour la pool virtuelle id=", pool.id, pool);
                    continue;
                }
                for (const match of pool.matches) {
                    console.log("Création du match de poule avec poolSqlId:", poolSqlId, match);
                    await createAndPersistMatch(match, poolSqlId);
                }
            }
        } else {
            const generatedMatches = generateEliminationMatches(players);
            for (const m of generatedMatches) {
                await createAndPersistMatch(m);
            }
        }

        toast.success('Tournoi lancé !');
        await fetchTournament(tournamentId.value);
        launchingTournamentId.value = null;
    } catch (err) {
        console.error('Erreur de lancement:', err);
        handleError(err, 'Problème lors du lancement');
    } finally {
        loading.value = false;
    }
};

async function generateFinalStage() {
    try {
        let qualified: { user_id: number, name: string, pool_id: number }[] = [];
        let nextRound = currentRound.value + 1;

        // Vérifier les matchs existants pour le tour suivant
        const existingNextRoundMatches = matches.value.filter(
            m => m.pool_id == null && m.round === nextRound
        );
        if (existingNextRoundMatches.length > 0) {
            toast.error(`Le tour ${nextRound} existe déjà. Veuillez compléter ou supprimer les matchs existants.`);
            return;
        }

        if (currentRound.value === 0) {
            // Phase post-poules : sélectionner les joueurs qualifiés
            if (poolIds.value.length === 1) {
                // Cas d'une seule poule : top 4
                const poolMatches = matches.value.filter(m => m.pool_id != null);
                qualified = computePoolRanking(poolMatches).slice(0, 4).map(entry => ({
                    user_id: entry.user_id,
                    name: entry.name,
                    pool_id: poolIds.value[0]
                }));
            } else {
                // Multi-poules : top 3 pour poules de 4+, top 2 pour poules de 3 ou moins
                for (const poolId of poolIds.value) {
                    const poolMatches = matches.value.filter(m => m.pool_id === poolId);
                    const poolSize = new Set(poolMatches.flatMap(m => m.players.map(p => p?.user_id))).size;
                    const numToQualify = poolSize >= 4 ? 3 : 2; // Top 3 pour 4+, top 2 sinon
                    const topPlayers = computePoolRanking(poolMatches).slice(0, numToQualify).map(entry => ({
                        user_id: entry.user_id,
                        name: entry.name,
                        pool_id: poolId
                    }));
                    qualified = qualified.concat(topPlayers);
                }

                // Pour 11 joueurs (3 pools: 4,4,3), on a 3+3+2=8 qualifiés
                // Si plus ou moins de 8, ajuster pour éviter les byes
                if (qualified.length > 8) {
                    // Réduire au top 8 basé sur les victoires/points globaux
                    qualified = qualified
                        .map(player => {
                            const poolMatches = matches.value.filter(m => m.pool_id === player.pool_id);
                            const stats = computePoolRanking(poolMatches).find(e => e.user_id === player.user_id);
                            return { ...player, wins: stats?.wins || 0, points: stats?.points || 0 };
                        })
                        .sort((a, b) => b.wins - a.wins || b.points - a.points)
                        .slice(0, 8);
                } else if (qualified.length < 8 && qualified.length % 2 !== 0) {
                    // Réduire à la puissance de 2 inférieure pour éviter les byes
                    qualified = qualified.slice(0, Math.pow(2, Math.floor(Math.log2(qualified.length))));
                }
            }

            // Organiser les qualifiés avec seeding (top seed vs bas seed)
            const nextMatches: Match[] = [];
            qualified = qualified
                .map(player => {
                    const poolMatches = matches.value.filter(m => m.pool_id === player.pool_id);
                    const stats = computePoolRanking(poolMatches).find(e => e.user_id === player.user_id);
                    return { ...player, wins: stats?.wins || 0, points: stats?.points || 0 };
                })
                .sort((a, b) => b.wins - a.wins || b.points - a.points);
            // Pair top seed vs lower seed, e.g., 1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5
            for (let i = 0; i < qualified.length / 2; i++) {
                nextMatches.push({
                    id: 0,
                    tournament_id: tournamentId.value,
                    match_date: null,
                    players: [
                        { user_id: qualified[i].user_id, name: qualified[i].name, score: null },
                        { user_id: qualified[qualified.length - 1 - i].user_id, name: qualified[qualified.length - 1 - i].name, score: null },
                    ],
                    status: 'pending',
                    round: nextRound,
                    pool_id: undefined,
                });
            }

            if (nextMatches.length === 0) {
                toast.error('Aucun match ne peut être généré pour le tour suivant');
                return;
            }

            console.log('Qualifiés pour tour', nextRound, ':', qualified);
            console.log('Matchs générés pour tour', nextRound, ':', nextMatches);

            for (const match of nextMatches) {
                await createAndPersistMatch(match);
            }
        } else {
            // Rounds éliminatoires suivants : même logique que avant, mais sans byes
            const previousRoundMatches = matches.value.filter(
                m => m.pool_id == null && m.round === currentRound.value
            );
            for (const match of previousRoundMatches) {
                const winner = getMatchWinner(match);
                if (winner) {
                    qualified.push({ user_id: winner.user_id, name: winner.name, pool_id: 0 });
                }
            }

            if (qualified.length < 2) {
                toast.error('Pas assez de joueurs qualifiés pour le tour suivant');
                return;
            }
            if (qualified.length % 2 !== 0) {
                // Réduire à la puissance de 2 inférieure pour éviter les byes
                qualified = qualified.slice(0, Math.pow(2, Math.floor(Math.log2(qualified.length))));
            }

            const nextMatches: Match[] = [];
            const shuffledQualified = [...qualified].sort(() => Math.random() - 0.5);
            for (let i = 0; i < shuffledQualified.length; i += 2) {
                if (i + 1 < shuffledQualified.length) {
                    nextMatches.push({
                        id: 0,
                        tournament_id: tournamentId.value,
                        match_date: null,
                        players: [
                            { user_id: shuffledQualified[i].user_id, name: shuffledQualified[i].name, score: null },
                            { user_id: shuffledQualified[i + 1].user_id, name: shuffledQualified[i + 1].name, score: null },
                        ],
                        status: 'pending',
                        round: nextRound,
                        pool_id: undefined,
                    });
                }
            }

            if (nextMatches.length === 0) {
                toast.error('Aucun match ne peut être généré pour le tour suivant');
                return;
            }

            console.log('Qualifiés pour tour', nextRound, ':', qualified);
            console.log('Matchs générés pour tour', nextRound, ':', nextMatches);

            for (const match of nextMatches) {
                await createAndPersistMatch(match);
            }
        }

        toast.success(`Tour ${nextRound} généré !`);
        await fetchMatches();
        await leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
    } catch (err) {
        console.error('Erreur lors de la génération du tour suivant:', err);
        handleError(err, 'générant le tour suivant');
    }
}

function extractPlayerId(p: any): number | null {
    if (p && typeof p.user_id === 'number') return p.user_id;
    if (p && typeof p.id === 'number') return p.id;
    return null;
}

async function createAndPersistMatch(match: Match, poolId?: number) {
    const playerIds = (match.players || [])
        .map(extractPlayerId)
        .filter((id): id is number => typeof id === 'number');

    if (playerIds.length !== 2) {
        console.warn("Match ignoré (il faut 2 joueurs):", match.players.map(p => p?.name).join(" vs "));
        return;
    }

    console.log("SAUVEGARDE MATCH : ", match.players.map(p => p?.name).join(" vs "));

    const payload: any = {
        tournament_id: tournamentId.value,
        player_ids: playerIds,
        status: "pending",
        round: match.round || 1, // Include round, default to 1 if not specified
    };

    if (poolId !== undefined && poolId !== null) {
        payload.pool_id = poolId;
    }

    await backendApi.post('/tournaments/matches/', payload, {
        headers: { Authorization: `Bearer ${authStore.token}` },
    });
}

const updateMatch = async (match: Match) => {
    try {
        const scoresPayload = match.players.map((player: any, index: number) => ({
            user_id: player.user_id || player.id,
            score: tempScores.value[match.id][index],
        }));
        await backendApi.patch(`/tournaments/matches/${match.id}`, {
            status: 'completed',
            scores: scoresPayload,
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Match mis à jour');
        await fetchMatches();
        await leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
        const currentYear = new Date().getFullYear();
        await leaderboardsStore.fetchSeasonLeaderboard(currentYear, authStore.token);

        // Si le tournoi est fini, clore automatiquement et annoncer le gagnant
        if (isTournamentFinished.value && getTournamentWinner.value) {
            await backendApi.patch(`/tournaments/${tournamentId.value}`, {
                status: 'closed'
            }, {
                headers: { Authorization: `Bearer ${authStore.token}` },
            });
            toast.success(`Tournoi terminé ! Vainqueur : ${getTournamentWinner.value.name}`);
            await fetchTournament(tournamentId.value);
        }
    } catch (err) {
        handleError(err, 'updating match');
    }
};

const getTournamentWinner = computed(() => {
    if (!isTournamentFinished.value) return null;
    const finalMatch = matches.value.find(
        m => m.pool_id == null && m.round === currentRound.value
    );
    if (!finalMatch) return null;
    return getMatchWinner(finalMatch);
});

const startRegisteringPlayer = (tournamentId: number) => {
    registeringTournamentId.value = tournamentId;
    newPlayerName.value = '';
    newPlayerEmail.value = '';
    fetchAllUsers();
};

const cancelRegisteringPlayer = () => {
    registeringTournamentId.value = null;
    newPlayerName.value = '';
    newPlayerEmail.value = '';
};

const registerExistingUserToTournament = async (userId: number | null, tournamentId: number) => {
    if (userId === null) return;
    try {
        await backendApi.post('/tournaments/registrations/', {
            user_id: userId,
            tournament_id: tournamentId,
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        selectedUserId.value = null;
        await fetchPlayers();
        toast.success('Joueur existant ajouté !');
    } catch (err) {
        handleError(err, 'registering existing user');
    }
};

const registerNewPlayer = async (tournamentId: number) => {
    try {
        const playerData = {
            name: newPlayerName.value,
            email: newPlayerEmail.value || null,
            tournament_id: tournamentId,
        };
        await backendApi.post('/tournaments/register-player', playerData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        await fetchPlayers();
        toast.success('Joueur inscrit avec succès.');
        newPlayerName.value = '';
        newPlayerEmail.value = '';
    } catch (err) {
        handleError(err, 'registering player');
    }
};

const unregisterPlayer = async (playerId: number, tournamentId: number) => {
    try {
        await backendApi.delete(`/tournaments/registrations/${playerId}/${tournamentId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        });
        toast.success('Joueur désinscrit avec succès.');
        await fetchPlayers();
    } catch (err) {
        handleError(err, 'unregistering player');
    }
};

const resetTournament = async (tournamentId: number) => {
    loading.value = true;
    try {
        await backendApi.post(`/tournaments/${tournamentId}/reset`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        await fetchTournament(tournamentId);
        toast.success('Tournoi réinitialisé !');
    } catch (err) {
        handleError(err, 'erreur pendant la réinitialisation');
    } finally {
        loading.value = false;
    }
};

const closeTournament = async (tournamentId: number) => {
    try {
        const updatePayload = {
            status: 'closed',
        };
        await backendApi.patch(`/tournaments/${tournamentId}`, updatePayload, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Tournoi clôturé avec succès.');
        await fetchTournament(tournamentId);
    } catch (err) {
        handleError(err, 'closing tournament');
    }
};

onMounted(() => {
    fetchTournament(tournamentId.value);
    tournamentStore.fetchTournamentDetail(tournamentId.value);
    leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
    const currentYear = new Date().getFullYear();
    leaderboardsStore.fetchSeasonLeaderboard(currentYear, authStore.token);
});
</script>

<template>
    <div v-if="authStore.scopes.includes('admin')">
        <div v-if="loading">Chargement...</div>
        <div v-if="error" class="error">{{ error }}</div>

        <div v-if="tournament" class="module">
            <h2>Gérer le tournoi</h2>
            <div class="tournament-details">
                <h3>Détails</h3>
                <p>Nom : {{ tournament.name }}</p>
                <p>Type : {{ tournament.type || 'Non défini' }}</p>
                <p>Description : {{ tournament.description || 'Aucune description' }}</p>
                <p>Date de début : {{ new Date(tournament.start_date.split('T')[0]).toLocaleDateString() }}</p>
                <p>Statut : {{ tournament.status }}</p>
                <button @click="startEditing">Modifier le tournoi</button>
            </div>

            <!-- Formulaire de modification du tournoi -->
            <div v-if="isEditing" class="tournament-edit-form">
                <h3>Modifier le tournoi</h3>
                <label>Nom :
                    <input v-model="editForm.name" class="form-input" />
                </label>
                <label>Description :
                    <textarea v-model="editForm.description" class="form-input" />
                </label>
                <label>Date de début :
                    <input v-model="editForm.start_date" type="date" class="form-input" />
                </label>
                <label>Type :
                    <select v-model="editForm.type" class="form-input">
                        <option value="pool">Poule</option>
                        <option value="elimination">Élimination</option>
                    </select>
                </label>
                <label>Statut :
                    <select v-model="editForm.status" class="form-input">
                        <option value="open">Ouvert</option>
                        <option value="running">En cours</option>
                        <option value="closed">Terminé</option>
                    </select>
                </label>
                <button @click="updateTournament">Mettre à jour le tournoi</button>
                <button @click="cancelEditing">Annuler</button>
            </div>

            <button v-if="tournament" @click="openProjection">
                Projeter l’arborescence
            </button>

            <div class="tournament-actions">
                <button v-if="tournament.status === 'open'" @click="startLaunchingTournament(tournament.id)">
                    Lancer
                </button>
                <button v-if="tournament.status === 'running'" @click="closeTournament(tournament.id)">
                    Clôturer
                </button>
                <button @click="deleteTournament">Supprimer</button>
                <button @click="resetTournament(tournament.id)">Réinitialiser</button>
            </div>

            <!-- Formulaire de lancement du tournoi -->
            <div v-if="launchingTournamentId === tournament.id" class="launch-form module">
                <h4>Lancer {{ tournament.name }}</h4>
                <label>Nombre de cibles disponibles (optionnel) :
                    <input v-model.number="launchTargetCount" type="number" min="1" class="form-input" />
                </label>
                <label>Mode de type :
                    <select v-model="launchTypeMode" class="form-input">
                        <option value="auto">Sélection automatique</option>
                        <option value="manual">Sélection manuelle</option>
                    </select>
                </label>
                <label v-if="launchTypeMode === 'manual'">Type de tournoi :
                    <select v-model="launchTournamentType" class="form-input">
                        <option value="pool">Poule</option>
                        <option value="elimination">Élimination</option>
                    </select>
                </label>
                <button @click="launchTournament()">Lancer</button>
                <button @click="cancelLaunchingTournament">Annuler</button>
            </div>

            <div v-if="tournament.status === 'open'" class="players-section">
                <h4>Joueurs inscrits</h4>
                <table v-if="players?.length">
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="player in players" :key="player.id">
                            <td>{{ player.name }}</td>
                            <td>
                                <button title="Désinscrire ce joueur"
                                    style="color: red; background: none; border: none; font-size: 1.2em; cursor: pointer;"
                                    @click="unregisterPlayer(player.id, tournament.id)">✖️</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <p v-else>Aucun joueur inscrit pour le moment.</p>
                <button @click="startRegisteringPlayer(tournament.id)">Inscrire un joueur</button>
                <!-- Formulaire d'inscription d'un joueur -->
                <div v-if="registeringTournamentId === tournament.id" class="register-form module">
                    <h4>Inscrire un joueur pour {{ tournament.name }}</h4>
                    <label>Choisir un joueur existant :
                        <select v-model="selectedUserId" class="form-input">
                            <option :value="null">-- Sélectionner --</option>
                            <option v-for="user in selectableUsers" :value="user.id" :key="user.id">
                                {{ user.name }}
                            </option>
                        </select>
                    </label>
                    <button :disabled="!selectedUserId"
                        @click="registerExistingUserToTournament(selectedUserId, tournament.id)">
                        Ajouter le joueur sélectionné
                    </button>
                    <hr />
                    <label>Ou ajouter un nouveau joueur :</label>
                    <label>Nom du joueur :
                        <input v-model="newPlayerName" class="form-input" required />
                    </label>
                    <label>Email du joueur (optionnel) :
                        <input v-model="newPlayerEmail" class="form-input" />
                    </label>
                    <button @click="registerNewPlayer(tournament.id)">Inscrire</button>
                    <button @click="cancelRegisteringPlayer">Fermer</button>
                </div>
            </div>

            <!-- Classements par poule -->
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

            <div v-if="tournament.status === 'running' || tournament.status === 'closed'" class="matches-section">
                <h4>Matchs</h4>
                <div v-for="round in Array.from({ length: currentRound + 1 }, (_, i) => i)" :key="round">
                    <h5>{{ round === 0 ? 'Poules' : `Tour ${round}` }}</h5>
                    <table
                        v-if="matches.filter(m => (round === 0 && m.pool_id != null) || (m.pool_id == null && m.round === round)).length">
                        <thead>
                            <tr>
                                <th>Joueurs</th>
                                <th>Statut</th>
                                <th>Scores</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="match in matches.filter(m => (round === 0 && m.pool_id != null) || (m.pool_id == null && m.round === round && m.players.length === 2))"
                                :key="match.id">
                                <td>{{(match.players || []).map((p: any) => p.name).join(' vs ')}}</td>
                                <td>{{ match.status }}</td>
                                <td>
                                    <div v-if="match.status === 'completed'">
                                        {{(match.players || []).map((p: any) => p.score ?? 'N/A').join(', ')}}
                                    </div>
                                    <div v-else>
                                        <input v-for="(_, index) in (match.players || [])"
                                            v-model="tempScores[match.id][index]" type="number" :key="index" />
                                    </div>
                                </td>
                                <td>
                                    <button v-if="match.status === 'pending'" @click="updateMatch(match)">Mettre à jour
                                        les scores</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else>Aucun match pour ce tour.</p>
                </div>

                <!-- Bouton pour générer le tour suivant ou afficher le gagnant-->
                <div v-if="isTournamentFinished && getTournamentWinner">
                    <h4>Tournoi terminé !</h4>
                    <p>Vainqueur : {{ getTournamentWinner.name }}</p>
                </div>
                <button v-else-if="isCurrentRoundFinished" @click="generateFinalStage">
                    Générer le tour {{ currentRound === 0 ? 'des éliminatoires' : currentRound + 1 }}
                </button>
            </div>
        </div>
    </div>

    <div v-if="!authStore.isAuthenticated" class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour gérer les tournois.</p>
    </div>
</template>