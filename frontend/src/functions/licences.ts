import { ref } from 'vue';
import backendApi from '../axios/backendApi';
import { useAuthStore } from '../stores/useAuthStore';

const errorMessage = ref('');

interface Licence {
    id: number;
    ligue: string;
    comite: string;
    club_number: number;
    club_name: string;
    name: string;
    surname: string;
    category: string;
    licence_number: number;
    user_id: number;
}

const isFetchingLicence = ref(false);

export const licence = ref<Licence | null>(null);

export const fetchLicence = async () => {
    const authStore = useAuthStore();

    if (isFetchingLicence.value || !authStore.isAuthenticated) {
        return;
    }
    isFetchingLicence.value = true;
    try {
        const response = await backendApi.get('/licences/me', {
            headers: { Authorization: `Bearer ${authStore.token}` }
        });
        licence.value = response.data;
    } catch (error: any) {
        console.error('Fetch licence error:', error);
        if (error.response?.status === 404) {
            console.warn('No licence found for this user');
            licence.value = null;
        } else {
            errorMessage.value = 'Erreur lors du chargement de la licence';
        }
    } finally {
        isFetchingLicence.value = false;
    }
};

const ligueMap: Record<string, string> = {
    'SDE': 'Sud-Est',
    'NRD': 'Nord',
    'AQU': 'Aquitaine',
    'BRE': 'Bretagne',
    'EST': 'Est',
    'PDL': 'Pays de la Loire',
    'SDO': 'Sud-Ouest',
};

const comiteMap: Record<string, string> = {
    "MER": "Méridional",
    "AUV": "Auvergne",
    "AQN": "Aquitaine Nord",
    "AQS": "Aquitaine Sud",
    "CDA": "Côtes-d'Armor",
    "FIN": "Finistère",
    "IEV": "Ile et Vilaine",
    "MAN": "Manche",
    "MOR": "Morbihan",
    "ASL": "Alsace",
    "NIE": "Nièvre",
    "VOS": "Vosges",
    "NPC": "Nord-Pas-de-Calais",
    "PAR": "Paris",
    "PIC": "Picardie",
    "ANJ": "Anjou",
    "CEN": "Centre",
    "LAT": "Loire-Atlantique",
    "MAI": "Maine",
    "ALP": "Alpes",
    "VDR": "Vallée du Rhône",
    "MPY": "Midi-Pyrénées",
    "PYA": "Pyrénées-Atlantique",
    "TGA": "Tarn-et-Garonne",
};

const categoryMap: Record<string, string> = {
    'M': 'Masculine',
    'F': 'Féminine',
    'V': 'Vétéran',
    'J': 'Junior',
};

export const mapLigue = (code: string): string => {
    return ligueMap[code] || code;
};

export const mapComite = (code: string): string => {
    return comiteMap[code] || code;
};

export const mapCategory = (code: string): string => {
    return categoryMap[code] || code;
};