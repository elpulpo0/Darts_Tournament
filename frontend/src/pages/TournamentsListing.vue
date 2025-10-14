<template>
    <div v-if="authStore.isAuthenticated" class="module">
        <div v-if="loading" class="loading">Chargement...</div>

        <h2>Tournois</h2>
        <div v-if="tournamentStore.tournaments.length" class="tournament-grid">
            <div v-for="tournament in tournamentStore.tournaments" class="tournament-card"
                :class="{ 'selected': selectedTournament?.id === tournament.id }" @click="selectTournament(tournament)">
                <div class="card-content">
                    <h3>{{ tournament.name }}</h3>
                    <div class="status" :class="tournament.status">
                        <span>{{ getStatusLabel(tournament.status) }}</span>
                    </div>
                    <p class="info">📅 {{ formatDate(tournament.start_date) }}</p>
                    <p class="info">{{ tournament.description || '' }}</p>
                </div>
                <img :src="getTournamentImage(tournament.id)" alt="Affiche du tournoi" class="tournament-image"
                    :key="tournament.id">
            </div>
        </div>

        <div v-else class="no-tournaments">
            <p>Aucun tournoi disponible.</p>
        </div>

        <!-- Modal pour les détails du tournoi -->
        <div v-if="selectedTournament" class="tournament-modal" @click.self="selectedTournament = null">
            <div class="modal-content">
                <h3>{{ selectedTournament.name }}</h3>
                <p>{{ selectedTournament.description || 'Aucune description' }}</p>
                <p><strong>Date :</strong> {{ formatDate(selectedTournament.start_date) }}</p>
                <p><strong>Mode :</strong> {{ getModeLabel(selectedTournament.mode) }}</p>

                <div v-if="selectedTournament.status === 'open'">
                    <button v-if="!registrationStatus[selectedTournament.id]"
                        @click="registerToTournament(selectedTournament.id)">
                        S’inscrire
                    </button>
                    <div v-else>
                        <p>Vous êtes inscrit.</p>
                        <button @click="unregisterFromTournament(selectedTournament.id)">Se
                            désinscrire</button>
                    </div>
                </div>
                <p v-else-if="selectedTournament.status === 'closed' || selectedTournament.status === 'finished'">{{
                    getStatusLabel(selectedTournament.status) }}</p>

                <div v-if="selectedTournament.status === 'open'" class="participants">
                    <h4>Participants ({{ tournamentStore.participants?.length || 0 }})</h4>
                    <ul v-if="tournamentStore.participants?.length">
                        <li v-for="participant in tournamentStore.participants" :key="participant.id">
                            {{ participant.name }}
                            <span v-if="selectedTournament.mode === 'double'">
                                ({{participant.users.map(u => u.nickname || 'Inconnu').join(' & ')}})
                            </span>
                        </li>
                    </ul>
                    <p v-else>Aucun participant.</p>
                </div>

                <button v-if="isEditor"
                    @click="router.push({ name: 'TournamentManagement', params: { tournamentId: selectedTournament.id } })">
                    Gérer
                </button>
                <button v-if="['running', 'finished'].includes(selectedTournament.status)" @click="openProjection">
                    Voir l’arborescence
                </button>
                <button @click="selectedTournament = null">Fermer</button>
            </div>
        </div>

        <!-- Bouton pour créer un tournoi -->
        <button v-if="isEditor" class="add-button" @click="showCreateTournament = true">
            + Ajouter un tournoi
        </button>

        <!-- Modal pour créer un tournoi -->
        <div v-if="showCreateTournament" class="create-modal" @click.self="toggleCreateTournamentForm">
            <div class="modal-content">
                <h3>Ajouter un tournoi</h3>
                <input v-model="newTournamentName" placeholder="Nom" class="form-input" />
                <input v-model="newTournamentDescription" placeholder="Description" class="form-input" />
                <input v-model="newTournamentStartDate" type="datetime-local" class="form-input" />
                <select v-model="newTournamentMode" class="form-input">
                    <option value="single">Simple</option>
                    <option value="double">Double</option>
                </select>
                <div class="modal-actions">
                    <button @click="createTournament">Ajouter</button>
                    <button @click="toggleCreateTournamentForm">Annuler</button>
                </div>
            </div>
        </div>
    </div>

    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour voir les tournois.</p>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import backendApi from '../axios/backendApi';
import { useToast } from 'vue-toastification';
import { useAuthStore } from '../stores/useAuthStore';
import { useRouter } from 'vue-router';
import { handleError } from '../functions/utils';
import { useTournamentStore } from '../stores/useTournamentStore';

const authStore = useAuthStore();
const toast = useToast();
const router = useRouter();
const tournamentStore = useTournamentStore();

const selectedTournament = ref<Tournament | null>(null);
const loading = ref(false);
const showCreateTournament = ref(false);
const newTournamentName = ref('');
const newTournamentDescription = ref('');
const newTournamentStartDate = ref('');
const newTournamentMode = ref<'single' | 'double'>('single');
const registrationStatus = ref<{ [key: number]: boolean }>({});

const isEditor = computed(() => authStore.scopes.includes('editor') || authStore.scopes.includes('admin'));

const getTournamentImage = (tournamentId: number) => {
    return new URL(`../assets/affiche_tournoi_${tournamentId}.jpg`, import.meta.url).href;
};

const getStatusLabel = (status: Tournament['status']) => {
    const labels: Record<Tournament['status'], string> = {
        open: 'Inscriptions ouvertes',
        closed: 'Inscriptions fermées',
        finished: 'Tournoi terminé',
        running: 'Tournoi en cours',
    };
    return labels[status] || '';
};

const getModeLabel = (mode: Tournament['mode']) => {
    const labels: Record<NonNullable<Tournament['mode']>, string> = {
        single: 'Individuel',
        double: 'Double',
    };
    if (mode === null) {
        return '';
    }
    return labels[mode] || '';
};

const formatDate = (date: string) => new Date(date).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' });

const toggleCreateTournamentForm = () => {
    showCreateTournament.value = !showCreateTournament.value;
    if (!showCreateTournament.value) {
        newTournamentName.value = '';
        newTournamentDescription.value = '';
        newTournamentStartDate.value = '';
        newTournamentMode.value = 'single';
    }
};

const createTournament = async () => {
    if (!newTournamentName.value || !newTournamentStartDate.value) {
        toast.error('Nom et date requis.');
        return;
    }
    const localDate = newTournamentStartDate.value;

    const tournamentData = {
        name: newTournamentName.value,
        description: newTournamentDescription.value || null,
        start_date: localDate,
        is_active: true,
        status: 'open',
        mode: newTournamentMode.value,
    };
    try {
        await backendApi.post('/tournaments/', tournamentData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Tournoi créé.');
        tournamentStore.fetchTournaments();
        toggleCreateTournamentForm();
    } catch (err) {
        handleError(err, 'création du tournoi');
    }
};

const registerToTournament = async (tournamentId: number) => {
    const playerData = { user_id: authStore.userId, tournament_id: tournamentId };
    try {
        await backendApi.post('/tournaments/registrations/', playerData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Inscription réussie.');
        registrationStatus.value[tournamentId] = true;
        await tournamentStore.fetchParticipants(tournamentId);
    } catch (err) {
        handleError(err, 'inscription au tournoi');
    }
};

const checkIfUserRegistered = async (tournamentId: number): Promise<boolean> => {
    try {
        const { data } = await backendApi.get(`/tournaments/${tournamentId}/my-registration`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        return data;
    } catch (err: any) {
        if (err.response?.status === 401) {
            toast.error('Connexion requise.');
        } else {
            handleError(err, 'vérification de l’inscription');
        }
        return false;
    }
};

const unregisterFromTournament = async (tournamentId: number) => {
    try {
        await backendApi.delete(`/tournaments/registrations/${tournamentId}`, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Désinscription réussie.');
        registrationStatus.value[tournamentId] = false;
        await tournamentStore.fetchParticipants(tournamentId);
    } catch (err) {
        handleError(err, 'désinscription du tournoi');
    }
};

const selectTournament = async (tournament: Tournament) => {
    selectedTournament.value = tournament;
    await tournamentStore.fetchParticipants(tournament.id);
    registrationStatus.value[tournament.id] = await checkIfUserRegistered(tournament.id);
};

watch(() => authStore.isAuthenticated, (isAuthenticated: boolean) => {
    if (isAuthenticated) tournamentStore.fetchTournaments();
}, { immediate: true });

const openProjection = () => {
    if (!selectedTournament.value) return;
    router.push(`/tournaments/${selectedTournament.value.id}/projection`);
};
</script>

<style scoped>
.tournaments-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

.tournament-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(250px, 1fr));
    gap: 0.75rem;
}

.tournament-card {
    background: var(--color-light-shadow);
    border-radius: var(--radius);
    padding: 0.75rem;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    display: flex;
    align-items: stretch;
    overflow: hidden;
}

.tournament-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.tournament-card.selected {
    background: var(--color-accent-bis);
    color: var(--color-bg);
}

.card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.tournament-card h3 {
    margin: 0 0 0.5rem;
    font-size: 1.1rem;
    font-weight: 600;
}

.status {
    font-size: 0.8rem;
    display: inline;
    margin-bottom: 0.5rem;
}

.status span {
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    display: inline-block;
    background: inherit;
}

.status.open span {
    background: #28a745;
    color: white;
}

.status.closed span {
    background: #dc3545;
    color: white;
}

.status.running span {
    background: #007bff;
    color: white;
}

.status.finished span {
    background: #6c757d;
    color: white;
}

.info {
    font-size: 0.85rem;
    margin: 0.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.tournament-image {
    width: 100px;
    height: 100%;
    object-fit: contain;
    border-radius: var(--radius);
}

.modal-image {
    width: 350px;
    height: 100%;
    border-radius: var(--radius);
}

.tournament-modal,
.create-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: var(--color-bg);
    padding: 1.5rem;
    border-radius: var(--radius);
    max-width: 500px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

.participants ul {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0;
}

.participants li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--color-light-shadow);
}

.add-button {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    cursor: pointer;
}

.form-input {
    display: block;
    width: 100%;
    padding: 0.5rem;
    margin: 0.5rem 0;
    border: 1px solid var(--color-light-shadow);
    border-radius: var(--radius);
}

.modal-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}

.no-tournaments,
.loading {
    text-align: center;
    padding: 2rem;
    color: var(--color-fg);
}

.centered-block {
    text-align: center;
    padding: 2rem;
}

@media (max-width: 768px) {
    .tournament-grid {
        display: grid;
        grid-template-columns: repeat(1, minmax(150px, 1fr));
        gap: 0.75rem;
    }
}
</style>
