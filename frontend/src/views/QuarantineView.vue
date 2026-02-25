<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/stores/authStore';
import { useRouter } from 'vue-router';
import { useMailTable } from '@/composables/useMailTable';
// Correct import for vue-toastification
import { useToast } from 'vue-toastification';
import MailTableComponent from '@/components/MailTableComponent.vue';
import FileDropZone from '@/components/FileDropZone.vue';
import MistralResponseModal from '@/components/MistralResponseModal.vue';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();

// État pour contrôler la visibilité de la modal de drag & drop
const isUploadModalOpen = ref(false);

// Fonction pour ouvrir/fermer la modal de drag & drop
const openUploadModal = () => {
  isUploadModalOpen.value = true;
};

// Fonction pour fermer la modal de drag & drop
const closeUploadModal = () => {
  isUploadModalOpen.value = false;
};

// Utiliser le composable useMailTable pour la logique de gestion des mails
const {
  loading,
  error,
  expandedMailId,
  selectedMails,
  sortColumn,
  sortDirection,
  sortedMails,
  searchQuery,
  currentPage,
  pageSize,
  totalItems,
  totalPages,
  loadMails,
  toggleSelectAll,
  toggleSelect,
  toggleExpand,
  toggleSort,
  bulkUpdateStatus,
  updateMailStatus,
  updateSearchQuery,
  resetSearch,
  mistralLoading,
  mistralResponse,
  mistralError,
  mistralEmailId,
  askMistral,
  resetMistral,
  setPage
} = useMailTable();

const scanInProgress = ref(false);
const scanProgress = ref(0);
let scanTimer = null;

const startScanProgress = () => {
  if (scanTimer) {
    clearInterval(scanTimer);
  }

  scanInProgress.value = true;
  scanProgress.value = 5;

  scanTimer = setInterval(() => {
    if (scanProgress.value < 95) {
      scanProgress.value += 3;
    }
  }, 900);

  setTimeout(async () => {
    scanProgress.value = 100;
    if (scanTimer) {
      clearInterval(scanTimer);
      scanTimer = null;
    }
    await loadQuarantineMails();
    setTimeout(() => {
      scanInProgress.value = false;
    }, 800);
  }, 30000);
};

// Fonctions spécifiques à la vue Quarantine
const loadQuarantineMails = async () => {
  // Charger les mails avec statut QUARANTINE ou ERROR
  await loadMails('QUARANTINE,ERROR');
};

// Actions spécifiques à la vue Quarantine
const bulkMarkAsSafe = async () => {
  if (selectedMails.value.length === 0) {
    toast.warning('Please select at least one email to mark as safe.');
    return;
  }

  const selectedCount = selectedMails.value.length; // Stocker le nombre avant l'action

  try {
    await bulkUpdateStatus('SAFE');
    toast.success(`${selectedCount} email(s) marked as safe successfully!`);
    // Recharger spécifiquement les mails en quarantaine après la mise à jour
    await loadQuarantineMails();
  } catch (error) {
    toast.error('Failed to mark emails as safe. Please try again.');
    console.error(error);
  }
};

const bulkDelete = async () => {
  if (selectedMails.value.length === 0) {
    toast.warning('Please select at least one email to delete.');
    return;
  }

  const selectedCount = selectedMails.value.length; // Stocker le nombre avant l'action

  if (confirm(`Are you sure you want to delete ${selectedCount} email(s)?`)) {
    try {
      await bulkUpdateStatus('DELETED');
      toast.success(`${selectedCount} email(s) deleted successfully!`);
      // Recharger spécifiquement les mails en quarantaine après la mise à jour
      await loadQuarantineMails();
    } catch (error) {
      toast.error('Failed to delete emails. Please try again.');
      console.error(error);
    }
  }
};

const markAsSafe = async (mailId) => {
  try {
    await updateMailStatus(mailId, 'SAFE');
    toast.success('Email marked as safe successfully!');
    // Recharger spécifiquement les mails en quarantaine après la mise à jour
    await loadQuarantineMails();
  } catch (error) {
    toast.error('Failed to mark email as safe. Please try again.');
    console.error(error);
  }
};

const deleteMail = async (mailId) => {
  if (confirm('Are you sure you want to delete this email?')) {
    try {
      await updateMailStatus(mailId, 'DELETED');
      toast.success('Email deleted successfully!');
      // Recharger spécifiquement les mails en quarantaine après la mise à jour
      await loadQuarantineMails();
    } catch (error) {
      toast.error('Failed to delete email. Please try again.');
      console.error(error);
    }
  }
};

// Méthodes pour la recherche
const handleSearch = (query) => {
  updateSearchQuery(query);
// Ne pas recharger les mails, car cela réinitialise searchQuery
  // Le filtrage est déjà géré par le computed filteredMails dans useMailTable
};

const handleResetSearch = () => {
  resetSearch();
// Pas besoin de recharger les mails ici non plus
};

// Fonction pour gérer les uploads réussis
const handleUploadSuccess = async ({ fileName }) => {
  console.log(`File ${fileName} uploaded successfully`);
  toast.success(`File ${fileName} uploaded. Scan is running in background...`);
  startScanProgress();
};

// Fonction pour gérer les erreurs d'upload
const handleUploadError = ({ fileName, error }) => {
  console.error(`Error uploading ${fileName}:`, error);
  toast.error(`Error uploading ${fileName}: ${error}`);
};

const handleAskMistral = async (mailId) => {
  try {
    await askMistral(mailId);
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: "Impossible to obtain en explanation for this mail",
      life: 3000
    });
    console.error('Error asking Mistral:', error);
  }
};

// Vérifier l'authentification et charger les données au montage
onMounted(async () => {
  authStore.initialize();

  if (authStore.isLoggedIn) {
    try {
      await loadQuarantineMails();
    } catch (error) {
      toast.error('Failed to load quarantined emails. Please refresh the page.');
      console.error(error);
    }
  } else {
    // Rediriger vers login si non connecté
    router.push('/login');
  }
});

onUnmounted(() => {
  if (scanTimer) {
    clearInterval(scanTimer);
    scanTimer = null;
  }
});
</script>

<template>
  <section class="py-4">
    <div class="container mx-auto px-2">
      <div class="max-w-full mx-auto">
        <!-- Section d'upload pour les fichiers eml -->
        <div class="mb-6">
          <div class="flex justify-between items-center mb-2">
            <h2 class="text-lg font-semibold">Upload New Emails for Analysis</h2>
            <button
              @click="openUploadModal"
              class="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 flex items-center"
            >
              <i class="pi pi-upload mr-1"></i>
              Upload Email
            </button>
          </div>

          <p class="text-sm text-gray-500">
            Click the Upload button to analyze new .eml files for potential threats.
          </p>

          <div v-if="scanInProgress" class="mt-3 rounded-md border border-blue-200 bg-blue-50 px-3 py-2">
            <div class="flex justify-between text-xs text-blue-700 mb-1">
              <span>Email scanning in progress</span>
              <span>{{ scanProgress }}%</span>
            </div>
            <div class="h-2 w-full bg-blue-100 rounded">
              <div class="h-2 bg-blue-500 rounded transition-all duration-500" :style="{ width: `${scanProgress}%` }"></div>
            </div>
          </div>

          <!-- Modal de drag & drop -->
          <FileDropZone
            :is-open="isUploadModalOpen"
            :max-size="1000 * 1024 * 1024"
            @upload-success="handleUploadSuccess"
            @upload-error="handleUploadError"
            @close="closeUploadModal"
          /> <!-- 1GB -->
        </div>

        <MailTableComponent
          :mails="sortedMails"
          :loading="loading"
          :error="error"
          :expanded-mail-id="expandedMailId"
          :selected-mails="selectedMails"
          :sort-column="sortColumn"
          :sort-direction="sortDirection"
          :status-types="['QUARANTINE', 'ERROR']"
          :search-query="searchQuery"
          :pagination="{ page: currentPage, limit: pageSize, total: totalItems, totalPages }"
          @toggle-select-all="toggleSelectAll"
          @toggle-select="toggleSelect"
          @toggle-expand="toggleExpand"
          @toggle-sort="toggleSort"
          @refresh="loadQuarantineMails"
          @page-change="setPage"
          @search="handleSearch"
          @reset-search="handleResetSearch"
          @ask-mistral="handleAskMistral"
        >
          <!-- Header slot avec titre personnalisé -->
          <template #header>
            <h1 class="text-3xl font-bold">Quarantine</h1>
          </template>

          <!-- Description slot -->
          <template #description>
            <p class="text-sm text-gray-600 mb-3">
              All emails detected as potentially malicious or containing errors.
            </p>
          </template>

          <!-- Message quand la liste est vide -->
          <template #empty-message>
            The system has not detected any suspicious emails
          </template>

          <!-- Actions en masse -->
          <template #bulk-actions="{ selectedCount }">
            <button
              @click="bulkMarkAsSafe"
              class="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 mr-2 disabled:opacity-50"
              :disabled="selectedCount === 0"
            >
              <i class="pi pi-check mr-1 text-xs"></i> Mark as Safe
            </button>
            <button
              @click="bulkDelete"
              class="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 disabled:opacity-50"
              :disabled="selectedCount === 0"
            >
              <i class="pi pi-trash mr-1 text-xs"></i> Delete
            </button>
          </template>

          <!-- Actions par ligne -->
          <template #row-actions="{ mail }">
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
          </template>
        </MailTableComponent>

        <!-- Modal pour afficher la réponse de Mistral -->
        <MistralResponseModal
          v-if="mistralLoading || mistralResponse || mistralError"
          :loading="mistralLoading"
          :response="mistralResponse"
          :error="mistralError"
          :emailId="mistralEmailId"
          @close="resetMistral"
        />
      </div>
    </div>
  </section>
</template>
