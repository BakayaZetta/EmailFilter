<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import api from '@/services/api';
import { useRouter } from 'vue-router';

const router = useRouter();
const authStore = useAuthStore();
const mails = ref([]);
const loading = ref(true);
const error = ref(null);
const expandedMailId = ref(null); // Pour suivre quel mail est développé

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

// Charger les mails en quarantaine et avec erreur
const loadQuarantineMails = async () => {
  loading.value = true;
  error.value = null;
  selectedMails.value = []; // Réinitialiser la sélection
  expandedMailId.value = null; // Réinitialiser l'expansion

  try {
    if (!authStore.isLoggedIn) {
      throw new Error('User must be logged in');
    }

    // Récupérer TOUS les mails en quarantaine et avec erreur (vue administrateur)
    const response = await api.get(`/mails/status/filter`, {
      params: { status: 'QUARANTINE,ERROR' }
    });

    // Initialiser les propriétés d'affichage pour chaque mail
    mails.value = response.data.map(mail => ({
      ...mail,
      showRawHtml: false
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

// Actions en masse
const bulkMarkAsSafe = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to mark as safe.');
    return;
  }

  try {
    loading.value = true;
    const promises = selectedMails.value.map(mailId =>
      api.put(`/mails/${mailId}`, { status: 'SAFE' })
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

const bulkDelete = async () => {
  if (selectedMails.value.length === 0) {
    alert('Please select at least one email to delete.');
    return;
  }

  if (confirm(`Are you sure you want to delete ${selectedMails.value.length} email(s)?`)) {
    try {
      loading.value = true;
      const promises = selectedMails.value.map(mailId =>
        api.put(`/mails/${mailId}`, { status: 'DELETED' })
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

// Actions individuelles
const markAsSafe = async (mailId) => {
  try {
    await api.put(`/mails/${mailId}`, { status: 'SAFE' });
    // Recharger la liste après modification
    await loadQuarantineMails();
  } catch (err) {
    console.error('Failed to update mail status:', err);
    alert('Failed to update mail status. Please try again.');
  }
};

// Supprimer un mail
const deleteMail = async (mailId) => {
  if (confirm('Are you sure you want to delete this mail?')) {
    try {
      await api.put(`/mails/${mailId}`, { status: 'DELETED' });
      // Recharger la liste après modification
      await loadQuarantineMails();
    } catch (err) {
      console.error('Failed to delete mail:', err);
      alert('Failed to delete mail. Please try again.');
    }
  }
};

// Nouvelle fonction pour sécuriser le HTML des emails
const sanitizeHtml = (html) => {
  if (!html) return '<em>The content of this email is not available or is empty.</em>';

  // Wrapper pour le contenu avec intercepteur de clics
  return `
    <div class="secured-email-content">
      ${html}
    </div>
  `;
};

// Empêcher les clics sur le contenu des emails
const preventClicks = (event) => {
  // Vérifier si la cible ou l'un de ses parents est un lien
  let target = event.target;
  while (target) {
    if (target.tagName && target.tagName.toLowerCase() === 'a') {
      event.preventDefault();
      event.stopPropagation();

      // Afficher un message d'alerte
      alert('Link clicking is disabled for security reasons. This email may be a phishing attempt.');
      return;
    }
    target = target.parentElement;
  }
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

        <div v-if="loading" class="flex justify-center py-6">
          <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-red-500"></div>
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
            <div class="overflow-auto max-h-[80vh]">
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
                    <th scope="col" class="w-[5%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th scope="col" class="w-[5%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">ID</th>
                    <th scope="col" class="w-[15%] px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Sender</th>
                    <th scope="col" class="w-[40%] px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                    <th scope="col" class="w-[17%] px-2 py-2 text-left font-medium text-gray-500 uppercase tracking-wider">Received</th>
                    <th scope="col" class="w-[15%] px-2 py-2 text-center font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <template v-for="mail in mails" :key="mail.ID_Mail">
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
                          <!-- Nouveau bouton Examiner -->
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

                    <!-- Ligne de contenu développée -->
                    <tr v-if="expandedMailId === mail.ID_Mail">
                      <td colspan="7" class="bg-gray-50 px-4 py-4">
                        <div class="animate-fadeIn">
                          <div class="bg-white rounded-md shadow p-4">
                            <!-- En-tête détaillé du mail -->
                            <div class="mb-3 border-b pb-3">
                              <div class="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                  <span class="font-semibold">From:</span> {{ mail.Emetteur }}
                                </div>
                                <div>
                                  <span class="font-semibold">Date:</span> {{ formatDate(mail.Date_Reception) }}
                                </div>
                                <div>
                                  <span class="font-semibold">Subject:</span> {{ mail.Sujet }}
                                </div>
                                <div>
                                  <span class="font-semibold">Status:</span> {{ mail.Statut }}
                                </div>
                              </div>
                            </div>

                            <!-- Corps du mail -->
                            <div class="mb-3">
                              <div class="flex justify-between items-center mb-2">
                                <h3 class="text-sm font-semibold">Email Content</h3>
                                <div class="flex space-x-2">
                                  <button
                                    @click="mail.showRawHtml = !mail.showRawHtml"
                                    class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded"
                                    :class="{'bg-blue-100': mail.showRawHtml}"
                                  >
                                    <i class="pi" :class="mail.showRawHtml ? 'pi-eye' : 'pi-code' "></i>
                                    <span class="ml-1">{{ mail.showRawHtml ? 'Show Rendered' : 'Show Raw HTML' }}</span>
                                  </button>
                                  <button
                                    @click="expandedMailId = null"
                                    class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded"
                                  >
                                    <i class="pi pi-times mr-1"></i> Close
                                  </button>
                                </div>
                              </div>

                              <!-- Contenu interprété (par défaut) -->
                              <div
                                v-if="!mail.showRawHtml"
                                class="email-content bg-white p-3 rounded border relative"
                                @click="preventClicks"
                              >
                                <!-- Indicateur de sécurité -->
                                <div class="bg-red-100 text-red-800 px-3 py-1 mb-3 text-sm rounded flex items-center">
                                  <i class="pi pi-lock mr-1 text-sm"></i>
                                  <span>Secure View: Links and forms are disabled</span>
                                </div>

                                <!-- Contenu HTML rendu de façon sécurisée -->
                                <div v-html="sanitizeHtml(mail.Contenu)"></div>
                              </div>

                              <!-- Contenu brut (option) -->
                              <div v-else class="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border overflow-auto max-h-[400px] font-mono">
                                {{ mail.Contenu || "The content of this email is not available or is empty." }}
                              </div>

                              <!-- Avertissement de sécurité -->
                              <div class="text-xs text-amber-600 mt-1 flex items-center">
                                <i class="pi pi-exclamation-triangle mr-1 text-xs"></i>
                                <span>Warning: This email may contain unsafe content</span>
                              </div>
                            </div>

                            <!-- Pied de page avec action fermer -->
                            <div class="mt-3 flex justify-end">
                              <button
                                @click="expandedMailId = null"
                                class="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs rounded"
                              >
                                <i class="pi pi-times mr-1"></i> Close
                              </button>
                            </div>
                          </div>
                        </div>
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

/* Styles pour le contenu des emails */
.email-content {
  max-height: 500px;
  overflow: auto;
  position: relative; /* Pour le positionnement des éléments enfants */
}

/* Styles de base pour le HTML des emails */
.email-content :deep(table) {
  border-collapse: collapse;
  margin: 0.5rem 0;
}

.email-content :deep(td),
.email-content :deep(th) {
  border: 1px solid #ddd;
  padding: 0.5rem;
}

.email-content :deep(img) {
  max-width: 100%;
  height: auto;
}

.email-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}

/* Styles pour les liens dans le contenu rendu sécurisé */
.email-content :deep(a) {
  color: #3b82f6;
  text-decoration: line-through; /* Barrer les liens pour indiquer qu'ils ne sont pas cliquables */
  cursor: not-allowed;
  pointer-events: all;
  position: relative;
}

/* Ajouter un effet visuel sur survol des liens pour indiquer qu'ils ne sont pas cliquables */
.email-content :deep(a):hover::after {
  content: "⛔ Link disabled";
  position: absolute;
  bottom: 100%;
  left: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 10px;
  white-space: nowrap;
}

/* Désactiver les formulaires et les éléments interactifs */
.email-content :deep(form),
.email-content :deep(button),
.email-content :deep(input),
.email-content :deep(select),
.email-content :deep(textarea) {
  pointer-events: none;
  opacity: 0.7;
  cursor: not-allowed;
}

/* Style pour le conteneur sécurisé */
.secured-email-content {
  position: relative;
}
</style>
