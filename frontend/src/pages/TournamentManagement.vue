<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="authStore.scopes.includes('editor')">
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
                    <label>Mode :
                        <select v-model="editForm.mode" class="form-input">
                            <option value="single">Single</option>
                            <option value="double">Double</option>
                        </select>
                    </label>
                    <button @click="updateTournament">Mettre à jour le tournoi</button>
                    <button @click="cancelEditing">Annuler</button>
                </div>

                <button v-if="tournament.status === 'open'" @click="closeRegistrations(tournament.id)">
                    Fermer les inscriptions
                </button>
                <button v-if="tournament.status === 'closed'" @click="openRegistrations(tournament.id)">
                    Ouvrir les inscriptions
                </button>

                <button v-if="tournament && ['running', 'finished'].includes(tournament.status)"
                    @click="openProjection">
                    Projeter l’arborescence
                </button>

                <div class="tournament-actions">
                    <button v-if="tournament.status === 'open' || tournament.status === 'closed'"
                        @click="startLaunchingTournament(tournament.id)">
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

                <div v-if="tournament.status === 'open' || tournament.status === 'closed'" class="participants-section">
                    <h4>Joueurs inscrits ({{ registeredUsersCount }})</h4>
                    <table v-if="tournamentStore.registeredUsers?.length">
                        <thead>
                            <tr>
                                <th>Nom</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="user in unregisteredTeamUsers" :key="user.id">
                                <td>{{ user.name ? user.nickname + ' (' + user.name + ')' : user.nickname }}</td>
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
                                    <td>{{ participant.name }}</td>
                                    <td
                                        :title="participant.users.map(u => u.name || u.nickname || 'Inconnu').join(' & ')">
                                        {{participant.users.map(u => u.nickname).join(' & ')}}
                                    </td>
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
                                    {{ user.name ? user.nickname + ' (' + user.name + ')' : user.nickname }}
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
                                    {{ user.name ? user.nickname + ' (' + user.name + ')' : user.nickname }}
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
                <div v-if="leaderboardsStore.poolsLeaderboardError" class="error">{{
                    leaderboardsStore.poolsLeaderboardError
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

                <p>{{matches.filter(m => m.status === 'pending').length}} matchs en attente de validation.</p>

                <div v-if="tournament.status === 'running' || tournament.status === 'finished'" class="matches-section">
                    <h4>Matchs</h4>
                    <!-- Section Barrage -->
                    <div v-if="hasBarrage">
                        <h5>Barrage</h5>
                        <table>
                            <thead>
                                <tr>
                                    <th>Cible</th>
                                    <th>Participants</th>
                                    <th>Statut</th>
                                    <th>Scores</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(match, index) in matches.filter(m => m.round === 0 && m.pool_id == null && m.participants.length === 2)"
                                    :key="match.id">
                                    <td>{{ getTargetNumber(index, launchTargetCount) }}</td>
                                    <td :title="match.participants.map(p => getParticipantName(p)).join(' vs ')">
                                        {{match.participants.map(p => getParticipantDisplayNickname(p)).join(' vs ')}}
                                    </td>
                                    <td>{{ match.status }}</td>
                                    <td>
                                        <div v-if="match.status === 'completed'">
                                            {{match.participants.map(p => p?.score ?? 'N/A').join(', ')}}
                                        </div>
                                        <div v-else class="score-inputs">
                                            <input v-for="(_, index) in match.participants"
                                                v-model="tempScores[match.id][index]" type="number" :key="index" />
                                        </div>
                                    </td>
                                    <td>
                                        <button v-if="match.status === 'pending'" class="valid-btn"
                                            title="Valider les scores" @click="updateMatch(match)">✔️</button>
                                        <button v-if="match.status === 'completed'" class="edit-btn"
                                            title="Réinitialiser les scores"
                                            @click="cancelMatchScores(match.id)">✖️</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <!-- Section Poules -->
                    <div v-if="poolIds.length">
                        <h5>Poules</h5>
                        <div v-for="poolId in poolIds" :key="poolId">
                            <h6>{{ getPoolName(poolId) }} (Cible {{ getTargetNumber(poolId, launchTargetCount) }})
                            </h6>
                            <table
                                v-if="matches.filter(m => m.pool_id === poolId && m.participants.length === 2).length">
                                <thead>
                                    <tr>
                                        <th>Participants</th>
                                        <th>Statut</th>
                                        <th>Scores</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="match in matches.filter(m => m.pool_id === poolId && m.participants.length === 2)"
                                        :key="match.id">
                                        <td :title="match.participants.map(p => getParticipantName(p)).join(' vs ')">
                                            {{match.participants.map(p =>
                                                getParticipantDisplayNickname(p)).join(' vs ')}}
                                        </td>
                                        <td>{{ match.status }}</td>
                                        <td>
                                            <div v-if="match.status === 'completed'">
                                                {{match.participants.map(p => p?.score ?? 'N/A').join(', ')}}
                                            </div>
                                            <div v-else class="score-inputs">
                                                <input v-for="(_, index) in match.participants"
                                                    v-model="tempScores[match.id][index]" type="number"
                                                    @keyup.enter="updateMatch(match)" :key="index" />
                                            </div>
                                        </td>
                                        <td>
                                            <button v-if="match.status === 'pending'" class="valid-btn"
                                                title="Valider les scores" @click="updateMatch(match)">✔️</button>
                                            <button v-if="match.status === 'completed'" class="edit-btn"
                                                title="Réinitialiser les scores"
                                                @click="cancelMatchScores(match.id)">✖️</button>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            <p v-else>Aucun match pour {{ getPoolName(poolId) }}.</p>
                        </div>
                    </div>

                    <!-- Section Tours d'élimination -->
                    <div v-if="currentRound > 0">
                        <div v-for="round in Array.from({ length: currentRound }, (_, i) => i + 1)" :key="round">
                            <h5>Tour {{ round }}</h5>
                            <table
                                v-if="matches.filter(m => m.pool_id == null && m.round === round && m.participants.length === 2).length">
                                <thead>
                                    <tr>
                                        <th>Cible</th>
                                        <th>Participants</th>
                                        <th>Statut</th>
                                        <th>Scores</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(match, index) in matches.filter(m => m.pool_id == null && m.round === round && m.participants.length === 2)"
                                        :key="match.id">
                                        <td>{{ getNonPoolTargetNumber(index, launchTargetCount) }}</td>
                                        <td :title="match.participants.map(p => getParticipantName(p)).join(' vs ')">
                                            {{match.participants.map(p =>
                                                getParticipantDisplayNickname(p)).join(' vs ')}}
                                        </td>
                                        <td>{{ match.status }}</td>
                                        <td>
                                            <div v-if="match.status === 'completed'">
                                                {{match.participants.map(p => p?.score ?? 'N/A').join(', ')}}
                                            </div>
                                            <div v-else class="score-inputs">
                                                <input v-for="(_, index) in match.participants"
                                                    v-model="tempScores[match.id][index]" type="number" :key="index" />
                                            </div>
                                        </td>
                                        <td>
                                            <button v-if="match.status === 'pending'" class="valid-btn"
                                                title="Valider les scores" @click="updateMatch(match)">✔️</button>
                                            <button v-if="match.status === 'completed'" class="edit-btn"
                                                title="Réinitialiser les scores"
                                                @click="cancelMatchScores(match.id)">✖️</button>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            <p v-else>Aucun match pour ce tour.</p>
                        </div>
                    </div>

                    <div v-if="isTournamentFinished && getTournamentWinner">
                        <h4>Tournoi terminé !</h4>
                        <p>Vainqueur : {{ getParticipantDisplayNickname(getTournamentWinner) }}</p>
                    </div>
                    <button v-else-if="showGenerateButton" @click="generateFinalStage">
                        Générer {{ currentRound === 0 && hasBarrage ? (tournament?.type === 'pool' ?
                            'les poules' : 'la phase suivante') : `le tour ${currentRound + 1}` }}
                    </button>
                </div>
            </div>
        </div>
        <div v-if="!authStore.scopes.includes('editor')">
            <div class="module module-prel">
                <p>Vous n'avez pas les droits suffisants pour accéder à cette section</p>
            </div>
        </div>
    </div>
    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour gérer les tournois.</p>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { createPools, generateEliminationMatches, getMatchWinner, participantToMatchParticipant } from '../functions/tournamentStructure';
import { handleError } from '../functions/utils';
import { useRoute } from 'vue-router';
import { useRouter } from 'vue-router';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';
import { useTournamentStore } from '../stores/useTournamentStore';
import { getParticipantDisplayNickname, getParticipantName } from '../functions/management';

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

const hasBarrage = computed(() => {
    const result = matches.value.some(m => m.round === 0 && m.pool_id == null);
    console.log('hasBarrage:', result, 'Matches with round 0 and pool_id null:', matches.value.filter(m => m.round === 0 && m.pool_id == null));
    return result;
});

const closeRegistrations = async (tournamentId: number) => {
    try {
        await backendApi.patch(`/tournaments/${tournamentId}/registrations/close`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Inscriptions fermées avec succès.');
        await fetchTournament(tournamentId);
    } catch (err) {
        handleError(err, 'closing registrations');
    }
};

const openRegistrations = async (tournamentId: number) => {
    try {
        await backendApi.patch(`/tournaments/${tournamentId}/registrations/open`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Inscriptions ouvertes avec succès.');
        await fetchTournament(tournamentId);
    } catch (err) {
        handleError(err, 'opening registrations');
    }
};

// Fonction pour obtenir le numéro de la cible en fonction du pool_id
const getTargetNumber = (poolId: number | undefined, totalTargets: number): number => {
    if (!poolId || totalTargets <= 0) return 1; // Par défaut pour les matchs sans poule
    const poolIndex = poolIds.value.indexOf(poolId); // Index de la poule dans poolIds
    if (poolIndex === -1) return 1; // Fallback si poule non trouvée
    return (poolIndex % totalTargets) + 1; // Associe la poule à une cible (1 à totalTargets)
};

// Fonction pour les matchs hors poules (barrage et élimination)
const getNonPoolTargetNumber = (matchIndex: number, totalTargets: number): number => {
    if (totalTargets <= 0) return 1;
    return (matchIndex % totalTargets) + 1;
};

const getPoolName = (poolId: number | undefined): string => {
    if (!poolId) return 'N/A';
    const pool = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === poolId);
    return pool?.pool_name || `Poule ${poolId}`;
};

const poolIds = computed(() => {
    const ids = matches.value.map(m => m.pool_id).filter(id => id != null);
    return [...new Set(ids)];
});

const showGenerateButton = computed(() => {
    if (!isCurrentRoundFinished.value) return false; // Ne pas afficher si le round actuel n'est pas terminé
    if (isTournamentFinished.value) return false; // Ne pas afficher si le tournoi est terminé
    if (currentRound.value === 0 && hasBarrage.value) {
        // Afficher pendant le barrage si aucune poule ou match d'élimination n'existe
        return poolIds.value.length === 0 && matches.value.filter(m => m.pool_id == null && (m.round ?? 0) > 0).length === 0;
    }
    // Afficher pour les tours suivants si aucun match n'existe pour le tour suivant
    return matches.value.filter(m => m.pool_id == null && (m.round ?? 0) === currentRound.value + 1).length === 0;
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
    const finalMatches = matches.value.filter(m => m.pool_id == null && m.round !== 0);
    console.log('Final matches for currentRound:', finalMatches.map(m => ({ id: m.id, round: m.round, pool_id: m.pool_id })));
    if (finalMatches.length === 0) return 0; // Retourne 0 si seuls des matchs de barrage ou aucun match
    return Math.max(...finalMatches.map(m => m.round || 0));
});

const isCurrentRoundFinished = computed(() => {
    if (currentRound.value === 0) {
        if (hasBarrage.value) {
            // Cas barrage
            return matches.value
                .filter(m => m.round === 0 && m.pool_id == null)
                .every(m => m.status === 'completed');
        } else {
            // Cas poules
            return isPoolFinished.value;
        }
    } else {
        return matches.value
            .filter(m => m.pool_id == null && m.round === currentRound.value)
            .every(m => m.status === 'completed');
    }
});

const unregisteredTeamUsers = computed(() => {
    // Filter users who are not in any participant (team)
    const usersNotInTeam = tournamentStore.registeredUsers.filter(user =>
        !tournamentStore.participants.some(p => p.users.some(u => u.id === user.id))
    );

    return usersNotInTeam.sort((a, b) => {
        return new Date(a.id).getTime() - new Date(b.id).getTime();
    });
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
        if (data.status === 'running' || data.status === 'finished') {
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
        if (data.status === 'running' || data.status === 'finished') {
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
        tournamentStore.fetchParticipants(tournamentId.value)
        if ((tournamentStore.participants?.length ?? 0) < 4) throw new Error("Minimum 4 participants requis");

        const N = tournamentStore.participants.length;
        let useBarrage = N > 32;
        const effectiveN = useBarrage ? 32 : N;

        let tournamentType: 'pool' | 'elimination';
        let numPools: number;

        // Définir des bornes pour le nombre de joueurs par poule (par exemple, 4 à 8 joueurs)
        const minPlayersPerPool = 4;
        const maxPlayersPerPool = 8;

        // Calculer le nombre maximum de poules possibles (basé sur le minimum de joueurs par poule)
        const maxPossiblePools = Math.floor(effectiveN / minPlayersPerPool);
        // Calculer le nombre minimum de poules nécessaires (basé sur le maximum de joueurs par poule)
        const minPossiblePools = Math.ceil(effectiveN / maxPlayersPerPool);

        if (launchTypeMode.value === 'manual') {
            tournamentType = launchTournamentType.value;
            if (tournamentType === 'elimination') {
                numPools = 0; // Pas de poules en mode élimination
                if (effectiveN % 2 !== 0) {
                    throw new Error("Nombre impair de participants non supporté en mode élimination sans ajustement");
                }
            } else {
                // Utiliser launchTargetCount, mais limiter entre minPossiblePools et maxPossiblePools
                numPools = Math.max(minPossiblePools, Math.min(launchTargetCount.value, maxPossiblePools));
            }
        } else {
            // Mode automatique : utiliser launchTargetCount si défini, sinon fallback sur une logique par défaut
            if (effectiveN <= 4) {
                tournamentType = 'elimination';
                numPools = 0;
            } else {
                tournamentType = 'pool';
                // Si launchTargetCount est défini (> 0), l'utiliser, sinon fallback sur la logique par défaut
                if (launchTargetCount.value > 0) {
                    numPools = Math.max(minPossiblePools, Math.min(launchTargetCount.value, maxPossiblePools));
                } else {
                    // Logique par défaut : essayer d'avoir environ 4 à 8 joueurs par poule
                    numPools = Math.max(minPossiblePools, Math.min(Math.ceil(effectiveN / 6), maxPossiblePools));
                }
            }
        }

        console.log('Mode de lancement:', launchTypeMode.value, 'Type de tournoi:', tournamentType, 'Nombre de poules:', numPools);

        // Mettre à jour le tournoi avec le type principal
        await backendApi.patch(`/tournaments/${tournamentId.value}`, {
            type: tournamentType,
            status: 'running'
        }, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });

        if (useBarrage) {
            // Générer barrage pour éliminer N - 32
            const excess = N - 32;
            const numBarragePlayers = 2 * excess;
            const shuffledParticipants = [...tournamentStore.participants].sort(() => Math.random() - 0.5);
            const barrageParticipants = shuffledParticipants.slice(-numBarragePlayers);
            const barrageMatches = generateEliminationMatches(barrageParticipants);
            barrageMatches.forEach(match => {
                match.round = 0;  // Marquer comme barrage
            });
            for (const match of barrageMatches) {
                await createAndPersistMatch(match);
            }
            console.log(`Barrage généré : ${excess} matchs pour réduire à 32.`);
        } else {
            if (tournamentType === 'pool') {
                const pools = createPools(tournamentStore.participants, numPools);
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
                }
                for (const pool of pools) {
                    const poolSqlId = poolIdMap[pool.id];
                    for (const match of pool.matches) {
                        await createAndPersistMatch(match, poolSqlId);
                    }
                }
            } else {
                const generatedMatches = generateEliminationMatches(tournamentStore.participants);
                for (const m of generatedMatches) {
                    await createAndPersistMatch(m);
                }
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
        let qualified: Participant[] = [];
        let nextRound = currentRound.value + 1;

        const existingNextRoundMatches = matches.value.filter(
            m => m.pool_id == null && m.round === nextRound
        );
        if (existingNextRoundMatches.length > 0) {
            toast.error(`Le tour ${nextRound} existe déjà. Veuillez compléter ou supprimer les matchs existants.`);
            return;
        }

        const isBarrage = currentRound.value === 0 && poolIds.value.length === 0;
        if (isBarrage) {
            // Transition depuis barrage
            const barrageMatches = matches.value.filter(m => m.round === 0 && m.pool_id == null);
            const barragePlayerIds = new Set(barrageMatches.flatMap(m => m.participants.map(p => p?.participant_id)));
            const participants = tournamentStore.participants; // Assume chargés
            const byes = participants.filter(p => !barragePlayerIds.has(p.id));
            const winners = barrageMatches
                .map(match => getMatchWinner(match))
                .filter((w): w is MatchParticipantSchema => w != null)
                .map(w => {
                    const participant = tournamentStore.participants.find(p => p.id === w.participant_id);
                    if (!participant) throw new Error(`Participant ${w.participant_id} not found`);
                    return participant;
                });

            qualified = [...byes, ...winners];
            if (qualified.length !== 32) {
                throw new Error(`Nombre de qualifiés inattendu après barrage : ${qualified.length}`);
            }

            // Générer phase principale avec qualified
            const mainType = tournament.value?.type ?? 'pool'; // Fallback si type non défini
            const effectiveN = 32;
            let numPools = Math.ceil(effectiveN / 8); // Par défaut pour 32 participants

            if (mainType === 'pool') {
                const pools = createPools(qualified, numPools);
                const poolIdMap: Record<number, number> = {};
                for (const pool of pools) {
                    const { data: createdPool } = await backendApi.post(
                        `/tournaments/${tournamentId.value}/pools`,
                        {
                            name: pool.name || null,
                            participant_ids: pool.participants.map(p => p.id),
                        },
                        { headers: { Authorization: `Bearer ${authStore.token}` } }
                    );
                    poolIdMap[pool.id] = createdPool.id;
                }
                for (const pool of pools) {
                    const poolSqlId = poolIdMap[pool.id];
                    for (const match of pool.matches) {
                        await createAndPersistMatch(match, poolSqlId);
                    }
                }
            } else {
                const nextMatches = generateEliminationMatches(qualified);
                nextMatches.forEach(m => { m.round = 1; });
                for (const match of nextMatches) {
                    await createAndPersistMatch(match);
                }
            }
        } else if (currentRound.value === 0) {
            // Cas poules
            const totalParticipants = new Set(matches.value.flatMap(m => m.participants.map(p => p?.participant_id))).size;
            const targetQualifiers = totalParticipants <= 12 ? 8 : totalParticipants <= 24 ? 16 : 32;

            if (poolIds.value.length === 1) {
                const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === poolIds.value[0]);
                if (poolLeaderboard) {
                    qualified = poolLeaderboard.leaderboard
                        .slice(0, Math.min(targetQualifiers, poolLeaderboard.leaderboard.length))
                        .map(entry => {
                            const participant = tournamentStore.participants.find(p => p.id === entry.participant_id);
                            if (!participant) throw new Error(`Participant ${entry.participant_id} not found`);
                            return participant;
                        });
                }
            } else {
                for (const poolId of poolIds.value) {
                    const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p => p.pool_id === poolId);
                    if (poolLeaderboard) {
                        const poolSize = new Set(
                            matches.value
                                .filter(m => m.pool_id === poolId)
                                .flatMap(m => m.participants.map(p => p?.participant_id))
                        ).size;
                        const numToQualify = poolSize >= 4 ? 4 : 2;
                        const topParticipants = poolLeaderboard.leaderboard
                            .slice(0, numToQualify)
                            .map(entry => {
                                const participant = tournamentStore.participants.find(p => p.id === entry.participant_id);
                                if (!participant) throw new Error(`Participant ${entry.participant_id} not found`);
                                return participant;
                            });
                        qualified = qualified.concat(topParticipants);
                    }
                }
            }

            // Trier les qualifiés selon les critères
            qualified = qualified
                .map(participant => {
                    const poolLeaderboard = leaderboardsStore.poolsLeaderboard.find(p =>
                        matches.value.some(m => m.pool_id === p.pool_id && m.participants.some(p => p?.participant_id === participant.id))
                    );
                    const stats = poolLeaderboard?.leaderboard.find(e => e.participant_id === participant.id);
                    return { participant, wins: stats?.wins || 0, total_manches: stats?.total_manches || 0 };
                })
                .sort((a, b) => b.wins - a.wins || b.total_manches - a.total_manches)
                .map(item => item.participant);

            if (qualified.length > targetQualifiers) {
                qualified = qualified.slice(0, targetQualifiers);
            } else if (qualified.length < targetQualifiers) {
                qualified = qualified.slice(0, Math.pow(2, Math.floor(Math.log2(qualified.length))));
            }

            // Generate matches for round 1 by pairing consecutive winners
            const nextMatches: Match[] = [];
            for (let i = 0; i < qualified.length / 2; i += 2) {
                const match1Winner = qualified[i];
                const match2Winner = qualified[i + 1];
                if (match1Winner && match2Winner) {
                    nextMatches.push({
                        id: 0,
                        tournament_id: tournamentId.value,
                        match_date: null,
                        participants: [
                            participantToMatchParticipant(match1Winner),
                            participantToMatchParticipant(match2Winner),
                        ].filter((p): p is MatchParticipantSchema => p != null),
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
        } else {
            // Elimination phase: Pair winners of previous round matches sequentially
            const previousRoundMatches = matches.value.filter(
                m => m.pool_id == null && m.round === currentRound.value
            ).sort((a, b) => a.id - b.id); // Sort by match ID to ensure order

            for (const match of previousRoundMatches) {
                const winner = getMatchWinner(match);
                if (winner) {
                    const participant = tournamentStore.participants.find(p => p.id === winner.participant_id);
                    if (participant) {
                        qualified.push(participant);
                    }
                }
            }

            if (qualified.length < 2) {
                toast.error('Pas assez de participants qualifiés pour le tour suivant');
                return;
            }

            // Pair winners sequentially: match 1 vs. match 2, match 3 vs. match 4, etc.
            const nextMatches: Match[] = [];
            for (let i = 0; i < qualified.length / 2; i++) {
                const match1Winner = qualified[2 * i];
                const match2Winner = qualified[2 * i + 1];
                if (match1Winner && match2Winner) {
                    nextMatches.push({
                        id: 0,
                        tournament_id: tournamentId.value,
                        match_date: null,
                        participants: [
                            participantToMatchParticipant(match1Winner),
                            participantToMatchParticipant(match2Winner),
                        ].filter((p): p is MatchParticipantSchema => p != null),
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

    console.log("SAUVEGARDE MATCH : ", match.participants.map(p => p?.name).join(" vs "), "Round:", match.round, "Pool ID:", poolId);

    const payload: any = {
        tournament_id: tournamentId.value,
        participant_ids: participantIds,
        status: "pending",
        round: match.round ?? 1, // Utiliser ?? pour préserver 0
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
        const scoresPayload = match.participants
            .filter(p => p?.participant_id !== undefined)
            .map((participant: any, index: number) => ({
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
                status: 'finished'
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

const cancelMatchScores = async (matchId: number) => {
    try {
        await backendApi.post(`/tournaments/matches/${matchId}/cancel`, {}, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Scores du match réinitialisés');
        await fetchMatches();
        await leaderboardsStore.fetchPoolsLeaderboard(tournamentId.value, authStore.token);

        // If the tournament was finished due to this match, revert the tournament status
        if (tournament.value?.status === 'finished' && isTournamentFinished.value) {
            await backendApi.patch(`/tournaments/${tournamentId.value}`, {
                status: 'running'
            }, {
                headers: { Authorization: `Bearer ${authStore.token}` },
            });
            await fetchTournament(tournamentId.value);
        }
    } catch (err) {
        handleError(err, 'canceling match scores');
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
            status: 'finished',
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