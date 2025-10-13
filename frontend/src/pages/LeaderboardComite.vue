<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="leaderboardsStore.loading">Chargement du classement CMER...</div>
        <div v-if="leaderboardsStore.error" class="error">{{ leaderboardsStore.error }}</div>
        <div class="module">
            <div class="filters">
                <label for="category-select">Catégorie :</label>
                <select id="category-select" v-model="selectedCategory">
                    <option value="">Toutes</option>
                    <option v-for="category in leaderboardsStore.cmerLeaderboard" :value="category.category"
                        :key="category.category">
                        {{ formatCategory(category.category) }}
                    </option>
                </select>

                <label>
                    <input v-model="onlyCurrentUser" type="checkbox" class="styled-checkbox" />
                    Mes résultats uniquement
                </label>
            </div>

            <h2>Classement Comité Méridional 2024</h2>
            <div v-for="category in filteredCategories" :key="category.category">
                <h3>{{ formatCategory(category.category) }}</h3>
                <table v-if="category.entries.length">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Joueur</th>
                            <th>PTS</th>
                            <th class="hideonmobile">OC1</th>
                            <th class="hideonmobile">CC</th>
                            <th class="hideonmobile">OC2</th>
                            <th class="hideonmobile">OC3</th>
                            <th class="hideonmobile">OC4</th>
                            <th class="hideonmobile">OC5</th>
                            <th class="hideonmobile">E1</th>
                            <th class="hideonmobile">E2</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(entry, index) in category.entries"
                            :class="{ 'current-user': isCurrentUser(entry.joueur) }" :key="index">
                            <td>{{ entry.clt }}</td>
                            <td>{{ entry.joueur }}</td>
                            <td>{{ entry.pts }}</td>
                            <td class="hideonmobile">{{ entry.oc1 }}</td>
                            <td class="hideonmobile">{{ entry.cc }}</td>
                            <td class="hideonmobile">{{ entry.oc2 }}</td>
                            <td class="hideonmobile">{{ entry.oc3 }}</td>
                            <td class="hideonmobile">{{ entry.oc4 }}</td>
                            <td class="hideonmobile">{{ entry.oc5 }}</td>
                            <td class="hideonmobile">{{ entry.e1 }}</td>
                            <td class="hideonmobile">{{ entry.e2 }}</td>
                        </tr>
                    </tbody>
                </table>
                <p v-else>Aucune entrée dans cette catégorie.</p>
            </div>
        </div>
    </div>
    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour accéder au classement.</p>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAuthStore } from '../stores/useAuthStore';
import { useLeaderboardsStore } from '../stores/useLeaderboardsStore';

const authStore = useAuthStore();
const leaderboardsStore = useLeaderboardsStore();

const selectedCategory = ref('');
const onlyCurrentUser = ref(false);

const formatCategory = (cat: string) => {
    return cat.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};

const filteredCategories = computed(() => {
    return leaderboardsStore.cmerLeaderboard
        .filter(cat => !selectedCategory.value || cat.category === selectedCategory.value)
        .map(cat => {
            const entries = onlyCurrentUser.value
                ? cat.entries.filter(entry => isCurrentUser(entry.joueur))
                : cat.entries;
            return { ...cat, entries };
        });
});

const currentUserName = computed(() => (authStore.name || '').trim());
console.log(currentUserName.value)

const normalize = (str: string) => {
    return str
        .normalize('NFD')                  // Décompose accents
        .replace(/[\u0300-\u036f]/g, '')   // Supprime accents
        .replace(/\([^)]*\)/g, '')         // Supprime parenthèses (club)
        .replace(/[^a-zA-Z\s-]/g, '')      // Supprime ponctuation, numéros
        .toLowerCase()
        .trim();
};

const isCurrentUser = (joueur: string) => {
    const normalizedPlayer = normalize(joueur);
    const normalizedUser = normalize(currentUserName.value);

    // On découpe les mots du nom de l'utilisateur
    const userWords = normalizedUser.split(/\s+/);

    // Il faut que tous les mots apparaissent dans le texte du joueur
    return userWords.every(word => normalizedPlayer.includes(word));
};

onMounted(() => {
    if (authStore.token) {
        leaderboardsStore.fetchCmerLeaderboard();
    }
});
</script>

<style>
.current-user {
    color: var(--color-error);
    font-weight: bold;
}

@media screen and (max-width: 600px) {
    .hideonmobile {
        display: none;
    }
}
</style>