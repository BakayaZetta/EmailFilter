<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import api from '@/services/api';
import { useRouter } from 'vue-router';
import MailComponent from '@/components/MailComponent.vue';

const router = useRouter();
const authStore = useAuthStore();
const mails = ref([]);
const loading = ref(true);
const error = ref(null);
const expandedMailId = ref(null);

// Pour la sélection multiple
const selectedMails = ref([]);
const allSelected = computed(() => {
  return mails.value.length > 0 && selectedMails.value.length === mails.value.length;
});

// Fonction pour basculer l'affichage du contenu d'un mail
const toggleExpand = (mailId) => {
  if (expandedMailId.value === mailId) {
    expandedMailId.value = null; // Fermer si déjà ouvert
  } else {
    expandedMailId.value = mailId; // Ouvrir ce mail
  }
};

// Formater la date pour l'affichage au format h:min:s d/m/y
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);

  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();

  return `${hours}:${minutes}:${seconds} ${day}/${month}/${year}`;
};

// Obtenir les classes pour l'indicateur de statut
const getStatusClass = (status) => {
  switch(status?.toUpperCase()) {
    case 'QUARANTINE': return 'bg-yellow-500';
    case 'ERROR': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
};

// Map de statuts pour la légende
const statusMap = [
  { name: 'Quarantine', color: 'bg-yellow-500' },
  { name: 'Error', color: 'bg-red-500' }
];

// Charger les mails en quarantaine et avec erreur - MISE À JOUR POUR NOUVELLE API
const loadQuarantineMails = async () => {
  loading.value = true;
  error.value = null;
  selectedMails.value = []; // Réinitialiser la sélection
  expandedMailId.value = null; // Réinitialiser l'expansion

  try {
    if (!authStore.isLoggedIn) {
      throw new Error('User must be logged in');
    }

    // Utiliser la nouvelle route API
    const response = await api.get('/mails/status', {
      params: { status: 'QUARANTINE,ERROR' }
    });

    // Normaliser les données pour compatibilité
    mails.value = response.data.map(mail => ({
      ID_Mail: mail.id || mail.ID_Mail,
      ID_Utilisateur: mail.user?.id || mail.ID_Utilisateur,
      Emetteur: mail.sender || mail.Emetteur,
      Sujet: mail.subject || mail.Sujet,
      Date_Reception: mail.receivedDate || mail.Date_Reception,
      Statut: mail.status || mail.Statut,
      // Conserver l'objet original également
      originalData: mail
    }));
  } catch (err) {
    console.error('Failed to load quarantine mails:', err);
    error.value = 'Failed to load quarantine mails. Please try again later.';
  } finally {
    loading.value = false;
  }
};

// Gérer la sélection de tous les mails
const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedMails.value = [];
  } else {
    selectedMails.value = mails.value.map(mail => mail.ID_Mail);
  }
};

// Gérer la sélection individuelle
const toggleSelect = (mailId) => {
  const index = selectedMails.value.indexOf(mailId);
  if (index === -1) {
    selectedMails.value.push(mailId);
  } else {
    selectedMails.value.splice(index, 1);
  }
};

// Vérifier si un mail est sélectionné
const isSelected = (mailId) => {
  return selectedMails.value.includes(mailId);
};

// Actions en masse - MISE À JOUR POUR NOUVELLE API
const bulkMarkAsSafe = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to mark as safe.');
    return;
  }

  try {
    loading.value = true;
    const promises = selectedMails.value.map(mailId =>
      // Utiliser le bon endpoint pour mettre à jour le statut
      api.put(`/mails/${mailId}/status`, { status: 'SAFE' })
    );

    await Promise.all(promises);
    await loadQuarantineMails();

  } catch (err) {
    console.error('Failed to update mail status:', err);
    alert('Failed to update mail status. Please try again.');
  } finally {
    loading.value = false;
  }
};

// MISE À JOUR POUR NOUVELLE API
const bulkDelete = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to delete.');
    return;
  }

  if (confirm(`Are you sure you want to delete ${selectedMails.value.length} email(s)?`)) {
    try {
      loading.value = true;
      const promises = selectedMails.value.map(mailId =>
        api.put(`/mails/${mailId}/status`, { status: 'DELETED' })
      );

      await Promise.all(promises);
      await loadQuarantineMails();

    } catch (err) {
      console.error('Failed to delete mails:', err);
      alert('Failed to delete mails. Please try again.');
    } finally {
      loading.value = false;
    }
  }
};

// Actions individuelles - MISE À JOUR POUR NOUVELLE API
const markAsSafe = async (mailId) => {
  try {
    await api.put(`/mails/${mailId}/status`, { status: 'SAFE' });
    await loadQuarantineMails();
  } catch (err) {
    console.error('Failed to update mail status:', err);
    alert('Failed to update mail status. Please try again.');
  }
};

// Supprimer un mail - MISE À JOUR POUR NOUVELLE API
const deleteMail = async (mailId) => {
  if (confirm('Are you sure you want to delete this mail?')) {
    try {
      await api.put(`/mails/${mailId}/status`, { status: 'DELETED' });
      await loadQuarantineMails();
    } catch (err) {
      console.error('Failed to delete mail:', err);
      alert('Failed to delete mail. Please try again.');
    }
  }
};

// Fermer un mail développé
const closeExpandedMail = () => {
  expandedMailId.value = null;
};

// Nouvelles variables pour le tri
const sortColumn = ref('Date_Reception'); // Colonne triée par défaut
const sortDirection = ref('desc'); // Direction du tri ('asc' ou 'desc')

// Fonction pour trier les mails
const sortMails = computed(() => {
  if (!mails.value?.length) return [];

  // Copie du tableau pour ne pas modifier l'original
  const sortedMails = [...mails.value];

  // Tri selon la colonne et la direction actuelles
  sortedMails.sort((a, b) => {
    let valA, valB;

    // Déterminer les valeurs à comparer selon la colonne
    switch(sortColumn.value) {
      case 'Statut':
        valA = a.Statut || '';
        valB = b.Statut || '';
        break;
      case 'ID_Utilisateur':
        valA = a.ID_Utilisateur || 0;
        valB = b.ID_Utilisateur || 0;
        break;
      case 'Emetteur':
        valA = a.Emetteur || '';
        valB = b.Emetteur || '';
        break;
      case 'Sujet':
        valA = a.Sujet || '';
        valB = b.Sujet || '';
        break;
      case 'Date_Reception':
        valA = new Date(a.Date_Reception || 0).getTime();
        valB = new Date(b.Date_Reception || 0).getTime();
        break;
      default:
        valA = a[sortColumn.value] || '';
        valB = b[sortColumn.value] || '';
    }

    // Comparaison selon la direction
    if (sortDirection.value === 'asc') {
      return valA > valB ? 1 : valA < valB ? -1 : 0;
    } else {
      return valA < valB ? 1 : valA > valB ? -1 : 0;
    }
  });

  return sortedMails;
});

// Fonction pour changer la colonne de tri
const toggleSort = (column) => {
  if (sortColumn.value === column) {
    // Si déjà trié sur cette colonne, inverser la direction
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    // Sinon, changer la colonne et trier en ascendant
    sortColumn.value = column;
    sortDirection.value = 'asc';
  }
};

// Modifier la fonction pour renvoyer toujours une icône
const getSortIcon = (column) => {
  if (sortColumn.value !== column) {
    return 'pi-filter text-gray-300'; // Icône neutre pour les colonnes non triées
  }
  return sortDirection.value === 'asc'
    ? 'pi-sort-amount-up-alt text-blue-500'
    : 'pi-sort-amount-down text-blue-500';
};

// Vérifier l'authentification et charger les données
onMounted(async () => {
  authStore.initialize();

  if (authStore.isLoggedIn) {
    await loadQuarantineMails();
  } else {
    // Rediriger vers login si non connecté
    router.push('/login');
  }
});
</script>

<template>
  <section class="py-4">
    <div class="container mx-auto px-2">
      <div class="max-w-full mx-auto">
        <div class="flex justify-between items-center mb-2">
          <h1 class="text-3xl font-bold">Quarantine</h1>
          <button
            @click="loadQuarantineMails"
            class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center"
          >
            <i class="pi pi-refresh mr-1 text-xs"></i>Refresh
          </button>
        </div>

        <p class="text-sm text-gray-600 mb-3">All emails detected as potentially malicious or containing errors.</p>

        <!-- Légende des statuts -->
        <div class="flex flex-wrap items-center space-x-4 mb-2 text-xs">
          <div class="text-gray-500">Status:</div>
          <div v-for="status in statusMap" :key="status.name" class="flex items-center">
            <div :class="['w-3 h-3 rounded-full mr-1', status.color]"></div>
            <span>{{ status.name }}</span>
          </div>
        </div>

        <div v-if="loading" class="flex justify-center py-10">
          <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
          <span class="ml-3 text-red-500">Loading emails...</span>
        </div>

        <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-2 mb-3 text-sm">
          <p class="text-red-700">{{ error }}</p>
        </div>

        <div v-else-if="mails.length === 0" class="bg-gray-50 rounded-lg p-4 text-center">
          <div class="text-gray-500 text-sm mb-1">No quarantined emails found</div>
          <p class="text-gray-400 text-xs">The system has not detected any suspicious emails</p>
        </div>

        <div v-else>
          <!-- Barre d'actions en masse -->
          <div class="bg-gray-50 p-3 mb-3 rounded-lg flex justify-between items-center">
            <div class="flex items-center">
              <span class="text-sm mr-2">With selected:</span>
              <button
                @click="bulkMarkAsSafe"
                class="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 mr-2 disabled:opacity-50"
                :disabled="selectedMails.length === 0"
              >
                <i class="pi pi-check mr-1 text-xs"></i> Mark as Safe
              </button>
              <button
                @click="bulkDelete"
                class="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 disabled:opacity-50"
                :disabled="selectedMails.length === 0"
              >
                <i class="pi pi-trash mr-1 text-xs"></i> Delete
              </button>
            </div>
            <div class="text-sm text-gray-500">
              {{ selectedMails.length }} of {{ mails.length }} selected
            </div>
          </div>

          <!-- Wrapper with shadow and rounded corners -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <!-- Container for both horizontal and vertical scrolling -->
            <div class="overflow-auto max-h-[85vh]">
              <table class="w-full divide-y divide-gray-200 text-sm table-fixed">
                <thead class="bg-gray-50 sticky top-0 z-10">
                  <tr class="text-xs">
                    <th scope="col" class="w-[3%] px-2 py-2 text-center">
                      <input
                        type="checkbox"
                        :checked="allSelected"
                        @change="toggleSelectAll"
                        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                    <th
                      scope="col"
                      @click="toggleSort('Statut')"
                      class="w-[5%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div class="flex items-center justify-center">
                        <span>Status</span>
                        <i class="pi ml-1" :class="getSortIcon('Statut')"></i>
                      </div>
                    </th>
                    <th
                      scope="col"
                      @click="toggleSort('ID_Utilisateur')"
                      class="w-[5%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div class="flex items-center justify-center">
                        <span>ID</span>
                        <i class="pi ml-1" :class="getSortIcon('ID_Utilisateur')"></i>
                      </div>
                    </th>
                    <th
                      scope="col"
                      @click="toggleSort('Emetteur')"
                      class="w-[15%] px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div class="flex items-center">
                        <span>Sender</span>
                        <i class="pi ml-1" :class="getSortIcon('Emetteur')"></i>
                      </div>
                    </th>
                    <th
                      scope="col"
                      @click="toggleSort('Sujet')"
                      class="w-[40%] px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div class="flex items-center">
                        <span>Subject</span>
                        <i class="pi ml-1" :class="getSortIcon('Sujet')"></i>
                      </div>
                    </th>
                    <th
                      scope="col"
                      @click="toggleSort('Date_Reception')"
                      class="w-[17%] px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    >
                      <div class="flex items-center">
                        <span>Received</span>
                        <i class="pi ml-1" :class="getSortIcon('Date_Reception')"></i>
                      </div>
                    </th>
                    <th scope="col" class="w-[15%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <template v-for="mail in sortMails" :key="mail.ID_Mail">
                    <!-- Ligne normale du mail -->
                    <tr class="hover:bg-gray-50">
                      <td class="px-2 py-2 text-center">
                        <input
                          type="checkbox"
                          :checked="isSelected(mail.ID_Mail)"
                          @change="toggleSelect(mail.ID_Mail)"
                          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td class="px-2 py-2 text-center">
                        <!-- Status indicator dot -->
                        <div
                          :class="['w-3 h-3 rounded-full mx-auto', getStatusClass(mail.Statut)]"
                          :title="mail.Statut"
                        ></div>
                      </td>
                      <td class="px-2 py-2 text-center text-xs">
                        {{ mail.ID_Utilisateur }}
                      </td>
                      <td class="px-2 py-2 truncate" :title="mail.Emetteur">
                        {{ mail.Emetteur }}
                      </td>
                      <td class="px-2 py-2 truncate" :title="mail.Sujet">
                        {{ mail.Sujet }}
                      </td>
                      <td class="px-2 py-2 text-xs">
                        {{ formatDate(mail.Date_Reception) }}
                      </td>
                      <td class="px-2 py-2 text-center whitespace-nowrap">
                        <div class="flex justify-center space-x-2">
                          <!-- Bouton Examiner -->
                          <button
                            @click="toggleExpand(mail.ID_Mail)"
                            :title="expandedMailId === mail.ID_Mail ? 'Hide content' : 'Examine content'"
                            :class="[
                              'px-2 py-1 text-white rounded-full',
                              expandedMailId === mail.ID_Mail ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'
                            ]"
                          >
                            <i class="pi pi-search text-xs"></i>
                          </button>
                          <button
                            @click="markAsSafe(mail.ID_Mail)"
                            title="Mark as Safe"
                            class="px-2 py-1 text-white bg-green-500 hover:bg-green-600 rounded-full"
                          >
                            <i class="pi pi-check text-xs"></i>
                          </button>
                          <button
                            @click="deleteMail(mail.ID_Mail)"
                            title="Delete"
                            class="px-2 py-1 text-white bg-red-500 hover:bg-red-600 rounded-full"
                          >
                            <i class="pi pi-trash text-xs"></i>
                          </button>
                        </div>
                      </td>
                    </tr>

                    <!-- Ligne de contenu développée utilisant MailComponent -->
                    <tr v-if="expandedMailId === mail.ID_Mail">
                      <td colspan="7" class="bg-gray-50 px-4 py-4">
                        <MailComponent
                          :mail="mail"
                          :expanded="true"
                          @close="closeExpandedMail"
                        />
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Animation pour l'apparition du contenu développé */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fadeIn {
  animation: fadeIn 0.2s ease-out forwards;
}

/* Styles pour les en-têtes de colonnes triables */
th.cursor-pointer {
  position: relative;
  transition: background-color 0.2s;
}

th .pi {
  font-size: 0.75rem;
  transition: all 0.2s;
}

th:hover .pi.text-gray-300 {
  color: #6b7280; /* Rendre l'icône plus visible au survol de l'en-tête */
}

/* Mise en évidence de la colonne active */
th:has(.text-blue-500) {
  background-color: rgba(219, 234, 254, 0.3); /* Bleu très clair */
}
</style>
