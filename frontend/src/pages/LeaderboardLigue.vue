<template>
    <div v-if="authStore.isAuthenticated">
        <div v-if="leaderboardsStore.loading">Chargement du classement LSEF...</div>
        <div v-if="leaderboardsStore.error" class="error">{{ leaderboardsStore.error }}</div>
        <div class="module">
            <h2>Classement Ligue Sud Est 2025</h2>
            <div class="filters">
                <label for="category-select">Catégorie :</label>
                <select id="category-select" v-model="selectedCategory">
                    <option value="">Toutes</option>
                    <option v-for="category in leaderboardsStore.lsefLeaderboard" :value="category.category"
                        :key="category.category">
                        {{ formatCategory(category.category) }}
                    </option>
                </select>

                <label>
                    <input v-model="onlyCurrentUser" type="checkbox" class="styled-checkbox" />
                    Mes résultats uniquement
                </label>
            </div>

            <div v-for="category in filteredCategories" :key="category.category">
                <h3>{{ formatCategory(category.category) }}</h3>
                <table class="leaderboardtable">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Joueur</th>
                            <th>PTS</th>
                            <th class="hideonmobile ptsdetails">Open de <br>Ligue #1</th>
                            <th class="hideonmobile ptsdetails">Open de <br>Ligue #2</th>
                            <th class="hideonmobile ptsdetails">Open de <br>Ligue #3</th>
                            <th class="hideonmobile ptsdetails">Coupe de <br>la Ligue</th>
                            <th class="hideonmobile ptsdetails">Hors <br>Comité #1</th>
                            <th class="hideonmobile ptsdetails">Hors <br>Ligue #1</th>
                            <th class="hideonmobile ptsdetails">Hors <br>Ligue #2</th>
                            <th class="hideonmobile ptsdetails">Master <br>Régionnaux</th>
                            <th class="hideonmobile ptsdetails">Points <br>Comité</th>
                        </tr>
                        <tr class="hideonmobile">
                            <th></th>
                            <th></th>
                            <th></th>
                            <th class="city">Cournon (63)</th>
                            <th class="city">Albertville (73)</th>
                            <th class="city">Ecully (69)</th>
                            <th class="city">Saint-Flour (15)</th>
                            <th class="city">Pernes-les-Fontaines (84)</th>
                            <th></th>
                            <th></th>
                            <th></th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody v-if="category.entries.length">
                        <tr v-for="(entry, index) in category.entries"
                            :class="{ 'current-user': isCurrentUser(entry.joueur) }" :key="index">
                            <td>{{ entry.clt }}</td>
                            <td>{{ entry.joueur }}</td>
                            <td>{{ entry.pts }}</td>
                            <td class="hideonmobile">{{ entry.ol1 }}</td>
                            <td class="hideonmobile">{{ entry.ol2 }}</td>
                            <td class="hideonmobile">{{ entry.ol3 }}</td>
                            <td class="hideonmobile">{{ entry.cl }}</td>
                            <td class="hideonmobile">{{ entry.ol4 }}</td>
                            <td class="hideonmobile">{{ entry.e1 }}</td>
                            <td class="hideonmobile">{{ entry.e2 }}</td>
                            <td class="hideonmobile">{{ entry.master }}</td>
                            <td class="hideonmobile">{{ entry.pts_com }}</td>
                        </tr>
                    </tbody>
                    <p v-else>Aucune entrée dans cette catégorie.</p>
                </table>
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
    return leaderboardsStore.lsefLeaderboard
        .filter(cat => !selectedCategory.value || cat.category === selectedCategory.value)
        .map(cat => {
            const entries = onlyCurrentUser.value
                ? cat.entries.filter(entry => isCurrentUser(entry.joueur))
                : cat.entries;
            return { ...cat, entries };
        });
});

const currentUserName = computed(() => (authStore.name || '').trim());

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
        leaderboardsStore.fetchLsefLeaderboard();
    }
});
</script>
