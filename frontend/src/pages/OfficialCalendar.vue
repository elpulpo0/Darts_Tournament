<template>
    <div v-if="authStore.isAuthenticated" class="module">
        <div v-if="loading" class="loading">Chargement...</div>

        <h2>Tournois du Comité Méridional et de la Ligue Sud Est</h2>
        <div v-if="Object.keys(groupedEvents).length">
            <div v-for="(events, month) in groupedEvents" class="month-group" :key="month">
                <h3 class="month-header">{{ month }}</h3>
                <div class="event-grid">
                    <div v-for="event in events" class="event-card"
                        :class="{ 'selected': selectedEvent?.id === event.id }" @click="selectEvent(event)">
                        <div class="card-content">
                            <h3> {{ event.date }} : {{ event.name }}</h3>
                            <p class="info"> {{ event.description || '' }}</p>
                            <p class="info"> Organisé par {{ event.organiser || '' }}</p>
                            <p class="info"><span class="icon">📍</span> {{ event.place || '' }}</p>
                        </div>
                        <img :src="getEventImage(event.id)" alt="Affiche du tournoi" class="event-image"
                            @error="onImageError" :key="event.id">
                    </div>
                </div>
            </div>
        </div>

        <div v-else class="no-events">
            <p>Aucun tournoi disponible.</p>
        </div>

        <!-- Modal pour les détails du tournoi -->
        <div v-if="selectedEvent" class="event-modal" @click.self="selectedEvent = null">
            <div class="modal-content">
                <h3 v-if="!editMode">{{ selectedEvent.name }}</h3>
                <input v-else v-model="editName" placeholder="Nom" class="form-input" />

                <img v-if="!editMode" :src="getEventImage(selectedEvent.id)" alt="Affiche du tournoi"
                    class="modal-image" @error="onImageError" :key="selectedEvent.id">

                <div v-if="!editMode" class="event-details">
                    <p v-if="selectedEvent.description"><strong>Description :</strong> {{ selectedEvent.description }}
                    </p>
                    <p v-if="selectedEvent.organiser">
                        <strong>Organisateur : </strong>{{ selectedEvent.organiser }}
                        <a v-if="getOrganiserLink(selectedEvent.organiser)"
                            :href="getOrganiserLink(selectedEvent.organiser)" target="_blank"
                            rel="noopener noreferrer">(Plus d'info)</a>
                    </p>
                    <p v-if="selectedEvent.place"><strong>Lieu :</strong> {{ selectedEvent.place }}</p>
                    <p v-if="selectedEvent.date"><strong>Date :</strong> {{ selectedEvent.date }}</p>
                </div>

                <div v-if="editMode">
                    <input v-model="editDescription" placeholder="Description" class="form-input" />
                    <input v-model="editOrganiser" placeholder="Organisateur" class="form-input" />
                    <input v-model="editPlace" placeholder="Lieu" class="form-input" />
                    <input v-model="editDate" placeholder="Date" class="form-input" />
                </div>

                <div>
                    <button v-if="isEditor && !editMode" @click="startEdit">
                        Modifier
                    </button>
                    <template v-if="editMode">
                        <button @click="updateEvent">Sauvegarder</button>
                        <button @click="cancelEdit">Annuler</button>
                    </template>
                    <router-link v-if="selectedEvent && hasInscriptions(selectedEvent)"
                        :to="`/inscriptions?tournament=${selectedEvent.name}&date=${encodeURIComponent(selectedEvent.date)}&place=${encodeURIComponent(selectedEvent.place || '')}`"
                        class="btn-inscription">
                        <button>Voir les inscriptions</button>
                    </router-link>
                    <button @click="selectedEvent = null">Fermer</button>
                </div>
            </div>
        </div>

        <!-- Bouton pour créer un tournoi -->
        <button v-if="isEditor" class="add-button" @click="showCreateEvent = true">
            + Ajouter un tournoi
        </button>

        <!-- Modal pour créer un tournoi -->
        <div v-if="showCreateEvent" class="create-modal" @click.self="toggleCreateEventForm">
            <div class="modal-content">
                <h3>Ajouter un tournoi</h3>
                <input v-model="newEventName" placeholder="Nom" class="form-input" />
                <input v-model="newEventDescription" placeholder="Description" class="form-input" />
                <input v-model="newEventPlace" placeholder="Lieu" class="form-input" />
                <input v-model="newEventOrganiser" placeholder="Organisateur" class="form-input" />
                <input v-model="newEventDate" placeholder="Date" class="form-input" />
                <div class="modal-actions">
                    <button @click="createEvent">Ajouter</button>
                    <button @click="toggleCreateEventForm">Annuler</button>
                </div>
            </div>
        </div>
    </div>

    <div v-else class="centered-block">
        <h2>🔒 Connexion requise</h2>
        <p>Veuillez vous connecter pour voir le calendrier.</p>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import backendApi from '../axios/backendApi';
import { toast } from 'vue3-toastify';
import { useAuthStore } from '../stores/useAuthStore';
import { handleError } from '../functions/utils';
import { useEventStore } from '../stores/useEventStore';
import { useInscriptionsStore } from '../stores/useInscriptionsStore'

const authStore = useAuthStore();
const eventStore = useEventStore();

const selectedEvent = ref<OfficialEvent | null>(null);
const loading = ref(false);
const showCreateEvent = ref(false);
const newEventName = ref('');
const newEventDescription = ref('');
const newEventDate = ref('');
const newEventPlace = ref('');
const newEventOrganiser = ref('');

const editMode = ref(false);
const editName = ref('');
const editDescription = ref('');
const editDate = ref('');
const editPlace = ref('');
const editOrganiser = ref('');

const inscriptionsStore = useInscriptionsStore()

const isEditor = computed(() => authStore.scopes.includes('editor') || authStore.scopes.includes('admin'));

const getEventImage = (eventId: number) => {
    return new URL(`../assets/affiche_event_${eventId}.jpg`, import.meta.url).href;
};

const getFallbackImage = () => {
    return new URL(`../assets/404.png`, import.meta.url).href;
};

const onImageError = (event: Event) => {
    if (event.target) {
        (event.target as HTMLImageElement).src = getFallbackImage();
    }
};

const monthMap: Record<string, number> = {
    'Janvier': 1,
    'Février': 2,
    'Mars': 3,
    'Avril': 4,
    'Mai': 5,
    'Juin': 6,
    'Juillet': 7,
    'Août': 8,
    'Septembre': 9,
    'Octobre': 10,
    'Novembre': 11,
    'Décembre': 12
};

const groupedEvents = computed(() => {
    const groups: { [key: string]: OfficialEvent[] } = {};

    const sortedEvents = eventStore.events.slice().sort((a, b) => {
        const parseDateStr = (dateStr: string) => {
            const year = dateStr.slice(-4);
            const nonNumeric = dateStr.replace(/[\d- ]/g, '').trim();
            const monthStr = nonNumeric.charAt(0).toUpperCase() + nonNumeric.slice(1).toLowerCase();
            const monthNum = monthMap[monthStr] || 0;
            const dayPart = dateStr.split(' ')[0];
            const startDay = dayPart.split('-')[0].padStart(2, '0');
            return `${year}-${monthNum.toString().padStart(2, '0')}-${startDay}`;
        };
        return parseDateStr(a.date).localeCompare(parseDateStr(b.date));
    });

    sortedEvents.forEach((event) => {
        const year = event.date.slice(-4);
        const nonNumeric = event.date.replace(/[\d- ]/g, '').trim();
        const month = nonNumeric.charAt(0).toUpperCase() + nonNumeric.slice(1);
        const key = `${month} ${year}`;
        if (!groups[key]) {
            groups[key] = [];
        }
        groups[key].push(event);
    });

    return groups;
});

const organiserLinks: Record<string, string> = {
    "un 20 cible": "https://www.facebook.com/p/UN-20-CIBLE-100063697832214",
    "olympic darts albertville": "https://www.facebook.com/p/Olympic-Darts-Albertville-61559336854314",
    "lyon darts academy": "https://www.lyondartsacademy.fr/",
    "perno li darts": "https://www.facebook.com/pernolidarts",
    "les dartistes du pays de fayence": "https://www.facebook.com/les.dartistes.du.pays.de.fayence",
    "pouss'in the darts - la fléchette sanfloraine": "https://www.facebook.com/LaFlechetteSanfloraine",
    "droit aux bulls": "https://www.instagram.com/droitobullsclub",
    "drap darts": "https://www.facebook.com/groups/1024078255149460",
    "la fléchette de salm": "https://www.facebook.com/LaFlechetteDeSalm88"
};

const getOrganiserLink = (organiser: string | undefined | null): string | undefined => {
    if (!organiser) return undefined;
    const lowerOrganiser = organiser.toLowerCase().trim();
    return organiserLinks[lowerOrganiser] || undefined;
};

const toggleCreateEventForm = () => {
    showCreateEvent.value = !showCreateEvent.value;
    if (!showCreateEvent.value) {
        newEventName.value = '';
        newEventDescription.value = '';
        newEventDate.value = '';
        newEventOrganiser.value = '';
        newEventPlace.value = '';
    }
};

const createEvent = async () => {
    if (!newEventName.value || !newEventDate.value) {
        toast.error('Nom et date requis.');
        return;
    }

    const eventData = {
        name: newEventName.value,
        description: newEventDescription.value || null,
        organiser: newEventOrganiser.value || null,
        place: newEventPlace.value || null,
        date: newEventDate.value || null,
    };
    try {
        await backendApi.post('/events/', eventData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Tournoi créé.');
        eventStore.fetchEvents();
        toggleCreateEventForm();
    } catch (err) {
        handleError(err, 'création du tournoi');
    }
};

const selectEvent = async (event: OfficialEvent) => {
    selectedEvent.value = event;
    if (authStore.token) {
        await inscriptionsStore.fetchActiveInscriptions(authStore.token)
    }
}

const hasInscriptions = (event: OfficialEvent) => {
    if (!inscriptionsStore.activeInscriptions) return false;
    return inscriptionsStore.activeInscriptions.some((inscription) => {
        return inscription.date === event.date;
    });
};

const startEdit = () => {
    if (selectedEvent.value) {
        editName.value = selectedEvent.value.name;
        editDescription.value = selectedEvent.value.description || '';
        editOrganiser.value = selectedEvent.value.organiser || '';
        editPlace.value = selectedEvent.value.place || '';
        editDate.value = selectedEvent.value.date || '';
        editMode.value = true;
    }
};

const cancelEdit = () => {
    editMode.value = false;
};

const updateEvent = async () => {
    if (!selectedEvent.value || !editName.value || !editDate.value) {
        toast.error('Nom et date requis.');
        return;
    }

    const eventData = {
        name: editName.value,
        description: editDescription.value || null,
        organiser: editOrganiser.value || null,
        place: editPlace.value || null,
        date: editDate.value,
    };
    try {
        await backendApi.patch(`/events/${selectedEvent.value.id}`, eventData, {
            headers: { Authorization: `Bearer ${authStore.token}` },
        });
        toast.success('Tournoi mis à jour.');
        eventStore.fetchEvents();
        editMode.value = false;
        // Update local selectedEvent with new values
        if (selectedEvent.value) {
            selectedEvent.value.name = eventData.name;
            selectedEvent.value.description = eventData.description;
            selectedEvent.value.organiser = eventData.organiser;
            selectedEvent.value.place = eventData.place;
            selectedEvent.value.date = eventData.date;
        }
    } catch (err) {
        handleError(err, 'mise à jour du tournoi');
    }
};

watch(() => authStore.isAuthenticated, (isAuthenticated: boolean) => {
    if (isAuthenticated) eventStore.fetchEvents();
}, { immediate: true });

onMounted(async () => {
    if (authStore.isAuthenticated) {
        await eventStore.fetchEvents();
        if (authStore.token) {
            await inscriptionsStore.fetchActiveInscriptions(authStore.token)
        }
    }
})
</script>

<style scoped>
.events-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
}

.month-group {
    margin-bottom: 2rem;
}

.month-header {
    text-align: center;
    color: var(--color-accent);
    margin: 1rem 0;
    font-size: 1.5rem;
    border-bottom: 1px solid var(--color-light-shadow);
    padding-bottom: 0.5rem;
}

.event-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(250px, 1fr));
    gap: 1rem;
}

.event-card {
    background: var(--color-bg);
    border: 1px solid var(--color-light-shadow);
    border-radius: var(--radius);
    padding: 1rem;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    display: flex;
    align-items: stretch;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.event-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.event-card.selected {
    background: var(--color-accent-bis);
    color: var(--color-bg);
    border-color: var(--color-accent);
}

.card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.event-card h3 {
    margin: 0 0 0.75rem;
    font-size: 1.2rem;
    font-weight: 600;
    display: flex;
    align-items: center;
}

.info {
    font-size: 0.9rem;
    margin: 0.3rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
}

.icon {
    font-size: 1.1rem;
    color: var(--color-accent);
}

.event-image {
    width: 120px;
    height: 100%;
    object-fit: cover;
    border-radius: var(--radius);
}

.modal-image {
    width: 300px;
    height: auto;
    border-radius: var(--radius);
    margin-bottom: 1rem;
}

.event-details {
    margin-bottom: 1rem;
}

.event-details p {
    margin: 0.5rem 0;
    font-size: 1rem;
}

.event-details a {
    color: var(--color-accent);
    text-decoration: underline;
    margin-left: 0.5rem;
}

.event-modal,
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
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
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

.no-events,
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
    .event-grid {
        grid-template-columns: repeat(1, minmax(200px, 1fr));
    }

    .event-image {
        width: auto;
        height: 150px;
    }
}
</style>
