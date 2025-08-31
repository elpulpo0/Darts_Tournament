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
                <p>Mode : {{ tournament.mode || 'Non défini' }}</p>
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
                <label>Mode :
                    <select v-model="editForm.mode" class="form-input">
                        <option value="single">Single</option>
                        <option value="double">Double</option>
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

            <button v-if="tournament && ['running', 'closed'].includes(tournament.status)" @click="openProjection">
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

            <div v-if="tournament.status === 'open'" class="participants-section">
                <h4>Joueurs inscrits ({{ registeredUsersCount }})</h4>
                <table v-if="tournamentStore.registeredUsers?.length">
                    <thead>
                        <tr>
                            <th>Nom</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in tournamentStore.registeredUsers" :key="user.id">
                            <td>{{ user.name }}</td>
                            <td>
                                <button title="Désinscrire ce joueur" class="delete-btn"
                                    @click="unregisterPlayer(user.id, tournament.id)">✖️</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <p v-else>Aucun joueur inscrit pour le moment.</p>

                <div v-if="tournament.mode === 'double'" class="participants-section">
                    <h4>Participants ({{ participantsCount }})</h4>
                    <table v-if="tournamentStore.participants?.length">
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Membres</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="participant in tournamentStore.participants" :key="participant.id">
                                <td>{{ getParticipantDisplayName(participant) }}</td>
                                <td>{{participant.users.map(u => u.name).join(' & ')}}</td>
                                <td>
                                    <button title="Supprimer ce participant" class="delete-btn"
                                        @click="deleteParticipant(participant.id, tournament.id)">✖️</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else>Aucun participant pour le moment.</p>
                </div>

                <button @click="startRegisteringPlayer(tournament.id)">
                    Inscrire un joueur
                </button>
                <button v-if="tournament.mode === 'double'" @click="startCreatingParticipant(tournament.id)">
                    Créer une équipe
                </button>

                <!-- Formulaire d'inscription d'un joueur -->
                <div v-if="registeringTournamentId === tournament.id" class="module">
                    <h4>Inscrire un joueur pour {{ tournament.name }}</h4>
                    <label>Choisir un joueur existant :
                        <select v-model="selectedUserId">
                            <option :value="null">-- Sélectionner --</option>
                            <option v-for="user in selectableUsers" :value="user.id" :key="user.id">
                                {{ user.name }}
                            </option>
                        </select>
                    </label>
                    <div>
                        <button :disabled="!selectedUserId"
                            @click="registerExistingUserToTournament(selectedUserId, tournament.id)">
                            Ajouter le joueur sélectionné
                        </button>
                        <button @click="cancelRegisteringPlayer">
                            Fermer
                        </button>
                    </div>
                </div>

                <!-- Formulaire de création d'équipe (participant) -->
                <div v-if="creatingParticipantTournamentId === tournament.id" class="register-form module">
                    <h4>Créer une équipe pour {{ tournament.name }}</h4>
                    <label>Nom de l'équipe :
                        <input v-model="newTeamName" required />
                    </label>
                    <label>Joueurs de l’équipe :
                        <select v-model="selectedTeamUsers" multiple :size="selectableParticipantUsers.length">
                            <option v-for="user in selectableParticipantUsers" :value="user.id" :key="user.id">
                                {{ user.name }}
                            </option>
                        </select>
                    </label>
                    <button @click="createParticipant(tournament.id)">Créer équipe</button>
                    <button @click="cancelCreatingParticipant">Fermer</button>
                </div>
            </div>

            <!-- Classements par poule -->
            <h4 v-if="leaderboardsStore.poolsLeaderboard.length">Classements par poule</h4>
            <div v-if="leaderboardsStore.poolsLeaderboardLoading">Chargement des classements par poule...</div>
            <div v-if="leaderboardsStore.poolsLeaderboardError" class="error">{{ leaderboardsStore.poolsLeaderboardError
            }}</div>
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
                            <tr v-for="entry in poolLeaderboard.leaderboard" :key="entry.participant_id">
                                <td>{{getParticipantDisplayName(tournamentStore.participants.find(p => p.id ===
                                    entry.participant_id) ?? null)}}</td>
                                <td>{{ entry.wins }}</td>
                                <td>{{ entry.total_manches }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div v-if="tournament.status === 'running' || tournament.status === 'closed'" class="matches-section">
                <h4>Matchs</h4>
                <div v-for="round in Array.from({ length: currentRound + 1 }, (_, i) => i)" :key="round">
                    <h5>{{ round === 0 ? 'Poules' : `Tour ${round}` }}</h5>
                    <table
                        v-if="matches.filter(m => (round === 0 && m.pool_id != null) || (m.pool_id == null && m.round === round)).length">
                        <thead>
                            <tr>
                                <th>Participants</th>
                                <th>Statut</th>
                                <th>Scores</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="match in matches.filter(m => (round === 0 && m.pool_id != null) || (m.pool_id == null && m.round === round && m.participants.length === 2))"
                                :key="match.id">
                                <td>
                                    {{match.participants.map(p => getParticipantDisplayName(p)).join(' vs ')}}
                                </td>
                                <td>{{ match.status }}</td>
                                <td>
                                    <div v-if="match.status === 'completed'">
                                        {{match.participants.map(p => p?.score ?? 'N/A').join(', ')}}
                                    </div>
                                    <div v-else>
                                        <input v-for="(_, index) in match.participants"
                                            v-model="tempScores[match.id][index]" type="number" :key="index" />
                                    </div>
                                </td>
                                <td>
                                    <button v-if="match.status === 'pending'" @click="updateMatch(match)">Mettre à jour
                                        les
                                        scores</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <p v-else>Aucun match pour ce tour.</p>
                </div>

                <div v-if="isTournamentFinished && getTournamentWinner">
                    <h4>Tournoi terminé !</h4>
                    <p>Vainqueur : {{ getParticipantDisplayName(getTournamentWinner) }}</p>

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

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { createPools, generateEliminationMatches, getMatchWinner } from '../functions/tournamentStructure';
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
const matches = ref<Match[]>([]);
const loading = ref(false);
const error = ref('');
const registeringTournamentId = ref<number | null>(null);
const creatingParticipantTournamentId = ref<number | null>(null);
const editForm = ref<any>({});
const newTeamName = ref<string>('');
const tempScores = ref<{ [matchId: number]: number[] }>({});
const launchingTournamentId = ref<number | null>(null);
const launchTargetCount = ref<number>(4);
const launchTypeMode = ref<'auto' | 'manual'>('auto');
const launchTournamentType = ref<'pool' | 'elimination'>('pool');
const isEditing = ref(false);
const allUsers = ref<User[]>([]);
const selectedUserId = ref<number | null>(null);
const selectedTeamUsers = ref<number[]>([]);

const registeredUsersCount = computed(() => tournamentStore.registeredUsers?.length || 0);
const participantsCount = computed(() => tournamentStore.participants?.length || 0);

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
    if (currentRound.value === 0) return false;
    const currentRoundMatches = matches.value.filter(
        m => m.pool_id == null && m.round === currentRound.value
    );
    if (currentRoundMatches.length === 1 && currentRoundMatches[0].status === 'completed') {
        const winner = getMatchWinner(currentRoundMatches[0]);
        return !!winner;
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

const selectableUsers = computed(() => {
    const alreadyRegisteredIds = new Set(tournamentStore.registeredUsers.map(user => user.id));
    return allUsers.value.filter(user => !alreadyRegisteredIds.has(user.id));
});

const selectableParticipantUsers = computed(() => {
    return tournamentStore.registeredUsers.filter(user =>
        !tournamentStore.participants.some(p => p.users.some(u => u.id === user.id))
    );
});

const getParticipantDisplayName = (participant: MatchParticipantSchema | Participant | null): string => {
    if (!participant) return 'N/A';

    let fullParticipant: MatchParticipantSchema | Participant = participant;
    // Check for participant_id (MatchParticipantSchema) or id (Participant)
    const participantId = 'participant_id' in participant ? participant.participant_id : participant.id;
    if ((!participant.users || participant.users.length === 0) && participantId) {
        const storedParticipant = tournamentStore.participants.find(p => p.id === participantId);
        if (storedParticipant) {
            fullParticipant = storedParticipant;
        }
    }

    const baseName = fullParticipant.name || (fullParticipant.users?.length === 1 ? fullParticipant.users[0]?.name || 'N/A' : 'N/A');
    if (fullParticipant.users?.length === 2) {
        const userNames = fullParticipant.users.map(u => u.name || 'Unknown').join(' & ');
        return `${baseName} (${userNames})`;
    }

    return baseName;
};

const openProjection = () => {
    if (!tournament.value) return;
    router.push(`/tournaments/${tournament.value.id}/projection`);
};

const fetchTournament = async (id: number) => {
    loading.value = true;
    error.value = '';
    try {
        const { data } = await backendApi.get(`/tournaments/${id}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        console.log('Tournament:', data); // Debug log
        tournament.value = data;
        resetEditForm(data);
        await Promise.all([
            tournamentStore.fetchRegisteredUsers(id),
            tournamentStore.fetchParticipants(id),
        ]);
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
        mode: data.mode,
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

const fetchMatches = async () => {
    try {
        const { data } = await backendApi.get(`/tournaments/matches/tournament/${tournamentId.value}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        matches.value = data;
        for (const match of data) {
            if (match.status === 'pending') {
                tempScores.value[match.id] = match.participants.map(() => 0);
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
        await fetchTournament(tournamentId.value);
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
        const { data: participants } = await backendApi.get(`/tournaments/${tournamentId.value}/participants`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        if ((participants?.length ?? 0) < 4) throw new Error("Minimum 4 participants requis");

        let tournamentType: 'pool' | 'elimination';
        let numPools: number = 1;

        if (launchTypeMode.value === 'manual') {
            tournamentType = launchTournamentType.value;
            numPools = Math.max(1, Math.min(launchTargetCount.value, participants.length));
            if (tournamentType === 'elimination' && participants.length % 2 !== 0) {
                throw new Error("Nombre impair de participants non supporté en mode élimination sans ajustement");
            }
        } else {
            const N = participants.length;
            if (N <= 4) {
                tournamentType = 'elimination';
                numPools = 0;
            } else if (N <= 12) {
                tournamentType = 'pool';
                numPools = N === 5 ? 1 : 2; // Single pool for 5 participants, otherwise 2 pools
            } else if (N <= 24) {
                tournamentType = 'pool';
                numPools = Math.ceil(N / 5);
            } else {
                tournamentType = 'pool';
                numPools = Math.ceil(N / 8);
            }
        }

        console.log('Mode de lancement:', launchTypeMode.value, 'Type de tournoi:', tournamentType, 'Nombre de poules:', numPools);

        await backendApi.patch(`/tournaments/${tournamentId.value}`, {
            type: tournamentType,
            status: 'running'
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });

        if (tournamentType === 'pool') {
            const pools = createPools(participants, numPools);
            const poolIdMap: Record<number, number> = {};
            for (const pool of pools) {
                const { data: createdPool } = await backendApi.post(
                    `/tournaments/${tournamentId.value}/pools`,
                    {
                        name: pool.name || null,
                        participant_ids: pool.participants.map((p: Participant) => p.id),
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
            const generatedMatches = generateEliminationMatches(participants);
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
        let qualified: { participant_id: number, name: string, pool_id: number }[] = [];
        let nextRound = currentRound.value + 1;

        const existingNextRoundMatches = matches.value.filter(
            m => m.pool_id == null && m.round === nextRound
        );
        if (existingNextRoundMatches.length > 0) {
            toast.error(`Le tour ${nextRound} existe déjà.Veuillez compléter ou supprimer les matchs existants.`);
            return;
        }

        if (currentRound.value === 0) {
            const totalParticipants = new Set(matches.value.flatMap(m => m.participants.map(p => p?.participant_id))).size;
            const targetQualifiers = totalParticipants <= 12 ? 8 : totalParticipants <= 24 ? 16 : 32;

            if (poolIds.value.length === 1) {
                const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === poolIds.value[0]);
                if (poolLeaderboard) {
                    qualified = poolLeaderboard.leaderboard.slice(0, Math.min(targetQualifiers, poolLeaderboard.leaderboard.length)).map(entry => ({
                        participant_id: entry.participant_id,
                        name: entry.name,
                        pool_id: poolIds.value[0]
                    }));
                }
            } else {
                for (const poolId of poolIds.value) {
                    const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === poolId);
                    if (poolLeaderboard) {
                        const poolSize = new Set(matches.value.filter(m => m.pool_id === poolId)
                            .flatMap(m => m.participants.map(p => p?.participant_id))).size;
                        const numToQualify = poolSize >= 4 ? 4 : 2; // Top 4 pour ≥4, top 2 pour <4
                        const topParticipants = poolLeaderboard.leaderboard.slice(0, numToQualify).map(entry => ({
                            participant_id: entry.participant_id,
                            name: entry.name,
                            pool_id: poolId
                        }));
                        qualified = qualified.concat(topParticipants);
                    }
                }
            }

            qualified = qualified
                .map(participant => {
                    const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === participant.pool_id);
                    const stats = poolLeaderboard?.leaderboard.find(e => e.participant_id === participant.participant_id);
                    return { ...participant, wins: stats?.wins || 0, total_manches: stats?.total_manches || 0 };
                })
                .sort((a, b) => b.wins - a.wins || b.total_manches - a.total_manches);

            if (qualified.length > targetQualifiers) {
                qualified = qualified.slice(0, targetQualifiers);
            } else if (qualified.length < targetQualifiers) {
                qualified = qualified.slice(0, Math.pow(2, Math.floor(Math.log2(qualified.length))));
            }

            const nextMatches: Match[] = [];
            for (let i = 0; i < qualified.length / 2; i++) {
                nextMatches.push({
                    id: 0,
                    tournament_id: tournamentId.value,
                    match_date: null,
                    participants: [
                        { participant_id: qualified[i].participant_id, name: qualified[i].name, score: null, users: [] },
                        { participant_id: qualified[qualified.length - 1 - i].participant_id, name: qualified[qualified.length - 1 - i].name, score: null, users: [] },
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
            const previousRoundMatches = matches.value.filter(
                m => m.pool_id == null && m.round === currentRound.value
            );
            for (const match of previousRoundMatches) {
                const winner = getMatchWinner(match);
                if (winner) {
                    qualified.push({ participant_id: winner.participant_id, name: winner.name, pool_id: 0 });
                }
            }

            if (qualified.length < 2) {
                toast.error('Pas assez de participants qualifiés pour le tour suivant');
                return;
            }

            const nextMatches: Match[] = [];
            qualified = qualified
                .map(participant => {
                    const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === participant.pool_id);
                    const stats = poolLeaderboard?.leaderboard.find(e => e.participant_id === participant.participant_id);
                    return { ...participant, wins: stats?.wins || 0, total_manches: stats?.total_manches || 0 };
                })
                .sort((a, b) => b.wins - a.wins || b.total_manches - a.total_manches);
            for (let i = 0; i < qualified.length / 2; i++) {
                nextMatches.push({
                    id: 0,
                    tournament_id: tournamentId.value,
                    match_date: null,
                    participants: [
                        { participant_id: qualified[i].participant_id, name: qualified[i].name, score: null, users: [] },
                        { participant_id: qualified[qualified.length - 1 - i].participant_id, name: qualified[qualified.length - 1 - i].name, score: null, users: [] },
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
        }

        toast.success(`Tour ${nextRound} généré!`);
        await fetchMatches();
        await leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
    } catch (err) {
        console.error('Erreur lors de la génération du tour suivant:', err);
        handleError(err, 'générant le tour suivant');
    }
}

async function createAndPersistMatch(match: Match, poolId?: number) {
    const participantIds = (match.participants || [])
        .map((p): number | null => p?.participant_id || null)
        .filter((id): id is number => typeof id === 'number');

    if (participantIds.length !== 2) {
        console.warn("Match ignoré (il faut 2 participants):", match.participants.map(p => p?.name).join(" vs "));
        return;
    }

    console.log("SAUVEGARDE MATCH : ", match.participants.map(p => p?.name).join(" vs "));

    const payload: any = {
        tournament_id: tournamentId.value,
        participant_ids: participantIds,
        status: "pending",
        round: match.round || 1,
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
        const scoresPayload = match.participants.map((participant: any, index: number) => ({
            participant_id: participant.participant_id || participant.id,
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
    newTeamName.value = '';
    selectedTeamUsers.value = [];
    fetchAllUsers();
};

const startCreatingParticipant = (tournamentId: number) => {
    creatingParticipantTournamentId.value = tournamentId;
    newTeamName.value = '';
    selectedTeamUsers.value = [];
    tournamentStore.fetchRegisteredUsers(tournamentId);
};

const cancelRegisteringPlayer = () => {
    registeringTournamentId.value = null;
    newTeamName.value = '';
    selectedTeamUsers.value = [];
};

const cancelCreatingParticipant = () => {
    creatingParticipantTournamentId.value = null;
    newTeamName.value = '';
    selectedTeamUsers.value = [];
};

const registerExistingUserToTournament = async (userId: number | null, tournamentId: number) => {
    if (userId === null) return;
    try {
        await backendApi.post('/tournaments/register-player', {
            user_id: userId,
            tournament_id: tournamentId,
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        selectedUserId.value = null;
        await tournamentStore.fetchRegisteredUsers(tournamentId);
        // Ne pas appeler fetchParticipants ici en mode double, car le joueur n'est pas encore un participant
        if (tournament.value?.mode !== 'double') {
            await tournamentStore.fetchParticipants(tournamentId);
        }
        toast.success('Joueur existant ajouté !');
    } catch (err) {
        handleError(err, 'registering existing user');
    }
};

const createParticipant = async (tournamentId: number) => {
    if (!newTeamName.value || selectedTeamUsers.value.length !== 2) {
        toast.error('Veuillez sélectionner exactement 2 joueurs et un nom pour l’équipe.');
        return;
    }
    try {
        const participantData = {
            name: newTeamName.value,
            user_ids: selectedTeamUsers.value,
        };
        await backendApi.post(`/tournaments/${tournamentId}/participants`, participantData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Équipe créée.');
        await tournamentStore.fetchRegisteredUsers(tournamentId);
        await tournamentStore.fetchParticipants(tournamentId);
        newTeamName.value = '';
        selectedTeamUsers.value = [];
        creatingParticipantTournamentId.value = null;
    } catch (err) {
        handleError(err, 'création de l’équipe');
    }
};

const unregisterPlayer = async (userId: number, tournamentId: number) => {
    try {
        await backendApi.delete(`/tournaments/registrations/user/${userId}/${tournamentId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        });
        toast.success('Joueur désinscrit avec succès.');
        await tournamentStore.fetchRegisteredUsers(tournamentId);
        await tournamentStore.fetchParticipants(tournamentId);
    } catch (err) {
        handleError(err, 'unregistering player');
    }
};

const deleteParticipant = async (participantId: number, tournamentId: number) => {
    try {
        await backendApi.delete(`/tournaments/${tournamentId}/participants/${participantId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` }
        });
        toast.success('Participant supprimé avec succès.');
        await tournamentStore.fetchRegisteredUsers(tournamentId);
        await tournamentStore.fetchParticipants(tournamentId);
    } catch (err) {
        handleError(err, 'deleting participant');
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
    tournamentStore.fetchParticipants(tournamentId.value);
    leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);
});
</script>