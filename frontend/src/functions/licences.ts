import { ref } from 'vue';
import backendApi from '../axios/backendApi';
import { useAuthStore } from '../stores/useAuthStore';
import ffdLogo from '@/assets/ffd.png';

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

export const printLicence = () => {
    if (!licence.value) {
        console.warn('No licence to print');
        return;
    }

    const lic = licence.value; // Stocke pour éviter null

    // Chargement de l'image comme base64
    const img = new Image();
    img.src = ffdLogo;
    img.crossOrigin = 'Anonymous'; // Pour éviter CORS si besoin
    img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.drawImage(img, 0, 0);
        const base64Logo = canvas.toDataURL('image/png');

        // Contenu imprimable COMPLET avec tous les styles et données
        const printContent = `
      <html>
      <head>
        <style>
          @page { size: 85.6mm 53.98mm; margin: 0; }
          body { margin: 0; padding: 0; font-family: Arial, sans-serif; background: white; }
          .print-card { 
            width: 85.6mm; 
            height: 53.98mm; 
            border: 1px solid #000; 
            border-radius: 5mm; 
            overflow: hidden;
            box-sizing: border-box;
            position: relative;
            page-break-after: always; /* Sépare recto/verso */
          }
          .card-front, .card-back {
            width: 100%;
            height: 100%;
            padding: 5mm;
            box-sizing: border-box;
          }
          .card-header {
            display: flex;
            align-items: center;
            border-bottom: 1px solid #ccc;
            padding-bottom: 2mm;
            margin-bottom: 2mm;
          }
          .logo {
            width: 15mm;
            height: auto;
            margin-right: 3mm;
          }
          .header-text h1 {
            margin: 0;
            font-size: 4mm;
            color: #0056b3;
          }
          .header-text p {
            margin: 1mm 0 0;
            font-size: 2.5mm;
          }
          .season {
            font-weight: bold;
            font-size: 3mm;
          }
          .holder-name {
            font-size: 4mm;
            font-weight: bold;
            margin: 2mm 0;
            text-transform: uppercase;
          }
          .licence-number {
            font-size: 3mm;
            margin: 1mm 0;
          }
          .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1mm;
            font-size: 2.5mm;
            margin-top: 2mm;
          }
          .card-back {
            display: flex;
            justify-content: center;
            align-items: center;
            background: white;
          }
          .back-logo {
            width: 40mm;
            height: auto;
          }
        </style>
      </head>
      <body>
        <!-- Recto -->
        <div class="print-card card-front">
          <div class="card-header">
            <img src="${base64Logo}" alt="FFD Logo" class="logo" />
            <div class="header-text">
              <h1>Fédération Française de Darts</h1>
              <p>Affiliée à la World Darts Federation</p>
              <p class="season">Saison: 2025 - 2026</p>
            </div>
          </div>
          <div>
            <p class="holder-name"><strong>${lic.name} ${lic.surname}</strong></p>
            <p class="licence-number"><strong>Licence N°:</strong> ${lic.licence_number}</p>
            <div class="info-grid">
              <div><strong>${lic.club_name}</strong></div>
              <div><strong>Catégorie</strong> ${mapCategory(lic.category)}</div>
              <div><strong>Ligue</strong> ${mapLigue(lic.ligue)} (${lic.ligue})</div>
              <div><strong>Comité</strong> ${mapComite(lic.comite)} (${lic.comite})</div>
            </div>
          </div>
        </div>
        <!-- Verso -->
        <div class="print-card card-back">
          <img src="${base64Logo}" alt="FFD Logo Verso" class="back-logo" />
        </div>
      </body>
      </html>
    `;

        const printWindow = window.open('', '_blank');
        if (printWindow) {
            printWindow.document.open();
            printWindow.document.write(printContent);
            printWindow.document.close();
            // Attendre que les images soient chargées
            printWindow.onload = () => {
                printWindow.focus();
                printWindow.print();
                printWindow.close();
            };
        }
    };
    img.onerror = () => console.error('Failed to load logo for print');
};