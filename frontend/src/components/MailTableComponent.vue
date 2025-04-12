<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import MailComponent from '@/components/MailComponent.vue';
import { formatDateTime, getStatusClass, getStatusMap } from '@/utils/formatters';
import SearchBarComponent from '@/components/SearchBarComponent.vue';
import MistralResponseModal from '@/components/MistralResponseModal.vue';
import mistralService from '@/services/mistralService';
import mailService from '@/services/mailService';

const props = defineProps({
  mails: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  expandedMailId: {
    type: [Number, String, null],
    default: null
  },
  selectedMails: {
    type: Array,
    default: () => []
  },
  sortColumn: {
    type: String,
    default: 'Date_Reception'
  },
  sortDirection: {
    type: String,
    default: 'desc'
  },
  statusTypes: {
    type: Array,
    default: () => []
  },
  searchQuery: {
    type: Object,
    default: () => ({})
  },
  // Nouvelle prop pour contrôler l'affichage du bouton Mistral
  showMistralButton: {
    type: Boolean,
    default: true
  }
});

// Référence pour le composant de mail développé
const mailComponentRef = ref(null);

// Émissions pour communiquer avec le composant parent
const emit = defineEmits([
  'toggle-select-all',
  'toggle-select',
  'toggle-expand',
  'toggle-sort',
  'update-mail-status',
  'bulk-update-status',
  'refresh',
  'search',
  'reset-search',
]);

// États pour la fonctionnalité Mistral
const showMistralModal = ref(false);
const mistralLoading = ref(false);
const mistralResponse = ref(null);
const mistralError = ref(null);
const mistralEmailId = ref(null);
const mistralMailDetails = ref(null);

// Computed pour vérifier si tous les mails sont sélectionnés
const allSelected = computed(() => {
  return props.mails.length > 0 && props.selectedMails.length === props.mails.length;
});

// Vérifier si un mail est sélectionné
const isSelected = (mailId) => {
  return props.selectedMails.includes(mailId);
};

const statusMap = computed(() => {
  // Si les types de statuts sont fournis, utiliser ceux-là
  if (props.statusTypes.length > 0) {
    return props.statusTypes.map(status => ({
      name: status,
      color: getStatusClass(status)
    }));
  }
  // Sinon utiliser la map par défaut
  return getStatusMap();
});

// Obtenir l'icône pour le tri
const getSortIcon = (column) => {
  if (props.sortColumn !== column) {
    return 'pi-filter text-gray-300';
  }
  return props.sortDirection === 'asc'
    ? 'pi-sort-amount-up-alt text-blue-500'
    : 'pi-sort-amount-down text-blue-500';
};

// Gestionnaire de clic sur une ligne pour développer/réduire le mail
const handleRowClick = (event, mailId) => {
  // Ne pas développer si on clique sur une checkbox ou un bouton
  if (event.target.type === 'checkbox' ||
    event.target.tagName === 'BUTTON' ||
    event.target.closest('button') ||
    event.target.tagName === 'I') {
    return;
  }

  emit('toggle-expand', mailId);
};

// Fonction pour demander une explication à Mistral
const askMistral = async (emailId) => {
  mistralLoading.value = true;
  mistralError.value = null;
  mistralResponse.value = null;
  mistralEmailId.value = emailId;
  mistralMailDetails.value = null;
  showMistralModal.value = true;

  try {
    // Récupérer les détails du mail
    const mailDetails = await mailService.getMailDetails(emailId);
    mistralMailDetails.value = mailDetails;

    // Envoyer ces détails à Mistral
    const data = await mistralService.getExplanation(emailId, mailDetails);
    mistralResponse.value = data.explanation;
  } catch (error) {
    console.error("Erreur lors de la demande d'explication à Mistral:", error);

    if (error.response) {
      mistralError.value = error.response.data?.message || "Erreur lors de la communication avec l'API";
    } else {
      mistralError.value = "Impossible de contacter le service d'explication. Veuillez réessayer plus tard.";
    }
  } finally {
    mistralLoading.value = false;
  }
};

// Fonction pour fermer le modal Mistral
const closeMistralModal = () => {
  showMistralModal.value = false;
  setTimeout(() => {
    mistralLoading.value = false;
    mistralResponse.value = null;
    mistralError.value = null;
    mistralEmailId.value = null;
  }, 300); // Délai pour l'animation de fermeture
};

// Gestionnaire pour fermer le mail détaillé quand on clique en dehors
const handleDocumentClick = (event) => {
  // Si aucun mail n'est développé, on ne fait rien
  if (!props.expandedMailId) return;

  // Vérifier si le clic est sur un élément interactif (bouton, checkbox, etc.)
  const isInteractive = event.target.closest('button') ||
    event.target.tagName === 'INPUT' ||
    event.target.tagName === 'BUTTON' ||
    event.target.tagName === 'A' ||
    event.target.tagName === 'I';

  // Ne pas fermer si on clique sur un élément interactif
  if (isInteractive) return;

  // Vérifier si le clic est à l'intérieur du composant mail développé
  const mailComponent = document.getElementById(`mail-detail-${props.expandedMailId}`);
  if (mailComponent && mailComponent.contains(event.target)) return;

  // Vérifier si le clic est sur une ligne de mail
  const clickedRow = event.target.closest('tr');
  if (clickedRow) {
    // Si c'est la ligne du mail développé, ne pas fermer
    const mailIdAttribute = clickedRow.getAttribute('data-mail-id');
    if (mailIdAttribute && parseInt(mailIdAttribute) === props.expandedMailId) return;
  }

  // Dans tous les autres cas, fermer le mail développé
  emit('toggle-expand', null);
};

// Ajouter et supprimer le gestionnaire de clic sur le document
onMounted(() => {
  document.addEventListener('click', handleDocumentClick);
});

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick);
});
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-2">
      <slot name="header">
        <!-- Slot par défaut pour le titre -->
        <h1 class="text-3xl font-bold">Mail List</h1>
      </slot>

      <button @click="emit('refresh')"
        class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center">
        <i class="pi pi-refresh mr-1 text-xs"></i>Refresh
      </button>
    </div>

    <slot name="description">
      <!-- Slot pour la description -->
    </slot>

    <!-- Barre de recherche -->
    <SearchBarComponent :status-options="statusTypes" :initial-query="searchQuery"
      @search="query => emit('search', query)" @reset="emit('reset-search')" />

    <!-- Légende des statuts -->
    <div class="flex flex-wrap items-center space-x-4 mb-2 text-xs">
      <div class="text-gray-500">Status:</div>
      <div v-for="status in statusMap" :key="status.name" class="flex items-center">
        <div :class="['w-3 h-3 rounded-full mr-1', status.color]"></div>
        <span>{{ status.name }}</span>
      </div>
    </div>

    <!-- Indicateur de filtrage -->
    <div v-if="Object.values(searchQuery).some(v => v !== '')"
      class="bg-blue-50 border-l-4 border-blue-500 p-2 text-sm mb-3">
      <p class="text-blue-700">
        Showing {{ mails.length }} filtered results
        <button @click="$emit('reset-search')" class="ml-2 text-blue-600 hover:text-blue-800 underline">
          Reset filters
        </button>
      </p>
    </div>

    <!-- Ajouter dans le template après l'indicateur de filtrage, à enlever après débogage -->
    <div v-if="false" class="bg-gray-100 p-2 text-xs mb-3 whitespace-pre overflow-auto max-h-32">
      Structure de données: {{ JSON.stringify(mails[0], null, 2) }}
    </div>

    <!-- Indicateur de chargement -->
    <div v-if="loading" class="flex justify-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
      <span class="ml-3 text-red-500">Loading emails...</span>
    </div>

    <!-- Message d'erreur -->
    <div v-else-if="error" class="bg-red-50 border-l-4 border-red-500 p-2 mb-3 text-sm">
      <p class="text-red-700">{{ error }}</p>
    </div>

    <!-- Aucun résultat -->
    <div v-else-if="mails.length === 0" class="bg-gray-50 rounded-lg p-4 text-center">
      <div class="text-gray-500 text-sm mb-1">No emails found</div>
      <p class="text-gray-400 text-xs">
        <slot name="empty-message">No emails match the current filters</slot>
      </p>
    </div>

    <!-- Affichage des emails -->
    <div v-else>
      <!-- Barre d'actions en masse -->
      <div class="bg-gray-50 p-3 mb-3 rounded-lg flex justify-between items-center">
        <div class="flex items-center">
          <span class="text-sm mr-2">With selected:</span>
          <slot name="bulk-actions" :selectedCount="selectedMails.length"></slot>
        </div>
        <div class="text-sm text-gray-500">
          {{ selectedMails.length }} of {{ mails.length }} selected
        </div>
      </div>

      <!-- Table des emails -->
      <div class="bg-white shadow rounded-lg overflow-hidden">
        <div class="overflow-auto max-h-[85vh]">
          <table class="w-full divide-y divide-gray-200 text-sm table-fixed">
            <thead class="bg-gray-50 sticky top-0 z-10">
              <tr class="text-xs">
                <!-- Checkbox pour tout sélectionner -->
                <th scope="col" class="w-[3%] px-2 py-2 text-center">
                  <input type="checkbox" :checked="allSelected" @change="emit('toggle-select-all')"
                    class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                </th>

                <!-- Colonnes triables -->
                <th v-for="(column, index) in [
                  { key: 'Statut', name: 'Status', width: 'w-[5%]', center: true },
                  { key: 'ID_Utilisateur', name: 'ID', width: 'w-[5%]', center: true },
                  { key: 'Emetteur', name: 'Sender', width: 'w-[20%]' },
                  { key: 'Sujet', name: 'Subject', width: 'w-[42%]' },
                  { key: 'Date_Reception', name: 'Received', width: 'w-[17%]' }
                ]" :key="index" scope="col" @click="emit('toggle-sort', column.key)" :class="[
                  column.width,
                  'px-2 py-2 font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100',
                  column.center ? 'text-center' : 'text-left'
                ]">
                  <div :class="['flex items-center', column.center ? 'justify-center' : '']">
                    <span>{{ column.name }}</span>
                    <i class="pi ml-1" :class="getSortIcon(column.key)"></i>
                  </div>
                </th>

                <!-- Colonne actions - réduite en largeur -->
                <th scope="col" class="w-[8%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>

            <tbody class="bg-white divide-y divide-gray-200">
              <template v-for="mail in mails" :key="mail.ID_Mail">
                <!-- Ligne de mail cliquable -->
                <tr class="hover:bg-gray-50 cursor-pointer" :class="{
                  'bg-blue-50': expandedMailId === mail.ID_Mail,
                  'bg-blue-100': isSelected(mail.ID_Mail) && expandedMailId !== mail.ID_Mail
                }" @click="handleRowClick($event, mail.ID_Mail)" :data-mail-id="mail.ID_Mail">
                  <!-- Checkbox -->
                  <td class="px-2 py-2 text-center">
                    <input type="checkbox" :checked="isSelected(mail.ID_Mail)"
                      @change="emit('toggle-select', mail.ID_Mail)" @click.stop
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                  </td>

                  <!-- Statut -->
                  <td class="px-2 py-2 text-center">
                    <div :class="['w-3 h-3 rounded-full mx-auto', getStatusClass(mail.Statut)]" :title="mail.Statut">
                    </div>
                  </td>

                  <!-- ID Utilisateur -->
                  <td class="px-2 py-2 text-center text-xs">
                    {{ mail.ID_Utilisateur }}
                  </td>

                  <!-- Émetteur -->
                  <td class="px-2 py-2 truncate" :title="mail.Emetteur">
                    {{ mail.Emetteur }}
                  </td>

                  <!-- Sujet -->
                  <td class="px-2 py-2 truncate" :title="mail.Sujet">
                    {{ mail.Sujet }}
                  </td>

                  <!-- Date de réception -->
                  <td class="px-2 py-2 text-xs">
                    {{ formatDateTime(mail.Date_Reception) }}
                  </td>

                  <!-- Actions - Bouton Mistral et actions spécifiques uniquement -->
                  <td class="px-2 py-2 text-center whitespace-nowrap">
                    <div class="flex justify-center space-x-2">
                      <!-- Bouton Mistral - maintenant conditionnel -->
                      <button v-if="showMistralButton" @click.stop="askMistral(mail.ID_Mail)"
                        title="Expliquer avec Mistral"
                        class="px-2 py-1 text-white rounded-full bg-purple-500 hover:bg-purple-600">
                        <i class="pi pi-comment text-xs"></i>
                      </button>

                      <!-- Slot pour actions spécifiques -->
                      <slot name="row-actions" :mail="mail"></slot>
                    </div>
                  </td>
                </tr>

                <!-- Ligne de contenu développée utilisant MailComponent -->
                <tr v-if="expandedMailId === mail.ID_Mail">
                  <td colspan="7" class="bg-gray-50 px-4 py-4">
                    <div :id="`mail-detail-${mail.ID_Mail}`">
                      <MailComponent ref="mailComponentRef" :mail="mail" :expanded="true"
                        @close="emit('toggle-expand', mail.ID_Mail)" />
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Modal Mistral -->
    <MistralResponseModal v-if="showMistralModal" :response="mistralResponse" :loading="mistralLoading"
      :error="mistralError" :emailId="mistralEmailId" @close="closeMistralModal" />
  </div>
</template>

<style scoped>
/* Animation pour l'apparition du contenu développé */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  color: #6b7280;
  /* Rendre l'icône plus visible au survol de l'en-tête */
}

/* Mise en évidence de la colonne active */
th:has(.text-blue-500) {
  background-color: rgba(219, 234, 254, 0.3);
  /* Bleu très clair */
}

/* Style pour indiquer qu'une ligne est cliquable */
tbody tr:hover {
  background-color: rgba(243, 244, 246, 0.8);
  /* Gris très léger au survol */
}

/* Style pour la ligne active/sélectionnée */
tbody tr.selected {
  background-color: rgba(219, 234, 254, 0.5);
  /* Bleu très clair */
}

/* Style pour la ligne sélectionnée */
tbody tr.bg-blue-100 {
  background-color: rgba(219, 234, 254, 0.7);
}

/* Style pour rendre le tableau focusable mais sans bordure visible */
.overflow-auto:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  /* Subtil halo bleu quand focus */
}
</style>
