<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="inscriptionsStore.loading">Chargement des inscriptions...</div>
        <div v-if="inscriptionsStore.error" class="error">{{ inscriptionsStore.error }}</div>

        <div class="module">
            <h2>
                Inscriptions - {{ route.query.tournament }}
                <span>
                    ({{ route.query.date }} - {{ route.query.place }})
                </span>
            </h2>

            <!-- GROUPÉ PAR DATE -->
            <div v-for="dateGroup in filteredInscriptionsByDate" :key="dateGroup.date">
                <div class="mobile-rotate-notice hideonmobile-off">
                    <span>📱</span> Tourne ton téléphone pour voir toutes les colonnes
                </div>
                <table class="leaderboardtable">
                    <thead>
                        <tr>
                            <th>Joueur</th>
                            <th>Club</th>
                            <th class="hideonmobile">Simple</th>
                            <th class="hideonmobile">Double</th>
                            <th class="hideonmobile">Doublette</th>
                        </tr>
                    </thead>
                    <tbody v-if="dateGroup.inscriptions.length">
                        <tr v-for="(inscription, index) in dateGroup.inscriptions"
                            :class="{ 'current-user': isCurrentUser(inscription) }" :key="index">
                            <td class="player">{{ getPlayerName(inscription) }}</td>
                            <td class="club">{{ getClubName(inscription.club) }}</td>
                            <td class="hideonmobile">{{ formatCategory(inscription.category_simple) }}</td>
                            <td class="hideonmobile">{{ formatCategory(inscription.category_double) }}</td>
                            <td class="hideonmobile">{{ getDoubletteDisplay(inscription) }}</td>
                        </tr>
                    </tbody>
                    <p v-else class="no-entries">Aucune inscription pour cette date.</p>
                </table>
            </div>
        </div>
    </div>

    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour accéder aux inscriptions.</p>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from '../stores/useAuthStore';
import { useInscriptionsStore } from '../stores/useInscriptionsStore';
import { useRoute } from 'vue-router';

const route = useRoute();
const authStore = useAuthStore();
const inscriptionsStore = useInscriptionsStore();

const selectedDate = ref('');
const onlyCurrentUser = ref(false);

// MAPPING CLUBS
const clubMapping: Record<string, string> = {
    'APD': "ArpaDarts",
    'VDA': "Vojvo Darts",
    'HDC': "Hérault Darts Club",
    'DOB': "Droit Aux Bulls",
    'DPF': "Les Dartistes du Pays de Fayence",
    'PDC': "Crau'Darts",
    'DKN': "Darts Knights de la Crau"
};

// MAPPING CATÉGORIES
const categoryMapping: Record<string, string> = {
    'V': 'Vétéran',
    'M': 'Mixte',
    'F': 'Féminine',
    'J': 'Junior'
};

// GROUPÉ PAR DATE
const filteredInscriptionsByDate = computed(() => {
    let filtered = inscriptionsStore.activeInscriptions;

    // Filtre par date sélectionnée
    if (selectedDate.value) {
        filtered = filtered.filter(i => i.date === selectedDate.value);
    }

    // Filtre utilisateur actuel
    if (onlyCurrentUser.value) {
        filtered = filtered.filter(isCurrentUser);
    }

    // Grouper par date
    const grouped: { date: string, inscriptions: InscriptionResponse[] }[] = [];
    const dates = [...new Set(filtered.map(i => i.date))].sort();

    dates.forEach(date => {
        grouped.push({
            date,
            inscriptions: filtered.filter(i => i.date === date)
                .sort((a, b) => a.name.localeCompare(b.name))
        });
    });

    return grouped;
});

const currentUserName = computed(() => (authStore.name || '').trim());

const normalize = (str: string) => {
    return str
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/\([^)]*\)/g, '')
        .replace(/[^a-zA-Z\s-]/g, '')
        .toLowerCase()
        .trim();
};

const isCurrentUser = (inscription: InscriptionResponse) => {
    const normalizedPlayer = normalize(`${inscription.name} ${inscription.surname}`);
    const normalizedUser = normalize(currentUserName.value);
    const userWords = normalizedUser.split(/\s+/);
    return userWords.every(word => normalizedPlayer.includes(word));
};

const getPlayerName = (inscription: InscriptionResponse) => {
    return `${inscription.name.toUpperCase()} ${inscription.surname}`;
};

const getClubName = (clubCode: string) => {
    return clubMapping[clubCode] || clubCode;
};

const formatCategory = (category: string | null) => {
    if (!category) return '';
    return categoryMapping[category] || category;
};

const getDoubletteDisplay = (inscription: InscriptionResponse) => {
    if (!inscription.doublette) return '';

    const sameDateInscriptions = inscriptionsStore.activeInscriptions.filter(
        i => i.date === inscription.date
    );

    const doubletteInscription = sameDateInscriptions.find(i => i.id === inscription.doublette);

    if (doubletteInscription) {
        return getPlayerName(doubletteInscription);
    }

    return '';
};

onMounted(() => {
    if (authStore.token) {
        inscriptionsStore.fetchActiveInscriptions(authStore.token);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
});
</script>